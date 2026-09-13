import pytest

from blockchain_sim.transaction import Transaction
from blockchain_sim.wallet import Wallet


def _wallet(name="Alice", password="pw"):
    return Wallet.create(name, password, kdf_iterations=1000)


def _signed_transfer(sender: Wallet, receiver: Wallet, amount: int = 5):
    tx = Transaction.create_transfer(sender.address, receiver.address, amount, sender.public_key, timestamp="2026-09-13T12:00:00+00:00")
    tx.sign(sender.unlock_private_key("pw"))
    return tx


def test_valid_signed_transfer_verifies():
    sender = _wallet()
    receiver = _wallet("Bob")
    tx = _signed_transfer(sender, receiver)
    assert tx.verify()
    assert tx.transaction_id
    assert tx.signature


def test_modifying_amount_or_receiver_invalidates_transfer():
    sender = _wallet()
    receiver = _wallet("Bob")
    other = _wallet("Carol")
    tx = _signed_transfer(sender, receiver)
    tx.amount += 1
    assert not tx.verify()
    tx.amount -= 1
    tx.receiver_address = other.address
    assert not tx.verify()


def test_sender_address_must_match_public_key():
    sender = _wallet()
    receiver = _wallet("Bob")
    impostor = _wallet("Mallory")
    tx = Transaction.create_transfer(impostor.address, receiver.address, 5, sender.public_key, timestamp="2026-09-13T12:00:00+00:00")
    tx.sign(sender.unlock_private_key("pw"))
    assert not tx.verify()


def test_non_positive_amount_is_rejected():
    sender = _wallet()
    receiver = _wallet("Bob")
    with pytest.raises(ValueError, match="greater than zero"):
        Transaction.create_transfer(sender.address, receiver.address, 0, sender.public_key)


def test_transaction_round_trip_preserves_verification():
    sender = _wallet()
    receiver = _wallet("Bob")
    tx = _signed_transfer(sender, receiver)
    restored = Transaction.from_dict(tx.to_dict())
    assert restored.to_dict() == tx.to_dict()
    assert restored.verify()
