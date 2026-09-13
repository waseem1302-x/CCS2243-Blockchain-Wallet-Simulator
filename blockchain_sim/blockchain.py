from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .block import Block
from .config import (
    DEFAULT_DIFFICULTY,
    DEFAULT_FAUCET_AMOUNT,
    DEFAULT_MINING_REWARD,
    GENESIS_MINER,
    GENESIS_PREVIOUS_HASH,
    SCHEMA_VERSION,
)
from .transaction import Transaction
from .crypto_utils import validate_address


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    errors: list[str]


@dataclass(frozen=True)
class MiningResult:
    block: Block
    attempts: int


class Blockchain:
    def __init__(
        self,
        *,
        difficulty: int = DEFAULT_DIFFICULTY,
        mining_reward: int = DEFAULT_MINING_REWARD,
        faucet_amount: int = DEFAULT_FAUCET_AMOUNT,
        create_genesis: bool = True,
    ) -> None:
        if difficulty < 1:
            raise ValueError("Difficulty must be at least 1")
        if mining_reward <= 0 or faucet_amount <= 0:
            raise ValueError("Reward and faucet amounts must be positive")
        self.schema_version = SCHEMA_VERSION
        self.difficulty = difficulty
        self.mining_reward = mining_reward
        self.faucet_amount = faucet_amount
        self.chain: list[Block] = []
        self.pending_transactions: list[Transaction] = []
        if create_genesis:
            self.chain.append(self._create_genesis_block())

    def _create_genesis_block(self) -> Block:
        block = Block(0, utc_now(), [], "0" * 64, "GENESIS", 0, nonce=0)
        block.hash = block.calculate_hash()
        return block

    def all_confirmed_transactions(self) -> list[Transaction]:
        return [tx for block in self.chain[1:] for tx in block.transactions]

    def get_confirmed_balance(self, address: str) -> int:
        balance = 0
        for tx in self.all_confirmed_transactions():
            if tx.transaction_type == "transfer":
                if tx.sender_address == address:
                    balance -= tx.amount
                if tx.receiver_address == address:
                    balance += tx.amount
            elif tx.is_system and tx.receiver_address == address:
                balance += tx.amount
        return balance

    def get_pending_outgoing(self, address: str) -> int:
        return sum(tx.amount for tx in self.pending_transactions if tx.transaction_type == "transfer" and tx.sender_address == address)

    def get_available_balance(self, address: str) -> int:
        return self.get_confirmed_balance(address) - self.get_pending_outgoing(address)

    def _transaction_id_exists(self, transaction_id: str) -> bool:
        return any(tx.transaction_id == transaction_id for tx in self.all_confirmed_transactions()) or any(tx.transaction_id == transaction_id for tx in self.pending_transactions)

    def add_transaction(self, transaction: Transaction) -> str:
        if transaction.transaction_type != "transfer":
            raise ValueError("Only signed user transfers can be added through add_transaction")
        if self._transaction_id_exists(transaction.transaction_id):
            raise ValueError("Duplicate transaction")
        if not transaction.verify():
            raise ValueError("Invalid transaction signature or transaction data")
        if self.get_available_balance(transaction.sender_address) < transaction.amount:
            raise ValueError("Insufficient confirmed balance")
        self.pending_transactions.append(transaction)
        return transaction.transaction_id

    def _has_faucet_claim(self, address: str) -> bool:
        return any(tx.transaction_type == "faucet" and tx.receiver_address == address for tx in self.all_confirmed_transactions() + self.pending_transactions)

    def request_faucet(self, address: str) -> Transaction:
        if not validate_address(address):
            raise ValueError("Invalid wallet address")
        if self._has_faucet_claim(address):
            raise ValueError("This address has already claimed the educational faucet")
        tx = Transaction.create_system(address, self.faucet_amount, "faucet")
        self.pending_transactions.append(tx)
        return tx

    def mine_pending_transactions(self, miner_address: str) -> MiningResult:
        if not validate_address(miner_address):
            raise ValueError("Invalid miner wallet address")
        if not self.pending_transactions:
            raise ValueError("No pending transactions to mine")
        current_validation = self.validate_chain()
        if not current_validation.valid:
            raise ValueError("Cannot mine on an invalid blockchain")
        reward = Transaction.create_system(miner_address, self.mining_reward, "mining_reward")
        candidate_transactions = list(self.pending_transactions) + [reward]
        block = Block(len(self.chain), utc_now(), candidate_transactions, self.chain[-1].hash, miner_address, self.difficulty)
        attempts = block.mine()
        validation = self.validate_chain(self.chain + [block])
        if not validation.valid:
            raise ValueError("Mined block failed validation: " + "; ".join(validation.errors))
        self.chain.append(block)
        self.pending_transactions.clear()
        return MiningResult(block=block, attempts=attempts)

    def validate_chain(self, chain: list[Block] | None = None) -> ValidationResult:
        blocks = self.chain if chain is None else chain
        errors: list[str] = []
        if not blocks:
            return ValidationResult(False, ["Blockchain has no genesis block"])
        genesis = blocks[0]
        if genesis.index != 0:
            errors.append("Genesis block index must be 0")
        if genesis.previous_hash != "0" * 64:
            errors.append("Genesis previous hash is invalid")
        if genesis.transactions:
            errors.append("Genesis block must not contain transactions")
        if genesis.miner_address != "GENESIS":
            errors.append("Genesis miner marker is invalid")
        if genesis.difficulty != 0:
            errors.append("Genesis difficulty must be 0")
        if genesis.hash != genesis.calculate_hash():
            errors.append("Genesis block hash mismatch")

        balances: dict[str, int] = {}
        faucet_claims: set[str] = set()
        seen_ids: set[str] = set()
        for position, block in enumerate(blocks[1:], start=1):
            if block.index != position:
                errors.append(f"Block {position}: index mismatch")
            if block.previous_hash != blocks[position - 1].hash:
                errors.append(f"Block {position}: previous-hash link mismatch")
            if block.hash != block.calculate_hash():
                errors.append(f"Block {position}: stored hash mismatch")
            if block.difficulty < 1 or not block.hash.startswith("0" * block.difficulty):
                errors.append(f"Block {position}: Proof of Work target not satisfied")
            if not validate_address(block.miner_address):
                errors.append(f"Block {position}: invalid miner address")
            rewards = [tx for tx in block.transactions if tx.transaction_type == "mining_reward"]
            if len(rewards) != 1:
                errors.append(f"Block {position}: exactly one mining reward is required")
            elif block.transactions and block.transactions[-1].transaction_type != "mining_reward":
                errors.append(f"Block {position}: mining reward must be the last transaction")
            block_start_balances = dict(balances)
            spent_in_block: dict[str, int] = {}
            for tx_index, tx in enumerate(block.transactions):
                label = f"Block {position} transaction {tx_index}"
                if tx.transaction_id in seen_ids:
                    errors.append(f"{label}: duplicate transaction ID")
                    continue
                seen_ids.add(tx.transaction_id)
                if tx.transaction_type == "transfer":
                    if not tx.verify():
                        errors.append(f"{label}: invalid signed transaction")
                        continue
                    already_spent = spent_in_block.get(tx.sender_address, 0)
                    spendable = block_start_balances.get(tx.sender_address, 0) - already_spent
                    if spendable < tx.amount:
                        errors.append(f"{label}: transaction overspends confirmed balance")
                        continue
                    spent_in_block[tx.sender_address] = already_spent + tx.amount
                    balances[tx.sender_address] = balances.get(tx.sender_address, 0) - tx.amount
                    balances[tx.receiver_address] = balances.get(tx.receiver_address, 0) + tx.amount
                elif tx.transaction_type == "faucet":
                    if not tx.system_integrity_valid():
                        errors.append(f"{label}: invalid faucet transaction structure")
                        continue
                    if not validate_address(tx.receiver_address):
                        errors.append(f"{label}: invalid faucet receiver address")
                        continue
                    if tx.amount != self.faucet_amount:
                        errors.append(f"{label}: faucet amount violates chain policy")
                        continue
                    if tx.receiver_address in faucet_claims:
                        errors.append(f"{label}: duplicate faucet claim")
                        continue
                    faucet_claims.add(tx.receiver_address)
                    balances[tx.receiver_address] = balances.get(tx.receiver_address, 0) + tx.amount
                elif tx.transaction_type == "mining_reward":
                    if not tx.system_integrity_valid():
                        errors.append(f"{label}: invalid mining reward structure")
                        continue
                    if tx.receiver_address != block.miner_address:
                        errors.append(f"{label}: reward receiver does not match miner")
                        continue
                    if tx.amount != self.mining_reward:
                        errors.append(f"{label}: mining reward violates chain policy")
                        continue
                    balances[tx.receiver_address] = balances.get(tx.receiver_address, 0) + tx.amount
                else:
                    errors.append(f"{label}: unsupported transaction type {tx.transaction_type!r}")
        return ValidationResult(valid=not errors, errors=errors)

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version, "difficulty": self.difficulty, "mining_reward": self.mining_reward, "faucet_amount": self.faucet_amount, "chain": [block.to_dict() for block in self.chain], "pending_transactions": [tx.to_dict() for tx in self.pending_transactions]}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Blockchain":
        if int(data.get("schema_version", -1)) != SCHEMA_VERSION:
            raise ValueError("Unsupported blockchain schema version")
        required = {"difficulty", "mining_reward", "faucet_amount", "chain", "pending_transactions"}
        missing = sorted(required - data.keys())
        if missing:
            raise ValueError(f"Blockchain data missing fields: {', '.join(missing)}")
        if not isinstance(data["chain"], list) or not isinstance(data["pending_transactions"], list):
            raise ValueError("Blockchain chain and pending_transactions must be lists")
        instance = cls(difficulty=int(data["difficulty"]), mining_reward=int(data["mining_reward"]), faucet_amount=int(data["faucet_amount"]), create_genesis=False)
        instance.chain = [Block.from_dict(item) for item in data["chain"]]
        instance.pending_transactions = [Transaction.from_dict(item) for item in data["pending_transactions"]]
        if not instance.chain:
            raise ValueError("Persisted blockchain is missing its genesis block")
        return instance
