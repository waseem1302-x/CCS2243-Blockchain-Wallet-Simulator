import json
import pytest

from blockchain_sim.wallet import Wallet


def test_wallet_creation_produces_unique_valid_addresses():
    a = Wallet.create("Alice", "pw-a", kdf_iterations=1000)
    b = Wallet.create("Bob", "pw-b", kdf_iterations=1000)
    assert a.address != b.address
    assert a.public_key != b.public_key


def test_wallet_unlocks_with_correct_password_and_rejects_wrong_password():
    wallet = Wallet.create("Alice", "correct", kdf_iterations=1000)
    private_key = wallet.unlock_private_key("correct")
    assert len(private_key) == 32
    with pytest.raises(ValueError, match="password|tampered"):
        wallet.unlock_private_key("wrong")


def test_wallet_serialization_never_contains_plaintext_private_key():
    wallet = Wallet.create("Alice", "top-secret", kdf_iterations=1000)
    data = wallet.to_dict()
    serialized = json.dumps(data)
    assert "private_key" not in data
    assert "top-secret" not in serialized
    assert data["encrypted_private_key"]
