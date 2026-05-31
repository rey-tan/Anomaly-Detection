from src.api import security


def test_password_hash_and_verify():
    pwd = "s3cret-pass"
    hashed = security.get_password_hash(pwd)
    assert isinstance(hashed, str)
    assert security.verify_password(pwd, hashed)
    assert not security.verify_password("wrong", hashed)


def test_token_create_and_decode():
    data = {"sub": "tester", "role": "analyst"}
    token = security.create_access_token(data)
    assert isinstance(token, str)
    decoded = security.decode_access_token(token)
    assert decoded is not None
    assert decoded.get("sub") == "tester"
