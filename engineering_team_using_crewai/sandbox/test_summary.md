import unittest
from datetime import datetime, timedelta

from backend import (
    AccountManager,
    AccountNotFoundError,
    InsufficientFundsError,
    InsufficientSharesError,
    InvalidAmountError,
    InvalidQuantityError,
    TransactionType,
    UnknownSymbolError,
    get_share_price,
)


class TestSharePriceProvider(unittest.TestCase):
    def test_get_share_price_returns_fixed_prices(self) -> None:
        self.assertEqual(get_share_price("AAPL"), 150.0)
        self.assertEqual(get_share_price("TSLA"), 250.0)
        self.assertEqual(get_share_price("GOOGL"), 2800.0)

    def test_get_share_price_is_case_insensitive(self) -> None:
        self.assertEqual(get_share_price("aapl"), 150.0)
        self.assertEqual(get_share_price("tsla"), 250.0)

    def test_get_share_price_unknown_symbol_raises(self) -> None:
        with self.assertRaises(UnknownSymbolError):
            get_share_price("MSFT")


class TestAccountCreation(unittest.TestCase):
    def setUp(self) -> None:
        self.manager = AccountManager()

    def test_create_account_with_initial_deposit(self) -> None:
        account = self.manager.create_account("Alice", 1000)
        self.assertEqual(account.cash_balance, 1000.0)
        self.assertEqual(len(account.transactions), 1)
        self.assertEqual(account.transactions[0].transaction_type, TransactionType.DEPOSIT)

    def test_create_account_with_zero_initial_deposit(self) -> None:
        account = self.manager.create_account("Bob", 0)
        self.assertEqual(account.cash_balance, 0.0)
        self.assertEqual(len(account.transactions), 0)

    def test_create_account_negative_initial_deposit_raises(self) -> None:
        with self.assertRaises(InvalidAmountError):
            self.manager.create_account("Bob", -1)

    def test_create_account_blank_owner_name_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.manager.create_account("   ", 0)


class TestDeposits(unittest.TestCase):
    def setUp(self) -> None:
        self.manager = AccountManager()
        self.account = self.manager.create_account("Alice", 100)

    def test_deposit_increases_cash_balance(self) -> None:
        self.manager.deposit(self.account.account_id, 50)
        self.assertEqual(self.account.cash_balance, 150.0)

    def test_deposit_records_transaction(self) -> None:
        tx = self.manager.deposit(self.account.account_id, 50)
        self.assertEqual(tx.transaction_type, TransactionType.DEPOSIT)
        self.assertEqual(len(self.account.transactions), 2)

    def test_deposit_zero_raises(self) -> None:
        with self.assertRaises(InvalidAmountError):
            self.manager.deposit(self.account.account_id, 0)

    def test_deposit_negative_raises(self) -> None:
        with self.assertRaises(InvalidAmountError):
            self.manager.deposit(self.account.account_id, -10)


class TestWithdrawals(unittest.TestCase):
    def setUp(self) -> None:
        self.manager = AccountManager()
        self.account = self.manager.create_account("Alice", 100)

    def test_withdraw_decreases_cash_balance(self) -> None:
        self.manager.withdraw(self.account.account_id, 40)
        self.assertEqual(self.account.cash_balance, 60.0)

    def test_withdraw_records_transaction(self) -> None:
        tx = self.manager.withdraw(self.account.account_id, 40)
        self.assertEqual(tx.transaction_type, TransactionType.WITHDRAW)
        self.assertEqual(len(self.account.transactions), 2)

    def test_withdraw_more_than_cash_raises(self) -> None:
        with self.assertRaises(InsufficientFundsError):
            self.manager.withdraw(self.account.account_id, 101)

    def test_failed_withdraw_does_not_create_transaction(self) -> None:
        before = len(self.account.transactions)
        with self.assertRaises(InsufficientFundsError):
            self.manager.withdraw(self.account.account_id, 101)
        self.assertEqual(len(self.account.transactions), before)
        self.assertEqual(self.account.cash_balance, 100.0)


class TestBuyingShares(unittest.TestCase):
    def setUp(self) -> None:
        self.manager = AccountManager()
        self.account = self.manager.create_account("Alice", 1000)

    def test_buy_reduces_cash_and_increases_holdings(self) -> None:
        self.manager.buy(self.account.account_id, "AAPL", 2)
        self.assertEqual(self.account.cash_balance, 700.0)
        self.assertEqual(self.account.holdings, {"AAPL": 2})

    def test_buy_records_transaction_with_execution_price(self) -> None:
        tx = self.manager.buy(self.account.account_id, "AAPL", 2)
        self.assertEqual(tx.transaction_type, TransactionType.BUY)
        self.assertEqual(tx.share_price, 150.0)
        self.assertEqual(tx.total_trade_value, 300.0)

    def test_buy_more_than_cash_raises(self) -> None:
        with self.assertRaises(InsufficientFundsError):
            self.manager.buy(self.account.account_id, "GOOGL", 1)

    def test_failed_buy_does_not_mutate_state(self) -> None:
        before_cash = self.account.cash_balance
        before_tx = len(self.account.transactions)
        with self.assertRaises(InsufficientFundsError):
            self.manager.buy(self.account.account_id, "GOOGL", 1)
        self.assertEqual(self.account.cash_balance, before_cash)
        self.assertEqual(len(self.account.transactions), before_tx)

    def test_buy_invalid_quantity_raises(self) -> None:
        with self.assertRaises(InvalidQuantityError):
            self.manager.buy(self.account.account_id, "AAPL", 0)

    def test_buy_unknown_symbol_raises(self) -> None:
        with self.assertRaises(UnknownSymbolError):
            self.manager.buy(self.account.account_id, "MSFT", 1)


class TestSellingShares(unittest.TestCase):
    def setUp(self) -> None:
        self.manager = AccountManager()
        self.account = self.manager.create_account("Alice", 1000)
        self.manager.buy(self.account.account_id, "AAPL", 3)

    def test_sell_increases_cash_and_decreases_holdings(self) -> None:
        self.manager.sell(self.account.account_id, "AAPL", 1)
        self.assertEqual(self.account.cash_balance, 700.0)
        self.assertEqual(self.account.holdings, {"AAPL": 2})

    def test_sell_records_transaction_with_execution_price(self) -> None:
        tx = self.manager.sell(self.account.account_id, "AAPL", 1)
        self.assertEqual(tx.transaction_type, TransactionType.SELL)
        self.assertEqual(tx.share_price, 150.0)
        self.assertEqual(tx.total_trade_value, 150.0)

    def test_sell_more_than_owned_raises(self) -> None:
        with self.assertRaises(InsufficientSharesError):
            self.manager.sell(self.account.account_id, "AAPL", 4)

    def test_failed_sell_does_not_mutate_state(self) -> None:
        before_cash = self.account.cash_balance
        before_holdings = self.account.holdings
        before_tx = len(self.account.transactions)
        with self.assertRaises(InsufficientSharesError):
            self.manager.sell(self.account.account_id, "AAPL", 4)
        self.assertEqual(self.account.cash_balance, before_cash)
        self.assertEqual(self.account.holdings, before_holdings)
        self.assertEqual(len(self.account.transactions), before_tx)

    def test_sell_invalid_quantity_raises(self) -> None:
        with self.assertRaises(InvalidQuantityError):
            self.manager.sell(self.account.account_id, "AAPL", 0)

    def test_sell_unknown_symbol_raises(self) -> None:
        with self.assertRaises(UnknownSymbolError):
            self.manager.sell(self.account.account_id, "MSFT", 1)


class TestHoldingsReports(unittest.TestCase):
    def setUp(self) -> None:
        self.manager = AccountManager()
        self.account = self.manager.create_account("Alice", 1000)
        self.manager.buy(self.account.account_id, "TSLA", 1)
        self.manager.buy(self.account.account_id, "AAPL", 2)

    def test_get_holdings_returns_current_holdings_with_market_values(self) -> None:
        holdings = self.manager.get_holdings(self.account.account_id)
        self.assertEqual(len(holdings), 2)
        self.assertEqual(holdings[0].symbol, "AAPL")
        self.assertEqual(holdings[0].market_value, 300.0)

    def test_get_holdings_excludes_zero_quantity_positions(self) -> None:
        self.manager.sell(self.account.account_id, "TSLA", 1)
        holdings = self.manager.get_holdings(self.account.account_id)
        self.assertEqual([h.symbol for h in holdings], ["AAPL"])

    def test_get_holdings_sorted_by_symbol(self) -> None:
        holdings = self.manager.get_holdings(self.account.account_id)
        self.assertEqual([h.symbol for h in holdings], ["AAPL", "TSLA"])


class TestPortfolioSummary(unittest.TestCase):
    def setUp(self) -> None:
        self.manager = AccountManager()
        self.account = self.manager.create_account("Alice", 1000)

    def test_portfolio_summary_total_value(self) -> None:
        summary = self.manager.get_portfolio_summary(self.account.account_id)
        self.assertEqual(summary.total_value, 1000.0)

    def test_portfolio_summary_profit_loss_with_no_trades(self) -> None:
        summary = self.manager.get_portfolio_summary(self.account.account_id)
        self.assertEqual(summary.profit_loss, 0.0)
        self.assertEqual(summary.profit_loss_from_initial_deposit, 0.0)

    def test_portfolio_summary_profit_loss_after_buy(self) -> None:
        self.manager.buy(self.account.account_id, "AAPL", 2)
        summary = self.manager.get_portfolio_summary(self.account.account_id)
        self.assertEqual(summary.total_value, 1000.0)
        self.assertEqual(summary.profit_loss, 0.0)

    def test_portfolio_summary_net_cash_contributed_after_deposit_and_withdrawal(self) -> None:
        self.manager.deposit(self.account.account_id, 200)
        self.manager.withdraw(self.account.account_id, 100)
        summary = self.manager.get_portfolio_summary(self.account.account_id)
        self.assertEqual(summary.net_cash_contributed, 1100.0)
        self.assertEqual(summary.profit_loss, 0.0)


class TestTransactionHistory(unittest.TestCase):
    def setUp(self) -> None:
        self.manager = AccountManager()
        self.account = self.manager.create_account("Alice", 100)

    def test_list_transactions_returns_all_transactions_in_order(self) -> None:
        self.manager.deposit(self.account.account_id, 50)
        self.manager.withdraw(self.account.account_id, 25)
        txs = self.manager.list_transactions(self.account.account_id)
        self.assertEqual([t.transaction_type for t in txs], [TransactionType.DEPOSIT, TransactionType.DEPOSIT, TransactionType.WITHDRAW])

    def test_transaction_ids_are_unique(self) -> None:
        self.manager.deposit(self.account.account_id, 50)
        ids = [t.transaction_id for t in self.manager.list_transactions(self.account.account_id)]
        self.assertEqual(len(ids), len(set(ids)))

    def test_transactions_include_cash_balance_after(self) -> None:
        self.manager.deposit(self.account.account_id, 50)
        txs = self.manager.list_transactions(self.account.account_id)
        self.assertEqual(txs[-1].cash_balance_after, 150.0)


class TestHistoricalReports(unittest.TestCase):
    def setUp(self) -> None:
        self.manager = AccountManager()
        self.account = self.manager.create_account("Alice", 0)
        self.t1 = datetime(2024, 1, 1, 9, 0, 0)
        self.t2 = self.t1 + timedelta(minutes=1)
        self.t3 = self.t1 + timedelta(minutes=2)
        self.t4 = self.t1 + timedelta(minutes=3)
        self.account.deposit(1000, timestamp=self.t1)
        self.account.buy("AAPL", 2, timestamp=self.t2)
        self.account.buy("TSLA", 1, timestamp=self.t3)
        self.account.sell("AAPL", 1, timestamp=self.t4)

    def test_get_snapshot_as_of_timestamp(self) -> None:
        snap = self.account.get_snapshot(self.t2)
        self.assertEqual(snap.cash_balance, 700.0)
        self.assertEqual(snap.holdings, {"AAPL": 2})

    def test_get_holdings_as_of_timestamp(self) -> None:
        holdings = self.account.get_holdings(self.t3)
        self.assertEqual([h.symbol for h in holdings], ["AAPL", "TSLA"])

    def test_get_portfolio_summary_as_of_timestamp(self) -> None:
        summary = self.account.get_portfolio_summary(self.t4)
        self.assertEqual(summary.cash_balance, 600.0)
        self.assertEqual(summary.holdings_value, 400.0)
        self.assertEqual(summary.total_value, 1000.0)

    def test_list_transactions_as_of_timestamp(self) -> None:
        txs = self.account.list_transactions(self.t2)
        self.assertEqual([t.transaction_type for t in txs], [TransactionType.DEPOSIT, TransactionType.BUY])


class TestAccountManager(unittest.TestCase):
    def setUp(self) -> None:
        self.manager = AccountManager()

    def test_create_account_stores_account(self) -> None:
        account = self.manager.create_account("Alice", 100)
        self.assertIs(self.manager.get_account(account.account_id), account)

    def test_get_missing_account_raises(self) -> None:
        with self.assertRaises(AccountNotFoundError):
            self.manager.get_account("missing")

    def test_manager_deposit_delegates_to_account(self) -> None:
        account = self.manager.create_account("Alice", 100)
        tx = self.manager.deposit(account.account_id, 50)
        self.assertEqual(tx.cash_balance_after, 150.0)

    def test_manager_buy_delegates_to_account(self) -> None:
        account = self.manager.create_account("Alice", 1000)
        tx = self.manager.buy(account.account_id, "AAPL", 1)
        self.assertEqual(tx.symbol, "AAPL")
        self.assertEqual(self.manager.get_account(account.account_id).holdings, {"AAPL": 1})


if __name__ == "__main__":
    unittest.main()