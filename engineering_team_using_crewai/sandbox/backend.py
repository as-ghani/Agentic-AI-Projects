from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Callable
from uuid import uuid4


class AccountError(Exception):
    pass


class AccountNotFoundError(AccountError):
    pass


class InvalidAmountError(AccountError):
    pass


class InvalidQuantityError(AccountError):
    pass


class InsufficientFundsError(AccountError):
    pass


class InsufficientSharesError(AccountError):
    pass


class UnknownSymbolError(AccountError):
    pass


class TransactionType(Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"
    BUY = "BUY"
    SELL = "SELL"


_FIXED_PRICES = {"AAPL": 150.0, "TSLA": 250.0, "GOOGL": 2800.0}


def get_share_price(symbol: str) -> float:
    normalized = symbol.strip().upper()
    try:
        return _FIXED_PRICES[normalized]
    except KeyError as exc:
        raise UnknownSymbolError(f"Unknown symbol: {symbol}") from exc


@dataclass(frozen=True)
class Transaction:
    transaction_id: str
    account_id: str
    transaction_type: TransactionType
    timestamp: datetime
    cash_amount: float | None
    symbol: str | None
    quantity: int | None
    share_price: float | None
    total_trade_value: float | None
    cash_balance_after: float
    notes: str


@dataclass(frozen=True)
class Holding:
    symbol: str
    quantity: int
    current_price: float
    market_value: float


@dataclass(frozen=True)
class PortfolioSummary:
    account_id: str
    owner_name: str
    as_of: datetime
    cash_balance: float
    holdings_value: float
    total_value: float
    initial_deposit: float
    net_cash_contributed: float
    profit_loss: float
    profit_loss_percent: float | None
    profit_loss_from_initial_deposit: float


@dataclass(frozen=True)
class AccountSnapshot:
    account_id: str
    owner_name: str
    as_of: datetime
    cash_balance: float
    holdings: dict[str, int]
    total_deposits: float
    total_withdrawals: float


class TradingAccount:
    def __init__(self, account_id: str, owner_name: str, initial_deposit: float = 0.0, price_lookup: Callable[[str], float] = get_share_price, created_at: datetime | None = None) -> None:
        owner_name = owner_name.strip()
        if not owner_name:
            raise ValueError("owner_name must be non-empty")
        if initial_deposit < 0:
            raise InvalidAmountError("initial_deposit must be >= 0")
        self._account_id = account_id
        self._owner_name = owner_name
        self._created_at = created_at or datetime.now()
        self._price_lookup = price_lookup
        self._initial_deposit = self._round_money(initial_deposit)
        self._cash_balance = 0.0
        self._holdings: dict[str, int] = {}
        self._transactions: list[Transaction] = []
        if initial_deposit > 0:
            self._cash_balance = self._round_money(initial_deposit)
            self._record_transaction(TransactionType.DEPOSIT, initial_deposit, None, None, None, None, self._cash_balance, "Initial deposit", self._created_at)

    @property
    def account_id(self) -> str:
        return self._account_id

    @property
    def owner_name(self) -> str:
        return self._owner_name

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def cash_balance(self) -> float:
        return self._cash_balance

    @property
    def holdings(self) -> dict[str, int]:
        return dict(self._holdings)

    @property
    def transactions(self) -> list[Transaction]:
        return list(self._transactions)

    def _validate_amount(self, amount: float) -> None:
        if amount is None or amount <= 0:
            raise InvalidAmountError("amount must be greater than zero")

    def _validate_quantity(self, quantity: int) -> None:
        if not isinstance(quantity, int) or quantity <= 0:
            raise InvalidQuantityError("quantity must be a positive integer")

    def _normalize_symbol(self, symbol: str) -> str:
        if symbol is None or not str(symbol).strip():
            raise UnknownSymbolError("symbol must be provided")
        normalized = str(symbol).strip().upper()
        self._price_lookup(normalized)
        return normalized

    def _new_transaction_id(self) -> str:
        return str(uuid4())

    def _now(self) -> datetime:
        return datetime.now()

    def _round_money(self, amount: float) -> float:
        return round(float(amount), 2)

    def _record_transaction(self, transaction_type: TransactionType, cash_amount: float | None, symbol: str | None, quantity: int | None, share_price: float | None, total_trade_value: float | None, cash_balance_after: float, notes: str, timestamp: datetime | None = None) -> Transaction:
        tx = Transaction(self._new_transaction_id(), self._account_id, transaction_type, timestamp or self._now(), self._round_money(cash_amount) if cash_amount is not None else None, symbol, quantity, self._round_money(share_price) if share_price is not None else None, self._round_money(total_trade_value) if total_trade_value is not None else None, self._round_money(cash_balance_after), notes)
        self._transactions.append(tx)
        return tx

    def deposit(self, amount: float, timestamp: datetime | None = None) -> Transaction:
        self._validate_amount(amount)
        self._cash_balance = self._round_money(self._cash_balance + amount)
        return self._record_transaction(TransactionType.DEPOSIT, amount, None, None, None, None, self._cash_balance, "Deposit", timestamp)

    def withdraw(self, amount: float, timestamp: datetime | None = None) -> Transaction:
        self._validate_amount(amount)
        if amount > self._cash_balance:
            raise InsufficientFundsError("insufficient cash balance")
        self._cash_balance = self._round_money(self._cash_balance - amount)
        return self._record_transaction(TransactionType.WITHDRAW, amount, None, None, None, None, self._cash_balance, "Withdraw", timestamp)

    def buy(self, symbol: str, quantity: int, timestamp: datetime | None = None) -> Transaction:
        normalized = self._normalize_symbol(symbol)
        self._validate_quantity(quantity)
        share_price = self._price_lookup(normalized)
        total = self._round_money(quantity * share_price)
        if total > self._cash_balance:
            raise InsufficientFundsError("insufficient cash to buy shares")
        self._cash_balance = self._round_money(self._cash_balance - total)
        self._holdings[normalized] = self._holdings.get(normalized, 0) + quantity
        return self._record_transaction(TransactionType.BUY, None, normalized, quantity, share_price, total, self._cash_balance, "Buy shares", timestamp)

    def sell(self, symbol: str, quantity: int, timestamp: datetime | None = None) -> Transaction:
        normalized = self._normalize_symbol(symbol)
        self._validate_quantity(quantity)
        if self._holdings.get(normalized, 0) < quantity:
            raise InsufficientSharesError("insufficient shares to sell")
        share_price = self._price_lookup(normalized)
        total = self._round_money(quantity * share_price)
        self._cash_balance = self._round_money(self._cash_balance + total)
        remaining = self._holdings[normalized] - quantity
        if remaining:
            self._holdings[normalized] = remaining
        else:
            self._holdings.pop(normalized, None)
        return self._record_transaction(TransactionType.SELL, None, normalized, quantity, share_price, total, self._cash_balance, "Sell shares", timestamp)

    def _replay(self, as_of: datetime | None = None) -> AccountSnapshot:
        cash_balance = 0.0
        holdings: dict[str, int] = {}
        total_deposits = 0.0
        total_withdrawals = 0.0
        for tx in self._transactions:
            if as_of is not None and tx.timestamp > as_of:
                break
            if tx.transaction_type == TransactionType.DEPOSIT:
                cash_balance += tx.cash_amount or 0.0
                total_deposits += tx.cash_amount or 0.0
            elif tx.transaction_type == TransactionType.WITHDRAW:
                cash_balance -= tx.cash_amount or 0.0
                total_withdrawals += tx.cash_amount or 0.0
            elif tx.transaction_type == TransactionType.BUY:
                cash_balance -= tx.total_trade_value or 0.0
                holdings[tx.symbol] = holdings.get(tx.symbol, 0) + (tx.quantity or 0)
            elif tx.transaction_type == TransactionType.SELL:
                cash_balance += tx.total_trade_value or 0.0
                holdings[tx.symbol] = holdings.get(tx.symbol, 0) - (tx.quantity or 0)
                if holdings[tx.symbol] <= 0:
                    holdings.pop(tx.symbol, None)
        return AccountSnapshot(self._account_id, self._owner_name, as_of or self._now(), self._round_money(cash_balance), holdings, self._round_money(total_deposits), self._round_money(total_withdrawals))

    def get_snapshot(self, as_of: datetime | None = None) -> AccountSnapshot:
        return self._replay(as_of)

    def get_holdings(self, as_of: datetime | None = None) -> list[Holding]:
        snap = self._replay(as_of)
        return [Holding(symbol, qty, self._price_lookup(symbol), self._round_money(qty * self._price_lookup(symbol))) for symbol, qty in sorted(snap.holdings.items()) if qty > 0]

    def get_portfolio_summary(self, as_of: datetime | None = None) -> PortfolioSummary:
        snap = self._replay(as_of)
        holdings = self.get_holdings(as_of)
        holdings_value = self._round_money(sum(h.market_value for h in holdings))
        total_value = self._round_money(snap.cash_balance + holdings_value)
        net_cash = self._round_money(snap.total_deposits - snap.total_withdrawals)
        profit_loss = self._round_money(total_value - net_cash)
        profit_loss_percent = None if net_cash <= 0 else self._round_money(profit_loss / net_cash * 100)
        return PortfolioSummary(self._account_id, self._owner_name, as_of or self._now(), snap.cash_balance, holdings_value, total_value, self._initial_deposit, net_cash, profit_loss, profit_loss_percent, self._round_money(total_value - self._initial_deposit))

    def list_transactions(self, as_of: datetime | None = None) -> list[Transaction]:
        return list(self._transactions) if as_of is None else [tx for tx in self._transactions if tx.timestamp <= as_of]


class AccountManager:
    def __init__(self, price_lookup: Callable[[str], float] = get_share_price) -> None:
        self._price_lookup = price_lookup
        self._accounts: dict[str, TradingAccount] = {}

    def create_account(self, owner_name: str, initial_deposit: float = 0.0) -> TradingAccount:
        account_id = f"ACC-{uuid4().hex[:8].upper()}"
        while account_id in self._accounts:
            account_id = f"ACC-{uuid4().hex[:8].upper()}"
        account = TradingAccount(account_id, owner_name, initial_deposit, price_lookup=self._price_lookup)
        self._accounts[account_id] = account
        return account

    def get_account(self, account_id: str) -> TradingAccount:
        try:
            return self._accounts[account_id]
        except KeyError as exc:
            raise AccountNotFoundError(account_id) from exc

    def list_accounts(self) -> list[TradingAccount]:
        return sorted(self._accounts.values(), key=lambda a: (a.created_at, a.owner_name))

    def deposit(self, account_id: str, amount: float) -> Transaction:
        return self.get_account(account_id).deposit(amount)

    def withdraw(self, account_id: str, amount: float) -> Transaction:
        return self.get_account(account_id).withdraw(amount)

    def buy(self, account_id: str, symbol: str, quantity: int) -> Transaction:
        return self.get_account(account_id).buy(symbol, quantity)

    def sell(self, account_id: str, symbol: str, quantity: int) -> Transaction:
        return self.get_account(account_id).sell(symbol, quantity)

    def get_holdings(self, account_id: str, as_of: datetime | None = None) -> list[Holding]:
        return self.get_account(account_id).get_holdings(as_of)

    def get_portfolio_summary(self, account_id: str, as_of: datetime | None = None) -> PortfolioSummary:
        return self.get_account(account_id).get_portfolio_summary(as_of)

    def list_transactions(self, account_id: str, as_of: datetime | None = None) -> list[Transaction]:
        return self.get_account(account_id).list_transactions(as_of)
