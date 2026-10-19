import csv
from datetime import date, timedelta
from pathlib import Path

OUTPUT = Path(__file__).resolve().parent.parent / "data" / "synthetic"
CLAIM_COLUMNS = (
    "claim_ref",
    "patient_id",
    "facility_id",
    "service_code",
    "fund",
    "date_of_service",
    "amount_kes",
    "preauth_ref",
    "referral_ref",
    "icd_code",
    "member_status",
    "emergency",
    "lodging_date",
)
CASES: list[tuple[tuple, tuple]] = []


def case(
    patient,
    facility,
    service,
    fund,
    day,
    amount,
    verdict,
    failing="",
    preauth="",
    referral="",
    icd="",
    member="active",
    emergency=False,
    lodge_after=1,
):
    ref = f"clm-{len(CASES) + 1:03d}"
    lodging = (date.fromisoformat(day) + timedelta(days=lodge_after)).isoformat()
    claim = (
        ref,
        f"SYN-{patient}",
        facility,
        service,
        fund,
        day,
        amount,
        preauth,
        referral,
        icd,
        member,
        "true" if emergency else "false",
        lodging,
    )
    CASES.append((claim, (ref, verdict, failing)))


# Clean claims: every rule passes.
case("P01", "fac-02", "svc-OPD-01", "PHC", "2026-09-01", 900, "PASS", icd="J06.9")
case("P02", "fac-02", "svc-LAB-01", "PHC", "2026-09-02", 400, "PASS", icd="B50.9")
case("P03", "fac-03", "svc-DEL-01", "PHC", "2026-09-03", 10000, "PASS", icd="O80", lodge_after=3)
case("P04", "fac-03", "svc-CS-01", "PHC", "2026-09-04", 30000, "PASS", icd="O82", lodge_after=3)
case("P05", "fac-12", "svc-ER-01", "SHIF", "2026-09-05", 15000, "PASS", icd="T14.9")
case(
    "P06",
    "fac-15",
    "svc-MRI-01",
    "SHIF",
    "2026-09-06",
    17500,
    "PASS",
    preauth="PA-20931",
    referral="REF-7001",
    icd="M54.5",
)
case(
    "P07",
    "fac-15",
    "svc-ONC-01",
    "ECCIF",
    "2026-09-07",
    76000,
    "PASS",
    preauth="PA-20944",
    icd="C50.9",
)
case(
    "P08",
    "fac-12",
    "svc-OPD-01",
    "SHIF",
    "2026-09-08",
    1200,
    "PASS",
    referral="REF-7002",
    icd="J06.9",
)
case(
    "P09",
    "fac-12",
    "svc-CS-01",
    "SHIF",
    "2026-09-09",
    58000,
    "PASS",
    preauth="PA-20960",
    referral="REF-7003",
    icd="O82",
)
case(
    "P10",
    "fac-12",
    "svc-APP-01",
    "SHIF",
    "2026-09-10",
    44000,
    "PASS",
    preauth="PA-20971",
    referral="REF-7004",
    icd="K35.8",
)
case(
    "P11",
    "fac-15",
    "svc-CAT-01",
    "SHIF",
    "2026-09-11",
    33000,
    "PASS",
    preauth="PA-20988",
    referral="REF-7005",
    icd="H25.9",
)
case(
    "P12",
    "fac-12",
    "svc-DIA-01",
    "ECCIF",
    "2026-09-12",
    10650,
    "PASS",
    preauth="PA-21001",
    icd="N18.6",
)
# R1 member eligibility.
case(
    "P13",
    "fac-12",
    "svc-OPD-01",
    "SHIF",
    "2026-09-13",
    1200,
    "WILL_FAIL",
    "R1",
    referral="REF-7010",
    icd="J06.9",
    member="inactive",
)
case(
    "P14",
    "fac-03",
    "svc-DEL-01",
    "PHC",
    "2026-09-14",
    10000,
    "WILL_FAIL",
    "R1",
    icd="O80",
    member="inactive",
)
case(
    "P15",
    "fac-02",
    "svc-OPD-01",
    "PHC",
    "2026-09-15",
    900,
    "AT_RISK",
    "R1",
    icd="J06.9",
    member="unknown",
)
case(
    "P16",
    "fac-12",
    "svc-LAB-01",
    "SHIF",
    "2026-09-16",
    400,
    "AT_RISK",
    "R1",
    referral="REF-7011",
    icd="B50.9",
    member="unknown",
)
# R2 facility contract (St. Luke's PHC contract ended 2026-03-31).
case("P17", "fac-09", "svc-OPD-01", "PHC", "2026-09-17", 900, "WILL_FAIL", "R2", icd="J06.9")
case("P18", "fac-09", "svc-DEL-01", "PHC", "2026-09-18", 10000, "WILL_FAIL", "R2", icd="O80")
# R3 pre-authorisation.
case(
    "P19",
    "fac-12",
    "svc-CS-01",
    "SHIF",
    "2026-09-19",
    45000,
    "WILL_FAIL",
    "R3",
    referral="REF-7012",
    icd="O82",
)
case(
    "P20",
    "fac-15",
    "svc-DIA-01",
    "SHIF",
    "2026-09-20",
    10650,
    "WILL_FAIL",
    "R3",
    referral="REF-7013",
    icd="N18.6",
)
case(
    "P21",
    "fac-15",
    "svc-MRI-01",
    "SHIF",
    "2026-09-21",
    17000,
    "WILL_FAIL",
    "R3",
    referral="REF-7014",
    icd="M54.5",
)
# R4 benefit coverage.
case(
    "P22",
    "fac-15",
    "svc-ONC-01",
    "SHIF",
    "2026-09-22",
    70000,
    "WILL_FAIL",
    "R4",
    referral="REF-7015",
    icd="C50.9",
)
case("P23", "fac-03", "svc-DEN-01", "PHC", "2026-09-23", 2800, "WILL_FAIL", "R4", icd="K02.1")
case("P24", "fac-12", "svc-OPD-01", "ECCIF", "2026-09-24", 700, "WILL_FAIL", "R4", icd="J06.9")
# R5 facility level.
case(
    "P25",
    "fac-12",
    "svc-ONC-01",
    "ECCIF",
    "2026-09-25",
    76000,
    "WILL_FAIL",
    "R5",
    preauth="PA-21033",
    icd="C50.9",
)
# R6 tariff cap, one on a tariff read from SHA's published schedule.
case(
    "P26",
    "fac-12",
    "svc-OPD-01",
    "SHIF",
    "2026-09-26",
    2500,
    "WILL_FAIL",
    "R6",
    referral="REF-7020",
    icd="J06.9",
)
case(
    "P27",
    "fac-12",
    "svc-APP-01",
    "SHIF",
    "2026-09-27",
    52000,
    "WILL_FAIL",
    "R6",
    preauth="PA-21058",
    referral="REF-7021",
    icd="K35.8",
)
case("P28", "fac-03", "svc-CS-01", "PHC", "2026-09-28", 35000, "WILL_FAIL", "R6", icd="O82")
# R7 documentation, R9 clinical consistency, R10 timely lodging, R11 referral.
case("P29", "fac-02", "svc-OPD-01", "PHC", "2026-09-29", 900, "AT_RISK", "R7")
case(
    "P30",
    "fac-12",
    "svc-APP-01",
    "SHIF",
    "2026-09-30",
    44000,
    "AT_RISK",
    "R9",
    preauth="PA-21070",
    referral="REF-7022",
    icd="O82",
)
case(
    "P31",
    "fac-02",
    "svc-OPD-01",
    "PHC",
    "2026-10-01",
    900,
    "AT_RISK",
    "R10",
    icd="J06.9",
    lodge_after=15,
)
case("P32", "fac-12", "svc-OPD-01", "SHIF", "2026-10-02", 1200, "AT_RISK", "R11", icd="J06.9")
case("P33", "fac-12", "svc-CS-01", "SHIF", "2026-10-03", 58000, "PASS", icd="O82", emergency=True)
# R8 duplicates and frequency.
case(
    "P34",
    "fac-12",
    "svc-OPD-01",
    "SHIF",
    "2026-10-01",
    1200,
    "PASS",
    referral="REF-7030",
    icd="J06.9",
)
case(
    "P34",
    "fac-12",
    "svc-OPD-01",
    "SHIF",
    "2026-10-01",
    1200,
    "WILL_FAIL",
    "R8",
    referral="REF-7030",
    icd="J06.9",
)
case("P35", "fac-03", "svc-LAB-01", "PHC", "2026-10-02", 400, "PASS", icd="B50.9")
case("P35", "fac-03", "svc-LAB-01", "PHC", "2026-10-02", 400, "WILL_FAIL", "R8", icd="B50.9")
for day in ("2026-10-05", "2026-10-07", "2026-10-09"):
    case(
        "P36",
        "fac-15",
        "svc-DIA-01",
        "SHIF",
        day,
        10650,
        "PASS",
        preauth="PA-21100",
        referral="REF-7040",
        icd="N18.6",
    )
case(
    "P36",
    "fac-15",
    "svc-DIA-01",
    "SHIF",
    "2026-10-11",
    10650,
    "WILL_FAIL",
    "R8",
    preauth="PA-21100",
    referral="REF-7040",
    icd="N18.6",
)
# Several rules at once.
case(
    "P37",
    "fac-12",
    "svc-CS-01",
    "SHIF",
    "2026-10-12",
    70000,
    "WILL_FAIL",
    "R3;R6",
    referral="REF-7050",
    icd="O82",
)
case(
    "P38",
    "fac-03",
    "svc-CS-01",
    "SHIF",
    "2026-10-13",
    60000,
    "WILL_FAIL",
    "R1;R2;R3;R5;R11",
    icd="O82",
    member="inactive",
)
case(
    "P39",
    "fac-09",
    "svc-ONC-01",
    "SHIF",
    "2026-10-14",
    80000,
    "WILL_FAIL",
    "R2;R4;R11",
    icd="C50.9",
)


def write(name: str, header: tuple, rows: list) -> None:
    with (OUTPUT / name).open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


if __name__ == "__main__":
    write("claims.csv", CLAIM_COLUMNS, [claim for claim, _ in CASES])
    write(
        "expected.csv",
        ("claim_ref", "verdict", "failing_rules"),
        [expected for _, expected in CASES],
    )
