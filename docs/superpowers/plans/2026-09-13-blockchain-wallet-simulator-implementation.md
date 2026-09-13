# Blockchain Wallet Simulator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a complete local educational blockchain wallet simulator that demonstrates wallet key generation, password-protected private keys, signed transfers, account balances, faucet funding, Proof-of-Work mining, chain validation, tamper detection, persistence, and a Streamlit classroom UI.

**Architecture:** The domain logic lives in a focused `blockchain_sim` package and remains independent from Streamlit. Wallets use ECDSA/secp256k1, private keys are encrypted with PBKDF2-HMAC-SHA256 + AES-256-GCM, balances are replayed from confirmed transactions, pending spends are tracked to prevent mempool overspending, and blocks are mined with a classroom-safe SHA-256 prefix difficulty. JSON persistence stores blockchain state and encrypted keystores.

**Tech Stack:** Python 3.11+, `cryptography`, `ecdsa`, `streamlit`, `pytest`.

**Spec:** `docs/superpowers/specs/2026-09-13-blockchain-wallet-simulator-design.md`

## Global Constraints

- Single-node local educational simulator only; no real cryptocurrency network.
- Account-based balance model.
- ECDSA on secp256k1 for normal user transaction signatures.
- SHA-256 for transaction IDs, block hashes, Proof of Work, and integrity demonstrations.
- Wallet addresses derived from public-key bytes using SHA-256 then RIPEMD-160 with Base58Check-style encoding.
- Private keys encrypted with PBKDF2-HMAC-SHA256 and AES-256-GCM; plaintext private keys are never persisted.
- Blockchain and wallet metadata persist as local JSON.
- Faucet and mining rewards are controlled system transactions.
- Monetary values are stored internally as integer atomic units; UI converts from/to whole or decimal demo coins.
- Default Proof-of-Work difficulty remains low enough for classroom use.
- UI must expose hashes, signatures, nonces, validation findings, and cryptographic algorithms instead of hiding them.

---

## File Map

- `blockchain_sim/config.py` — constants, atomic-unit helpers, chain policy.
- `blockchain_sim/crypto_utils.py` — hashing, address encoding, secp256k1 keys/signatures, KDF, AES-GCM.
- `blockchain_sim/wallet.py` — wallet creation, encrypted keystore, unlock/sign helpers.
- `blockchain_sim/transaction.py` — canonical transaction data, IDs, signing, verification, serialization.
- `blockchain_sim/block.py` — block model, hashing, Proof of Work.
- `blockchain_sim/blockchain.py` — ledger policy, mempool, faucet, mining, validation, tamper analysis helpers.
- `blockchain_sim/storage.py` — atomic JSON persistence and repository paths.
- `app.py` — Streamlit presentation layer.
- `tests/` — focused domain and persistence tests.
- `.github/workflows/tests.yml` — CI verification.
- `README.md` — setup, demo sequence, algorithms, limitations.

---

### Task 1: Project foundation and cryptographic primitives

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `blockchain_sim/__init__.py`
- Create: `blockchain_sim/config.py`
- Create: `blockchain_sim/crypto_utils.py`
- Create: `tests/test_crypto.py`
- Create: `.github/workflows/tests.yml`

**Interfaces:**
- Produces: `sha256_hex(data)`, `canonical_json(data)`, `generate_private_key_bytes()`, `private_to_public_bytes()`, `public_key_to_address()`, `sign_message()`, `verify_signature()`, `encrypt_private_key()`, `decrypt_private_key()`.

- [ ] Write tests for deterministic SHA-256, address derivation, ECDSA sign/verify, modified-message rejection, wrong-key rejection, encrypted private-key round trip, wrong-password rejection, and ciphertext tamper rejection.
- [ ] Add dependency pins/ranges and CI command `pytest -q`.
- [ ] Implement cryptographic helpers using `ecdsa.SECP256k1` and `cryptography.hazmat.primitives.ciphers.aead.AESGCM`.
- [ ] Run `pytest tests/test_crypto.py -q` and confirm all cryptography tests pass.
- [ ] Commit with message `feat: add cryptographic foundation`.

### Task 2: Password-protected wallets and persistence

**Files:**
- Create: `blockchain_sim/storage.py`
- Create: `blockchain_sim/wallet.py`
- Create: `tests/test_wallet.py`
- Create: `tests/test_storage.py`

**Interfaces:**
- Consumes: Task 1 cryptographic helpers.
- Produces: `Wallet.create(name, password)`, `Wallet.from_dict()`, `Wallet.to_dict()`, `Wallet.unlock_private_key(password)`, `save_wallet()`, `load_wallet()`, `list_wallets()`.

- [ ] Write tests proving two wallets have unique addresses, persisted wallet JSON contains no plaintext private key, correct password unlocks, wrong password fails, and storage round trips preserve metadata.
- [ ] Implement safe JSON writes with temp-file replacement.
- [ ] Implement wallet creation and encrypted keystore serialization.
- [ ] Run wallet/storage tests and confirm they pass.
- [ ] Commit with message `feat: add encrypted wallet keystore`.

### Task 3: Signed transactions and account ledger rules

**Files:**
- Create: `blockchain_sim/transaction.py`
- Create: `tests/test_transaction.py`
- Create: `blockchain_sim/blockchain.py` with transaction/mempool subset.
- Create: `tests/test_blockchain.py` with transaction/mempool cases.

**Interfaces:**
- Produces: `Transaction.create_transfer()`, `Transaction.create_system()`, `Transaction.sign()`, `Transaction.verify()`, `Blockchain.get_confirmed_balance()`, `Blockchain.get_available_balance()`, `Blockchain.add_transaction()`, `Blockchain.request_faucet()`.

- [ ] Write tests for valid signing, modified amount/receiver rejection, address-public-key mismatch, non-positive amount rejection, faucet creation, insufficient balance rejection, and pending overspend rejection.
- [ ] Implement canonical unsigned transaction payload and deterministic transaction ID rules.
- [ ] Implement signed transfer validation and system transaction creation guardrails.
- [ ] Implement replay-based confirmed balances plus pending outgoing deductions.
- [ ] Run transaction/blockchain subset tests and confirm they pass.
- [ ] Commit with message `feat: add signed transactions and ledger rules`.

### Task 4: Blocks, Proof of Work, mining rewards, and full validation

**Files:**
- Create: `blockchain_sim/block.py`
- Modify: `blockchain_sim/blockchain.py`
- Create: `tests/test_block.py`
- Extend: `tests/test_blockchain.py`

**Interfaces:**
- Produces: `Block.calculate_hash()`, `Block.mine()`, `Block.is_pow_valid()`, `Blockchain.mine_pending_transactions()`, `Blockchain.validate_chain()`.

- [ ] Write tests for deterministic block hashing, successful low-difficulty mining, post-mine tamper failure, genesis validity, multi-block linking, mining reward credit, duplicate transaction rejection, and historical tamper detection.
- [ ] Implement deterministic block serialization and nonce search.
- [ ] Implement genesis block rules and mining reward system transaction.
- [ ] Implement full chain replay validation: indexes, previous hashes, stored hashes, PoW, transaction IDs, signatures, ownership mapping, duplicate IDs, overspending, reward policy.
- [ ] Run block/blockchain tests and confirm they pass.
- [ ] Commit with message `feat: add proof of work blockchain validation`.

### Task 5: Blockchain state persistence and recovery

**Files:**
- Modify: `blockchain_sim/storage.py`
- Modify: `blockchain_sim/blockchain.py`
- Extend: `tests/test_storage.py`

**Interfaces:**
- Produces: `save_blockchain()`, `load_blockchain()`, `Blockchain.to_dict()`, `Blockchain.from_dict()`.

- [ ] Write tests for chain save/load equality, mempool preservation, clean initialization when no state file exists, and corrupt-schema rejection.
- [ ] Implement schema-versioned serialization for blocks, transactions, and chain state.
- [ ] Ensure a restarted application restores the same valid chain and wallet list.
- [ ] Run persistence tests and full suite.
- [ ] Commit with message `feat: persist blockchain state`.

### Task 6: Streamlit classroom interface and security lab

**Files:**
- Create: `app.py`
- Add: `data/.gitkeep`
- Add: `data/wallets/.gitkeep`

**Interfaces:**
- Consumes all domain APIs without duplicating cryptographic logic.

- [ ] Implement Dashboard metrics and chain validity panel.
- [ ] Implement Wallets page for create/list/balance/faucet with public-key and encrypted-keystore evidence.
- [ ] Implement Send Transaction page with password unlock, resulting transaction ID, signature, and verification status.
- [ ] Implement Mempool & Mining page with miner selection, nonce, difficulty, hash, elapsed time, and reward.
- [ ] Implement Blockchain Explorer with block headers, transactions, previous hash links, and PoW status.
- [ ] Implement Security Lab on deep copies: change amount, receiver, or nonce and show structured validation failures; add wrong-password and wrong-key signature demonstrations plus SHA-256 avalanche comparison.
- [ ] Implement About/System page describing algorithms and limitations.
- [ ] Manually launch with `streamlit run app.py` and exercise the complete demo sequence.
- [ ] Commit with message `feat: add Streamlit blockchain simulator UI`.

### Task 7: Documentation and final verification

**Files:**
- Create: `README.md`
- Optionally add: `docs/demo-checklist.md`

**Interfaces:**
- Documents installation, local run, demo flow, algorithms, project limitations, test commands, and report screenshot checklist.

- [ ] Document Python setup: virtual environment, `pip install -r requirements.txt`, `pytest -q`, `streamlit run app.py`.
- [ ] Document exact 14-step classroom demonstration from wallet creation through tamper detection.
- [ ] Document cryptographic algorithms and why each exists.
- [ ] Document that the project is educational and not a production cryptocurrency.
- [ ] Run the complete automated suite with `pytest -q`.
- [ ] Run Streamlit locally and perform smoke test for wallet create -> faucet -> mine -> send -> mine -> validate -> tamper lab.
- [ ] Commit with message `docs: add setup and demonstration guide`.

## Final Acceptance Checklist

- [ ] Automated tests pass in GitHub Actions.
- [ ] Wallet private key is never stored in plaintext.
- [ ] Wrong password fails AES-GCM authenticated decryption.
- [ ] Valid ECDSA transfer verifies; modified transfer fails.
- [ ] Pending overspend is rejected.
- [ ] Faucet funds are only confirmed after mining.
- [ ] Mining finds a nonce satisfying the configured SHA-256 target.
- [ ] Mining reward is credited by a controlled system transaction.
- [ ] Chain validator detects transaction tampering, nonce/hash tampering, and broken previous-hash linkage.
- [ ] JSON save/load preserves a valid chain.
- [ ] Streamlit UI exposes cryptographic evidence suitable for a live exam demonstration.
- [ ] README contains local commands and a presentation checklist.
