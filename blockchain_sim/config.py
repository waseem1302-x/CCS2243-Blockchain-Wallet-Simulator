from decimal import Decimal, InvalidOperation, ROUND_DOWN

SCHEMA_VERSION = 1
CHAIN_NAME = "CCS2243 Educational Chain"
ADDRESS_VERSION = b"\x00"
COIN = 100_000_000
DEFAULT_DIFFICULTY = 3
DEFAULT_MINING_REWARD = 10 * COIN
DEFAULT_FAUCET_AMOUNT = 100 * COIN
PBKDF2_ITERATIONS = 200_000
WALLET_AAD = b"CCS2243-wallet-v1"
SYSTEM_ADDRESS = "SYSTEM"
GENESIS_PREVIOUS_HASH = "0" * 64
GENESIS_MINER = "GENESIS"


def coins_to_atomic(value: str | int | float | Decimal) -> int:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("Invalid coin amount") from exc
    if amount <= 0:
        raise ValueError("Amount must be greater than zero")
    atomic = (amount * COIN).quantize(Decimal("1"), rounding=ROUND_DOWN)
    if atomic != amount * COIN:
        raise ValueError("Amount has more than 8 decimal places")
    return int(atomic)


def atomic_to_coins(value: int) -> Decimal:
    return Decimal(value) / Decimal(COIN)
