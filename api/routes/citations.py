from fastapi import APIRouter, Depends, HTTPException, status

from api.security import Principal, current_principal
from reasoner.kb import load_kb

router = APIRouter(prefix="/v1/citations", tags=["citations"])


@router.get("/{rule_id}")
def get_citation(rule_id: str, _: Principal = Depends(current_principal)) -> dict:
    kb = load_kb()
    if rule_id not in kb.citations["rules"]:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown rule")
    return kb.citation_for(rule_id)
