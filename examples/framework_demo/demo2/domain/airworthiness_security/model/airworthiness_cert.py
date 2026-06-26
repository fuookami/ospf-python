"""适航证书定义 / Airworthiness certificate definition.

定义飞机适航证书信息。
Defines the airworthiness certificate information of an aircraft.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class AirworthinessCert:
    """适航证书 / Airworthiness certificate.

    描述飞机的适航证书信息，用于验证飞机是否具备
    合法的适航资格。
    Describes the airworthiness certificate information of an
    aircraft, used to verify whether the aircraft has valid
    airworthiness qualification.

    Attributes:
        cert_id: 证书编号 / Certificate identifier.
        aircraft_type: 适用机型 / Applicable aircraft type.
        valid_until: 有效期截止日 / Expiry date.
    """

    cert_id: str
    aircraft_type: str
    valid_until: date

    @staticmethod
    def create(
        *,
        cert_id: str,
        aircraft_type: str,
        valid_until: date,
    ) -> AirworthinessCert:
        """创建适航证书 / Create airworthiness certificate.

        Args:
            cert_id: 证书编号 / Certificate identifier.
            aircraft_type: 适用机型 / Applicable aircraft type.
            valid_until: 有效期截止日 / Expiry date.

        Returns:
            适航证书实例 / AirworthinessCert instance.
        """
        return AirworthinessCert(
            cert_id=cert_id,
            aircraft_type=aircraft_type,
            valid_until=valid_until,
        )

    def is_valid_on(self, check_date: date) -> bool:
        """检查在指定日期是否有效。

        Check whether the certificate is valid on the
        given date.

        Args:
            check_date: 待检查日期。/ Date to check.

        Returns:
            若检查日期不晚于有效期截止日则返回 True。
            True if check date is not after the expiry date.
        """
        return check_date <= self.valid_until

    def is_valid(self) -> bool:
        """检查当前是否有效 / Check current validity.

        Returns:
            若今天不晚于有效期截止日则返回 True。
            True if today is not after the expiry date.
        """
        return date.today() <= self.valid_until

    def remaining_days(self, from_date: date | None = None) -> int:
        """计算剩余有效天数 / Calculate remaining valid days.

        Args:
            from_date: 起算日期，默认今天。
                Reference date, defaults to today.

        Returns:
            剩余有效天数，已过期返回负数。
            Remaining valid days; negative if expired.
        """
        ref = from_date or date.today()
        return (self.valid_until - ref).days

    def matches_aircraft(self, aircraft_type: str) -> bool:
        """检查是否匹配机型。

        Check whether the certificate matches the aircraft type.

        Args:
            aircraft_type: 待匹配机型。/ Aircraft type to match.

        Returns:
            若机型匹配则返回 True。
            True if aircraft type matches.
        """
        return self.aircraft_type == aircraft_type
