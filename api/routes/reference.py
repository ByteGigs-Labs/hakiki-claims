from fastapi import APIRouter, Depends

from api.security import Principal, current_principal
from reasoner.kb import load_kb

router = APIRouter(prefix="/v1/reference", tags=["reference"])


@router.get("")
def reference_data(_: Principal = Depends(current_principal)) -> dict:
    kb = load_kb()
    return {
        "rulebook_version": kb.version,
        "facilities": [
            {
                "id": facility["id"],
                "name": facility["name"],
                "level": facility["level"],
                "funds": sorted({contract["fund"] for contract in facility["contracts"]}),
            }
            for facility in kb.facilities
        ],
        "services": [
            {
                "id": service["id"],
                "name": service["name"],
                "levels": service["levels"],
                "preauth_funds": service["preauth_funds"],
                "funds": sorted(service["tariffs"]),
            }
            for service in kb.services
        ],
        "rules": [
            {"id": rule_id, "name": rule["name"]}
            for rule_id, rule in sorted(
                kb.citations["rules"].items(), key=lambda item: int(item[0][1:])
            )
            if rule.get("implemented", True)
        ],
    }
