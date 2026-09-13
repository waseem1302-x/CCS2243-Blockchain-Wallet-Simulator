from __future__ import annotations

import base64
import hashlib
import json
import os
from typing import Any

from cryptography.exceptions import InvalidSignature, InvalidTag
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .config import ADDRESS_VERSION, PBKDF2_ITERATIONS, WALLET_AAD

_B58_ALPHABET = b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_bytes(data: bytes | str) -> bytes:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).digest()


def sha256_hex(data: bytes | str) -> str:
    return sha256_bytes(data).hex()


def double_sha256(data: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


def _ripemd160(data: bytes) -> bytes:
    try:
        h = hashlib.new("ripemd160")
    except ValueError as exc:
        raise RuntimeError("RIPEMD-160 is unavailable in this Python/OpenSSL build") from exc
    h.update(data)
    return h.digest()


def b58encode(data: bytes) -> str:
    value = int.from_bytes(data, "big")
    encoded = bytearray()
    while value:
        value, rem = divmod(value, 58)
        encoded.append(_B58_ALPHABET[rem])
    leading_zeroes = len(data) - len(data.lstrip(b"\x00"))
    prefix = _B58_ALPHABET[:1] * leading_zeroes
    body = bytes(reversed(encoded)) if encoded else b""
    return (prefix + body).decode("ascii")


def b58decode(value: str) -> bytes:
    if not value:
        return b""
    number = 0
    for char in value.encode("ascii"):
        idx = _B58_ALPHABET.find(bytes([char]))
        if idx < 0:
            raise ValueError("Invalid Base58 character")
        number = number * 58 + idx
    body = number.to_bytes((number.bit_length() + 7) // 8, "big") if number else b""
    leading_ones = len(value) - len(value.lstrip("1"))
    return b"\x00" * leading_ones + body


def generate_private_key_bytes() -> bytes:
    key = ec.generate_private_key(ec.SECP256K1())
    value = key.private_numbers().private_value
    return value.to_bytes(32, "big")


def _private_key_from_bytes(private_key_bytes: bytes) -> ec.EllipticCurvePrivateKey:
    if len(private_key_bytes) != 32:
        raise ValueError("secp256k1 private keys must be exactly 32 bytes")
    value = int.from_bytes(private_key_bytes, "big")
    if value <= 0:
        raise ValueError("Invalid secp256k1 private key")
    try:
        return ec.derive_private_key(value, ec.SECP256K1())
    except ValueError as exc:
        raise ValueError("Invalid secp256k1 private key") from exc


def private_to_public_bytes(private_key_bytes: bytes) -> bytes:
    key = _private_key_from_bytes(private_key_bytes)
    return key.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.CompressedPoint,
    )


def public_key_from_bytes(public_key_bytes: bytes) -> ec.EllipticCurvePublicKey:
    try:
        return ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256K1(), public_key_bytes)
    except ValueError as exc:
        raise ValueError("Invalid secp256k1 public key") from exc


def public_key_to_address(public_key_bytes: bytes) -> str:
    key_hash = _ripemd160(sha256_bytes(public_key_bytes))
    payload = ADDRESS_VERSION + key_hash
    checksum = double_sha256(payload)[:4]
    return b58encode(payload + checksum)


def validate_address(address: str) -> bool:
    try:
        decoded = b58decode(address)
    except (ValueError, UnicodeError):
        return False
    if len(decoded) != 25 or decoded[:1] != ADDRESS_VERSION:
        return False
    payload, checksum = decoded[:-4], decoded[-4:]
    return double_sha256(payload)[:4] == checksum


def sign_message(private_key_bytes: bytes, message: bytes | str) -> str:
    if isinstance(message, str):
        message = message.encode("utf-8")
    signature = _private_key_from_bytes(private_key_bytes).sign(message, ec.ECDSA(hashes.SHA256()))
    return signature.hex()


def verify_signature(public_key_bytes: bytes, message: bytes | str, signature_hex: str) -> bool:
    if isinstance(message, str):
        message = message.encode("utf-8")
    try:
        signature = bytes.fromhex(signature_hex)
        public_key_from_bytes(public_key_bytes).verify(signature, message, ec.ECDSA(hashes.SHA256()))
        return True
    except (ValueError, InvalidSignature):
        return False


def derive_password_key(password: str, salt: bytes, iterations: int = PBKDF2_ITERATIONS) -> bytes:
    if not password:
        raise ValueError("Password cannot be empty")
    if iterations < 1:
        raise ValueError("PBKDF2 iterations must be positive")
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=iterations)
    return kdf.derive(password.encode("utf-8"))


def encrypt_private_key(
    private_key_bytes: bytes,
    password: str,
    *,
    iterations: int = PBKDF2_ITERATIONS,
) -> dict[str, str | int]:
    salt = os.urandom(16)
    nonce = os.urandom(12)
    key = derive_password_key(password, salt, iterations)
    ciphertext = AESGCM(key).encrypt(nonce, private_key_bytes, WALLET_AAD)
    return {
        "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
        "salt": base64.b64encode(salt).decode("ascii"),
        "nonce": base64.b64encode(nonce).decode("ascii"),
        "kdf_iterations": iterations,
    }


def decrypt_private_key(payload: dict[str, str | int], password: str) -> bytes:
    try:
        ciphertext = base64.b64decode(str(payload["ciphertext"]), validate=True)
        salt = base64.b64decode(str(payload["salt"]), validate=True)
        nonce = base64.b64decode(str(payload["nonce"]), validate=True)
        iterations = int(payload["kdf_iterations"])
    except (KeyError, ValueError, TypeError) as exc:
        raise ValueError("Invalid encrypted private-key payload") from exc
    key = derive_password_key(password, salt, iterations)
    try:
        plaintext = AESGCM(key).decrypt(nonce, ciphertext, WALLET_AAD)
    except InvalidTag as exc:
        raise ValueError("Incorrect password or tampered private-key data") from exc
    if len(plaintext) != 32:
        raise ValueError("Decrypted private key has invalid length")
    return plaintext
