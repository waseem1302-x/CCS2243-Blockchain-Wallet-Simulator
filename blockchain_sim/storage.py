from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .wallet import Wallet


def write_json_atomic(path: Path, data: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=True, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def read_json(path: Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("JSON root must be an object")
    return data


def wallet_path(address: str, wallets_dir: Path) -> Path:
    return Path(wallets_dir) / f"{address}.json"


def save_wallet(wallet: Wallet, wallets_dir: Path) -> Path:
    path = wallet_path(wallet.address, wallets_dir)
    write_json_atomic(path, wallet.to_dict())
    return path


def load_wallet(address: str, wallets_dir: Path) -> Wallet:
    path = wallet_path(address, wallets_dir)
    if not path.exists():
        raise FileNotFoundError(f"Wallet not found: {address}")
    return Wallet.from_dict(read_json(path))


def list_wallets(wallets_dir: Path) -> list[Wallet]:
    directory = Path(wallets_dir)
    if not directory.exists():
        return []
    wallets: list[Wallet] = []
    for path in sorted(directory.glob("*.json")):
        wallets.append(Wallet.from_dict(read_json(path)))
    return wallets


def save_blockchain(blockchain, path: Path) -> Path:
    path = Path(path)
    write_json_atomic(path, blockchain.to_dict())
    return path


def load_blockchain(
    path: Path,
    *,
    difficulty: int | None = None,
    mining_reward: int | None = None,
    faucet_amount: int | None = None,
):
    from .blockchain import Blockchain
    from .config import DEFAULT_DIFFICULTY, DEFAULT_FAUCET_AMOUNT, DEFAULT_MINING_REWARD

    path = Path(path)
    if not path.exists():
        return Blockchain(
            difficulty=DEFAULT_DIFFICULTY if difficulty is None else difficulty,
            mining_reward=DEFAULT_MINING_REWARD if mining_reward is None else mining_reward,
            faucet_amount=DEFAULT_FAUCET_AMOUNT if faucet_amount is None else faucet_amount,
        )
    return Blockchain.from_dict(read_json(path))
