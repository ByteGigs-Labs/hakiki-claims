import pytest

from ingest.pseudonymise import patient_token, pseudonymise

KEY = b"k" * 32


def test_same_identifier_gives_same_token():
    assert pseudonymise("A123456", KEY) == pseudonymise("A123456", KEY)


def test_normalises_case_and_whitespace():
    assert pseudonymise("  Jane   Wanjiku ", KEY) == pseudonymise("jane wanjiku", KEY)


def test_different_identifiers_give_different_tokens():
    assert pseudonymise("A123456", KEY) != pseudonymise("A123457", KEY)


def test_different_keys_give_different_tokens():
    assert pseudonymise("A123456", KEY) != pseudonymise("A123456", b"x" * 32)


def test_token_does_not_contain_identifier():
    assert "123456" not in pseudonymise("A123456", KEY)


def test_blank_identifier_is_rejected():
    with pytest.raises(ValueError):
        pseudonymise("   ", KEY)


def test_settings_key_is_used():
    assert patient_token("A123456") == pseudonymise("A123456", b"test-hmac-key")
