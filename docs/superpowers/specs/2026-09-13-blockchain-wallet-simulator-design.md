# CCS2243 Blockchain Wallet Simulator — Design Specification

Date: 2026-09-13

## 1. Purpose

Build a complete educational blockchain wallet simulator for the CCS2243 Cryptography Essential project. The system must visibly demonstrate practical cryptography rather than only showing a blockchain-themed interface.

The finished application will allow a user to create password-protected wallets, obtain test coins from a controlled faucet, create and cryptographically sign transactions, verify signatures, place valid transactions into a mempool, mine blocks with Proof of Work, receive mining rewards, inspect the chain, validate balances, and deliberately tamper with data to observe integrity failures.

The simulator is local, single-node, and educational. It does not connect to Bitcoin, Ethereum, public blockchains, exchanges, or real money.

## 2. Agreed Scope

The selected architecture and requirements are:

- Python implementation with a modular package structure.
- Streamlit graphical user interface.
- Account-based balance model rather than UTXO.
- Local JSON persistence for blockchain state and wallet metadata.
- ECDSA on secp256k1 for wallet transaction signatures.
- SHA-256 for transaction IDs, block hashes, Proof of Work, and integrity demonstrations.
- Wallet addresses derived from public-key material using a SHA-256 / RIPEMD-160 style educational pipeline and Base58Check-style encoding.
- Password-protected private keys using PBKDF2-HMAC-SHA256 and AES-256-GCM.
- Educational faucet for initial test coins.
- Mining rewards.
- Single local blockchain node.
- Proof-of-Work mining with configurable low difficulty suitable for classroom demonstration.
- Automated test suite covering normal and negative/security cases.

## 3. Security and Educational Goals

The simulator must demonstrate the following cryptographic ideas clearly:

1. **Key ownership** — a wallet is controlled by a secp256k1 private key.
2. **Public-key cryptography** — public keys can be shared while private keys remain secret.
3. **Digital signatures** — a sender signs transaction data with ECDSA; the network verifies it with the sender public key.
4. **Hashing and integrity** — transaction and block hashes change when protected data changes.
5. **Tamper evidence** — changing historical block data breaks block hashes and subsequent previous-hash links.
6. **Proof of Work** — miners search for a nonce whose block hash satisfies a configurable prefix difficulty.
7. **Password-based key protection** — PBKDF2 derives a 256-bit AES key from a password and random salt.
8. **Authenticated encryption** — AES-256-GCM encrypts private-key bytes and detects incorrect passwords or tampering.
9. **Blockchain linkage** — every non-genesis block includes the previous block hash.
10. **Controlled coin issuance** — faucet and mining reward transactions are system transactions, distinct from user-signed transactions.

## 4. High-Level Architecture

Data flow:

`Streamlit UI -> Domain Models / Services -> Cryptographic Utilities -> Blockchain / Mempool -> JSON Storage`

Private-key flow:

`Password -> PBKDF2-HMAC-SHA256 -> AES-256-GCM -> Encrypted Private Key Keystore`

Transaction flow:

`Wallet -> Transaction Payload -> SHA-256 ID -> ECDSA Signature -> Verification -> Mempool -> Mining -> Confirmed Block`

Block flow:

`Pending Transactions -> Candidate Block -> Nonce Search -> Difficulty Check -> Append -> Persist -> Recalculate Balances`

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

Generated runtime data will be ignored by Git where appropriate; sample or placeholder directories may use `.gitkeep`.

## 6. Component Responsibilities

### `config.py`
Centralizes classroom-safe values such as chain name, difficulty, mining reward, faucet amount, PBKDF2 iteration count, key lengths, and schema version.

### `crypto_utils.py`
Provides focused cryptographic primitives and helpers:

- SHA-256 hashing.
- RIPEMD-160 helper where available via Python/OpenSSL.
- Base58/Base58Check encoding implemented locally or via a small dependency.
- secp256k1 key generation.
- Public-key serialization.
- ECDSA sign and verify.
- PBKDF2-HMAC-SHA256 key derivation.
- AES-256-GCM encrypt/decrypt for private-key protection.
- Canonical JSON serialization used before hashing/signing.

### `wallet.py`
Creates and loads wallets. A wallet exposes a name, address, and public key. Private-key bytes are only decrypted temporarily after the user enters the correct password. Plaintext private keys are never persisted.

### `transaction.py`
Represents normal transfers and system issuance transactions. It must generate deterministic transaction IDs from canonical transaction content, sign normal transfers, verify signatures, and serialize safely.

### `block.py`
Represents a block and performs deterministic block hashing and Proof-of-Work mining. Block hash calculation includes the nonce, previous hash, transaction content, index, and timestamp.

### `blockchain.py`
Owns chain-level policy:

- Genesis block creation.
- Mempool management.
- Balance calculation from confirmed transactions.
- Faucet issuance.
- Validation of user transactions.
- Mining reward creation.
- Block mining.
- Full-chain validation.
- Duplicate transaction rejection.
- Overspending prevention.
- Tamper detection.

### `storage.py`
Owns JSON persistence and schema validation. Writes use a temporary file followed by replacement where practical to reduce corruption risk.

### `app.py`
Contains presentation and user interaction only. Cryptographic/domain logic stays in package modules so it can be tested independently.

## 7. Data Models

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

The AES-GCM authentication tag is stored as part of the encrypted output according to the cryptography library representation.

### Normal transaction

```text
transaction_id
sender_address
receiver_address
amount
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
amount
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
mining_reward
faucet_amount
```

## 8. Transaction Lifecycle

1. User selects sender wallet and receiver address.
2. Application validates the amount is positive and the receiver address is well formed.
3. Blockchain computes sender confirmed balance.
4. Blockchain also accounts for sender transactions already pending in the mempool to prevent pending overspend.
5. Transaction content is canonicalized and hashed.
6. Sender private key is decrypted in memory after password validation.
7. Transaction is signed with ECDSA secp256k1.
8. Private-key bytes are discarded from the local function scope as soon as signing finishes.
9. Blockchain verifies that the supplied public key maps to the claimed sender address.
10. Blockchain verifies the signature.
11. Valid transaction is added to the mempool and persisted.
12. Mining moves pending valid transactions into a confirmed block.

## 9. Faucet Rules

The faucet is intentionally educational, not a normal signed user transfer.

- A wallet can request a configurable fixed amount of test coins.
- Faucet transactions are created only through `Blockchain.request_faucet()`.
- They use `SYSTEM` as sender and have no ECDSA signature.
- The UI clearly labels them as system-issued test coins.
- A simple per-address limit will prevent unlimited accidental clicking during demonstration while remaining easy to reset for classroom use.

## 10. Mining and Proof of Work

Mining operates on a candidate block containing current mempool transactions plus one mining reward transaction.

The miner repeatedly increments `nonce` and recalculates SHA-256 until:

`block_hash.startswith("0" * difficulty)`

The default difficulty will be intentionally small so mining normally completes in seconds on a student laptop. Difficulty is saved with each block so historical blocks can be independently revalidated.

When mining succeeds:

1. Candidate block is revalidated.
2. Block is appended to the chain.
3. Included mempool transactions are removed.
4. Chain state is persisted.
5. Mining reward becomes part of the confirmed ledger through the block's system reward transaction.

## 11. Chain Validation

Full validation checks every block and transaction, including:

- Genesis block rules.
- Stored block hash equals freshly calculated hash.
- Proof-of-Work requirement is satisfied.
- Each `previous_hash` equals the actual preceding block hash.
- Block indexes are sequential.
- Normal transaction IDs are correct.
- Normal transaction signatures verify.
- Sender public key maps to sender address.
- No duplicate confirmed transaction IDs.
- Ledger replay never permits a normal transfer to spend more confirmed funds than available at that point.
- Mining reward amounts match the configured policy expected for the block.
- System transaction types are only accepted under controlled rules.

Validation returns structured findings so the UI can show exactly why a chain is invalid.

## 12. Tamper Lab

The UI includes a separate educational security lab. It operates on a deep copy of persisted chain data by default so the user can demonstrate attacks without accidentally destroying the working chain.

Planned demonstrations:

- Change a confirmed transaction amount -> transaction ID/signature mismatch and block hash mismatch.
- Change a receiver address -> signature verification failure and hash mismatch.
- Change a historical block nonce -> Proof-of-Work or block-hash failure.
- Change a historical block transaction -> current block fails and subsequent previous-hash linkage becomes inconsistent.
- Attempt to verify a transaction with another wallet public key -> verification failure.
- Attempt to unlock a wallet using a wrong password -> AES-GCM authenticated decryption failure.

An optional explicit "apply destructive tamper to stored chain" action may be offered behind a strong confirmation, but it is not required for the core project because the safe-copy demonstration is sufficient and reproducible.

## 13. Streamlit User Interface

The UI will use a simple academic dashboard rather than excessive animation.

Pages/tabs:

1. **Dashboard** — chain height, confirmed transactions, mempool size, wallet count, current difficulty, validity status.
2. **Wallets** — create wallet, inspect address/public key, faucet request, balance.
3. **Send Transaction** — sender selection, password, receiver, amount, transaction hash/signature result.
4. **Mempool & Mining** — inspect pending transactions, select miner wallet, mine block, show nonce/hash/time/reward.
5. **Blockchain Explorer** — inspect every block and transaction, hashes, previous links, Proof-of-Work status.
6. **Security Lab** — tampering, wrong password, wrong-key verification, avalanche/hash comparison.
7. **System / About** — algorithms, project scope, limitations, reset/demo-data tools.

Private keys will not be displayed by default. If a classroom demonstration requires revealing one, the simulator may expose a temporary masked/explicit reveal action that never writes plaintext to disk.

## 14. Error Handling

The application will provide readable domain errors instead of Python tracebacks for expected cases:

- Wrong wallet password.
- Invalid address.
- Invalid amount.
- Insufficient balance.
- Invalid signature.
- Corrupt wallet file.
- Corrupt blockchain file.
- Duplicate transaction.
- Empty mempool when mining, if configured to require at least one user transaction.
- Invalid persisted schema.

Unexpected errors may still be logged for debugging, but normal UI operation should remain controlled.

## 15. Testing Strategy

Development will follow test-first implementation for domain behavior.

Core automated tests include:

### Cryptography
- SHA-256 deterministic output.
- New secp256k1 key pair signs and verifies.
- Modified message fails signature verification.
- Wrong public key fails verification.
- Private key encrypt/decrypt round trip succeeds.
- Wrong password fails authenticated decryption.
- Modified encrypted private-key payload fails authenticated decryption.

### Wallets
- Wallet creation produces unique addresses.
- Persisted wallet never contains plaintext private key.
- Correct password unlocks signing capability.

### Transactions
- Valid signed transaction verifies.
- Amount/receiver modification invalidates the transaction.
- Address/public-key mismatch is rejected.
- Non-positive amount is rejected.

### Blocks
- Block hashing is deterministic for identical serialized data.
- Mining finds a hash matching configured difficulty.
- Changing a mined block invalidates its stored hash or Proof of Work.

### Blockchain
- Genesis chain validates.
- Faucet increases confirmed balance after confirmation according to the chosen faucet confirmation flow.
- Signed transaction transfers balance after mining.
- Overspending is rejected.
- Pending overspending is rejected.
- Mining reward is credited.
- Multiple linked blocks validate.
- Historical tampering invalidates the chain.
- Duplicate transactions are rejected.

### Persistence
- Save/load round trip preserves chain state.
- Wallet metadata save/load round trip works.
- Missing-data initialization creates a clean state.

## 16. Implementation Phases

### Phase 1 — Cryptographic Foundation
- Repository foundation and dependencies.
- Cryptographic utilities.
- Wallet creation.
- Password-protected keystore.
- Initial unit tests.

### Phase 2 — Transactions and Ledger Rules
- Transaction model.
- ECDSA signing and verification.
- Address/public-key ownership checks.
- Account balances.
- Faucet issuance.
- Mempool and overspending rules.
- Unit tests.

### Phase 3 — Blockchain, Mining, and Persistence
- Genesis block.
- Block model.
- Proof of Work.
- Mining rewards.
- Chain validation.
- JSON storage/recovery.
- Tamper tests.

### Phase 4 — UI, Security Demonstrations, Documentation, Verification
- Streamlit dashboard and explorer.
- Wallet and transfer flows.
- Mining UI.
- Security Lab.
- README with local setup and demo script.
- Final automated test run.
- Manual local verification steps for the user.

## 17. Demo Success Criteria

A successful classroom demonstration must be able to show, in order:

1. Create Wallet A and Wallet B.
2. Explain private/public key generation and addresses.
3. Show encrypted private-key storage.
4. Fund Wallet A from the educational faucet.
5. Create a transfer from Wallet A to Wallet B.
6. Display transaction hash and ECDSA signature.
7. Verify the signature.
8. Mine the pending transaction into a block.
9. Show nonce, difficulty, block hash, and previous hash.
10. Show mining reward and updated balances.
11. Validate the complete blockchain.
12. Tamper with a copy of a confirmed transaction and show validation failure.
13. Demonstrate wrong-password or wrong-public-key failure.
14. Explain that the system is an educational single-node simulator, not a production cryptocurrency.

## 18. Non-Goals and Limitations

The project deliberately does not include peer-to-peer networking, distributed consensus between independent nodes, smart contracts, real cryptocurrency, exchange integration, hardware wallets, seed phrases, HD wallet derivation, transaction fees, dynamic mining difficulty, production-grade consensus security, or high-volume storage.

These features would distract from the cryptography learning goals and are unnecessary for the course demonstration.

## 19. Quality Bar

The final project should be easy for an examiner to inspect and defend: modular code, clear names, no hidden cryptographic decisions inside the UI, reproducible tests, explicit negative tests, deterministic serialization where required, and a UI that exposes hashes/signatures/nonces rather than hiding them.

The report can directly map this architecture to chapters on cryptographic background, system design, implementation, testing, CrypTool support, results, limitations, and conclusion.
