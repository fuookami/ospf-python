//! 非 Send 模型始终在创建线程访问和释放。 / Access and drop the non-Send model only on its creator thread.

use std::collections::BTreeMap;
use std::sync::Arc;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::mpsc::{Sender, channel, sync_channel};

use ospf_rust_core::model::MetaModel;

use crate::failure::Failure;
use crate::projection::ProjectionState;

pub(crate) struct OwnedModel {
    pub(crate) model: MetaModel<f64>,
    pub(crate) generation: u64,
    pub(crate) projections: BTreeMap<u64, ProjectionState>,
    next_projection: u64,
}

// shortcut: 8 MiB 仅覆盖已测见证；待上游非递归比较及调用路径验证后复审。
// shortcut: 8 MiB covers only tested witnesses; reassess after upstream non-recursive
// comparisons and call paths are verified.
const OWNER_STACK_BYTES: usize = 8 * 1024 * 1024;

impl OwnedModel {
    pub(crate) fn insert_projection(
        &mut self,
        projection: ProjectionState,
    ) -> Result<u64, Failure> {
        let id = self.next_projection;
        self.next_projection = id.checked_add(1).ok_or_else(|| {
            Failure::binding("OVERFLOW", "投影身份已耗尽 / Projection identity exhausted")
        })?;
        self.projections.insert(id, projection);
        Ok(id)
    }
}

type Operation = Box<dyn FnOnce(&mut Option<OwnedModel>) + Send>;

pub struct Owner {
    pub identity: u64,
    pub provenance: Arc<u8>,
    sender: Sender<Operation>,
    busy: AtomicBool,
    closed: Arc<AtomicBool>,
}

struct BusyGuard<'a>(&'a AtomicBool);

impl Drop for BusyGuard<'_> {
    fn drop(&mut self) {
        self.0.store(false, Ordering::Release);
    }
}

impl Owner {
    pub fn new(name: String) -> Result<Self, Failure> {
        let (sender, receiver) = channel::<Operation>();
        let (ready, identity) = sync_channel(1);
        std::thread::Builder::new()
            .name("ospf-model-owner".into())
            .stack_size(OWNER_STACK_BYTES)
            .spawn(move || {
                let model = MetaModel::<f64>::new(&name);
                if ready.send(model.model_identity()).is_err() {
                    return;
                }
                let mut state = Some(OwnedModel {
                    model,
                    generation: 0,
                    projections: BTreeMap::new(),
                    next_projection: 0,
                });
                for operation in receiver {
                    operation(&mut state);
                    if state.is_none() {
                        break;
                    }
                }
                // 最后一个 Python 句柄销毁后接收端断开，在本线程释放状态。 / Drop state here after the last handle disconnects.
            })
            .map_err(|error| {
                Failure::binding(
                    "RESOURCE_EXHAUSTED",
                    format!("无法启动模型线程 / Cannot start model owner: {error}"),
                )
            })?;
        let identity = identity.recv().map_err(|_| Self::unavailable())?;
        Ok(Self {
            identity,
            provenance: Arc::new(0),
            sender,
            busy: AtomicBool::new(false),
            closed: Arc::new(AtomicBool::new(false)),
        })
    }

    fn unavailable() -> Failure {
        Failure::binding("UNAVAILABLE", "模型所有者已停止 / Model owner has stopped")
    }

    fn closed_error() -> Failure {
        Failure::binding("NOT_INITIALIZED", "模型已关闭 / Model is closed")
    }

    fn request<T: Send + 'static>(
        &self,
        operation: impl FnOnce(&mut Option<OwnedModel>) -> Result<T, Failure> + Send + 'static,
    ) -> Result<T, Failure> {
        if self.closed.load(Ordering::Acquire) {
            return Err(Self::closed_error());
        }
        self.busy
            .compare_exchange(false, true, Ordering::AcqRel, Ordering::Acquire)
            .map_err(|_| Failure::binding("FAILED_PRECONDITION", "模型忙 / Model is busy"))?;
        let _busy = BusyGuard(&self.busy);
        if self.closed.load(Ordering::Acquire) {
            return Err(Self::closed_error());
        }
        let (reply, response) = sync_channel(1);
        let closed = Arc::clone(&self.closed);
        self.sender
            .send(Box::new(move |state| {
                let result = operation(state);
                if state.is_none() {
                    closed.store(true, Ordering::Release);
                }
                let _ = reply.send(result);
            }))
            .map_err(|_| Self::unavailable())?;
        response.recv().map_err(|_| Self::unavailable())?
    }

    pub fn close(&self) -> Result<(), Failure> {
        if self.closed.load(Ordering::Acquire) {
            return Ok(());
        }
        match self.request(|state| {
            state.take();
            Ok(())
        }) {
            Err(error)
                if error.category == "NOT_INITIALIZED" && self.closed.load(Ordering::Acquire) =>
            {
                Ok(())
            }
            result => result,
        }
    }

    pub(crate) fn with_state<T: Send + 'static>(
        &self,
        operation: impl FnOnce(&mut OwnedModel) -> Result<T, Failure> + Send + 'static,
    ) -> Result<T, Failure> {
        self.request(move |state| operation(state.as_mut().ok_or_else(Self::closed_error)?))
    }

    pub(crate) fn close_projection(&self, id: u64) -> Result<(), Failure> {
        if self.closed.load(Ordering::Acquire) {
            return Ok(());
        }
        match self.with_state(move |state| {
            state.projections.remove(&id);
            Ok(())
        }) {
            Err(error)
                if error.category == "NOT_INITIALIZED" && self.closed.load(Ordering::Acquire) =>
            {
                Ok(())
            }
            result => result,
        }
    }

    pub(crate) fn release_projection(&self, id: u64) {
        // 析构不能等待忙碌的模型线程。 / Destructors must not wait for a busy owner thread.
        let _ = self.sender.send(Box::new(move |state| {
            if let Some(state) = state {
                state.projections.remove(&id);
            }
        }));
    }

    pub fn with_model<T: Send + 'static>(
        &self,
        operation: impl FnOnce(&MetaModel<f64>) -> Result<T, Failure> + Send + 'static,
    ) -> Result<T, Failure> {
        self.with_model_and_generation(move |model, _| operation(model))
    }

    pub fn with_model_and_generation<T: Send + 'static>(
        &self,
        operation: impl FnOnce(&MetaModel<f64>, u64) -> Result<T, Failure> + Send + 'static,
    ) -> Result<T, Failure> {
        self.request(move |state| {
            let state = state.as_ref().ok_or_else(Self::closed_error)?;
            operation(&state.model, state.generation)
        })
    }

    pub fn mutate<T: Send + 'static>(
        &self,
        operation: impl FnOnce(&mut MetaModel<f64>) -> Result<T, Failure> + Send + 'static,
    ) -> Result<T, Failure> {
        self.request(move |state| {
            let state = state.as_mut().ok_or_else(Self::closed_error)?;
            let next = state.generation.checked_add(1).ok_or_else(|| {
                Failure::binding("OVERFLOW", "模型代次已耗尽 / Model generation exhausted")
            })?;
            let value = state.model.transaction(operation)?;
            state.generation = next;
            Ok(value)
        })
    }

    // 仅用于已验证的单步原子更新，批量修改必须使用事务。 / Only for prevalidated atomic steps; batches require a transaction.
    pub fn mutate_prevalidated<P, T: Send + 'static>(
        &self,
        validate: impl FnOnce(&MetaModel<f64>) -> Result<P, Failure> + Send + 'static,
        apply: impl FnOnce(&mut MetaModel<f64>, P) -> Result<T, Failure> + Send + 'static,
    ) -> Result<T, Failure> {
        self.request(move |state| {
            let state = state.as_mut().ok_or_else(Self::closed_error)?;
            let next = state.generation.checked_add(1).ok_or_else(|| {
                Failure::binding("OVERFLOW", "模型代次已耗尽 / Model generation exhausted")
            })?;
            let prepared = validate(&state.model)?;
            let result = apply(&mut state.model, prepared);
            // 提交出错也保守推进代次。 / Advance conservatively even if commit fails.
            state.generation = next;
            result
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use ospf_rust_core::variable::{Continuous, VariableRange};
    use std::sync::Arc;

    #[test]
    fn concurrent_requests_fail_without_waiting_or_mutation() {
        let owner = Arc::new(Owner::new("concurrency".into()).unwrap());
        let (ready, started) = sync_channel(0);
        let (finish, wait) = sync_channel(0);
        let other = Arc::clone(&owner);
        let task = std::thread::spawn(move || {
            other.with_model(move |_| {
                ready.send(()).unwrap();
                wait.recv().unwrap();
                Ok(())
            })
        });
        started.recv().unwrap();
        let error = owner.with_model(|_| Ok(())).unwrap_err();
        assert_eq!(error.category, "FAILED_PRECONDITION");
        finish.send(()).unwrap();
        task.join().unwrap().unwrap();
        assert_eq!(owner.with_model(|model| Ok(model.num_tokens())).unwrap(), 0);
    }

    #[test]
    fn model_and_its_operations_share_the_owner_thread() {
        let caller = std::thread::current().id();
        let owner = Owner::new("thread identity".into()).unwrap();
        let first = owner
            .with_model(|_| Ok(std::thread::current().id()))
            .unwrap();
        let second = owner
            .with_model(|_| Ok(std::thread::current().id()))
            .unwrap();
        assert_ne!(caller, first);
        assert_eq!(first, second);
    }

    #[test]
    fn failed_owner_is_unavailable_and_never_reinitialized() {
        let owner = Owner::new("failed owner".into()).unwrap();
        let identity = owner.identity;
        let error = owner
            .with_model::<()>(|_| panic!("injected owner failure"))
            .unwrap_err();
        assert_eq!(error.category, "UNAVAILABLE");
        assert_eq!(
            owner.with_model(|_| Ok(())).unwrap_err().category,
            "UNAVAILABLE"
        );
        assert_eq!(owner.identity, identity);
    }

    #[test]
    fn closed_owner_remains_closed_and_close_is_idempotent() {
        let owner = Owner::new("closed owner".into()).unwrap();
        owner.close().unwrap();
        assert!(owner.closed.load(Ordering::Acquire));
        assert_eq!(
            owner.with_model(|_| Ok(())).unwrap_err().category,
            "NOT_INITIALIZED"
        );
        owner.close().unwrap();
    }

    #[test]
    fn failed_mutation_rolls_back_model_and_generation() {
        let owner = Owner::new("generation rollback".into()).unwrap();
        owner
            .mutate(|model| {
                model
                    .register_auto_variable_with_range::<Continuous>(
                        "x",
                        VariableRange::bounded(0.0, 3.0),
                    )
                    .map_err(Failure::from)?;
                Ok(())
            })
            .unwrap();
        let error = owner
            .mutate::<()>(|model| {
                model
                    .set_variable_range_by_index(0, VariableRange::fixed(1.0))
                    .map_err(Failure::from)?;
                model
                    .register_auto_variable::<Continuous>("temporary")
                    .map_err(Failure::from)?;
                Err(Failure::input("事务失败 / Transaction failed"))
            })
            .unwrap_err();
        assert_eq!(error.category, "ILLEGAL_ARGUMENT");
        owner
            .with_model_and_generation(|model, generation| {
                assert_eq!(generation, 1);
                assert_eq!(model.num_tokens(), 1);
                assert_eq!(
                    model.variable_range_by_index(0),
                    Some(VariableRange::bounded(0.0, 3.0))
                );
                Ok(())
            })
            .unwrap();
    }

    #[test]
    fn generation_overflow_rejects_mutation_before_calling_it() {
        let owner = Owner::new("generation overflow".into()).unwrap();
        owner
            .request(|state| {
                state.as_mut().unwrap().generation = u64::MAX - 1;
                Ok(())
            })
            .unwrap();
        owner.mutate(|_| Ok(())).unwrap();
        let called = Arc::new(AtomicBool::new(false));
        let flag = Arc::clone(&called);
        let error = owner
            .mutate(move |model| {
                flag.store(true, Ordering::Release);
                model
                    .register_auto_variable::<Continuous>("never")
                    .map_err(Failure::from)?;
                Ok(())
            })
            .unwrap_err();
        assert_eq!(error.category, "OVERFLOW");
        assert!(!called.load(Ordering::Acquire));
        let flag = Arc::clone(&called);
        let error = owner
            .mutate_prevalidated(
                move |_| {
                    flag.store(true, Ordering::Release);
                    Ok(())
                },
                |_, ()| Ok(()),
            )
            .unwrap_err();
        assert_eq!(error.category, "OVERFLOW");
        assert!(!called.load(Ordering::Acquire));
        assert_eq!(
            owner
                .with_model_and_generation(|model, generation| Ok((model.num_tokens(), generation)))
                .unwrap(),
            (0, u64::MAX)
        );
    }

    #[test]
    fn projection_identity_overflow_does_not_publish_a_projection() {
        use ospf_rust_framework::solver::column_projection::ColumnProjection;
        use std::collections::BTreeSet;

        let owner = Owner::new("projection identity overflow".into()).unwrap();
        owner
            .with_state(|state| {
                state.next_projection = u64::MAX;
                let projection =
                    ColumnProjection::new(&state.model, vec![], BTreeSet::from(["block".into()]))
                        .map_err(Failure::from)?;
                let error = state
                    .insert_projection(ProjectionState::new(projection, BTreeMap::new()))
                    .unwrap_err();
                assert_eq!(error.category, "OVERFLOW");
                assert!(state.projections.is_empty());
                Ok(())
            })
            .unwrap();
    }

    #[test]
    fn prevalidated_updates_reject_before_writing_and_invalidate_after_commit_error() {
        let owner = Owner::new("prevalidated update".into()).unwrap();
        owner
            .mutate(|model| {
                model
                    .register_auto_variable_with_range::<Continuous>(
                        "x",
                        VariableRange::bounded(0.0, 3.0),
                    )
                    .map_err(Failure::from)?;
                Ok(())
            })
            .unwrap();
        let called = Arc::new(AtomicBool::new(false));
        let flag = Arc::clone(&called);
        let error = owner
            .mutate_prevalidated::<(), ()>(
                |_| Err(Failure::input("校验失败 / Validation failed")),
                move |_, ()| {
                    flag.store(true, Ordering::Release);
                    Ok(())
                },
            )
            .unwrap_err();
        assert_eq!(error.category, "ILLEGAL_ARGUMENT");
        assert!(!called.load(Ordering::Acquire));
        assert_eq!(owner.with_model_and_generation(|_, g| Ok(g)).unwrap(), 1);

        let error = owner
            .mutate_prevalidated::<_, ()>(
                |_| Ok(VariableRange::fixed(1.0)),
                |model, range| {
                    model
                        .set_variable_range_by_index(0, range)
                        .map_err(Failure::from)?;
                    Err(Failure::input("提交失败 / Commit failed"))
                },
            )
            .unwrap_err();
        assert_eq!(error.category, "ILLEGAL_ARGUMENT");
        assert_eq!(
            owner
                .with_model_and_generation(|model, generation| {
                    Ok((model.variable_range_by_index(0), generation))
                })
                .unwrap(),
            (Some(VariableRange::fixed(1.0)), 2)
        );
    }
}
