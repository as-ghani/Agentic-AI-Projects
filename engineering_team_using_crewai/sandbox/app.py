from __future__ import annotations

import gradio as gr

from backend import (
    AccountError,
    AccountManager,
    Holding,
    PortfolioSummary,
    Transaction,
    TradingAccount,
)

ACCOUNT_MANAGER = AccountManager()
SUPPORTED_SYMBOLS = ["AAPL", "TSLA", "GOOGL"]

CSS = """
:root {
    --red-900: #7f1d1d;
    --red-700: #b91c1c;
    --red-600: #dc2626;
    --black-950: #0a0a0a;
    --black-900: #1a1a1a;
    --gray-800: #2a2a2a;
    --gray-700: #3a3a3a;
    --gray-200: #e5e7eb;
    --gray-100: #f3f4f6;
    --panel-bg: rgba(255, 255, 255, 0.92);
    --panel-border: rgba(185, 28, 28, 0.18);
    --text-main: #111827;
    --text-muted: #6b7280;
}
@media (prefers-color-scheme: dark) {
    :root {
        --panel-bg: rgba(10, 10, 10, 0.92);
        --panel-border: rgba(220, 38, 38, 0.28);
        --text-main: #f9fafb;
        --text-muted: #9ca3af;
    }
}
.gradio-container {
    background:
        radial-gradient(circle at top, rgba(220, 38, 38, 0.10), transparent 34%),
        linear-gradient(180deg, var(--black-950) 0%, var(--black-900) 100%);
    color: var(--text-main) !important;
}
.panel-card {
    background: var(--panel-bg);
    border: 1px solid var(--panel-border);
    border-radius: 18px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.18);
    padding: 16px;
    backdrop-filter: blur(10px);
}
.hero {
    padding: 12px 0 4px 0;
}
.hero h1 { color: #f9fafb; margin-bottom: 0.2rem; }
.hero p { color: #d1d5db; margin-top: 0; }
.gr-button {
    background: linear-gradient(135deg, var(--red-700), var(--red-600)) !important;
    color: white !important;
    border: none !important;
    font-weight: 600 !important;
}
.gr-button:hover { filter: brightness(1.05); }
.gr-textbox, .gr-number input, .gr-dropdown, .gr-dataframe {
    border-color: rgba(185, 28, 28, 0.22) !important;
}
"""


def format_account_choice(account: TradingAccount) -> str:
    return f"{account.account_id} - {account.owner_name}"


def extract_account_id(choice: str | None) -> str | None:
    if not choice:
        return None
    return choice.split(" - ", 1)[0].strip() or None


def get_account_choices() -> list[str]:
    return [format_account_choice(account) for account in ACCOUNT_MANAGER.list_accounts()]


def format_money(value: float) -> str:
    return f"${value:,.2f}"


def format_percent(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.2f}%"


def format_summary_rows(summary: PortfolioSummary) -> list[list[str]]:
    return [
        ["Account ID", summary.account_id],
        ["Owner", summary.owner_name],
        ["Cash Balance", format_money(summary.cash_balance)],
        ["Holdings Value", format_money(summary.holdings_value)],
        ["Total Portfolio Value", format_money(summary.total_value)],
        ["Initial Deposit", format_money(summary.initial_deposit)],
        ["Net Cash Contributed", format_money(summary.net_cash_contributed)],
        ["Profit/Loss", format_money(summary.profit_loss)],
        ["Profit/Loss %", format_percent(summary.profit_loss_percent)],
        ["Profit/Loss From Initial Deposit", format_money(summary.profit_loss_from_initial_deposit)],
        ["As Of", summary.as_of.isoformat(sep=" ", timespec="seconds")],
    ]


def format_holding_rows(holdings: list[Holding]) -> list[list[str | int]]:
    return [[h.symbol, h.quantity, format_money(h.current_price), format_money(h.market_value)] for h in holdings]


def format_transaction_rows(transactions: list[Transaction]) -> list[list[str | int | float | None]]:
    rows = []
    for tx in transactions:
        rows.append(
            [
                tx.timestamp.isoformat(sep=" ", timespec="seconds"),
                tx.transaction_type.value,
                format_money(tx.cash_amount) if tx.cash_amount is not None else None,
                tx.symbol,
                tx.quantity,
                format_money(tx.share_price) if tx.share_price is not None else None,
                format_money(tx.total_trade_value) if tx.total_trade_value is not None else None,
                format_money(tx.cash_balance_after),
                tx.notes,
                tx.transaction_id,
            ]
        )
    return rows


def build_empty_report_outputs() -> tuple[list[list], list[list], list[list]]:
    return [], [], []


def refresh_reports(account_id: str | None) -> tuple[list[list], list[list], list[list]]:
    if not account_id:
        return build_empty_report_outputs()
    try:
        summary = ACCOUNT_MANAGER.get_portfolio_summary(account_id)
        holdings = ACCOUNT_MANAGER.get_holdings(account_id)
        transactions = ACCOUNT_MANAGER.list_transactions(account_id)
        return format_summary_rows(summary), format_holding_rows(holdings), format_transaction_rows(transactions)
    except AccountError:
        return build_empty_report_outputs()


def _parse_amount(value: float | int | None) -> float:
    if value is None or value == "":
        return 0.0
    return float(value)


def _parse_quantity(value: float | int | None) -> int:
    if value is None or value == "":
        raise ValueError("Quantity is required")
    if isinstance(value, float) and not value.is_integer():
        raise ValueError("Quantity must be a whole number")
    quantity = int(value)
    if float(quantity) != float(value):
        raise ValueError("Quantity must be a whole number")
    return quantity


def handle_create_account(owner_name: str, initial_deposit: float | int | None):
    try:
        account = ACCOUNT_MANAGER.create_account(owner_name, _parse_amount(initial_deposit))
        choices = get_account_choices()
        summary, holdings, transactions = refresh_reports(account.account_id)
        return (
            f"Created account {account.account_id}",
            gr.Dropdown(choices=choices, value=format_account_choice(account)),
            account.account_id,
            summary,
            holdings,
            transactions,
        )
    except (AccountError, ValueError) as exc:
        return f"Error: {exc}", gr.Dropdown(choices=get_account_choices()), None, *build_empty_report_outputs()


def handle_select_account(account_choice: str | None):
    account_id = extract_account_id(account_choice)
    if not account_id:
        return "No account selected", None, *build_empty_report_outputs()
    try:
        ACCOUNT_MANAGER.get_account(account_id)
        return f"Selected {account_id}", account_id, *refresh_reports(account_id)
    except AccountError as exc:
        return f"Error: {exc}", None, *build_empty_report_outputs()


def handle_deposit(selected_account_id: str | None, amount: float | int | None):
    try:
        if not selected_account_id:
            raise AccountError("No account selected")
        ACCOUNT_MANAGER.deposit(selected_account_id, _parse_amount(amount))
        return "Deposit successful", *refresh_reports(selected_account_id)
    except (AccountError, ValueError) as exc:
        return f"Error: {exc}", *(refresh_reports(selected_account_id) if selected_account_id else build_empty_report_outputs())


def handle_withdraw(selected_account_id: str | None, amount: float | int | None):
    try:
        if not selected_account_id:
            raise AccountError("No account selected")
        ACCOUNT_MANAGER.withdraw(selected_account_id, _parse_amount(amount))
        return "Withdrawal successful", *refresh_reports(selected_account_id)
    except (AccountError, ValueError) as exc:
        return f"Error: {exc}", *(refresh_reports(selected_account_id) if selected_account_id else build_empty_report_outputs())


def handle_buy(selected_account_id: str | None, symbol: str | None, quantity: float | int | None):
    try:
        if not selected_account_id:
            raise AccountError("No account selected")
        ACCOUNT_MANAGER.buy(selected_account_id, symbol or "", _parse_quantity(quantity))
        return "Buy successful", *refresh_reports(selected_account_id)
    except (AccountError, ValueError) as exc:
        return f"Error: {exc}", *(refresh_reports(selected_account_id) if selected_account_id else build_empty_report_outputs())


def handle_sell(selected_account_id: str | None, symbol: str | None, quantity: float | int | None):
    try:
        if not selected_account_id:
            raise AccountError("No account selected")
        ACCOUNT_MANAGER.sell(selected_account_id, symbol or "", _parse_quantity(quantity))
        return "Sell successful", *refresh_reports(selected_account_id)
    except (AccountError, ValueError) as exc:
        return f"Error: {exc}", *(refresh_reports(selected_account_id) if selected_account_id else build_empty_report_outputs())


def build_app() -> gr.Blocks:
    with gr.Blocks(title="Trading Simulation Account Manager") as demo:
        gr.Markdown(
            "# Trading Simulation Account Manager\n"
            "Create an account, deposit or withdraw funds, buy and sell shares, and view your portfolio.",
            elem_classes=["hero"],
        )
        selected_account_state = gr.State(value=None)
        with gr.Row():
            with gr.Column(scale=1, elem_classes=["panel-card"]):
                owner_name_input = gr.Textbox(label="Owner Name", placeholder="Enter account owner name")
                initial_deposit_input = gr.Number(label="Initial Deposit", value=0)
                create_account_button = gr.Button("Create Account")
            with gr.Column(scale=1, elem_classes=["panel-card"]):
                account_dropdown = gr.Dropdown(label="Selected Account", choices=get_account_choices())
                cash_amount_input = gr.Number(label="Cash Amount", value=0)
                with gr.Row():
                    deposit_button = gr.Button("Deposit")
                    withdraw_button = gr.Button("Withdraw")
        with gr.Row():
            with gr.Column(scale=1, elem_classes=["panel-card"]):
                symbol_dropdown = gr.Dropdown(label="Symbol", choices=SUPPORTED_SYMBOLS, value=SUPPORTED_SYMBOLS[0])
                quantity_input = gr.Number(label="Quantity", value=1)
                with gr.Row():
                    buy_button = gr.Button("Buy")
                    sell_button = gr.Button("Sell")
            with gr.Column(scale=1, elem_classes=["panel-card"]):
                status_output = gr.Textbox(label="Status", interactive=False, lines=4)
        with gr.Row():
            summary_dataframe = gr.Dataframe(
                value=[],
                headers=["Metric", "Value"],
                datatype=["str", "str"],
                type="array",
                interactive=False,
            )
        with gr.Row():
            holdings_dataframe = gr.Dataframe(
                value=[],
                headers=["Symbol", "Quantity", "Current Price", "Market Value"],
                datatype=["str", "number", "str", "str"],
                type="array",
                interactive=False,
            )
        with gr.Row():
            transactions_dataframe = gr.Dataframe(
                value=[],
                headers=["Timestamp", "Type", "Cash Amount", "Symbol", "Quantity", "Share Price", "Trade Value", "Cash Balance After", "Notes", "Transaction ID"],
                datatype=["str"] * 10,
                type="array",
                interactive=False,
            )

        create_account_button.click(
            fn=handle_create_account,
            inputs=[owner_name_input, initial_deposit_input],
            outputs=[status_output, account_dropdown, selected_account_state, summary_dataframe, holdings_dataframe, transactions_dataframe],
        )
        account_dropdown.change(
            fn=handle_select_account,
            inputs=[account_dropdown],
            outputs=[status_output, selected_account_state, summary_dataframe, holdings_dataframe, transactions_dataframe],
        )
        deposit_button.click(
            fn=handle_deposit,
            inputs=[selected_account_state, cash_amount_input],
            outputs=[status_output, summary_dataframe, holdings_dataframe, transactions_dataframe],
        )
        withdraw_button.click(
            fn=handle_withdraw,
            inputs=[selected_account_state, cash_amount_input],
            outputs=[status_output, summary_dataframe, holdings_dataframe, transactions_dataframe],
        )
        buy_button.click(
            fn=handle_buy,
            inputs=[selected_account_state, symbol_dropdown, quantity_input],
            outputs=[status_output, summary_dataframe, holdings_dataframe, transactions_dataframe],
        )
        sell_button.click(
            fn=handle_sell,
            inputs=[selected_account_state, symbol_dropdown, quantity_input],
            outputs=[status_output, summary_dataframe, holdings_dataframe, transactions_dataframe],
        )
    return demo


if __name__ == "__main__":
    build_app().launch(inbrowser=True)
