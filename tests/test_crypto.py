import base64
import pytest

from blockchain_sim import crypto_utils as cu


def test_sha256_is_deterministic_and_known():
    assert cu.sha256_hex(b"abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_secp256k1_signatures_verify_and_modified_message_fails():
    private_key = cu.generate_private_key_bytes()
    public_key = cu.private_to_public_bytes(private_key)
    signature = cu.sign_message(private_key, b"pay bob 5")
    assert cu.verify_signature(public_key, b"pay bob 5", signature)
    assert not cu.verify_signature(public_key, b"pay bob 50", signature)


def test_wrong_public_key_cannot_verify_signature():
    private_a = cu.generate_private_key_bytes()
    private_b = cu.generate_private_key_bytes()
    sig = cu.sign_message(private_a, b"message")
    assert not cu.verify_signature(cu.private_to_public_bytes(private_b), b"message", sig)


def test_address_is_stable_for_public_key_and_checksum_valid():
    private_key = bytes.fromhex("01".zfill(64))
    public_key = cu.private_to_public_bytes(private_key)
    address = cu.public_key_to_address(public_key)
    assert address == cu.public_key_to_address(public_key)
    assert cu.validate_address(address)
    assert not cu.validate_address(address[:-1] + ("1" if address[-1] != "1" else "2"))


def test_private_key_encryption_round_trip_and_wrong_password_rejected():
    private_key = cu.generate_private_key_bytes()
    payload = cu.encrypt_private_key(private_key, "correct horse battery staple", iterations=1000)
    assert cu.decrypt_private_key(payload, "correct horse battery staple") == private_key
    with pytest.raises(ValueError, match="password|tampered"):
        cu.decrypt_private_key(payload, "wrong password")


def test_private_key_ciphertext_tamper_is_detected():
    private_key = cu.generate_private_key_bytes()
    payload = cu.encrypt_private_key(private_key, "secret", iterations=1000)
    raw = bytearray(base64.b64decode(payload["ciphertext"]))
    raw[0] ^= 1
    payload["ciphertext"] = base64.b64encode(bytes(raw)).decode("ascii")
    with pytest.raises(ValueError, match="password|tampered"):
        cu.decrypt_private_key(payload, "secret")
