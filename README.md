# Blockchain Wallet Simulator

A cryptography-focused educational blockchain wallet simulation system implementing secure wallets, digital signatures, transactions, Proof-of-Work mining, blockchain validation, and encrypted private-key storage.

> This project is a **single-node educational blockchain simulator**. It demonstrates blockchain and cryptography concepts for learning purposes. It is not a real cryptocurrency, production blockchain, or decentralized network.

---

## Project Overview

Blockchain Wallet Simulator is an educational application designed to demonstrate how blockchain systems combine cryptography, transaction processing, and data integrity mechanisms.

The system simulates:

- Wallet creation and secure key management
- Public/private key cryptography
- Digital transaction signing
- Transaction verification
- Mempool processing
- Proof-of-Work mining
- Blockchain validation
- Local blockchain persistence

The goal is to make the internal cryptographic processes visible rather than hiding them behind a simple blockchain interface.

---

## Features Implemented

## Wallet System

- Wallet creation
- secp256k1 public/private key generation
- Unique blockchain address generation
- Password-protected wallet unlocking
- Secure encrypted private-key storage
- Wallet persistence using JSON storage

## Cryptography

Implemented cryptographic techniques:

### SHA-256 Hashing

Used for:

- Transaction ID generation
- Block hashing
- Blockchain integrity verification
- Proof-of-Work mining

### ECDSA Digital Signatures

Using the **secp256k1 elliptic curve** for:

- Transaction authentication
- Private-key based signing
- Signature verification

### PBKDF2-HMAC-SHA256

Used for:

- Password-based encryption key derivation
- Secure wallet password handling

### AES-256-GCM Encryption

Used for:

- Private key encryption
- Authenticated encrypted wallet storage

### Address Generation

Includes:

- SHA-256 hashing
- RIPEMD-160 hashing
- Base58Check-style encoding
- Checksum validation

---

## Transaction System

The transaction engine provides:

- Transaction creation
- Digital signing with private keys
- Signature verification
- Transaction validation
- Balance verification
- Mempool management
- Duplicate transaction detection
- Overspending prevention

Transaction lifecycle:

```
Create Transaction
        |
        v
Sign With Private Key
        |
        v
Verify Signature
        |
        v
Add To Mempool
        |
        v
Included In Mined Block
```

---

## Blockchain System

Implemented blockchain features:

- Genesis block creation
- Block structure management
- Previous hash linking
- SHA-256 block hashing
- Proof-of-Work mining
- Mining rewards
- Blockchain integrity validation

Mining workflow:

```
Pending Transactions
        |
        v
Create Candidate Block
        |
        v
Search Valid Nonce
        |
        v
Verify Hash Difficulty
        |
        v
Add Block To Chain
```

---

## Persistence

The application stores data locally using JSON files:

- Blockchain state persistence
- Wallet metadata persistence
- Encrypted private-key storage
- Atomic file writing to reduce corruption risk

Private keys are never stored as plaintext.

---

# System Architecture

```
User Interface (Streamlit)
          |
          v
Wallet Layer
          |
          v
Transaction Layer
          |
          v
Cryptographic Layer
          |
          v
Blockchain Engine
          |
          v
Storage Layer
```

### User Interface Layer

Provides interaction for wallet creation, transactions, mining, blockchain exploration, and security demonstrations.

### Wallet Layer

Handles key generation, address creation, password unlocking, and encrypted wallet storage.

### Transaction Layer

Creates, signs, validates, and manages transactions.

### Cryptographic Layer

Provides hashing, encryption, digital signatures, and integrity verification.

### Blockchain Engine

Handles blocks, mining, validation, and chain management.

### Storage Layer

Maintains persistent blockchain and wallet data.

---

# Repository Structure

```
Blockchain-Wallet-Simulator/

├── app.py
├── requirements.txt
├── blockchain_sim/
│   ├── crypto_utils.py
│   ├── wallet.py
│   ├── transaction.py
│   ├── block.py
│   ├── blockchain.py
│   ├── storage.py
│   └── config.py
│
├── tests/
│   ├── test_crypto.py
│   ├── test_wallet.py
│   ├── test_transaction.py
│   ├── test_block.py
│   ├── test_blockchain.py
│   ├── test_storage.py
│   └── test_app_smoke.py
│
└── data/
```

---

# Technology Stack

**Programming Language**

- Python

**Framework**

- Streamlit

**Libraries**

- cryptography
- ecdsa
- pytest

**Development Tools**

- VS Code
- Git
- GitHub

---

# Installation Guide

```bash
git clone https://github.com/waseem1302-x/CCS2243-Blockchain-Wallet-Simulator.git

cd CCS2243-Blockchain-Wallet-Simulator

python -m venv .venv
```

Activate environment:

Windows:

```bash
.\.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# Running The Application

Start the Streamlit application:

```bash
python -m streamlit run app.py
```

The application will open in the browser at the local Streamlit address.

---

# Testing

The project includes automated tests covering:

- Cryptographic functions
- Wallet security
- Digital signatures
- Transaction validation
- Block creation
- Blockchain integrity
- Persistence
- Application startup

Run tests:

```bash
pytest
```

Example result:

```
28 tests passed
```

---

# Security Considerations

Implemented security mechanisms:

- Private keys are never stored as plaintext
- Password-based encryption protects wallet keys
- Transactions require valid digital signatures
- Hash verification detects modification
- Blockchain tampering is detected through validation
- Invalid passwords are rejected through authenticated encryption

---

# Limitations

This project is intentionally educational and simplified.

Current limitations:

- Single-node blockchain simulation
- No peer-to-peer networking
- No distributed consensus network
- Simplified Proof-of-Work difficulty
- No smart contract execution
- Not designed for real cryptocurrency usage

---

# Future Improvements

Possible future extensions:

- Multi-node blockchain simulation
- REST API integration
- Real network communication
- Database-based storage
- Advanced consensus mechanisms
- Smart contract support

---

# Application Screenshots

Future screenshots can be added here:

- Dashboard
- Wallet Creation
- Transaction Processing
- Mining Interface
- Blockchain Explorer
- Security Lab

---

## Educational Purpose

This repository demonstrates practical implementation of blockchain and cryptography concepts including secure wallets, digital signatures, hashing, encryption, mining, and blockchain validation.
