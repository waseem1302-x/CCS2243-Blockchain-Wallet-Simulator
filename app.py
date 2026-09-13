from __future__ import annotations

import copy
import json
import time
from pathlib import Path

import streamlit as st

from blockchain_sim.blockchain import Blockchain
from blockchain_sim.config import (
    CHAIN_NAME,
    DEFAULT_DIFFICULTY,
    DEFAULT_FAUCET_AMOUNT,
    DEFAULT_MINING_REWARD,
    atomic_to_coins,
    coins_to_atomic,
)
from blockchain_sim.crypto_utils import sha256_bytes, verify_signature
from blockchain_sim.storage import list_wallets, load_blockchain, save_blockchain, save_wallet
from blockchain_sim.transaction import Transaction
from blockchain_sim.wallet import Wallet

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
WALLETS_DIR = DATA_DIR / "wallets"
CHAIN_PATH = DATA_DIR / "blockchain.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)
WALLETS_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="CCS2243 Blockchain Wallet Simulator", page_icon="🔐", layout="wide")


def load_state() -> tuple[Blockchain, list[Wallet]]:
    try:
        chain = load_blockchain(
            CHAIN_PATH,
            difficulty=DEFAULT_DIFFICULTY,
            mining_reward=DEFAULT_MINING_REWARD,
            faucet_amount=DEFAULT_FAUCET_AMOUNT,
        )
        wallets = list_wallets(WALLETS_DIR)
        return chain, wallets
    except Exception as exc:
        st.error(f"Could not load local simulator state: {exc}")
        st.info("If the local JSON file was manually modified, restore it or use the reset option after backing it up.")
        st.stop()


def short(value: str, width: int = 16) -> str:
    if len(value) <= width * 2 + 3:
        return value
    return f"{value[:width]}...{value[-width:]}"


def coins(value: int) -> str:
    return f"{atomic_to_coins(value):,.8f}".rstrip("0").rstrip(".") + " EDU"


def wallet_label(wallet: Wallet) -> str:
    return f"{wallet.name} — {short(wallet.address, 8)}"


def tx_rows(transactions: list[Transaction]) -> list[dict[str, object]]:
    rows = []
    for tx in transactions:
        rows.append(
            {
                "Type": tx.transaction_type,
                "ID": short(tx.transaction_id, 10),
                "From": short(tx.sender_address, 8),
                "To": short(tx.receiver_address, 8),
                "Amount": coins(tx.amount),
                "Signed": bool(tx.signature),
            }
        )
    return rows


def render_validation(chain: Blockchain) -> None:
    result = chain.validate_chain()
    if result.valid:
        st.success("Blockchain VALID — hashes, Proof of Work, signatures, balances and issuance rules all passed.")
    else:
        st.error(f"Blockchain INVALID — {len(result.errors)} validation problem(s) detected.")
        for error in result.errors:
            st.write(f"• {error}")


chain, wallets = load_state()

st.title("🔐 Blockchain Wallet Simulator")
st.caption("CCS2243 Cryptography Essential — educational single-node blockchain with ECDSA, SHA-256, AES-GCM and Proof of Work")

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Wallets",
        "Send Transaction",
        "Mempool & Mining",
        "Blockchain Explorer",
        "Security Lab",
        "System & About",
    ],
)

st.sidebar.markdown("---")
st.sidebar.caption(CHAIN_NAME)
st.sidebar.caption(f"Difficulty: {chain.difficulty} leading zeroes")
st.sidebar.caption(f"Blocks: {len(chain.chain)} | Pending: {len(chain.pending_transactions)}")

if page == "Dashboard":
    validation = chain.validate_chain()
    confirmed_count = sum(len(block.transactions) for block in chain.chain[1:])
    cols = st.columns(5)
    cols[0].metric("Chain height", max(0, len(chain.chain) - 1))
    cols[1].metric("Wallets", len(wallets))
    cols[2].metric("Confirmed TX", confirmed_count)
    cols[3].metric("Mempool", len(chain.pending_transactions))
    cols[4].metric("Chain status", "VALID" if validation.valid else "INVALID")

    st.subheader("Cryptographic health check")
    render_validation(chain)

    st.subheader("Wallet balances")
    if not wallets:
        st.info("Create your first wallet from the Wallets page.")
    else:
        rows = []
        for wallet in wallets:
            rows.append(
                {
                    "Wallet": wallet.name,
                    "Address": wallet.address,
                    "Confirmed": coins(chain.get_confirmed_balance(wallet.address)),
                    "Available after pending spends": coins(chain.get_available_balance(wallet.address)),
                }
            )
        st.dataframe(rows, use_container_width=True, hide_index=True)

    st.subheader("How the simulator protects a transaction")
    st.code(
        "Wallet private key -> ECDSA signature\n"
        "Transaction fields -> canonical JSON -> SHA-256 transaction ID\n"
        "Pending transactions -> block -> nonce search -> SHA-256 Proof of Work\n"
        "Block N stores hash(Block N-1) -> tamper-evident chain",
        language="text",
    )

elif page == "Wallets":
    st.header("Wallets & encrypted private keys")
    st.write(
        "Each wallet uses a secp256k1 ECDSA key pair. The private key is encrypted locally with "
        "PBKDF2-HMAC-SHA256 + AES-256-GCM; the plaintext private key is never written to JSON."
    )

    with st.form("create_wallet", clear_on_submit=True):
        name = st.text_input("Wallet name", placeholder="Alice")
        password = st.text_input("Password", type="password")
        confirm = st.text_input("Confirm password", type="password")
        submitted = st.form_submit_button("Create encrypted wallet")
        if submitted:
            if password != confirm:
                st.error("Passwords do not match.")
            else:
                try:
                    wallet = Wallet.create(name, password)
                    save_wallet(wallet, WALLETS_DIR)
                    st.success(f"Wallet created: {wallet.address}")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

    st.subheader("Saved wallets")
    if not wallets:
        st.info("No wallets yet.")
    for wallet in wallets:
        with st.expander(f"{wallet.name} — {wallet.address}"):
            left, right = st.columns(2)
            left.write("**Public address**")
            left.code(wallet.address)
            left.write("**Compressed secp256k1 public key**")
            left.code(wallet.public_key)
            right.metric("Confirmed balance", coins(chain.get_confirmed_balance(wallet.address)))
            right.metric("Available balance", coins(chain.get_available_balance(wallet.address)))
            right.write("**Encrypted keystore evidence**")
            right.code(
                json.dumps(
                    {
                        "encrypted_private_key": short(wallet.encrypted_private_key, 22),
                        "salt": wallet.salt,
                        "nonce": wallet.nonce,
                        "kdf_iterations": wallet.kdf_iterations,
                    },
                    indent=2,
                ),
                language="json",
            )
            if st.button("Request 100 EDU test coins", key=f"faucet-{wallet.address}"):
                try:
                    chain.request_faucet(wallet.address)
                    save_blockchain(chain, CHAIN_PATH)
                    st.success("Faucet transaction added to the mempool. Mine a block to confirm it.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

elif page == "Send Transaction":
    st.header("Create & sign a transaction")
    if len(wallets) < 1:
        st.warning("Create a wallet first.")
    else:
        wallet_by_label = {wallet_label(w): w for w in wallets}
        sender_label = st.selectbox("Sender wallet", list(wallet_by_label))
        sender = wallet_by_label[sender_label]
        receiver_mode = st.radio("Receiver", ["Saved wallet", "Custom address"], horizontal=True)
        if receiver_mode == "Saved wallet" and wallets:
            receiver_options = {wallet_label(w): w.address for w in wallets if w.address != sender.address}
            if receiver_options:
                receiver_label = st.selectbox("Receiver wallet", list(receiver_options))
                receiver_address = receiver_options[receiver_label]
            else:
                receiver_address = ""
                st.info("Create another wallet or use a custom address.")
        else:
            receiver_address = st.text_input("Receiver address")

        amount_text = st.text_input("Amount (EDU)", value="1")
        password = st.text_input("Sender wallet password", type="password")
        if st.button("Hash, sign & add to mempool", type="primary"):
            try:
                amount = coins_to_atomic(amount_text)
                private_key = sender.unlock_private_key(password)
                tx = Transaction.create_transfer(sender.address, receiver_address.strip(), amount, sender.public_key)
                tx.sign(private_key)
                del private_key
                chain.add_transaction(tx)
                save_blockchain(chain, CHAIN_PATH)
                st.success("Transaction signature verified and transaction accepted into the mempool.")
                st.write("**Transaction ID (SHA-256)**")
                st.code(tx.transaction_id)
                st.write("**ECDSA signature (DER, hexadecimal)**")
                st.code(tx.signature or "")
                st.write(f"Signature verification: **{tx.verify()}**")
            except Exception as exc:
                st.error(str(exc))

elif page == "Mempool & Mining":
    st.header("Mempool & Proof-of-Work mining")
    if chain.pending_transactions:
        st.dataframe(tx_rows(chain.pending_transactions), use_container_width=True, hide_index=True)
    else:
        st.info("The mempool is empty. Request faucet coins or create a signed transfer first.")

    if wallets:
        miner_map = {wallet_label(w): w for w in wallets}
        miner = miner_map[st.selectbox("Miner wallet", list(miner_map))]
        st.write(
            f"Current target: block hash must start with **{'0' * chain.difficulty}**. "
            f"Mining reward: **{coins(chain.mining_reward)}**."
        )
        if st.button("Mine pending transactions", type="primary"):
            try:
                start = time.perf_counter()
                result = chain.mine_pending_transactions(miner.address)
                elapsed = time.perf_counter() - start
                save_blockchain(chain, CHAIN_PATH)
                st.success("Block mined and independently validated before being appended.")
                c1, c2, c3 = st.columns(3)
                c1.metric("Nonce", result.block.nonce)
                c2.metric("Hash attempts", result.attempts)
                c3.metric("Elapsed", f"{elapsed:.4f} s")
                st.write("**Block hash**")
                st.code(result.block.hash)
                st.write("**Previous block hash**")
                st.code(result.block.previous_hash)
            except Exception as exc:
                st.error(str(exc))

elif page == "Blockchain Explorer":
    st.header("Blockchain Explorer")
    render_validation(chain)
    for block in reversed(chain.chain):
        title = "Genesis Block" if block.index == 0 else f"Block #{block.index} — {len(block.transactions)} transaction(s)"
        with st.expander(title, expanded=block.index == len(chain.chain) - 1):
            c1, c2, c3 = st.columns(3)
            c1.write(f"**Timestamp:** {block.timestamp}")
            c1.write(f"**Miner:** {block.miner_address}")
            c2.write(f"**Difficulty:** {block.difficulty}")
            c2.write(f"**Nonce:** {block.nonce}")
            c3.write(f"**PoW valid:** {block.is_pow_valid() if block.index > 0 else block.hash == block.calculate_hash()}")
            st.write("**Block hash**")
            st.code(block.hash)
            st.write("**Previous hash**")
            st.code(block.previous_hash)
            if block.transactions:
                st.dataframe(tx_rows(block.transactions), use_container_width=True, hide_index=True)
                for tx in block.transactions:
                    with st.expander(f"Transaction details — {short(tx.transaction_id, 12)}"):
                        st.json(tx.to_dict())
            else:
                st.caption("Genesis contains no transactions by design.")

elif page == "Security Lab":
    st.header("Security Lab — demonstrate cryptographic failure")
    st.info("All tampering below happens on an in-memory deep copy. Your saved blockchain is not modified.")

    st.subheader("1. Blockchain tamper detection")
    tamperable = [b for b in chain.chain[1:] if b.transactions]
    if tamperable:
        indexes = [b.index for b in tamperable]
        chosen_index = st.selectbox("Block to attack", indexes)
        attack = st.radio("Attack", ["Change transaction amount", "Change block nonce"], horizontal=True)
        if st.button("Run tamper experiment"):
            attacked = copy.deepcopy(chain)
            target = attacked.chain[chosen_index]
            if attack == "Change transaction amount":
                target.transactions[0].amount += 1
            else:
                target.nonce += 1
            result = attacked.validate_chain()
            st.write(f"Validation result after attack: **{'VALID' if result.valid else 'INVALID'}**")
            for error in result.errors:
                st.error(error)
    else:
        st.caption("Mine at least one non-genesis block to enable this experiment.")

    st.subheader("2. Password-protected private key")
    if wallets:
        target_wallet = {wallet_label(w): w for w in wallets}[st.selectbox("Wallet for unlock test", [wallet_label(w) for w in wallets])]
        test_password = st.text_input("Password to test", type="password", key="lab-password")
        if st.button("Attempt AES-GCM wallet unlock"):
            try:
                target_wallet.unlock_private_key(test_password)
                st.success("Authenticated decryption succeeded: password and ciphertext are valid.")
            except Exception as exc:
                st.error(f"Authenticated decryption rejected the attempt: {exc}")

    st.subheader("3. Wrong-public-key signature verification")
    transfers = [tx for block in chain.chain for tx in block.transactions if tx.transaction_type == "transfer"]
    if transfers and len(wallets) >= 2:
        tx = transfers[-1]
        alternatives = [w for w in wallets if w.public_key != tx.sender_public_key]
        if alternatives:
            wrong_wallet = alternatives[0]
            if st.button("Verify latest transfer with a different wallet public key"):
                ok = verify_signature(bytes.fromhex(wrong_wallet.public_key), bytes.fromhex(tx.transaction_id), tx.signature or "")
                st.write(f"Verification with **{wrong_wallet.name}** public key: **{ok}**")
                if not ok:
                    st.success("Expected result: ECDSA rejects a signature checked with the wrong public key.")
    else:
        st.caption("Confirm at least one wallet-to-wallet transfer to enable this experiment.")

    st.subheader("4. SHA-256 avalanche demonstration")
    original = st.text_input("Original text", value="Blockchain")
    changed = st.text_input("Changed text", value="blockchain")
    h1 = sha256_bytes(original)
    h2 = sha256_bytes(changed)
    bit_changes = sum((a ^ b).bit_count() for a, b in zip(h1, h2))
    st.code(f"SHA-256(original) = {h1.hex()}\nSHA-256(changed)  = {h2.hex()}")
    st.write(f"Different output bits: **{bit_changes} / 256 ({bit_changes / 256 * 100:.2f}%)**")

elif page == "System & About":
    st.header("System & About")
    st.markdown(
        """
### Algorithms demonstrated
- **ECDSA over secp256k1** — proves that a transaction was authorized by the holder of a wallet private key.
- **SHA-256** — transaction IDs, block hashes, Proof of Work, and avalanche demonstration.
- **SHA-256 + RIPEMD-160 + Base58Check-style encoding** — readable educational wallet addresses with checksum.
- **PBKDF2-HMAC-SHA256** — converts a human password plus random salt into a 256-bit encryption key.
- **AES-256-GCM** — encrypts wallet private keys and authenticates the encrypted keystore.
- **Hash-linked blocks + Proof of Work** — makes historical modification observable during full-chain validation.

### Scope
This is a **single-node educational simulator**. It deliberately does not implement real peer-to-peer networking, distributed consensus, smart contracts, exchanges, seed phrases, hardware wallets, or real cryptocurrency.
        """
    )
    st.write("**Local blockchain state:**", CHAIN_PATH)
    st.write("**Encrypted wallet files:**", WALLETS_DIR)
    render_validation(chain)

    st.subheader("Reset classroom demo")
    st.warning("Reset deletes the local simulator blockchain and encrypted wallet files on this computer.")
    confirmation = st.text_input("Type RESET to enable")
    if st.button("Delete local demo state", disabled=confirmation != "RESET"):
        try:
            if CHAIN_PATH.exists():
                CHAIN_PATH.unlink()
            if WALLETS_DIR.exists():
                for item in WALLETS_DIR.glob("*.json"):
                    item.unlink()
            st.success("Local demo state reset.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))
