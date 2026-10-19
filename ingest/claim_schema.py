import hashlib
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Literal, Self
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ingest.pseudonymise import patient_token as tokenise

IDENTIFIER = r"^[A-Za-z0-9][A-Za-z0-9._-]{0,49}$"
PREAUTH_REFERENCE = r"^[A-Za-z0-9][A-Za-z0-9/_-]{2,39}$"
ICD_CODE = r"^[A-Z][0-9]{2}(\.[0-9A-Z]{1,4})?$"
SHA_LAUNCH = date(2024, 10, 1)
MAX_AMOUNT_KES = Decimal("10000000")
MAX_LODGING_LEAD_DAYS = 30

Fund = Literal["PHC", "SHIF", "ECCIF"]
MemberStatus = Literal["active", "inactive", "unknown"]


def today_in_kenya() -> date:
    return datetime.now(ZoneInfo("Africa/Nairobi")).date()


class ClaimInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    claim_ref: str | None = Field(None, pattern=IDENTIFIER)
    patient_token: str | None = Field(None, pattern=IDENTIFIER)
    patient_id: str | None = Field(
        None, min_length=3, max_length=40, pattern=r"^[A-Za-z0-9 ._/-]+$"
    )
    facility_id: str = Field(pattern=IDENTIFIER)
    service_code: str = Field(pattern=IDENTIFIER)
    fund: Fund
    date_of_service: date
    amount_kes: Decimal = Field(gt=0, le=MAX_AMOUNT_KES, max_digits=10, decimal_places=2)
    preauth_ref: str | None = Field(None, pattern=PREAUTH_REFERENCE)
    icd_code: str | None = Field(None, pattern=ICD_CODE)
    member_status: MemberStatus = "unknown"
    emergency: bool = False
    referral_ref: str | None = Field(None, pattern=PREAUTH_REFERENCE)
    discharge_date: date | None = None
    lodging_date: date | None = None

    @field_validator(
        "claim_ref", "patient_token", "patient_id", "preauth_ref", "icd_code", mode="before"
    )
    @classmethod
    def blank_is_missing(cls, value):
        return None if isinstance(value, str) and not value.strip() else value

    @field_validator("date_of_service")
    @classmethod
    def plausible_date(cls, value: date) -> date:
        if value < SHA_LAUNCH or value > today_in_kenya():
            raise ValueError("date_of_service must be between 2024-10-01 and today")
        return value

    @field_validator("discharge_date")
    @classmethod
    def plausible_discharge(cls, value: date | None) -> date | None:
        if value is not None and (value < SHA_LAUNCH or value > today_in_kenya()):
            raise ValueError("discharge_date must be between 2024-10-01 and today")
        return value

    @model_validator(mode="after")
    def consistent_dates(self) -> Self:
        if self.discharge_date and self.discharge_date < self.date_of_service:
            raise ValueError("discharge_date cannot be before date_of_service")
        earliest = self.discharge_date or self.date_of_service
        latest = today_in_kenya() + timedelta(days=MAX_LODGING_LEAD_DAYS)
        if self.lodging_date and not earliest <= self.lodging_date <= latest:
            raise ValueError("lodging_date must fall between discharge and 30 days from today")
        return self

    @model_validator(mode="after")
    def pseudonymise_patient(self) -> Self:
        if bool(self.patient_token) == bool(self.patient_id):
            raise ValueError("provide exactly one of patient_token or patient_id")
        if self.patient_id:
            self.patient_token = tokenise(self.patient_id)
            self.patient_id = None
        return self

    def to_claim(self) -> dict:
        amount = self.amount_kes
        event = "|".join(
            (self.patient_token, self.facility_id, self.service_code, str(self.date_of_service))
        )
        return {
            "claim_ref": self.claim_ref or "clm-" + hashlib.sha256(event.encode()).hexdigest()[:10],
            "patient_token": self.patient_token,
            "facility_id": self.facility_id,
            "service_code": self.service_code,
            "fund": self.fund,
            "date_of_service": self.date_of_service.isoformat(),
            "amount_kes": int(amount) if amount == amount.to_integral_value() else float(amount),
            "preauth_ref": self.preauth_ref,
            "icd_code": self.icd_code,
            "member_status": self.member_status,
            "emergency": self.emergency,
            "referral_ref": self.referral_ref,
            "discharge_date": self.discharge_date.isoformat() if self.discharge_date else None,
            "lodging_date": (self.lodging_date or today_in_kenya()).isoformat(),
        }
