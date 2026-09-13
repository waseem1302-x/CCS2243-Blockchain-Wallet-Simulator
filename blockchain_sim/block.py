from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .crypto_utils import canonical_json, sha256_hex
from .transaction import Transaction


@dataclass
class Block:
    index: int
    timestamp: str
    transactions: list[Transaction]
    previous_hash: str
    miner_address: str
    difficulty: int
    nonce: int = 0
    hash: str = ""

    def hash_payload(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "previous_hash": self.previous_hash,
            "miner_address": self.miner_address,
            "difficulty": self.difficulty,
            "nonce": self.nonce,
        }

    def calculate_hash(self) -> str:
        return sha256_hex(canonical_json(self.hash_payload()))

    def mine(self, max_nonce: int | None = None) -> int:
        if self.difficulty < 0:
            raise ValueError("Difficulty cannot be negative")
        target = "0" * self.difficulty
        attempts = 0
        while True:
            attempts += 1
            candidate = self.calculate_hash()
            if candidate.startswith(target):
                self.hash = candidate
                return attempts
            self.nonce += 1
            if max_nonce is not None and self.nonce > max_nonce:
                raise RuntimeError("Proof of Work nonce limit reached")

    def is_pow_valid(self) -> bool:
        if not self.hash:
            return False
        return self.hash == self.calculate_hash() and self.hash.startswith("0" * self.difficulty)

    def to_dict(self) -> dict[str, Any]:
        return {**self.hash_payload(), "hash": self.hash}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Block":
        required = {
            "index",
            "timestamp",
            "transactions",
            "previous_hash",
            "miner_address",
            "difficulty",
            "nonce",
            "hash",
        }
        missing = sorted(required - data.keys())
        if missing:
            raise ValueError(f"Block data missing fields: {', '.join(missing)}")
        transactions = data["transactions"]
        if not isinstance(transactions, list):
            raise ValueError("Block transactions must be a list")
        return cls(
            index=int(data["index"]),
            timestamp=str(data["timestamp"]),
            transactions=[Transaction.from_dict(item) for item in transactions],
            previous_hash=str(data["previous_hash"]),
            miner_address=str(data["miner_address"]),
            difficulty=int(data["difficulty"]),
            nonce=int(data["nonce"]),
            hash=str(data["hash"]),
        )
