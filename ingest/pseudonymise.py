import hashlib
import hmac

from api.config import get_settings

PATIENT_PREFIX = "pat-"


def _normalise(identifier: str) -> str:
    return " ".join(identifier.split()).casefold()


def pseudonymise(identifier: str, key: bytes) -> str:
    if not identifier.strip():
        raise ValueError("identifier must not be empty")
    digest = hmac.new(key, _normalise(identifier).encode(), hashlib.sha256).hexdigest()
    return PATIENT_PREFIX + digest[:32]


def patient_token(identifier: str) -> str:
    return pseudonymise(identifier, get_settings().hmac_key.get_secret_value().encode())
