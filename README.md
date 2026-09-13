# CCS2243 Blockchain Wallet Simulator

An educational **single-node blockchain wallet simulator** for CCS2243 Cryptography Essential. The project is designed for a live classroom demonstration: it exposes the cryptographic evidence behind wallets, transaction signatures, Proof of Work, hash-linked blocks, password-protected private keys, and tamper detection instead of hiding those details behind a generic blockchain UI.

> This project uses **test coins only**. It does not connect to Bitcoin, Ethereum, an exchange, or any real-money network.

## What the system demonstrates

- **ECDSA over secp256k1** wallet key pairs and transaction signatures.
- **SHA-256** transaction IDs, block hashes, Proof of Work, and avalanche behavior.
- **SHA-256 -> RIPEMD-160 -> Base58Check-style** wallet-address derivation with checksum validation.
- **PBKDF2-HMAC-SHA256** password-based key derivation using a random salt.
- **AES-256-GCM** authenticated encryption for local private-key storage.
- **Account-based balances** reconstructed from confirmed blockchain history.
- **Mempool rules** that prevent spending pending incoming funds or overspending with multiple pending transfers.
- **Educational faucet** transactions for initial test coins.
- **Proof-of-Work mining** with a configurable low classroom difficulty.
- **Mining rewards** issued as controlled system transactions.
- **Full-chain validation** of hashes, previous-hash links, Proof of Work, signatures, address ownership, duplicate IDs, faucet policy, mining rewards, and replayed balances.
- **Security Lab** demonstrations using an in-memory copy so tampering experiments do not destroy the saved chain.

## Architecture

```text
Streamlit UI
    |
    +--> Wallets --------> secp256k1 key pair
    |                        |
    |                        +--> PBKDF2-HMAC-SHA256
    |                        +--> AES-256-GCM encrypted keystore
    |
    +--> Transactions ----> canonical JSON -> SHA-256 ID -> ECDSA signature
    |                                         |
    |                                         +--> signature verification
    |
    +--> Mempool ---------> balance + duplicate + signature checks
    |
    +--> Miner -----------> candidate block -> nonce search -> SHA-256 target
    |
    +--> Blockchain -----> previous-hash links -> full validation -> JSON persistence
```

The UI is deliberately separated from the cryptographic and blockchain domain modules so the algorithms can be tested independently.

## Installation

Python 3.11 or newer is recommended.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m pytest -q
streamlit run app.py
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m pytest -q
streamlit run app.py
```

Streamlit will print a local URL, normally `http://localhost:8501`.

## Recommended classroom demonstration

1. Open **Wallets** and create `Alice`, `Bob`, and `Miner` with passwords.
2. Open Alice's wallet and point out the public address, compressed secp256k1 public key, random salt, nonce, PBKDF2 iteration count, and encrypted private-key ciphertext.
3. Explain that plaintext private keys are never stored in JSON.
4. Request the educational faucet for Alice. Show that Alice still has `0` confirmed coins while the faucet transaction is only in the mempool.
5. Open **Mempool & Mining**, select Miner, and mine the faucet transaction.
6. Show the nonce, number of hash attempts, leading-zero Proof-of-Work target, new block hash, and previous block hash.
7. Return to the dashboard and show Alice's confirmed balance plus the Miner's mining reward.
8. Open **Send Transaction** and send coins from Alice to Bob. Enter Alice's password so the private key is decrypted only for signing.
9. Show the SHA-256 transaction ID and the ECDSA signature. Point out that verification succeeds before the transaction is accepted into the mempool.
10. Mine the transfer into the next block.
11. Open **Blockchain Explorer** and show the genesis block, the linked hashes, the signed transfer, the mining-reward system transaction, and valid Proof of Work.
12. Run the complete chain validation and show `VALID`.
13. Open **Security Lab**, change a confirmed transaction amount in the in-memory copy, and show the resulting transaction/block-hash validation errors.
14. Change a block nonce and demonstrate Proof-of-Work/hash failure.
15. Try a wrong wallet password and show AES-GCM authenticated decryption rejection.
16. Verify the latest transfer with a different wallet's public key and show ECDSA rejection.
17. Change one character in the SHA-256 avalanche demo and compare the changed output bits.
18. End by explaining that this is a cryptography-focused simulator, not a production cryptocurrency or distributed peer-to-peer network.

A shorter printable sequence is available in [`docs/demo-checklist.md`](docs/demo-checklist.md).

## Security model

### Wallet creation

1. Generate a random **secp256k1** private key.
2. Derive its compressed public key.
3. Hash public-key bytes with SHA-256 then RIPEMD-160.
4. Add an address-version byte and four-byte double-SHA-256 checksum.
5. Encode with Base58.
6. Derive a 256-bit encryption key from the wallet password using PBKDF2-HMAC-SHA256 and a fresh random salt.
7. Encrypt the 32-byte private key with AES-256-GCM and a fresh random 96-bit nonce.

### Signed transfer

The transaction's unsigned fields are serialized in canonical JSON order, hashed with SHA-256, and the resulting ID is signed using ECDSA. Verification checks all of the following before the transaction enters the mempool:

- the sender public key maps to the claimed sender address;
- the transaction hash still matches the transaction fields;
- the ECDSA signature is valid;
- the receiver address checksum is valid;
- the amount is positive;
- the sender has enough confirmed balance after existing pending outgoing transfers.

### Block mining

A block contains its index, timestamp, transaction list, previous block hash, miner address, difficulty, and nonce. Mining increments the nonce until:

```text
SHA256(canonical_block_data).startswith("0" * difficulty)
```

The default difficulty is intentionally low for a classroom laptop. It is **not** intended to model the economic security level of a public cryptocurrency.

## Persistence

Runtime state is stored locally:

- `data/blockchain.json` — blockchain plus mempool state.
- `data/wallets/<address>.json` — public metadata and **encrypted** private-key ciphertext.

These runtime files are ignored by Git. JSON writes use a temporary file plus replacement to reduce partial-write corruption risk.

## Automated testing

Run:

```bash
python -m pytest -q
```

The test suite covers hashing, secp256k1 sign/verify, wrong-key rejection, AES-GCM private-key protection, wallet persistence, transaction tampering, Proof of Work, faucet confirmation, mining rewards, overspending, duplicate transactions, chain tampering, and blockchain persistence. GitHub Actions runs the same suite on pushes and pull requests.

## CrypTool 2 companion demonstration

The Python/Streamlit application is the **actual integrated implementation**. CrypTool 2 can be used separately as visual evidence in the report or presentation. A useful companion workflow is:

1. Open the CrypTool 2 **Blockchain Simulation** template.
2. Demonstrate addresses/participants and a sample transaction.
3. Show the signature-related components and mining/block creation.
4. Use a SHA-256 template to visualize how a small input change produces a very different digest.
5. Explain that the CrypTool workspace is a visual teaching aid, while this repository implements the complete wallet, key protection, transaction validation, ledger, mining, persistence, and automated tests.

## Important limitations

This simulator intentionally does **not** include peer-to-peer networking, independent-node consensus, smart contracts, transaction fees, dynamic difficulty adjustment, HD wallets/seed phrases, hardware-wallet integration, exchange connectivity, or production key-management guarantees. Python also cannot guarantee that decrypted key bytes are immediately erased from process memory; the implementation limits their lifetime in normal application flow but should not be described as secure memory wiping.

## Project documents

- Design specification: `docs/superpowers/specs/2026-09-13-blockchain-wallet-simulator-design.md`
- Implementation plan: `docs/superpowers/plans/2026-09-13-blockchain-wallet-simulator-implementation.md`
- Live demonstration checklist: `docs/demo-checklist.md`
