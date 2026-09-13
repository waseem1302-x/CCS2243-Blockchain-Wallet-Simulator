import pytest

from blockchain_sim.blockchain import Blockchain
from blockchain_sim.transaction import Transaction
from blockchain_sim.wallet import Wallet


def _wallet(name, password="pw"):
    return Wallet.create(name, password, kdf_iterations=1000)


def _transfer(sender: Wallet, receiver: Wallet, amount: int, password="pw"):
    tx = Transaction.create_transfer(sender.address, receiver.address, amount, sender.public_key)
    tx.sign(sender.unlock_private_key(password))
    return tx


def _fund(chain: Blockchain, wallet: Wallet, miner: Wallet):
    chain.request_faucet(wallet.address)
    assert chain.get_confirmed_balance(wallet.address) == 0
    chain.mine_pending_transactions(miner.address)


def test_genesis_chain_is_valid():
    chain = Blockchain(difficulty=1, mining_reward=7, faucet_amount=100)
    result = chain.validate_chain()
    assert result.valid, result.errors
    assert len(chain.chain) == 1


def test_faucet_requires_mining_then_credits_balance_and_only_once():
    chain = Blockchain(difficulty=1, mining_reward=7, faucet_amount=100)
    alice, miner = _wallet("Alice"), _wallet("Miner")
    chain.request_faucet(alice.address)
    assert chain.get_confirmed_balance(alice.address) == 0
    assert len(chain.pending_transactions) == 1
    chain.mine_pending_transactions(miner.address)
    assert chain.get_confirmed_balance(alice.address) == 100
    assert chain.get_confirmed_balance(miner.address) == 7
    with pytest.raises(ValueError, match="already"):
        chain.request_faucet(alice.address)


def test_valid_transfer_moves_confirmed_balance_after_mining():
    chain = Blockchain(difficulty=1, mining_reward=7, faucet_amount=100)
    alice, bob, miner = _wallet("Alice"), _wallet("Bob"), _wallet("Miner")
    _fund(chain, alice, miner)
    tx = _transfer(alice, bob, 25)
    chain.add_transaction(tx)
    assert chain.get_confirmed_balance(bob.address) == 0
    assert chain.get_available_balance(alice.address) == 75
    chain.mine_pending_transactions(miner.address)
    assert chain.get_confirmed_balance(alice.address) == 75
    assert chain.get_confirmed_balance(bob.address) == 25
    assert chain.validate_chain().valid


def test_overspending_and_pending_overspending_are_rejected():
    chain = Blockchain(difficulty=1, mining_reward=7, faucet_amount=100)
    alice, bob, carol, miner = _wallet("Alice"), _wallet("Bob"), _wallet("Carol"), _wallet("Miner")
    _fund(chain, alice, miner)
    with pytest.raises(ValueError, match="Insufficient"):
        chain.add_transaction(_transfer(alice, bob, 101))
    chain.add_transaction(_transfer(alice, bob, 60))
    with pytest.raises(ValueError, match="Insufficient"):
        chain.add_transaction(_transfer(alice, carol, 50))


def test_duplicate_pending_transaction_is_rejected():
    chain = Blockchain(difficulty=1, mining_reward=7, faucet_amount=100)
    alice, bob, miner = _wallet("Alice"), _wallet("Bob"), _wallet("Miner")
    _fund(chain, alice, miner)
    tx = _transfer(alice, bob, 10)
    chain.add_transaction(tx)
    with pytest.raises(ValueError, match="Duplicate"):
        chain.add_transaction(Transaction.from_dict(tx.to_dict()))


def test_historical_transaction_tamper_invalidates_chain():
    chain = Blockchain(difficulty=1, mining_reward=7, faucet_amount=100)
    alice, bob, miner = _wallet("Alice"), _wallet("Bob"), _wallet("Miner")
    _fund(chain, alice, miner)
    chain.add_transaction(_transfer(alice, bob, 20))
    chain.mine_pending_transactions(miner.address)
    assert chain.validate_chain().valid
    transfer = next(tx for tx in chain.chain[-1].transactions if tx.transaction_type == "transfer")
    transfer.amount = 2000
    result = chain.validate_chain()
    assert not result.valid
    assert any("hash" in e.lower() or "transaction" in e.lower() for e in result.errors)


def test_mining_requires_pending_work():
    chain = Blockchain(difficulty=1, mining_reward=7, faucet_amount=100)
    miner = _wallet("Miner")
    with pytest.raises(ValueError, match="pending"):
        chain.mine_pending_transactions(miner.address)
