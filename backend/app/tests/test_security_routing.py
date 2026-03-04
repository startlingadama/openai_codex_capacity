from backend.app.core.security import hash_password, hash_token, verify_password
from backend.app.services.routing_service import classify_support_category


def test_password_hash_and_verify():
    salt, digest = hash_password("supersecret")
    assert verify_password("supersecret", salt, digest)
    assert not verify_password("bad", salt, digest)


def test_token_hash_changes_value():
    token = "abc123"
    assert hash_token(token) != token


def test_routing_categories():
    assert classify_support_category("problème de connexion") == "authentication"
    assert classify_support_category("incident urgent") == "incident"
    assert classify_support_category("infos opcvm") == "product_info"
    assert classify_support_category("bonjour") == "general"
