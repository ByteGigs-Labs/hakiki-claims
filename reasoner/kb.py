import json
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path

KB_DIR = Path(__file__).resolve().parent.parent / "kb"
IMPLEMENTED_RULES = ("R1", "R2", "R3", "R4", "R5", "R6", "R8")


@dataclass(frozen=True)
class KnowledgeBase:
    version: str
    citations: dict
    facilities: tuple[dict, ...]
    services: tuple[dict, ...]
    program: str

    def rule(self, rule_id: str) -> dict:
        return self.citations["rules"][rule_id]

    def rule_label(self, rule_id: str) -> str:
        name = "".join(
            part.capitalize() for part in self.rule(rule_id)["name"].replace("-", "").split()
        )
        return f"{rule_id}-{name}"

    def citation_for(self, rule_id: str) -> dict:
        rule = self.rule(rule_id)
        source = self.citations["sources"][rule["source"]]
        return {
            "rule": rule_id,
            "name": rule["name"],
            "condition": rule["condition"],
            "document": source["document"],
            "section": rule["section"],
            "url": source["url"],
            "effective": rule["effective"],
            "verified": rule["verified"],
        }

    def contracted(self, facility: dict, fund: str, on: date) -> bool:
        return any(
            contract["fund"] == fund and contract["from"] <= on.isoformat() <= contract["to"]
            for contract in facility["contracts"]
        )


@lru_cache
def load_kb(directory: Path = KB_DIR) -> KnowledgeBase:
    def read_json(*parts: str) -> dict:
        return json.loads(directory.joinpath(*parts).read_text())

    programs = [directory / "combine.metta", directory / "rules" / "helpers.metta"]
    programs += sorted(path for path in (directory / "rules").glob("r*.metta"))
    return KnowledgeBase(
        version=directory.joinpath("VERSION").read_text().strip(),
        citations=read_json("citations.json"),
        facilities=tuple(
            sorted(read_json("reference", "facilities.json")["facilities"], key=lambda f: f["id"])
        ),
        services=tuple(
            sorted(read_json("reference", "services.json")["services"], key=lambda s: s["id"])
        ),
        program="\n".join(path.read_text() for path in programs),
    )
