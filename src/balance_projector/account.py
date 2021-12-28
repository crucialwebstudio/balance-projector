from typing import Union

import attr
import dateutil.parser as dp
import pandas as pd

from .exceptions import AccountNotFoundException, OutOfBoundsException
from .transaction import ScheduledTransactions

pd.options.mode.chained_assignment = None  # no warning message and no exception is raised


@attr.define(kw_only=True)
class Account:
    account_id: str = attr.ib()
    name: str = attr.ib()
    start_date: str = attr.ib()
    balance: float = attr.ib()
    transactions: list = attr.ib(factory=list)
    transactions_df: Union[pd.DataFrame, None] = attr.ib()

    @transactions_df.default
    def _default_transactions_df(self):
        return None

    def add_transactions(self, transactions):
        for t in transactions:
            self.add_transaction(t)

    def add_transaction(self, transaction):
        """
        Add a transaction to the Account

        :param transaction: Transaction
        :return:
        """
        if transaction.account_id != self.account_id:
            raise ValueError(f'Expected account id: {self.account_id} Received: {transaction.account_id}')
        self.transactions_df = None  # flip to None so it gets rebuilt on the next request
        self.transactions.append(transaction)

    def get_transactions_df(self):
        """
        Get master transactions_df

        :return: pd.DataFrame
        """
        if self.transactions_df is None:
            data = list(map(attr.asdict, self.transactions))
            df = pd.DataFrame(data, columns=['account_id', 'date', 'amount', 'name'])
            df = df.sort_values(by=['date', 'name'],
                                ascending=True,
                                ignore_index=True)
            self.transactions_df = df
        return self.transactions_df

    def get_balance(self, date):
        """
        Get balance for a date

        :param date: str
        :return: float
        """
        target_date = dp.parse(date)
        account_start = dp.parse(self.start_date)
        df = self.get_running_balance_grouped()
        if target_date < account_start:
            raise OutOfBoundsException(f'date {target_date} before start_date of the account: {account_start}')
        if len(df.index) == 0:
            return self.balance
        sub_df = df[df.index.to_pydatetime() <= target_date]
        if len(sub_df.index) == 0:
            return self.balance
        last_row_df = sub_df.iloc[-1:]
        balance = last_row_df.iloc[0]['balance']
        return balance

    def get_running_balance(self):
        """
        Get running balance df with transactions as separate row

        :return: pd.Datadrame
        """
        trans_df = self.get_transactions_df().copy()
        return self.apply_running_balance(self.balance, trans_df)

    def get_running_balance_grouped(self):
        """
        Get running balance df with transactions grouped and indexed by date

        :return: pd.DataFrame
        """
        trans_df = self.get_running_balance()
        # create new column with "transaction: amount" string
        trans_df['amt_desc'] = trans_df['amount'].astype(str).str.cat(trans_df['name'], sep=': ')
        # group by date
        df_date_group = trans_df.groupby('date').agg({
            'amt_desc': '<br>'.join,
            'amount':   'sum'
        })
        return self.apply_running_balance(self.balance, df_date_group)

    @classmethod
    def apply_running_balance(cls, starting_balance, trans_df):
        trans_df['balance'] = starting_balance + trans_df['amount'].cumsum()
        return trans_df


@attr.define(kw_only=True)
class Accounts:
    accounts: dict = attr.ib(factory=dict)

    @classmethod
    def from_spec(cls, spec, start_date, end_date):
        accounts = dict()
        for account_id, account_spec in spec['accounts'].items():
            accounts[account_id] = Account(account_id=account_id, name=account_spec['name'],
                                           start_date=start_date, balance=account_spec['balance'])
        return Accounts(accounts=accounts)

    def get_account(self, account_id: str):
        account = self.accounts.get(account_id, None)
        if account is None:
            raise AccountNotFoundException(f'account not found: {account_id}')
        return account

    def apply_scheduled_transactions(self, st: ScheduledTransactions):
        # apply plain transactions
        for t in st.plain:
            account = self.get_account(t.account_id)
            account.add_transaction(t)
        # apply cc transactions
        sorted_ccs = sorted(st.cc, key=lambda c: c.date)
        for cc in sorted_ccs:
            print(cc)
