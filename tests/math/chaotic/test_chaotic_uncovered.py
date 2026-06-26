"""未覆盖混沌系统测试。

Tests for chaotic systems at 0% coverage.
Covers tuple-based and NDArray-based chaotic attractors,
maps, and ODE systems.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

# -- Tuple-based 3D continuous systems --


class TestLorenzSystem:
    """Lorenz 系统测试。/ Lorenz system tests."""

    def test_call_returns_3tuple(self) -> None:
        """__call__ 返回 3 元组。/ __call__ returns 3-tuple."""
        from ospf_python.math.chaotic.lorenz_system import LorenzSystem

        s = LorenzSystem()
        result = s((1.0, 1.0, 1.0))
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert all(math.isfinite(v) for v in result)

    def test_iterate_finite(self) -> None:
        """迭代 50 步结果有限。/ Iterate 50 steps finite."""
        from ospf_python.math.chaotic.lorenz_system import LorenzSystem

        s = LorenzSystem()
        result = s.iterate((1.0, 1.0, 1.0), n=50)
        assert len(result) == 3
        assert all(math.isfinite(v) for v in result)

    def test_frozen(self) -> None:
        """frozen dataclass 属性不可变。/ frozen dataclass."""
        from ospf_python.math.chaotic.lorenz_system import LorenzSystem

        s = LorenzSystem(sigma=5.0)
        assert s.sigma == 5.0
        with pytest.raises(AttributeError):
            s.sigma = 10.0  # type: ignore[misc]


class TestLorenz84Model:
    """Lorenz-84 模型测试。/ Lorenz-84 model tests."""

    def test_call_returns_3tuple(self) -> None:
        from ospf_python.math.chaotic.lorenz84_model import Lorenz84Model

        m = Lorenz84Model()
        result = m((1.0, 1.0, 1.0))
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert all(math.isfinite(v) for v in result)

    def test_iterate_finite(self) -> None:
        from ospf_python.math.chaotic.lorenz84_model import Lorenz84Model

        m = Lorenz84Model()
        result = m.iterate((1.0, 1.0, 1.0), n=50)
        assert all(math.isfinite(v) for v in result)


class TestLorenz96Model:
    """Lorenz-96 模型测试。/ Lorenz-96 model tests."""

    def test_call_returns_tuple(self) -> None:
        from ospf_python.math.chaotic.lorenz96_model import Lorenz96Model

        m = Lorenz96Model(n=5)
        state = tuple([1.0] * 5)
        result = m(state)
        assert isinstance(result, tuple)
        assert len(result) == 5

    def test_iterate_finite(self) -> None:
        from ospf_python.math.chaotic.lorenz96_model import Lorenz96Model

        m = Lorenz96Model(n=4)
        state = tuple([1.0] * 4)
        result = m.iterate(state, n=20)
        assert all(math.isfinite(v) for v in result)


class TestLorenzMod1Attractor:
    """Lorenz Mod-1 吸引子测试。/ Lorenz Mod-1 tests."""

    def test_call_returns_3tuple(self) -> None:
        from ospf_python.math.chaotic.lorenz_mod1_attractor import (
            LorenzMod1Attractor,
        )

        m = LorenzMod1Attractor()
        result = m((1.0, 1.0, 1.0))
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert all(math.isfinite(v) for v in result)

    def test_iterate_finite(self) -> None:
        from ospf_python.math.chaotic.lorenz_mod1_attractor import (
            LorenzMod1Attractor,
        )

        m = LorenzMod1Attractor()
        result = m.iterate((1.0, 1.0, 1.0), n=30)
        assert all(math.isfinite(v) for v in result)


class TestLorenzMod2Attractor:
    """Lorenz Mod-2 吸引子测试。/ Lorenz Mod-2 tests."""

    def test_call_returns_3tuple(self) -> None:
        from ospf_python.math.chaotic.lorenz_mod2_attractor import (
            LorenzMod2Attractor,
        )

        m = LorenzMod2Attractor()
        result = m((1.0, 1.0, 1.0))
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert all(math.isfinite(v) for v in result)

    def test_iterate_finite(self) -> None:
        from ospf_python.math.chaotic.lorenz_mod2_attractor import (
            LorenzMod2Attractor,
        )

        m = LorenzMod2Attractor()
        result = m.iterate((1.0, 1.0, 1.0), n=30)
        assert all(math.isfinite(v) for v in result)


class TestLorenzStenfloAttractor:
    """Lorenz-Stenflo 吸引子测试。/ Lorenz-Stenflo tests."""

    def test_call_returns_4tuple(self) -> None:
        from ospf_python.math.chaotic.lorenz_stenflo_attractor import (
            LorenzStenfloAttractor,
        )

        m = LorenzStenfloAttractor()
        result = m((1.0, 1.0, 1.0, 1.0))
        assert isinstance(result, tuple)
        assert len(result) == 4
        assert all(math.isfinite(v) for v in result)

    def test_iterate_finite(self) -> None:
        from ospf_python.math.chaotic.lorenz_stenflo_attractor import (
            LorenzStenfloAttractor,
        )

        m = LorenzStenfloAttractor()
        result = m.iterate((1.0, 1.0, 1.0, 1.0), n=30)
        assert len(result) == 4
        assert all(math.isfinite(v) for v in result)


class TestLiuChenAttractor:
    """Liu-Chen 吸引子测试。/ Liu-Chen attractor tests."""

    def test_call_returns_3tuple(self) -> None:
        from ospf_python.math.chaotic.liu_chen_attractor import (
            LiuChenAttractor,
        )

        m = LiuChenAttractor()
        result = m((1.0, 1.0, 1.0))
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert all(math.isfinite(v) for v in result)

    def test_iterate_finite(self) -> None:
        from ospf_python.math.chaotic.liu_chen_attractor import (
            LiuChenAttractor,
        )

        m = LiuChenAttractor()
        result = m.iterate((1.0, 1.0, 1.0), n=30)
        assert all(math.isfinite(v) for v in result)


class TestLuChenAttractor:
    """Lu-Chen 吸引子测试。/ Lu-Chen attractor tests."""

    def test_call_returns_3tuple(self) -> None:
        from ospf_python.math.chaotic.lu_chen_attractor import (
            LuChenAttractor,
        )

        m = LuChenAttractor()
        result = m((1.0, 1.0, 1.0))
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert all(math.isfinite(v) for v in result)

    def test_iterate_finite(self) -> None:
        from ospf_python.math.chaotic.lu_chen_attractor import (
            LuChenAttractor,
        )

        m = LuChenAttractor()
        result = m.iterate((1.0, 1.0, 1.0), n=30)
        assert all(math.isfinite(v) for v in result)


class TestLuChenSystem:
    """Lu-Chen 系统测试。/ Lu-Chen system tests."""

    def test_call_returns_3tuple(self) -> None:
        from ospf_python.math.chaotic.lu_chen_system import LuChenSystem

        m = LuChenSystem()
        result = m((1.0, 1.0, 1.0))
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert all(math.isfinite(v) for v in result)

    def test_iterate_finite(self) -> None:
        from ospf_python.math.chaotic.lu_chen_system import LuChenSystem

        m = LuChenSystem()
        result = m.iterate((1.0, 1.0, 1.0), n=30)
        assert all(math.isfinite(v) for v in result)


class TestNewtonLeipnikAttractor:
    """Newton-Leipnik 吸引子测试。/ Newton-Leipnik tests."""

    def test_call_returns_3tuple(self) -> None:
        from ospf_python.math.chaotic.newton_leipnik_attractor import (
            NewtonLeipnikAttractor,
        )

        m = NewtonLeipnikAttractor()
        result = m((0.1, -0.1, 0.1))
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert all(math.isfinite(v) for v in result)

    def test_iterate_finite(self) -> None:
        from ospf_python.math.chaotic.newton_leipnik_attractor import (
            NewtonLeipnikAttractor,
        )

        m = NewtonLeipnikAttractor()
        result = m.iterate((0.1, -0.1, 0.1), n=20)
        assert all(math.isfinite(v) for v in result)


class TestNoseHooverAttractor:
    """Nose-Hoover 吸引子测试。/ Nose-Hoover tests."""

    def test_call_returns_3tuple(self) -> None:
        from ospf_python.math.chaotic.nose_hoover_attractor import (
            NoseHooverAttractor,
        )

        m = NoseHooverAttractor()
        result = m((1.0, 1.0, 0.0))
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert all(math.isfinite(v) for v in result)

    def test_iterate_finite(self) -> None:
        from ospf_python.math.chaotic.nose_hoover_attractor import (
            NoseHooverAttractor,
        )

        m = NoseHooverAttractor()
        result = m.iterate((1.0, 1.0, 0.0), n=30)
        assert all(math.isfinite(v) for v in result)


class TestQiAttractor:
    """Qi 吸引子测试。/ Qi attractor tests."""

    def test_call_returns_3tuple(self) -> None:
        from ospf_python.math.chaotic.qi_attractor import QiAttractor

        m = QiAttractor()
        result = m((1.0, 1.0, 1.0))
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert all(math.isfinite(v) for v in result)

    def test_iterate_finite(self) -> None:
        from ospf_python.math.chaotic.qi_attractor import QiAttractor

        m = QiAttractor()
        result = m.iterate((1.0, 1.0, 1.0), n=20)
        assert all(math.isfinite(v) for v in result)


# -- Tuple-based 1D/2D discrete maps --


class TestComplexQuadraticPolynomial:
    """复二次多项式测试。/ Complex quadratic polynomial tests."""

    def test_call_returns_float(self) -> None:
        from ospf_python.math.chaotic.complex_quadratic_polynomial import (
            ComplexQuadraticPolynomial,
        )

        m = ComplexQuadraticPolynomial()
        result = m(0.5)
        assert isinstance(result, float)
        assert math.isfinite(result)

    def test_iterate_returns_list(self) -> None:
        from ospf_python.math.chaotic.complex_quadratic_polynomial import (
            ComplexQuadraticPolynomial,
        )

        m = ComplexQuadraticPolynomial()
        result = m.iterate(0.5, n=10)
        assert isinstance(result, list)
        assert len(result) == 11
        assert all(math.isfinite(v) for v in result)

    def test_iterate_complex_returns_pairs(self) -> None:
        from ospf_python.math.chaotic.complex_quadratic_polynomial import (
            ComplexQuadraticPolynomial,
        )

        m = ComplexQuadraticPolynomial()
        result = m.iterate_complex(0.1, 0.1, n=5)
        assert isinstance(result, list)
        assert len(result) == 6
        for pair in result:
            assert isinstance(pair, tuple)
            assert len(pair) == 2

    def test_frozen(self) -> None:
        from ospf_python.math.chaotic.complex_quadratic_polynomial import (
            ComplexQuadraticPolynomial,
        )

        m = ComplexQuadraticPolynomial(c=-0.8)
        assert m.c == -0.8
        with pytest.raises(AttributeError):
            m.c = 0.0  # type: ignore[misc]


class TestMartinIterate:
    """Martin 迭代测试。/ Martin iterate tests."""

    def test_call_returns_float(self) -> None:
        from ospf_python.math.chaotic.martin_iterate import MartinIterate

        m = MartinIterate()
        result = m(0.5)
        assert isinstance(result, float)
        assert math.isfinite(result)

    def test_iterate_returns_float(self) -> None:
        """iterate 返回最终浮点值。/ iterate returns final float."""
        from ospf_python.math.chaotic.martin_iterate import MartinIterate

        m = MartinIterate()
        result = m.iterate(0.5, n=10)
        assert isinstance(result, float)
        assert math.isfinite(result)


class TestNewtonIterate:
    """Newton 迭代法测试。/ Newton iterate tests."""

    def test_call_returns_complex(self) -> None:
        from ospf_python.math.chaotic.newton_iterate import NewtonIterate

        m = NewtonIterate()
        result = m(complex(0.5, 0.5))
        assert isinstance(result, complex)

    def test_iterate_returns_complex(self) -> None:
        from ospf_python.math.chaotic.newton_iterate import NewtonIterate

        m = NewtonIterate()
        result = m.iterate(complex(0.5, 0.5), n=50)
        assert isinstance(result, complex)

    def test_frozen(self) -> None:
        from ospf_python.math.chaotic.newton_iterate import NewtonIterate

        m = NewtonIterate(power=5)
        assert m.power == 5
        with pytest.raises(AttributeError):
            m.power = 3  # type: ignore[misc]


class TestKaplanYorkeMap:
    """Kaplan-Yorke 映射测试。/ Kaplan-Yorke map tests."""

    def test_call_returns_2tuple(self) -> None:
        from ospf_python.math.chaotic.kaplan_yorke_map import KaplanYorkeMap

        m = KaplanYorkeMap()
        result = m((0.3, 0.7))
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert all(math.isfinite(v) for v in result)

    def test_iterate_returns_2tuple(self) -> None:
        from ospf_python.math.chaotic.kaplan_yorke_map import KaplanYorkeMap

        m = KaplanYorkeMap()
        result = m.iterate((0.3, 0.7), n=10)
        assert len(result) == 2
        assert all(math.isfinite(v) for v in result)


class TestKickedRotator:
    """受击转子测试。/ Kicked rotator tests."""

    def test_call_returns_2tuple(self) -> None:
        from ospf_python.math.chaotic.kicked_rotator import KickedRotator

        m = KickedRotator()
        result = m((0.5, 0.3))
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert all(math.isfinite(v) for v in result)

    def test_iterate_returns_2tuple(self) -> None:
        from ospf_python.math.chaotic.kicked_rotator import KickedRotator

        m = KickedRotator()
        result = m.iterate((0.5, 0.3), n=10)
        assert len(result) == 2


class TestLoziMap:
    """Lozi 映射测试。/ Lozi map tests."""

    def test_call_returns_2tuple(self) -> None:
        from ospf_python.math.chaotic.lozi_map import LoziMap

        m = LoziMap()
        result = m((0.1, 0.2))
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert all(math.isfinite(v) for v in result)

    def test_iterate_returns_2tuple(self) -> None:
        from ospf_python.math.chaotic.lozi_map import LoziMap

        m = LoziMap()
        result = m.iterate((0.1, 0.2), n=10)
        assert len(result) == 2


# -- NBodySystem --


class TestNBodySystem:
    """N 体引力系统测试。/ N-body system tests."""

    def test_call_2body(self) -> None:
        from ospf_python.math.chaotic.n_body_system import NBodySystem

        m = NBodySystem(n_bodies=2)
        state = (0.0, 0.0, 0.1, 0.0, 1.0, 0.0, 0.0, 0.1)
        result = m(state)
        assert isinstance(result, tuple)
        assert len(result) == 8
        assert all(math.isfinite(v) for v in result)

    def test_call_3body(self) -> None:
        from ospf_python.math.chaotic.n_body_system import NBodySystem

        m = NBodySystem(n_bodies=3)
        state = (
            0.0,
            0.0,
            0.1,
            0.0,
            1.0,
            0.0,
            0.0,
            0.1,
            0.0,
            1.0,
            -0.1,
            0.0,
        )
        result = m(state)
        assert isinstance(result, tuple)
        assert len(result) == 12
        assert all(math.isfinite(v) for v in result)

    def test_iterate_finite(self) -> None:
        from ospf_python.math.chaotic.n_body_system import NBodySystem

        m = NBodySystem(n_bodies=2)
        state = (0.0, 0.0, 0.5, 0.0, 1.0, 0.0, 0.0, 0.5)
        result = m.iterate(state, n=10)
        assert all(math.isfinite(v) for v in result)

    def test_frozen(self) -> None:
        from ospf_python.math.chaotic.n_body_system import NBodySystem

        m = NBodySystem(n_bodies=2, G=2.0)
        assert m.G == 2.0
        with pytest.raises(AttributeError):
            m.G = 1.0  # type: ignore[misc]


# -- NDArray-based 3D systems --


class TestAizawaAttractor:
    """Aizawa 吸引子测试。/ Aizawa attractor tests."""

    def test_call_returns_ndarray(self) -> None:
        from ospf_python.math.chaotic.aizawa_attractor import AizawaAttractor

        m = AizawaAttractor()
        x = np.array([1.0, 1.0, 1.0])
        result = m(x)
        assert isinstance(result, np.ndarray)
        assert result.shape == (3,)
        assert np.all(np.isfinite(result))

    def test_iterate_returns_list(self) -> None:
        from ospf_python.math.chaotic.aizawa_attractor import AizawaAttractor

        m = AizawaAttractor()
        x = np.array([1.0, 1.0, 1.0])
        result = m.iterate(x, n=10)
        assert isinstance(result, list)
        assert len(result) == 11
        assert all(np.all(np.isfinite(s)) for s in result)


class TestChenSystem:
    """Chen 系统测试。/ Chen system tests."""

    def test_call_returns_ndarray(self) -> None:
        from ospf_python.math.chaotic.chen_system import ChenSystem

        m = ChenSystem()
        x = np.array([1.0, 1.0, 1.0])
        result = m(x)
        assert isinstance(result, np.ndarray)
        assert result.shape == (3,)
        assert np.all(np.isfinite(result))

    def test_iterate_returns_list(self) -> None:
        from ospf_python.math.chaotic.chen_system import ChenSystem

        m = ChenSystem()
        x = np.array([1.0, 1.0, 1.0])
        result = m.iterate(x, n=10)
        assert isinstance(result, list)
        assert len(result) == 11


class TestChuaAttractor:
    """蔡氏吸引子测试。/ Chua attractor tests."""

    def test_call_returns_ndarray(self) -> None:
        from ospf_python.math.chaotic.chua_attractor import ChuaAttractor

        m = ChuaAttractor()
        x = np.array([0.1, 0.2, 0.1])
        result = m(x)
        assert isinstance(result, np.ndarray)
        assert result.shape == (3,)
        assert np.all(np.isfinite(result))

    def test_iterate_returns_list(self) -> None:
        from ospf_python.math.chaotic.chua_attractor import ChuaAttractor

        m = ChuaAttractor()
        x = np.array([0.1, 0.2, 0.1])
        result = m.iterate(x, n=10)
        assert isinstance(result, list)
        assert len(result) == 11


class TestChuaCircuit:
    """蔡氏电路测试。/ Chua circuit tests."""

    def test_call_returns_ndarray(self) -> None:
        from ospf_python.math.chaotic.chua_circuit import ChuaCircuit

        m = ChuaCircuit()
        x = np.array([0.1, 0.0, 0.0])
        result = m(x)
        assert isinstance(result, np.ndarray)
        assert np.all(np.isfinite(result))

    def test_iterate_returns_list(self) -> None:
        from ospf_python.math.chaotic.chua_circuit import ChuaCircuit

        m = ChuaCircuit()
        x = np.array([0.1, 0.0, 0.0])
        result = m.iterate(x, n=10)
        assert isinstance(result, list)
        assert len(result) == 11


class TestChuasCircuit:
    """Chua 电路变体测试。/ Chua's circuit variant tests."""

    def test_call_returns_ndarray(self) -> None:
        from ospf_python.math.chaotic.chuas_circuit import ChuasCircuit

        m = ChuasCircuit()
        x = np.array([0.1, 0.0, 0.0])
        result = m(x)
        assert isinstance(result, np.ndarray)
        assert np.all(np.isfinite(result))

    def test_iterate_returns_list(self) -> None:
        from ospf_python.math.chaotic.chuas_circuit import ChuasCircuit

        m = ChuasCircuit()
        x = np.array([0.1, 0.0, 0.0])
        result = m.iterate(x, n=10)
        assert isinstance(result, list)
        assert len(result) == 11


class TestCircuitChaotic:
    """电路混沌模型测试。/ Circuit chaotic model tests."""

    def test_call_returns_ndarray(self) -> None:
        from ospf_python.math.chaotic.circuit_chaotic import CircuitChaotic

        m = CircuitChaotic()
        x = np.array([0.1, 0.0, 0.0])
        result = m(x)
        assert isinstance(result, np.ndarray)
        assert np.all(np.isfinite(result))

    def test_iterate_returns_list(self) -> None:
        from ospf_python.math.chaotic.circuit_chaotic import CircuitChaotic

        m = CircuitChaotic()
        x = np.array([0.1, 0.0, 0.0])
        result = m.iterate(x, n=10)
        assert isinstance(result, list)
        assert len(result) == 11


class TestBogdanovMap:
    """Bogdanov 映射测试。/ Bogdanov map tests."""

    def test_call_returns_ndarray(self) -> None:
        from ospf_python.math.chaotic.bogdanov_map import BogdanovMap

        m = BogdanovMap()
        x = np.array([0.1, 0.1])
        result = m(x)
        assert isinstance(result, np.ndarray)
        assert result.shape == (2,)
        assert np.all(np.isfinite(result))

    def test_iterate_returns_list(self) -> None:
        from ospf_python.math.chaotic.bogdanov_map import BogdanovMap

        m = BogdanovMap()
        x = np.array([0.1, 0.1])
        result = m.iterate(x, n=10)
        assert isinstance(result, list)
        assert len(result) == 11


class TestBoualiAttractor:
    """Bouali 吸引子测试。/ Bouali attractor tests."""

    def test_call_returns_ndarray(self) -> None:
        from ospf_python.math.chaotic.bouali_attractor import BoualiAttractor

        m = BoualiAttractor()
        x = np.array([1.0, 1.0, 0.0])
        result = m(x)
        assert isinstance(result, np.ndarray)
        assert result.shape == (3,)
        assert np.all(np.isfinite(result))

    def test_iterate_returns_list(self) -> None:
        from ospf_python.math.chaotic.bouali_attractor import BoualiAttractor

        m = BoualiAttractor()
        x = np.array([1.0, 1.0, 0.0])
        result = m.iterate(x, n=10)
        assert isinstance(result, list)
        assert len(result) == 11


class TestBurkeShawAttractor:
    """Burke-Shaw 吸引子测试。/ Burke-Shaw attractor tests."""

    def test_call_returns_ndarray(self) -> None:
        from ospf_python.math.chaotic.burke_shaw_attractor import (
            BurkeShawAttractor,
        )

        m = BurkeShawAttractor()
        x = np.array([1.0, 0.0, 0.0])
        result = m(x)
        assert isinstance(result, np.ndarray)
        assert result.shape == (3,)
        assert np.all(np.isfinite(result))

    def test_iterate_returns_list(self) -> None:
        from ospf_python.math.chaotic.burke_shaw_attractor import (
            BurkeShawAttractor,
        )

        m = BurkeShawAttractor()
        x = np.array([1.0, 0.0, 0.0])
        result = m.iterate(x, n=10)
        assert isinstance(result, list)
        assert len(result) == 11


class TestArneodoAttractor:
    """Arneodo 吸引子测试。/ Arneodo attractor tests."""

    def test_call_returns_ndarray(self) -> None:
        from ospf_python.math.chaotic.arneodo_attractor import ArneodoAttractor

        m = ArneodoAttractor()
        x = np.array([1.0, 1.0, 1.0])
        result = m(x)
        assert isinstance(result, np.ndarray)
        assert result.shape == (3,)
        assert np.all(np.isfinite(result))

    def test_iterate_returns_list(self) -> None:
        from ospf_python.math.chaotic.arneodo_attractor import ArneodoAttractor

        m = ArneodoAttractor()
        x = np.array([1.0, 1.0, 1.0])
        result = m.iterate(x, n=10)
        assert isinstance(result, list)
        assert len(result) == 11


class TestArnoldsCatMap:
    """Arnold 猫映射测试。/ Arnold's cat map tests."""

    def test_call_returns_ndarray(self) -> None:
        from ospf_python.math.chaotic.arnolds_cat_map import ArnoldsCatMap

        m = ArnoldsCatMap()
        x = np.array([0.3, 0.7])
        result = m(x)
        assert isinstance(result, np.ndarray)
        assert result.shape == (2,)
        assert np.all(np.isfinite(result))

    def test_iterate_returns_list(self) -> None:
        from ospf_python.math.chaotic.arnolds_cat_map import ArnoldsCatMap

        m = ArnoldsCatMap()
        x = np.array([0.3, 0.7])
        result = m.iterate(x, n=10)
        assert isinstance(result, list)
        assert len(result) == 11


class TestAnishchenkoAstakhovAttractor:
    """Anishchenko-Astakhov 吸引子测试。/ AA attractor tests."""

    def test_call_returns_ndarray(self) -> None:
        from ospf_python.math.chaotic.anishchenko_astakhov_attractor import (
            AnishchenkoAstakhovAttractor,
        )

        m = AnishchenkoAstakhovAttractor()
        x = np.array([1.0, 1.0, 1.0])
        result = m(x)
        assert isinstance(result, np.ndarray)
        assert result.shape == (3,)
        assert np.all(np.isfinite(result))

    def test_iterate_returns_list(self) -> None:
        from ospf_python.math.chaotic.anishchenko_astakhov_attractor import (
            AnishchenkoAstakhovAttractor,
        )

        m = AnishchenkoAstakhovAttractor()
        x = np.array([1.0, 1.0, 1.0])
        result = m.iterate(x, n=10)
        assert isinstance(result, list)
        assert len(result) == 11


class TestChenCelikovskyAttractor:
    """Chen-Celikovsky 吸引子测试。/ Chen-Celikovsky tests."""

    def test_call_returns_ndarray(self) -> None:
        from ospf_python.math.chaotic.chen_celikovsky_attractor import (
            ChenCelikovskyAttractor,
        )

        m = ChenCelikovskyAttractor()
        x = np.array([1.0, 1.0, 1.0])
        result = m(x)
        assert isinstance(result, np.ndarray)
        assert result.shape == (3,)
        assert np.all(np.isfinite(result))

    def test_iterate_returns_list(self) -> None:
        from ospf_python.math.chaotic.chen_celikovsky_attractor import (
            ChenCelikovskyAttractor,
        )

        m = ChenCelikovskyAttractor()
        x = np.array([1.0, 1.0, 1.0])
        result = m.iterate(x, n=10)
        assert isinstance(result, list)
        assert len(result) == 11


class TestChenLeeAttractor:
    """Chen-Lee 吸引子测试。/ Chen-Lee attractor tests."""

    def test_call_returns_ndarray(self) -> None:
        from ospf_python.math.chaotic.chen_lee_attractor import ChenLeeAttractor

        m = ChenLeeAttractor()
        x = np.array([1.0, 1.0, 1.0])
        result = m(x)
        assert isinstance(result, np.ndarray)
        assert result.shape == (3,)
        assert np.all(np.isfinite(result))

    def test_iterate_returns_list(self) -> None:
        from ospf_python.math.chaotic.chen_lee_attractor import ChenLeeAttractor

        m = ChenLeeAttractor()
        x = np.array([1.0, 1.0, 1.0])
        result = m.iterate(x, n=10)
        assert isinstance(result, list)
        assert len(result) == 11


class TestCapacitanceEquation:
    """电容方程测试。/ Capacitance equation tests."""

    def test_call_returns_float(self) -> None:
        """__call__ 返回有限浮点数。/ __call__ returns finite float."""
        from ospf_python.math.chaotic.capacitance_equation import (
            CapacitanceEquation,
        )

        m = CapacitanceEquation()
        result = m(0.5)
        assert isinstance(result, float)
        assert math.isfinite(result)

    def test_iterate_returns_list(self) -> None:
        """iterate 返回列表。/ iterate returns list."""
        from ospf_python.math.chaotic.capacitance_equation import (
            CapacitanceEquation,
        )

        m = CapacitanceEquation()
        result = m.iterate(0.5, n=10)
        assert isinstance(result, list)
        assert len(result) == 11
        assert all(math.isfinite(v) for v in result)


class TestIntervalExchangeTransformation:
    """区间交换变换测试。/ Interval exchange tests."""

    def test_call_returns_float(self) -> None:
        """__call__ 返回浮点数。/ __call__ returns float."""
        from ospf_python.math.chaotic.interval_exchange_transformation import (
            IntervalExchangeTransformation,
        )

        m = IntervalExchangeTransformation()
        result = m(0.5)
        assert isinstance(result, float)
        assert math.isfinite(result)

    def test_iterate_returns_float(self) -> None:
        """iterate 返回最终浮点值。/ iterate returns final float."""
        from ospf_python.math.chaotic.interval_exchange_transformation import (
            IntervalExchangeTransformation,
        )

        m = IntervalExchangeTransformation()
        result = m.iterate(0.5, n=10)
        assert isinstance(result, float)
        assert math.isfinite(result)


class TestBiologyChaoticModel:
    """生物混沌模型测试。/ Biology chaotic model tests."""

    def test_call_returns_float(self) -> None:
        """__call__ 返回浮点数。/ __call__ returns float."""
        from ospf_python.math.chaotic.biology_chaotic_model import (
            BiologyChaoticModel,
        )

        m = BiologyChaoticModel()
        result = m(0.5)
        assert isinstance(result, float)
        assert math.isfinite(result)

    def test_iterate_returns_list(self) -> None:
        """iterate 返回列表。/ iterate returns list."""
        from ospf_python.math.chaotic.biology_chaotic_model import (
            BiologyChaoticModel,
        )

        m = BiologyChaoticModel()
        result = m.iterate(0.5, n=10)
        assert isinstance(result, list)
        assert all(math.isfinite(v) for v in result)
