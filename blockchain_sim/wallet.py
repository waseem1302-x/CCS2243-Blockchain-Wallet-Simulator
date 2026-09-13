from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .config import PBKDF2_ITERATIONS, SCHEMA_VERSION
from .crypto_utils import (
    decrypt_private_key,
    encrypt_private_key,
    generate_private_key_bytes,
    private_to_public_bytes,
    public_key_to_address,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


@dataclass(frozen=True)
class Wallet:
    name: str
    address: str
    public_key: str
    encrypted_private_key: str
    salt: str
    nonce: str
    kdf_iterations: int
    created_at: str
    schema_version: int = SCHEMA_VERSION

    @classmethod
    def create(
        cls,
        name: str,
        password: str,
        *,
        kdf_iterations: int = PBKDF2_ITERATIONS,
    ) -> "Wallet":
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Wallet name cannot be empty")
        if not password:
            raise ValueError("Wallet password cannot be empty")
        private_key = generate_private_key_bytes()
        public_key = private_to_public_bytes(private_key)
        encrypted = encrypt_private_key(private_key, password, iterations=kdf_iterations)
        return cls(
            name=clean_name,
            address=public_key_to_address(public_key),
            public_key=public_key.hex(),
            encrypted_private_key=str(encrypted["ciphertext"]),
            salt=str(encrypted["salt"]),
            nonce=str(encrypted["nonce"]),
            kdf_iterations=int(encrypted["kdf_iterations"]),
            created_at=_utc_now(),
        )

    def unlock_private_key(self, password: str) -> bytes:
        return decrypt_private_key(
            {
                "ciphertext": self.encrypted_private_key,
                "salt": self.salt,
                "nonce": self.nonce,
                "kdf_iterations": self.kdf_iterations,
            },
            password,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "name": self.name,
            "address": self.address,
            "public_key": self.public_key,
            "encrypted_private_key": self.encrypted_private_key,
            "salt": self.salt,
            "nonce": self.nonce,
            "kdf_iterations": self.kdf_iterations,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Wallet":
        if int(data.get("schema_version", -1)) != SCHEMA_VERSION:
            raise ValueError("Unsupported wallet schema version")
        required = {
            "name",
            "address",
            "public_key",
            "encrypted_private_key",
            "salt",
            "nonce",
            "kdf_iterations",
            "created_at",
        }
        missing = sorted(required - data.keys())
        if missing:
            raise ValueError(f"Wallet data missing fields: {', '.join(missing)}")
        return cls(
            name=str(data["name"]),
            address=str(data["address"]),
            public_key=str(data["public_key"]),
            encrypted_private_key=str(data["encrypted_private_key"]),
            salt=str(data["salt"]),
            nonce=str(data["nonce"]),
            kdf_iterations=int(data["kdf_iterations"]),
            created_at=str(data["created_at"]),
            schema_version=int(data["schema_version"]),
        )
