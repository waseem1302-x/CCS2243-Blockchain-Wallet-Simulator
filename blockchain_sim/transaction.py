from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .config import SYSTEM_ADDRESS
from .crypto_utils import (
    canonical_json,
    public_key_to_address,
    sha256_hex,
    sign_message,
    validate_address,
    verify_signature,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


@dataclass
class Transaction:
    transaction_id: str
    sender_address: str
    receiver_address: str
    amount: int
    timestamp: str
    sender_public_key: str | None
    signature: str | None
    transaction_type: str

    @classmethod
    def create_transfer(
        cls,
        sender_address: str,
        receiver_address: str,
        amount: int,
        sender_public_key: str,
        *,
        timestamp: str | None = None,
    ) -> "Transaction":
        if not isinstance(amount, int) or isinstance(amount, bool):
            raise ValueError("Transaction amount must be an integer number of atomic units")
        if amount <= 0:
            raise ValueError("Transaction amount must be greater than zero")
        tx = cls(
            transaction_id="",
            sender_address=sender_address,
            receiver_address=receiver_address,
            amount=amount,
            timestamp=timestamp or utc_now(),
            sender_public_key=sender_public_key,
            signature=None,
            transaction_type="transfer",
        )
        tx.transaction_id = tx.calculate_transaction_id()
        return tx

    @classmethod
    def create_system(
        cls,
        receiver_address: str,
        amount: int,
        transaction_type: str,
        *,
        timestamp: str | None = None,
    ) -> "Transaction":
        if transaction_type not in {"faucet", "mining_reward"}:
            raise ValueError("Unsupported system transaction type")
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise ValueError("System transaction amount must be greater than zero")
        tx = cls(
            transaction_id="",
            sender_address=SYSTEM_ADDRESS,
            receiver_address=receiver_address,
            amount=amount,
            timestamp=timestamp or utc_now(),
            sender_public_key=None,
            signature=None,
            transaction_type=transaction_type,
        )
        tx.transaction_id = tx.calculate_transaction_id()
        return tx

    @property
    def is_system(self) -> bool:
        return self.transaction_type in {"faucet", "mining_reward"}

    def unsigned_payload(self) -> dict[str, Any]:
        return {
            "sender_address": self.sender_address,
            "receiver_address": self.receiver_address,
            "amount": self.amount,
            "timestamp": self.timestamp,
            "sender_public_key": self.sender_public_key,
            "transaction_type": self.transaction_type,
        }

    def calculate_transaction_id(self) -> str:
        return sha256_hex(canonical_json(self.unsigned_payload()))

    def sign(self, private_key_bytes: bytes) -> None:
        if self.transaction_type != "transfer":
            raise ValueError("System transactions are not signed by user wallets")
        try:
            from .crypto_utils import private_to_public_bytes

            calculated_public = private_to_public_bytes(private_key_bytes).hex()
        except ValueError as exc:
            raise ValueError("Invalid private key") from exc
        if calculated_public != self.sender_public_key:
            raise ValueError("Private key does not match transaction sender public key")
        self.transaction_id = self.calculate_transaction_id()
        self.signature = sign_message(private_key_bytes, bytes.fromhex(self.transaction_id))

    def verify(self) -> bool:
        if self.transaction_type != "transfer":
            return False
        if not isinstance(self.amount, int) or isinstance(self.amount, bool) or self.amount <= 0:
            return False
        if not self.sender_public_key or not self.signature:
            return False
        if not validate_address(self.sender_address) or not validate_address(self.receiver_address):
            return False
        if self.calculate_transaction_id() != self.transaction_id:
            return False
        try:
            public_key = bytes.fromhex(self.sender_public_key)
        except ValueError:
            return False
        if public_key_to_address(public_key) != self.sender_address:
            return False
        return verify_signature(public_key, bytes.fromhex(self.transaction_id), self.signature)

    def system_integrity_valid(self) -> bool:
        if not self.is_system:
            return False
        return (
            self.sender_address == SYSTEM_ADDRESS
            and self.sender_public_key is None
            and self.signature is None
            and isinstance(self.amount, int)
            and not isinstance(self.amount, bool)
            and self.amount > 0
            and self.calculate_transaction_id() == self.transaction_id
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "transaction_id": self.transaction_id,
            "sender_address": self.sender_address,
            "receiver_address": self.receiver_address,
            "amount": self.amount,
            "timestamp": self.timestamp,
            "sender_public_key": self.sender_public_key,
            "signature": self.signature,
            "transaction_type": self.transaction_type,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Transaction":
        required = {
            "transaction_id",
            "sender_address",
            "receiver_address",
            "amount",
            "timestamp",
            "sender_public_key",
            "signature",
            "transaction_type",
        }
        missing = sorted(required - data.keys())
        if missing:
            raise ValueError(f"Transaction data missing fields: {', '.join(missing)}")
        return cls(
            transaction_id=str(data["transaction_id"]),
            sender_address=str(data["sender_address"]),
            receiver_address=str(data["receiver_address"]),
            amount=int(data["amount"]),
            timestamp=str(data["timestamp"]),
            sender_public_key=None if data["sender_public_key"] is None else str(data["sender_public_key"]),
            signature=None if data["signature"] is None else str(data["signature"]),
            transaction_type=str(data["transaction_type"]),
        )
