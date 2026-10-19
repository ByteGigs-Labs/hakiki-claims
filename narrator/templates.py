from reasoner.kb import KnowledgeBase

HEADLINES = {
    "en": {
        "WILL_FAIL": "This claim is likely to be rejected by SHA.",
        "AT_RISK": "This claim may be rejected because some checks could not be confirmed.",
        "PASS": "This claim passes every check.",
    },
    "sw": {
        "WILL_FAIL": "Dai hili linaweza kukataliwa na SHA.",
        "AT_RISK": (
            "Dai hili linaweza kukataliwa kwa sababu baadhi ya ukaguzi haukuweza kuthibitishwa."
        ),
        "PASS": "Dai hili limepita ukaguzi wote.",
    },
}
AT_RISK_LINE = {"en": "KES {amount} is at risk.", "sw": "KES {amount} iko hatarini."}
FIX_LABEL = {"en": "How to fix", "sw": "Jinsi ya kurekebisha"}
LANGUAGES = tuple(HEADLINES)


def rule_id(step: dict) -> str:
    return step["rule"].split("-")[0]


def render_step(kb: KnowledgeBase, step: dict, language: str) -> str:
    message = kb.rule(rule_id(step))["messages"][f"{step['result']}.{step['reason']}"][language]
    return message.format_map(step["values"])


def explain(kb: KnowledgeBase, result: dict, language: str) -> str:
    lines = [HEADLINES[language][result["verdict"]]]
    lines += [
        f"- {render_step(kb, step, language)}"
        for step in result["trace"]
        if step["result"] in {"fail", "warn"}
    ]
    if result["revenue_at_risk_kes"]:
        lines.append(AT_RISK_LINE[language].format(amount=f"{result['revenue_at_risk_kes']:,}"))
    action_key = "action" if language == "en" else "action_sw"
    lines += [f"{FIX_LABEL[language]}: {fix[action_key]}" for fix in result["fixes"]]
    return "\n".join(lines)
