# Design: Trading Simulation Account Management System

## 1. Goals and Scope

Build a simple in-memory account management system for a trading simulation platform.

The system must support:

- Creating accounts with an initial deposit.
- Depositing and withdrawing cash.
- Buying and selling shares.
- Preventing invalid financial operations:
  - No withdrawals that create a negative cash balance.
  - No purchases beyond available cash.
  - No selling more shares than currently held.
- Reporting:
  - Current and historical holdings.
  - Current and historical profit/loss.
  - Full transaction history over time.
- A Gradio frontend for interacting with the system.
- Unit tests for the backend.

Everything lives in the same sandbox directory. No packages or subdirectories.

---

## 2. File Layout

All files should be placed in the project root directory.

```text
backend.py
app.py
test_backend.py
```

Optional but not required:

```text
README.md
```

---

## 3. Backend Design

### Assigned to: `backend_engineer`

Implement all backend business logic in:

```text
backend.py
```

The backend must not import Gradio.

Use only the Python standard library.

Recommended standard library modules:

- `dataclasses`
- `datetime`
- `enum`
- `typing`
- `uuid`

---

## 4. Backend Concepts

### 4.1 Price Provider

The system has access to a function:

```python
get_share_price(symbol: str) -> float
```

For this project, implement a fixed test price provider.

Supported symbols:

| Symbol | Fixed Price |
|---|---:|
| `AAPL` | `150.00` |
| `TSLA` | `250.00` |
| `GOOGL` | `2800.00` |

Behavior:

- Symbol input should be normalized to uppercase.
- If the symbol is unsupported, raise `UnknownSymbolError`.

Signature:

```python
def get_share_price(symbol: str) -> float
```

---

## 5. Backend Exceptions

Define clear domain exceptions in `backend.py`.

Signatures:

```python
class AccountError(Exception)
```

```python
class AccountNotFoundError(AccountError)
```

```python
class InvalidAmountError(AccountError)
```

```python
class InvalidQuantityError(AccountError)
```

```python
class InsufficientFundsError(AccountError)
```

```python
class InsufficientSharesError(AccountError)
```

```python
class UnknownSymbolError(AccountError)
```

Validation expectations:

- Deposit and withdrawal amounts must be greater than zero.
- Trade quantity must be a positive integer.
- Symbols must exist in the fixed price provider.
- Failed operations must not mutate account state and must not create transactions.

---

## 6. Backend Data Models

Use dataclasses for structured backend results.

### 6.1 TransactionType

```python
class TransactionType(Enum)
```

Values:

```text
DEPOSIT
WITHDRAW
BUY
SELL
```

Notes:

- Account creation with an initial deposit should create a `DEPOSIT` transaction.
- If an account is created with `initial_deposit=0`, no deposit transaction is required.

---

### 6.2 Transaction

Represents one completed user action.

Signature:

```python
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
```

Field rules:

| Field | Deposit | Withdraw | Buy | Sell |
|---|---:|---:|---:|---:|
| `cash_amount` | amount | amount | `None` | `None` |
| `symbol` | `None` | `None` | symbol | symbol |
| `quantity` | `None` | `None` | quantity | quantity |
| `share_price` | `None` | `None` | execution price | execution price |
| `total_trade_value` | `None` | `None` | quantity × price | quantity × price |

---

### 6.3 Holding

Represents a holding in a single symbol at report time.

Signature:

```python
@dataclass(frozen=True)
class Holding:
    symbol: str
    quantity: int
    current_price: float
    market_value: float
```

Rules:

- Only include symbols with quantity greater than zero.
- `market_value = quantity * current_price`.

---

### 6.4 PortfolioSummary

Represents account-level report data.

Signature:

```python
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
```

Definitions:

```text
holdings_value = sum(quantity * current_share_price for all holdings)

total_value = cash_balance + holdings_value

net_cash_contributed = total deposits - total withdrawals

profit_loss = total_value - net_cash_contributed

profit_loss_percent = profit_loss / net_cash_contributed * 100
```

If `net_cash_contributed <= 0`, then:

```text
profit_loss_percent = None
```

Also include:

```text
profit_loss_from_initial_deposit = total_value - initial_deposit
```

This satisfies the explicit requirement to report profit/loss from the initial deposit while also giving a more accurate cash-flow-adjusted profit/loss when later deposits or withdrawals occur.

---

### 6.5 AccountSnapshot

Used internally or externally for historical replay.

Signature:

```python
@dataclass(frozen=True)
class AccountSnapshot:
    account_id: str
    owner_name: str
    as_of: datetime
    cash_balance: float
    holdings: dict[str, int]
    total_deposits: float
    total_withdrawals: float
```

Rules:

- This may be returned by an internal helper or public reporting method.
- It should be computed by replaying transactions up to a point in time.

---

## 7. Backend Domain Class: TradingAccount

Represents a single account.

Signature:

```python
class TradingAccount:
```

### Constructor

```python
def __init__(
    self,
    account_id: str,
    owner_name: str,
    initial_deposit: float = 0.0,
    price_lookup: Callable[[str], float] = get_share_price,
    created_at: datetime | None = None,
) -> None
```

Constructor behavior:

- Validate `owner_name` is non-empty after trimming.
- Validate `initial_deposit >= 0`.
- Store:
  - `account_id`
  - `owner_name`
  - `created_at`
  - `initial_deposit`
  - current `cash_balance`
  - current `holdings`
  - transaction list
- If `initial_deposit > 0`, record a `DEPOSIT` transaction with notes `"Initial deposit"`.

---

### Properties

```python
@property
def account_id(self) -> str
```

```python
@property
def owner_name(self) -> str
```

```python
@property
def created_at(self) -> datetime
```

```python
@property
def cash_balance(self) -> float
```

```python
@property
def holdings(self) -> dict[str, int]
```

```python
@property
def transactions(self) -> list[Transaction]
```

Rules:

- Return copies where mutation would otherwise be possible.
- External callers must not be able to mutate internal `holdings` or `transactions` directly.

---

### Deposit Funds

```python
def deposit(
    self,
    amount: float,
    timestamp: datetime | None = None,
) -> Transaction
```

Behavior:

- Validate `amount > 0`.
- Increase cash balance.
- Append a `DEPOSIT` transaction.
- Return the transaction.

---

### Withdraw Funds

```python
def withdraw(
    self,
    amount: float,
    timestamp: datetime | None = None,
) -> Transaction
```

Behavior:

- Validate `amount > 0`.
- Validate `amount <= current cash_balance`.
- Do not consider holdings as withdrawable cash.
- If invalid, raise `InsufficientFundsError`.
- Decrease cash balance.
- Append a `WITHDRAW` transaction.
- Return the transaction.

---

### Buy Shares

```python
def buy(
    self,
    symbol: str,
    quantity: int,
    timestamp: datetime | None = None,
) -> Transaction
```

Behavior:

- Normalize symbol to uppercase.
- Validate symbol using `price_lookup`.
- Validate `quantity` is a positive integer.
- Get current share price.
- Compute:

```text
total_trade_value = quantity * share_price
```

- Validate `total_trade_value <= cash_balance`.
- If invalid, raise `InsufficientFundsError`.
- Decrease cash balance.
- Increase holdings for symbol.
- Append a `BUY` transaction.
- Return the transaction.

---

### Sell Shares

```python
def sell(
    self,
    symbol: str,
    quantity: int,
    timestamp: datetime | None = None,
) -> Transaction
```

Behavior:

- Normalize symbol to uppercase.
- Validate symbol using `price_lookup`.
- Validate `quantity` is a positive integer.
- Validate account owns at least `quantity` shares.
- If invalid, raise `InsufficientSharesError`.
- Get current share price.
- Compute:

```text
total_trade_value = quantity * share_price
```

- Increase cash balance.
- Decrease holdings for symbol.
- Remove symbol from holdings if resulting quantity is zero.
- Append a `SELL` transaction.
- Return the transaction.

---

### Current Holdings Report

```python
def get_holdings(
    self,
    as_of: datetime | None = None,
) -> list[Holding]
```

Behavior:

- If `as_of is None`, use current account state.
- If `as_of` is provided, replay transactions through that timestamp.
- Return holdings sorted alphabetically by symbol.
- Use current share prices from `price_lookup` for market value.
- Do not return zero-quantity holdings.

---

### Portfolio Summary Report

```python
def get_portfolio_summary(
    self,
    as_of: datetime | None = None,
) -> PortfolioSummary
```

Behavior:

- If `as_of is None`, report current state.
- If `as_of` is provided, replay transactions through that timestamp.
- Use current share prices from `price_lookup` to value holdings.
- Include cash balance, holdings value, total value, net contributions, and profit/loss.

---

### Transaction Listing

```python
def list_transactions(
    self,
    as_of: datetime | None = None,
) -> list[Transaction]
```

Behavior:

- Return all transactions in chronological order.
- If `as_of` is provided, only return transactions with `timestamp <= as_of`.
- Return a copy of the list.

---

### Historical Snapshot

```python
def get_snapshot(
    self,
    as_of: datetime | None = None,
) -> AccountSnapshot
```

Behavior:

- Replay transaction history through `as_of`.
- If `as_of is None`, use current state.
- Return cash balance, holdings, total deposits, and total withdrawals.

This method enables reporting holdings and profit/loss at any point in time.

---

### Internal Validation Helpers

Signatures:

```python
def _validate_amount(self, amount: float) -> None
```

```python
def _validate_quantity(self, quantity: int) -> None
```

```python
def _normalize_symbol(self, symbol: str) -> str
```

```python
def _new_transaction_id(self) -> str
```

```python
def _now(self) -> datetime
```

```python
def _round_money(self, amount: float) -> float
```

```python
def _record_transaction(
    self,
    transaction_type: TransactionType,
    cash_amount: float | None,
    symbol: str | None,
    quantity: int | None,
    share_price: float | None,
    total_trade_value: float | None,
    cash_balance_after: float,
    notes: str,
    timestamp: datetime | None = None,
) -> Transaction
```

Money handling:

- Public API may accept floats for simplicity.
- Round stored money values to two decimal places.
- Tests should use fixed prices to avoid floating-point surprises.

---

## 8. Backend Service Class: AccountManager

The Gradio app should use this service rather than directly constructing accounts in multiple places.

Signature:

```python
class AccountManager:
```

### Constructor

```python
def __init__(
    self,
    price_lookup: Callable[[str], float] = get_share_price,
) -> None
```

---

### Create Account

```python
def create_account(
    self,
    owner_name: str,
    initial_deposit: float = 0.0,
) -> TradingAccount
```

Behavior:

- Generate a unique account id.
- Construct a `TradingAccount`.
- Store it in memory.
- Return the account.

Account id format recommendation:

```text
ACC-<short uuid>
```

Example:

```text
ACC-8F3A2C91
```

---

### Get Account

```python
def get_account(
    self,
    account_id: str,
) -> TradingAccount
```

Behavior:

- Return the matching account.
- If not found, raise `AccountNotFoundError`.

---

### List Accounts

```python
def list_accounts(self) -> list[TradingAccount]
```

Behavior:

- Return all accounts sorted by creation time or owner name.
- Return a copy.

---

### Convenience Operations

These methods delegate to the relevant `TradingAccount`.

```python
def deposit(
    self,
    account_id: str,
    amount: float,
) -> Transaction
```

```python
def withdraw(
    self,
    account_id: str,
    amount: float,
) -> Transaction
```

```python
def buy(
    self,
    account_id: str,
    symbol: str,
    quantity: int,
) -> Transaction
```

```python
def sell(
    self,
    account_id: str,
    symbol: str,
    quantity: int,
) -> Transaction
```

```python
def get_holdings(
    self,
    account_id: str,
    as_of: datetime | None = None,
) -> list[Holding]
```

```python
def get_portfolio_summary(
    self,
    account_id: str,
    as_of: datetime | None = None,
) -> PortfolioSummary
```

```python
def list_transactions(
    self,
    account_id: str,
    as_of: datetime | None = None,
) -> list[Transaction]
```

---

## 9. Frontend Design

### Assigned to: `frontend_engineer`

Implement the Gradio app in:

```text
app.py
```

The frontend should import backend functionality from `backend.py`.

Do not duplicate backend validation logic in the frontend. The frontend may do lightweight input cleanup, but the backend is the source of truth.

---

## 10. Gradio 6 API Guidance

Use Gradio 6 style APIs.

Import:

```python
import gradio as gr
```

Main structure:

```python
def build_app() -> gr.Blocks
```

Launch:

```python
if __name__ == "__main__":
    build_app().launch()
```

Use `Blocks`:

```python
with gr.Blocks(title="Trading Simulation Account Manager") as demo:
```

Event binding style:

```python
button.click(
    fn=handler_function,
    inputs=[input_component_1, input_component_2],
    outputs=[output_component_1, output_component_2],
)
```

Important Gradio 6 component update guidance:

- Prefer returning a new component instance to update component configuration.
- For example, to update dropdown choices, return:

```python
gr.Dropdown(choices=new_choices, value=selected_value)
```

- To update a dataframe value, return either:
  - A plain list of rows, when only changing value.
  - Or a new `gr.Dataframe(value=rows, headers=[...], type="array")` if also changing config.
- Avoid relying on older `gr.update(...)` patterns.

`gr.Dataframe` Gradio 6 constructor guidance:

Use:

```python
gr.Dataframe(
    value=[],
    headers=["Column 1", "Column 2"],
    datatype=["str", "number"],
    type="array",
    interactive=False,
)
```

Relevant Gradio 6 notes:

- Use `column_count`, not old `col_count`.
- `type="array"` is appropriate because backend/frontend formatting functions will return `list[list]`.
- Use `interactive=False` for report tables.
- `Button.click` accepts `fn`, `inputs`, and `outputs`.
- `demo.launch()` starts the app.

---

## 11. Frontend Global State

Create a single in-memory manager at module level:

```python
ACCOUNT_MANAGER: AccountManager
```

The app is a simple simulation, so in-memory state is acceptable.

Also use a Gradio `State` component for the selected account id:

```python
selected_account_state = gr.State(value=None)
```

The module-level manager stores all accounts; the Gradio state tracks which account the current UI is operating on.

---

## 12. Frontend UI Layout

### 12.1 Header

Components:

```python
gr.Markdown
```

Content:

```text
# Trading Simulation Account Manager
Create an account, deposit or withdraw funds, buy and sell shares, and view your portfolio.
```

---

### 12.2 Account Creation Section

Components:

```python
owner_name_input = gr.Textbox(...)
initial_deposit_input = gr.Number(...)
create_account_button = gr.Button(...)
account_dropdown = gr.Dropdown(...)
selected_account_state = gr.State(...)
```

Recommended labels:

| Component | Label |
|---|---|
| Owner name textbox | `"Owner Name"` |
| Initial deposit number | `"Initial Deposit"` |
| Create button | `"Create Account"` |
| Account dropdown | `"Selected Account"` |

Behavior:

- User enters owner name and initial deposit.
- Clicking create account:
  - Calls backend `AccountManager.create_account`.
  - Selects the new account.
  - Updates the dropdown choices.
  - Refreshes summary, holdings, and transactions.

Dropdown choices should be human-readable.

Recommended display format:

```text
ACC-12345678 - Alice
```

The backend account id should still be recoverable.

Simpler acceptable option:

```text
ACC-12345678
```

If using display labels with owner names, implement helper parsing carefully.

---

### 12.3 Cash Operations Section

Components:

```python
cash_amount_input = gr.Number(...)
deposit_button = gr.Button(...)
withdraw_button = gr.Button(...)
```

Recommended labels:

| Component | Label |
|---|---|
| Cash amount | `"Cash Amount"` |
| Deposit button | `"Deposit"` |
| Withdraw button | `"Withdraw"` |

Behavior:

- Deposit calls `AccountManager.deposit`.
- Withdraw calls `AccountManager.withdraw`.
- Display success or error in status output.
- Refresh reports after successful operations.

---

### 12.4 Trade Operations Section

Components:

```python
symbol_dropdown = gr.Dropdown(...)
quantity_input = gr.Number(...)
buy_button = gr.Button(...)
sell_button = gr.Button(...)
```

Supported symbol choices:

```text
AAPL
TSLA
GOOGL
```

Recommended labels:

| Component | Label |
|---|---|
| Symbol dropdown | `"Symbol"` |
| Quantity number | `"Quantity"` |
| Buy button | `"Buy"` |
| Sell button | `"Sell"` |

Behavior:

- Buy calls `AccountManager.buy`.
- Sell calls `AccountManager.sell`.
- Display success or error.
- Refresh reports after successful operations.

Quantity handling:

- Gradio `Number` may return `float`.
- Convert to `int` in the handler before calling the backend.
- If the value is not an integer, return a user-friendly error and do not call backend.

---

### 12.5 Reports Section

Use three dataframes.

#### Portfolio Summary Table

Component:

```python
summary_dataframe = gr.Dataframe(...)
```

Recommended headers:

```text
Metric
Value
```

Rows:

```text
Account ID
Owner
Cash Balance
Holdings Value
Total Portfolio Value
Initial Deposit
Net Cash Contributed
Profit/Loss
Profit/Loss %
Profit/Loss From Initial Deposit
As Of
```

---

#### Holdings Table

Component:

```python
holdings_dataframe = gr.Dataframe(...)
```

Recommended headers:

```text
Symbol
Quantity
Current Price
Market Value
```

---

#### Transactions Table

Component:

```python
transactions_dataframe = gr.Dataframe(...)
```

Recommended headers:

```text
Timestamp
Type
Cash Amount
Symbol
Quantity
Share Price
Trade Value
Cash Balance After
Notes
Transaction ID
```

---

### 12.6 Status Output

Component:

```python
status_output = gr.Textbox(...)
```

Recommended configuration:

```text
label="Status"
interactive=False
lines=3
```

All user-facing errors should be displayed here rather than crashing the Gradio app.

---

## 13. Frontend Helper Functions

Implement these in `app.py`.

### Account Choice Formatting

```python
def format_account_choice(account: TradingAccount) -> str
```

```python
def extract_account_id(choice: str | None) -> str | None
```

```python
def get_account_choices() -> list[str]
```

---

### Report Formatting

```python
def format_money(value: float) -> str
```

```python
def format_percent(value: float | None) -> str
```

```python
def format_summary_rows(summary: PortfolioSummary) -> list[list[str]]
```

```python
def format_holding_rows(holdings: list[Holding]) -> list[list[str | int]]
```

```python
def format_transaction_rows(transactions: list[Transaction]) -> list[list[str | int | float | None]]
```

---

### Refresh Reports

```python
def build_empty_report_outputs() -> tuple[list[list], list[list], list[list]]
```

```python
def refresh_reports(
    account_id: str | None,
) -> tuple[list[list], list[list], list[list]]
```

Returns:

```text
summary rows
holding rows
transaction rows
```

Behavior:

- If no account is selected, return empty tables.
- If account id is invalid, return empty tables or an error through the calling handler.

---

## 14. Frontend Event Handlers

All handlers should catch `AccountError` and `ValueError` and return user-friendly status messages.

### Create Account Handler

```python
def handle_create_account(
    owner_name: str,
    initial_deposit: float | int | None,
) -> tuple[str, gr.Dropdown, str, list[list], list[list], list[list]]
```

Returns:

```text
status message
updated account dropdown component
selected account id state
summary rows
holdings rows
transaction rows
```

Behavior:

- Convert `initial_deposit` to float, defaulting to `0.0` if blank.
- Call backend.
- Update account dropdown choices.
- Select newly created account.
- Refresh reports.

---

### Select Account Handler

```python
def handle_select_account(
    account_choice: str | None,
) -> tuple[str, str | None, list[list], list[list], list[list]]
```

Returns:

```text
status message
selected account id state
summary rows
holdings rows
transaction rows
```

---

### Deposit Handler

```python
def handle_deposit(
    selected_account_id: str | None,
    amount: float | int | None,
) -> tuple[str, list[list], list[list], list[list]]
```

Returns:

```text
status message
summary rows
holdings rows
transaction rows
```

---

### Withdraw Handler

```python
def handle_withdraw(
    selected_account_id: str | None,
    amount: float | int | None,
) -> tuple[str, list[list], list[list], list[list]]
```

Returns:

```text
status message
summary rows
holdings rows
transaction rows
```

---

### Buy Handler

```python
def handle_buy(
    selected_account_id: str | None,
    symbol: str | None,
    quantity: float | int | None,
) -> tuple[str, list[list], list[list], list[list]]
```

Returns:

```text
status message
summary rows
holdings rows
transaction rows
```

---

### Sell Handler

```python
def handle_sell(
    selected_account_id: str | None,
    symbol: str | None,
    quantity: float | int | None,
) -> tuple[str, list[list], list[list], list[list]]
```

Returns:

```text
status message
summary rows
holdings rows
transaction rows
```

---

## 15. Frontend Event Wiring

Inside `build_app()` wire events as follows.

### Create Account Button

```python
create_account_button.click(
    fn=handle_create_account,
    inputs=[owner_name_input, initial_deposit_input],
    outputs=[
        status_output,
        account_dropdown,
        selected_account_state,
        summary_dataframe,
        holdings_dataframe,
        transactions_dataframe,
    ],
)
```

---

### Account Dropdown Change

```python
account_dropdown.change(
    fn=handle_select_account,
    inputs=[account_dropdown],
    outputs=[
        status_output,
        selected_account_state,
        summary_dataframe,
        holdings_dataframe,
        transactions_dataframe,
    ],
)
```

---

### Deposit Button

```python
deposit_button.click(
    fn=handle_deposit,
    inputs=[selected_account_state, cash_amount_input],
    outputs=[
        status_output,
        summary_dataframe,
        holdings_dataframe,
        transactions_dataframe,
    ],
)
```

---

### Withdraw Button

```python
withdraw_button.click(
    fn=handle_withdraw,
    inputs=[selected_account_state, cash_amount_input],
    outputs=[
        status_output,
        summary_dataframe,
        holdings_dataframe,
        transactions_dataframe,
    ],
)
```

---

### Buy Button

```python
buy_button.click(
    fn=handle_buy,
    inputs=[selected_account_state, symbol_dropdown, quantity_input],
    outputs=[
        status_output,
        summary_dataframe,
        holdings_dataframe,
        transactions_dataframe,
    ],
)
```

---

### Sell Button

```python
sell_button.click(
    fn=handle_sell,
    inputs=[selected_account_state, symbol_dropdown, quantity_input],
    outputs=[
        status_output,
        summary_dataframe,
        holdings_dataframe,
        transactions_dataframe,
    ],
)
```

---

## 16. Unit Test Design

### Assigned to: `test_engineer`

Implement tests in:

```text
test_backend.py
```

Use Python standard library `unittest`.

Do not test Gradio UI directly.

Run tests with:

```text
uv run python -m unittest test_backend.py
```

---

## 17. Backend Unit Test Cases

### 17.1 Price Provider Tests

Test class:

```python
class TestSharePriceProvider(unittest.TestCase)
```

Test methods:

```python
def test_get_share_price_returns_fixed_prices(self) -> None
```

```python
def test_get_share_price_is_case_insensitive(self) -> None
```

```python
def test_get_share_price_unknown_symbol_raises(self) -> None
```

Expected:

- `AAPL` returns `150.00`.
- `TSLA` returns `250.00`.
- `GOOGL` returns `2800.00`.
- Lowercase symbols work.
- Unknown symbols raise `UnknownSymbolError`.

---

### 17.2 Account Creation Tests

Test class:

```python
class TestAccountCreation(unittest.TestCase)
```

Test methods:

```python
def test_create_account_with_initial_deposit(self) -> None
```

```python
def test_create_account_with_zero_initial_deposit(self) -> None
```

```python
def test_create_account_negative_initial_deposit_raises(self) -> None
```

```python
def test_create_account_blank_owner_name_raises(self) -> None
```

Expected:

- Initial deposit becomes cash balance.
- Initial deposit creates a deposit transaction.
- Zero initial deposit creates no transaction.
- Negative initial deposit raises `InvalidAmountError`.
- Blank owner name raises `ValueError` or `AccountError`, depending on backend implementation choice.

---

### 17.3 Deposit Tests

Test class:

```python
class TestDeposits(unittest.TestCase)
```

Test methods:

```python
def test_deposit_increases_cash_balance(self) -> None
```

```python
def test_deposit_records_transaction(self) -> None
```

```python
def test_deposit_zero_raises(self) -> None
```

```python
def test_deposit_negative_raises(self) -> None
```

Expected:

- Cash balance increases by deposit amount.
- Transaction type is `DEPOSIT`.
- Invalid deposits raise `InvalidAmountError`.

---

### 17.4 Withdrawal Tests

Test class:

```python
class TestWithdrawals(unittest.TestCase)
```

Test methods:

```python
def test_withdraw_decreases_cash_balance(self) -> None
```

```python
def test_withdraw_records_transaction(self) -> None
```

```python
def test_withdraw_more_than_cash_raises(self) -> None
```

```python
def test_failed_withdraw_does_not_create_transaction(self) -> None
```

Expected:

- Valid withdrawal reduces cash.
- Withdrawal beyond cash raises `InsufficientFundsError`.
- Failed withdrawal does not mutate cash or transaction history.

---

### 17.5 Buy Tests

Test class:

```python
class TestBuyingShares(unittest.TestCase)
```

Test methods:

```python
def test_buy_reduces_cash_and_increases_holdings(self) -> None
```

```python
def test_buy_records_transaction_with_execution_price(self) -> None
```

```python
def test_buy_more_than_cash_raises(self) -> None
```

```python
def test_failed_buy_does_not_mutate_state(self) -> None
```

```python
def test_buy_invalid_quantity_raises(self) -> None
```

```python
def test_buy_unknown_symbol_raises(self) -> None
```

Example:

- Account starts with `$1000`.
- Buy `2` shares of `AAPL` at `$150`.
- Cash becomes `$700`.
- Holdings become `{"AAPL": 2}`.

---

### 17.6 Sell Tests

Test class:

```python
class TestSellingShares(unittest.TestCase)
```

Test methods:

```python
def test_sell_increases_cash_and_decreases_holdings(self) -> None
```

```python
def test_sell_records_transaction_with_execution_price(self) -> None
```

```python
def test_sell_more_than_owned_raises(self) -> None
```

```python
def test_failed_sell_does_not_mutate_state(self) -> None
```

```python
def test_sell_invalid_quantity_raises(self) -> None
```

```python
def test_sell_unknown_symbol_raises(self) -> None
```

Example:

- Account starts with `$1000`.
- Buy `3` shares of `AAPL`.
- Sell `1` share of `AAPL`.
- Holdings become `{"AAPL": 2}`.
- Cash increases by `$150`.

---

### 17.7 Holdings Report Tests

Test class:

```python
class TestHoldingsReports(unittest.TestCase)
```

Test methods:

```python
def test_get_holdings_returns_current_holdings_with_market_values(self) -> None
```

```python
def test_get_holdings_excludes_zero_quantity_positions(self) -> None
```

```python
def test_get_holdings_sorted_by_symbol(self) -> None
```

Expected:

- Holdings include symbol, quantity, current price, and market value.
- Fully sold positions are absent.
- Rows are sorted by symbol.

---

### 17.8 Portfolio Summary Tests

Test class:

```python
class TestPortfolioSummary(unittest.TestCase)
```

Test methods:

```python
def test_portfolio_summary_total_value(self) -> None
```

```python
def test_portfolio_summary_profit_loss_with_no_trades(self) -> None
```

```python
def test_portfolio_summary_profit_loss_after_buy(self) -> None
```

```python
def test_portfolio_summary_net_cash_contributed_after_deposit_and_withdrawal(self) -> None
```

Expected:

- `total_value = cash_balance + holdings_value`.
- With fixed prices and no price changes, buying shares does not itself create profit/loss.
- Deposits and withdrawals are treated as cash flows, not trading profit.

---

### 17.9 Transaction Listing Tests

Test class:

```python
class TestTransactionHistory(unittest.TestCase)
```

Test methods:

```python
def test_list_transactions_returns_all_transactions_in_order(self) -> None
```

```python
def test_transaction_ids_are_unique(self) -> None
```

```python
def test_transactions_include_cash_balance_after(self) -> None
```

Expected:

- Transactions appear in chronological order.
- Every transaction has a unique id.
- Cash balance after each transaction is correct.

---

### 17.10 Historical Reporting Tests

Test class:

```python
class TestHistoricalReports(unittest.TestCase)
```

Test methods:

```python
def test_get_snapshot_as_of_timestamp(self) -> None
```

```python
def test_get_holdings_as_of_timestamp(self) -> None
```

```python
def test_get_portfolio_summary_as_of_timestamp(self) -> None
```

```python
def test_list_transactions_as_of_timestamp(self) -> None
```

Approach:

- Use explicit timestamps passed into account methods.
- Example timeline:
  - `t1`: deposit `$1000`
  - `t2`: buy `2 AAPL`
  - `t3`: buy `1 TSLA`
  - `t4`: sell `1 AAPL`
- Assert reports at `t2`, `t3`, and `t4`.

---

### 17.11 AccountManager Tests

Test class:

```python
class TestAccountManager(unittest.TestCase)
```

Test methods:

```python
def test_create_account_stores_account(self) -> None
```

```python
def test_get_missing_account_raises(self) -> None
```

```python
def test_manager_deposit_delegates_to_account(self) -> None
```

```python
def test_manager_buy_delegates_to_account(self) -> None
```

Expected:

- Manager stores and retrieves accounts.
- Invalid account ids raise `AccountNotFoundError`.
- Convenience methods work correctly.

---

## 18. Engineering Assignments

## `backend_engineer`

Owns:

```text
backend.py
```

Responsibilities:

1. Implement the fixed `get_share_price(symbol)` provider.
2. Implement backend exceptions.
3. Implement data models:
   - `TransactionType`
   - `Transaction`
   - `Holding`
   - `PortfolioSummary`
   - `AccountSnapshot`
4. Implement `TradingAccount`.
5. Implement `AccountManager`.
6. Ensure all operations validate before mutating state.
7. Ensure failed operations do not append transactions.
8. Ensure reports work for both current state and `as_of` timestamps.
9. Keep backend independent of Gradio.

Completion criteria:

- Backend supports all required account, cash, trading, reporting, and validation operations.
- Public method signatures match this design.
- Unit tests written by `test_engineer` pass.

---

## `frontend_engineer`

Owns:

```text
app.py
```

Responsibilities:

1. Build a Gradio 6 `Blocks` app.
2. Import and use `AccountManager` from `backend.py`.
3. Provide UI for:
   - Creating accounts.
   - Selecting accounts.
   - Depositing cash.
   - Withdrawing cash.
   - Buying shares.
   - Selling shares.
   - Viewing portfolio summary.
   - Viewing holdings.
   - Viewing transaction history.
4. Use supported symbols:
   - `AAPL`
   - `TSLA`
   - `GOOGL`
5. Display backend errors in the status textbox.
6. Refresh all report tables after successful operations.
7. Follow Gradio 6 update guidance:
   - Use `.click(fn=..., inputs=[...], outputs=[...])`.
   - Use `.change(fn=..., inputs=[...], outputs=[...])`.
   - Return new component instances when changing dropdown choices.
   - Use `gr.Dataframe(..., type="array", interactive=False)`.
   - Avoid old `gr.update(...)` patterns.

Completion criteria:

- Running `uv run python app.py` launches the app.
- User can complete the full flow:
  - Create account.
  - Deposit.
  - Buy shares.
  - Sell shares.
  - Withdraw.
  - View updated reports and transaction history.
- Invalid operations show user-friendly errors and do not crash the app.

---

## `test_engineer`

Owns:

```text
test_backend.py
```

Responsibilities:

1. Write `unittest` tests for backend only.
2. Cover:
   - Price provider.
   - Account creation.
   - Deposits.
   - Withdrawals.
   - Buying.
   - Selling.
   - Holdings reports.
   - Portfolio summaries.
   - Transaction history.
   - Historical reporting.
   - AccountManager.
3. Verify failed operations do not mutate state.
4. Use deterministic fixed share prices.
5. Use explicit timestamps for historical reporting tests.

Completion criteria:

- Running this command passes:

```text
uv run python -m unittest test_backend.py
```

---

## 19. End-to-End Acceptance Criteria

The system is complete when:

1. Backend unit tests pass.
2. Gradio app launches successfully.
3. A user can create an account with an initial deposit.
4. A user can deposit additional funds.
5. A user can withdraw available cash.
6. The system rejects withdrawals above cash balance.
7. A user can buy shares if they have enough cash.
8. The system rejects purchases above available cash.
9. A user can sell shares they own.
10. The system rejects selling shares not owned.
11. Holdings report shows current quantities and market values.
12. Portfolio summary shows:
    - Cash balance.
    - Holdings value.
    - Total portfolio value.
    - Profit/loss.
    - Profit/loss from initial deposit.
13. Transaction history lists all successful user actions over time.
14. Historical report methods support `as_of` timestamps in the backend.