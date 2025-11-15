"""
ERC-20 token client used for MOXI payouts.
Provides lightweight helpers for transferring tokens from the node's wallet.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, getcontext, ROUND_DOWN
from typing import Any, Dict, Optional

from .web3_config import get_web3_instance

try:
    from web3 import Web3
    from web3.types import TxReceipt
except ImportError:
    Web3 = None  # type: ignore
    TxReceipt = Any  # type: ignore

# Allow plenty of precision when converting token amounts
getcontext().prec = 78

# Minimal ERC-20 ABI required for payouts
ERC20_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"},
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
]


@dataclass
class TokenTransferResult:
    """Return payload for a token transfer."""

    tx_hash: str
    receipt: TxReceipt
    amount_wei: int
    amount_tokens: Decimal


class ERC20TokenClient:
    """Simple ERC-20 helper around Web3 for sending payouts."""

    def __init__(
        self,
        token_address: str,
        rpc_url: Optional[str],
        private_key: str,
    ):
        if Web3 is None:
            raise ImportError(
                "web3 is not installed. Install optional deps via `pip install -r node/requirements-web3.txt`."
            )

        if not token_address:
            raise ValueError("Token address is required for payouts.")
        if not private_key:
            raise ValueError("Private key is required for payouts.")

        self.w3 = get_web3_instance(rpc_url)
        if not self.w3:
            raise ValueError("Could not connect to RPC for token payouts. Check RPC URL.")

        # Normalize key + address
        self.contract_address = Web3.to_checksum_address(token_address)
        if private_key.startswith("0x"):
            private_key = private_key[2:]
        self.account = self.w3.eth.account.from_key(private_key)
        self.account_address = self.account.address
        self.contract = self.w3.eth.contract(address=self.contract_address, abi=ERC20_ABI)

        # Cache metadata for logs/UI
        try:
            self.decimals = int(self.contract.functions.decimals().call())
        except Exception:
            # Default to 18 if contract does not implement metadata
            self.decimals = 18
        try:
            self.symbol = self.contract.functions.symbol().call()
        except Exception:
            self.symbol = "MOXI"

    def _to_base_units(self, amount_tokens: Decimal) -> int:
        """Convert a Decimal token amount to its smallest unit."""
        if amount_tokens <= Decimal("0"):
            return 0
        scale = Decimal(10) ** self.decimals
        wei_amount = int((amount_tokens * scale).to_integral_value(rounding=ROUND_DOWN))
        return wei_amount

    def transfer_tokens(self, to_address: str, amount_tokens: Decimal) -> TokenTransferResult:
        """Transfer tokens and wait for inclusion."""
        if amount_tokens <= Decimal("0"):
            raise ValueError("Cannot transfer zero tokens.")

        if not to_address:
            raise ValueError("Destination address required.")

        destination = Web3.to_checksum_address(to_address)
        amount_wei = self._to_base_units(amount_tokens)
        if amount_wei == 0:
            raise ValueError("Amount rounds down to zero at current token decimals.")

        function_call = self.contract.functions.transfer(destination, amount_wei)
        try:
            gas_estimate = function_call.estimate_gas({"from": self.account_address})
        except Exception as exc:
            raise ValueError(f"Unable to estimate gas for payout: {exc}") from exc

        gas_limit = int(gas_estimate * 1.2) + 10_000  # Add buffer for safety
        nonce = self.w3.eth.get_transaction_count(self.account_address)

        tx = function_call.build_transaction(
            {
                "from": self.account_address,
                "nonce": nonce,
                "gas": gas_limit,
                "gasPrice": self.w3.eth.gas_price,
                "chainId": self.w3.eth.chain_id,
            }
        )

        signed = self.account.sign_transaction(tx)
        raw_tx = getattr(signed, "raw_transaction", None) or getattr(signed, "rawTransaction", None)
        if raw_tx is None:
            raise ValueError("Unable to access signed transaction bytes.")

        tx_hash = self.w3.eth.send_raw_transaction(raw_tx)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        scale = Decimal(10) ** self.decimals
        actual_tokens = Decimal(amount_wei) / scale

        return TokenTransferResult(
            tx_hash=tx_hash.hex(),
            receipt=receipt,
            amount_wei=amount_wei,
            amount_tokens=actual_tokens,
        )

    def get_token_balance(self) -> Decimal:
        """Return the node wallet's token balance."""
        balance = self.contract.functions.balanceOf(self.account_address).call()
        scale = Decimal(10) ** self.decimals
        return Decimal(balance) / scale
