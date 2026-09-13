# CCS2243 Blockchain Wallet Simulator — Design Specification

Date: 2026-09-13

## 1. Purpose

Build a complete educational blockchain wallet simulator for the CCS2243 Cryptography Essential project. The application must visibly demonstrate practical cryptography, not merely present a blockchain-themed interface.

The finished system will let a user create password-protected wallets, obtain test coins from a controlled faucet, create and cryptographically sign transactions, verify signatures, place valid transactions into a mempool, mine blocks with Proof of Work, receive mining rewards, inspect the chain, validate balances, persist state locally, and deliberately tamper with copied data to observe integrity failures.

The simulator is local, single-node, and educational. It does not connect to Bitcoin, Ethereum, public blockchains, exchanges, or real money.

## 2. Agreed Scope

- Python implementation with a modular package structure.
- Streamlit graphical user interface.
- Account-based balance model rather than UTXO.
- Local JSON persistence for blockchain state and wallet metadata.
- ECDSA on secp256k1 for wallet transaction signatures.
- SHA-256 for transaction IDs, block hashes, Proof of Work, and integrity demonstrations.
- Educational Base58Check-style wallet addresses derived from compressed public-key bytes through SHA-256 then RIPEMD-160, with version byte and checksum.
- Password-protected private keys using PBKDF2-HMAC-SHA256 and AES-256-GCM.
- Educational faucet for initial test coins.
- Mining rewards.
- Single local blockchain node.
- Proof-of-Work mining with configurable low difficulty suitable for classroom demonstration.
- Automated test suite covering normal, negative, and tamper cases.

## 3. Security and Educational Goals

The simulator must clearly demonstrate:

1. **Key ownership** — a wallet is controlled by a secp256k1 private key.
2. **Public-key cryptography** — public keys can be shared while private keys remain secret.
3. **Digital signatures** — a sender signs canonical transaction content; verification uses the sender public key.
4. **Hashing and integrity** — transaction and block hashes change when protected data changes.
5. **Tamper evidence** — modifying historical data breaks signatures, hashes, Proof of Work, and/or previous-hash links.
6. **Proof of Work** — miners search for a nonce whose SHA-256 block hash satisfies a configurable prefix difficulty.
7. **Password-based key protection** — PBKDF2-HMAC-SHA256 derives a 256-bit AES key from a password and random salt.
8. **Authenticated encryption** — AES-256-GCM encrypts private-key bytes and rejects wrong passwords or modified ciphertext.
9. **Blockchain linkage** — every non-genesis block commits to the previous block hash.
10. **Controlled coin issuance** — faucet and mining-reward transactions are system-issued and cannot be forged through the normal transaction API.

## 4. High-Level Architecture

Data flow:

`Streamlit UI -> Domain Models / Services -> Cryptographic Utilities -> Blockchain / Mempool -> JSON Storage`

Private-key flow:

`Password -> PBKDF2-HMAC-SHA256 -> AES-256-GCM -> Encrypted Private Key Keystore`

Transaction flow:

`Wallet -> Canonical Transaction Payload -> SHA-256 Transaction ID -> ECDSA Signature -> Verification -> Mempool -> Mining -> Confirmed Block`

Block flow:

`Pending Transactions -> Candidate Block + Mining Reward -> Nonce Search -> Difficulty Check -> Append -> Persist -> Ledger Replay`

## 5. Repository Structure

```text
CCS2243-Blockchain-Wallet-Simulator/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── blockchain_sim/
│   ├── __init__.py
│   ├── config.py
│   ├── crypto_utils.py
│   ├── wallet.py
│   ├── transaction.py
│   ├── block.py
│   ├── blockchain.py
│   └── storage.py
├── data/
│   ├── blockchain.json
│   └── wallets/
├── tests/
│   ├── test_crypto.py
│   ├── test_wallet.py
│   ├── test_transaction.py
│   ├── test_block.py
│   ├── test_blockchain.py
│   └── test_storage.py
└── docs/
    └── superpowers/
        └── specs/
```

Generated runtime data will be ignored by Git where appropriate; placeholder directories may use `.gitkeep`.

## 6. Component Responsibilities

### `config.py`
Centralizes chain name, address version, difficulty, mining reward, faucet amount, smallest-unit conversion, PBKDF2 iteration count, schema version, and related constants.

### `crypto_utils.py`
Provides focused helpers for:

- SHA-256 hashing.
- RIPEMD-160 hashing.
- Base58/Base58Check encoding and address checksum validation.
- secp256k1 key generation.
- Compressed public-key serialization.
- ECDSA signing and verification.
- PBKDF2-HMAC-SHA256 key derivation.
- AES-256-GCM private-key encryption/decryption.
- Canonical JSON serialization used before hashing/signing.

The implementation should prefer the `cryptography` library for secp256k1, ECDSA, PBKDF2, and AES-GCM, reducing unnecessary dependencies.

### `wallet.py`
Creates and loads wallets. A wallet exposes a name, address, and public key. Private-key bytes are decrypted only temporarily after the correct password is supplied. Plaintext private keys are never persisted.

### `transaction.py`
Represents normal transfers and system issuance transactions. It generates deterministic transaction IDs from canonical transaction content, signs normal transfers, verifies signatures, and serializes safely.

### `block.py`
Represents a block and performs deterministic block hashing and Proof-of-Work mining. Block hash calculation commits to index, timestamp, transactions, previous hash, nonce, miner address, and difficulty.

### `blockchain.py`
Owns chain policy:

- Genesis block creation.
- Mempool management.
- Confirmed-balance calculation through ledger replay.
- Faucet issuance.
- User-transaction validation.
- Mining-reward creation.
- Block mining.
- Full-chain validation.
- Duplicate transaction rejection.
- Pending overspend prevention.
- Tamper detection.

### `storage.py`
Owns JSON persistence and schema validation. Writes use a temporary file followed by replacement where practical to reduce corruption risk.

### `app.py`
Contains presentation and user interaction only. Cryptographic/domain logic stays in package modules so it can be tested independently.

## 7. Monetary Representation

To avoid floating-point errors, internal balances and transaction amounts use integer smallest units.

- `1 SIM = 100,000,000 units`.
- UI input/output may display decimal SIM values.
- Persisted transaction amounts use integer units.
- Conversion helpers reject values with more than eight decimal places.

This mirrors the general idea of using integer atomic units in real cryptocurrency software while keeping the project deterministic and testable.

## 8. Data Models

### Wallet metadata

```text
name
address
public_key
encrypted_private_key
salt
nonce
kdf_iterations
created_at
schema_version
```

The AES-GCM authentication tag is included in the encrypted output produced by the cryptography library.

### Normal transaction

```text
transaction_id
sender_address
receiver_address
amount_units
timestamp
sender_public_key
signature
transaction_type = "transfer"
```

### System transaction

```text
transaction_id
sender_address = "SYSTEM"
receiver_address
amount_units
timestamp
sender_public_key = null
signature = null
transaction_type = "faucet" | "mining_reward"
```

Only trusted blockchain methods may create system transactions.

### Block

```text
index
timestamp
transactions
previous_hash
nonce
miner_address
difficulty
hash
```

### Blockchain state

```text
schema_version
chain
pending_transactions
difficulty
mining_reward_units
faucet_amount_units
faucet_claimed_addresses
```

## 9. Transaction Lifecycle

1. User selects sender wallet and receiver address.
2. Application validates address checksum and verifies amount is positive.
3. Blockchain computes sender confirmed balance from chain replay.
4. Pending outgoing transfers from that sender are reserved; pending incoming transfers are not spendable until mined.
5. Application creates canonical unsigned transaction content.
6. Transaction ID is SHA-256 of the canonical unsigned content.
7. Sender private key is decrypted in memory after password validation.
8. The canonical unsigned content is signed using ECDSA with SHA-256 on secp256k1.
9. Blockchain verifies that the supplied public key derives to the claimed sender address.
10. Blockchain verifies the signature and transaction ID.
11. Blockchain checks for duplicates and available confirmed balance after pending reservations.
12. Valid transaction is added to the mempool and persisted.
13. Mining moves valid pending transactions into a confirmed block.

## 10. Faucet Rules

The faucet is educational system issuance, not a user-signed transfer.

- Each wallet address may claim the configured faucet amount once per blockchain state reset.
- `Blockchain.request_faucet(address)` creates a `faucet` system transaction and places it in the mempool.
- Faucet funds are **not spendable until the faucet transaction is mined into a block**.
- Faucet claims are recorded immediately to prevent duplicate pending claims.
- Faucet transactions use `SYSTEM` as sender and have no ECDSA signature.
- The UI labels them clearly as system-issued test coins.

This keeps issuance visible in the chain and avoids silently editing balances outside blockchain history.

## 11. Genesis Block

The genesis block is deterministic in structure:

- `index = 0`
- no transactions
- `previous_hash = 64 zero characters`
- `miner_address = "GENESIS"`
- `difficulty = 0`
- `nonce = 0`

Its hash is calculated normally from its canonical block content, but it does not require Proof of Work and does not contain a mining reward.

## 12. Mining and Proof of Work

A normal candidate block contains all currently valid mempool transactions plus exactly one `mining_reward` system transaction for the selected miner address.

The miner increments `nonce` and recalculates SHA-256 until:

`block_hash.startswith("0" * difficulty)`

The default difficulty is intentionally small so mining normally completes quickly on a student laptop. Difficulty is stored inside every block so historical Proof of Work can be revalidated.

When mining succeeds:

1. Pending transactions are revalidated against the confirmed ledger.
2. Exactly one correctly sized mining reward is appended.
3. Candidate block is mined.
4. The mined block is fully checked again.
5. Block is appended to the chain.
6. Included mempool transactions are removed.
7. State is persisted atomically where practical.
8. Miner reward becomes confirmed and spendable because it is now part of the block.

Mining an otherwise empty mempool is allowed for demonstration, but the block still contains exactly one mining-reward transaction.

## 13. Chain Validation

Full validation checks every block and transaction:

- Genesis block follows the fixed genesis rules.
- Stored block hash equals freshly calculated hash.
- Every non-genesis block satisfies its stored Proof-of-Work difficulty.
- Each `previous_hash` equals the actual preceding block hash.
- Block indexes are sequential.
- Normal transaction IDs equal freshly calculated IDs.
- Normal transaction signatures verify.
- Sender public key derives to sender address.
- Address checksums are valid.
- No duplicate confirmed transaction IDs.
- Ledger replay never allows a normal transfer to spend more confirmed funds than available at that point.
- Faucet transaction amount and per-address claim rule are respected.
- Every non-genesis block has exactly one mining reward transaction.
- Mining reward amount matches configured policy and recipient matches `miner_address`.
- Unknown system transaction types are rejected.

Validation returns structured findings so the UI can report the exact reason and block/transaction involved.

## 14. Tamper Lab

The Security Lab operates on a deep copy of the current chain by default so demonstrations cannot accidentally destroy the working ledger.

Required demonstrations:

- Change confirmed transaction amount -> transaction ID/signature mismatch and block hash mismatch.
- Change receiver address -> address/signature/hash validation failure.
- Change historical block nonce -> block hash and/or Proof-of-Work failure.
- Change a historical transaction -> affected block becomes invalid; subsequent chain linkage is also exposed when hashes are recomputed.
- Verify a transaction with another wallet public key -> verification fails.
- Unlock a wallet with wrong password -> AES-GCM authenticated decryption fails.
- Hash avalanche demonstration -> compare SHA-256 outputs and Hamming distance after a tiny input change.

The core project does not modify the persisted chain during tamper demonstrations; destructive editing is intentionally excluded to keep the classroom workflow reproducible.

## 15. Streamlit User Interface

The interface will use a clean academic dashboard rather than excessive animation.

1. **Dashboard** — chain height, confirmed transactions, mempool size, wallet count, difficulty, and current validity.
2. **Wallets** — create wallet, inspect address/public key, request faucet, and view confirmed/pending balance information.
3. **Send Transaction** — sender selection, password, receiver, amount, transaction ID, signature, and validation result.
4. **Mempool & Mining** — inspect pending transactions, select miner wallet, mine block, and display nonce/hash/time/reward.
5. **Blockchain Explorer** — inspect blocks, transactions, previous-hash links, Proof-of-Work status, and system vs user transactions.
6. **Security Lab** — transaction/block tampering, wrong password, wrong-key verification, and SHA-256 avalanche comparison.
7. **System / About** — algorithms, architecture summary, limitations, reset controls, and demo guidance.

Private keys are not displayed by default and are never written in plaintext. The project does not require a private-key reveal feature.

## 16. Error Handling

Expected errors become readable domain messages rather than raw tracebacks:

- Wrong wallet password.
- Invalid address or checksum.
- Invalid amount or too many decimal places.
- Insufficient balance.
- Invalid signature.
- Public-key/address mismatch.
- Corrupt wallet file.
- Corrupt blockchain file.
- Duplicate transaction.
- Duplicate faucet claim.
- Invalid persisted schema.

## 17. Testing Strategy

Development follows test-first implementation for domain behavior.

### Cryptography
- SHA-256 deterministic output.
- secp256k1 key pair signs and verifies.
- Modified message fails signature verification.
- Wrong public key fails verification.
- Address derives consistently from a public key.
- Address checksum corruption is rejected.
- Private-key encrypt/decrypt round trip succeeds.
- Wrong password fails AES-GCM decryption.
- Modified encrypted private-key payload fails authenticated decryption.

### Wallets
- Wallet creation produces unique addresses.
- Persisted wallet never contains plaintext private key.
- Correct password permits signing.

### Transactions
- Valid signed transfer verifies.
- Amount/receiver modification invalidates the transfer.
- Address/public-key mismatch is rejected.
- Non-positive amount is rejected.
- Amount conversion uses exact integer smallest units.

### Blocks
- Identical block content hashes deterministically.
- Mining produces a hash satisfying difficulty.
- Changing a mined block invalidates hash and/or Proof of Work.

### Blockchain
- Genesis-only chain validates.
- Faucet claim enters mempool but does not affect confirmed balance before mining.
- Mined faucet claim increases confirmed balance.
- Signed transfer changes confirmed balances only after mining.
- Overspending is rejected.
- Pending overspending is rejected.
- Mining reward is credited correctly.
- Empty-mempool reward-only mining is valid.
- Multiple linked blocks validate.
- Historical tampering invalidates the chain.
- Duplicate transaction IDs are rejected.
- Duplicate faucet claims are rejected.

### Persistence
- Save/load round trip preserves chain state.
- Wallet metadata save/load round trip works.
- Missing-data initialization creates a clean state.
- Runtime state is recoverable after application restart.

## 18. Implementation Phases

### Phase 1 — Cryptographic Foundation
- Repository foundation and dependencies.
- Cryptographic utilities.
- Wallet creation and address derivation.
- Password-protected keystore.
- Initial tests.

### Phase 2 — Transactions and Ledger Rules
- Transaction model.
- ECDSA signing and verification.
- Address/public-key ownership checks.
- Exact integer balances.
- Faucet issuance.
- Mempool and pending-overspend rules.
- Tests.

### Phase 3 — Blockchain, Mining, and Persistence
- Genesis block.
- Block model.
- Proof of Work.
- Mining rewards.
- Chain validation and ledger replay.
- JSON persistence/recovery.
- Tamper tests.

### Phase 4 — UI, Security Demonstrations, Documentation, Verification
- Streamlit dashboard and explorer.
- Wallet and transfer flows.
- Mining interface.
- Security Lab.
- README with setup, architecture, algorithm explanation, and demo script.
- Full automated verification.
- Manual local run checklist for the user.

## 19. Classroom Demo Success Criteria

A successful demonstration can show, in order:

1. Create Wallet A and Wallet B.
2. Explain private/public key generation and Base58Check-style addresses.
3. Show that the keystore contains encrypted rather than plaintext private-key material.
4. Request faucet funding for Wallet A.
5. Show funding pending in the mempool and not yet spendable.
6. Mine a block and show Wallet A's confirmed balance.
7. Create a signed transfer from Wallet A to Wallet B.
8. Display transaction ID, sender public key, and ECDSA signature.
9. Verify the signature.
10. Mine the transfer into a block.
11. Show nonce, difficulty, block hash, previous hash, mining reward, and updated balances.
12. Validate the complete blockchain.
13. Tamper with a copied confirmed transaction and show specific validation failures.
14. Demonstrate wrong-password and/or wrong-public-key failure.
15. Demonstrate SHA-256 avalanche behavior.
16. Explain that the system is an educational single-node simulator, not a production cryptocurrency.

## 20. Non-Goals and Limitations

The project deliberately excludes peer-to-peer networking, distributed consensus between independent nodes, smart contracts, real cryptocurrency, exchange integration, hardware wallets, seed phrases, HD derivation, transaction fees, dynamic difficulty adjustment, production-grade consensus security, and high-volume storage.

These features would distract from the cryptography learning goals and are unnecessary for the assessment.

## 21. Quality Bar

The final project must be easy for an examiner to inspect and defend: modular code, clear names, no cryptographic policy hidden in the UI, reproducible tests, explicit negative tests, deterministic serialization where required, exact money representation, visible hashes/signatures/nonces, and clear separation between user-signed transfers and system issuance.

The report can directly map this architecture to cryptographic background, system design, implementation, testing, CrypTool support, results, limitations, and conclusion.
