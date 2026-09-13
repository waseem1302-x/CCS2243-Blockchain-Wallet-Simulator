from blockchain_sim.block import Block
from blockchain_sim.transaction import Transaction


def test_block_hash_is_deterministic_for_identical_data():
    tx = Transaction.create_system("receiver", 10, "faucet", timestamp="2026-09-13T12:00:00+00:00")
    a = Block(1, "2026-09-13T12:00:01+00:00", [tx], "a" * 64, "miner", 1, nonce=7)
    b = Block(1, "2026-09-13T12:00:01+00:00", [Transaction.from_dict(tx.to_dict())], "a" * 64, "miner", 1, nonce=7)
    assert a.calculate_hash() == b.calculate_hash()


def test_mining_finds_hash_matching_difficulty_and_tamper_breaks_hash():
    tx = Transaction.create_system("receiver", 10, "faucet")
    block = Block(1, "2026-09-13T12:00:01+00:00", [tx], "a" * 64, "miner", 2)
    attempts = block.mine()
    assert attempts > 0
    assert block.hash.startswith("00")
    assert block.is_pow_valid()
    tx.amount += 1
    assert block.calculate_hash() != block.hash
