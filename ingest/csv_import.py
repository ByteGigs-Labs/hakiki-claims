import csv
import io
import re
from dataclasses import dataclass, field

from pydantic import ValidationError

from ingest.claim_schema import ClaimInput

REQUIRED_COLUMNS = ("facility_id", "service_code", "fund", "date_of_service", "amount_kes")
OPTIONAL_COLUMNS = (
    "claim_ref",
    "patient_id",
    "patient_token",
    "preauth_ref",
    "icd_code",
    "member_status",
)
ALLOWED_COLUMNS = (*REQUIRED_COLUMNS, *OPTIONAL_COLUMNS)
TEMPLATE_HEADER = (
    "claim_ref",
    "patient_id",
    *REQUIRED_COLUMNS,
    "preauth_ref",
    "icd_code",
    "member_status",
)
TEMPLATE_EXAMPLE = "clm-001,A1234567,fac-12,svc-CS-01,SHIF,2026-10-14,45000,PA-20931,O82,active"
FILENAME_CHARACTERS = re.compile(r"[^A-Za-z0-9._ -]")


class CsvImportError(ValueError):
    pass


@dataclass
class ParsedBatch:
    claims: list[dict] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.claims) + len(self.errors)


def template_csv() -> str:
    return ",".join(TEMPLATE_HEADER) + "\n" + TEMPLATE_EXAMPLE + "\n"


def safe_filename(name: str | None) -> str:
    base = (name or "upload.csv").replace("\\", "/").rsplit("/", 1)[-1]
    return FILENAME_CHARACTERS.sub("_", base)[:100] or "upload.csv"


def _decode(content: bytes) -> str:
    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise CsvImportError("File must be UTF-8 encoded CSV") from exc


def _check_header(columns: list[str] | None) -> None:
    if not columns:
        raise CsvImportError("File is empty")
    unknown = [name for name in columns if name not in ALLOWED_COLUMNS]
    missing = [name for name in REQUIRED_COLUMNS if name not in columns]
    if unknown:
        raise CsvImportError("File has unrecognised columns")
    if missing:
        raise CsvImportError("Missing required columns: " + ", ".join(missing))
    if not ({"patient_id", "patient_token"} & set(columns)):
        raise CsvImportError("Missing required column: patient_id or patient_token")


def _row_errors(error: ValidationError) -> list[str]:
    return sorted({".".join(str(part) for part in item["loc"]) or "row" for item in error.errors()})


def parse_csv(content: bytes, max_rows: int) -> ParsedBatch:
    reader = csv.DictReader(io.StringIO(_decode(content), newline=""), restkey="_extra")
    _check_header(reader.fieldnames)
    parsed, seen = ParsedBatch(), set()
    for row_number, row in enumerate(reader, start=1):
        if row_number > max_rows:
            raise CsvImportError(f"File has more than {max_rows} rows")
        if "_extra" in row or None in row.values():
            parsed.errors.append({"row": row_number, "fields": ["row"]})
            continue
        try:
            claim = ClaimInput.model_validate(
                {key: value for key, value in row.items() if value and value.strip()}
            ).to_claim()
        except ValidationError as error:
            parsed.errors.append({"row": row_number, "fields": _row_errors(error)})
            continue
        if claim["claim_ref"] in seen:
            parsed.errors.append({"row": row_number, "fields": ["claim_ref"]})
            continue
        seen.add(claim["claim_ref"])
        parsed.claims.append({"row": row_number, "claim": claim})
    if parsed.total == 0:
        raise CsvImportError("File has no data rows")
    return parsed
