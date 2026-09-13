# Live Demonstration Checklist

Use this sequence during the CCS2243 presentation.

1. Create three wallets: **Alice**, **Bob**, **Miner**.
2. Show Alice's address and compressed secp256k1 public key.
3. Show the encrypted keystore fields; emphasize no plaintext private key is stored.
4. Request Alice's faucet coins and show the pending transaction.
5. Mine the faucet transaction with Miner.
6. Show nonce, attempts, block hash, previous hash, difficulty, and Miner reward.
7. Create Alice -> Bob transfer and enter Alice's password.
8. Show transaction SHA-256 ID and ECDSA signature.
9. Show that signature verification is `True`.
10. Mine the signed transfer.
11. Open Blockchain Explorer and trace previous-hash links from newest block to genesis.
12. Run full validation and show `VALID`.
13. Security Lab: alter a confirmed transaction amount in the safe copy; show `INVALID` and the validator reasons.
14. Security Lab: alter a nonce; show block hash / Proof-of-Work failure.
15. Security Lab: attempt wrong wallet password; show AES-GCM rejection.
16. Security Lab: verify a transfer with another wallet public key; show ECDSA rejection.
17. Security Lab: compare SHA-256 of two nearly identical strings and report changed bits.
18. Close with limitations: single node, educational test coins, no public network, no real money.

## Screenshots worth capturing for the report

- Wallet public key/address + encrypted keystore metadata.
- Faucet transaction in mempool before mining.
- Mining result with nonce/hash/attempts.
- Signed transaction ID and ECDSA signature.
- Blockchain Explorer showing previous/current hashes.
- Full-chain `VALID` result.
- Tampered transaction `INVALID` result with reasons.
- SHA-256 avalanche result.
- `pytest -q` successful test output.
