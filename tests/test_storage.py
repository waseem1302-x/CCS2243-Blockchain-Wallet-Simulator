from pathlib import Path
import pytest

from blockchain_sim.blockchain import Blockchain
from blockchain_sim.storage import list_wallets, load_blockchain, load_wallet, save_blockchain, save_wallet
from blockchain_sim.wallet import Wallet


def test_wallet_storage_round_trip(tmp_path: Path):
    wallet = Wallet.create("Alice", "pw", kdf_iterations=1000)
    save_wallet(wallet, tmp_path)
    restored = load_wallet(wallet.address, tmp_path)
    assert restored.to_dict() == wallet.to_dict()
    assert [w.address for w in list_wallets(tmp_path)] == [wallet.address]


def test_blockchain_storage_round_trip_preserves_chain_and_mempool(tmp_path: Path):
    state = tmp_path / "blockchain.json"
    chain = Blockchain(difficulty=1, mining_reward=7, faucet_amount=100)
    alice = Wallet.create("Alice", "pw", kdf_iterations=1000)
    chain.request_faucet(alice.address)
    save_blockchain(chain, state)
    restored = load_blockchain(state)
    assert restored.to_dict() == chain.to_dict()


def test_missing_blockchain_file_initializes_clean_chain(tmp_path: Path):
    restored = load_blockchain(tmp_path / "missing.json", difficulty=1, mining_reward=7, faucet_amount=100)
    assert len(restored.chain) == 1
    assert restored.validate_chain().valid


def test_corrupt_schema_is_rejected(tmp_path: Path):
    state = tmp_path / "blockchain.json"
    state.write_text('{"schema_version": 999}', encoding="utf-8")
    with pytest.raises(ValueError, match="schema"):
        load_blockchain(state)
