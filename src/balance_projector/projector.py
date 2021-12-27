from typing import Union
import attr
import pandas as pd
from datetime import datetime
import dateutil.rrule as dr
import dateutil.parser as dp
from .exceptions import AccountNotFoundException, OutOfBoundsException

pd.options.mode.chained_assignment = None  # no warning message and no exception is raised

DATE_FORMAT = '%Y-%m-%d'

frequency_map = {
    'daily':   dr.DAILY,
    'weekly':  dr.WEEKLY,
    'monthly': dr.MONTHLY
}

weekday_map = {
    'mon': dr.MO,
    'tue': dr.TU,
    'wed': dr.WE,
    'thu': dr.TH,
    'fri': dr.FR,
    'sat': dr.SA,
    'sun': dr.SU
}


@attr.define(kw_only=True)
class DateSpec:
    start_date: str
    end_date: str
    frequency: str
    interval: int
    day_of_week: str = None
    day_of_month: int = None

    @classmethod
    def from_spec(cls, spec):
        return cls(start_date=spec['start_date'], end_date=spec['end_date'],
                   frequency=spec['frequency'], interval=spec['interval'],
                   day_of_week=spec['day_of_week'], day_of_month=spec['day_of_month'])

    def generate_dates(self, start_date, end_date):
        """
        Generate dates according to spec. Filtered by start_date, end_date

        :param start_date:
        :param end_date:
        :return:
        """
        start_date = dp.parse(start_date)
        end_date = dp.parse(end_date)
        rrule_start = dp.parse(self.start_date)
        # Dates from spec could (more likely as time progresses) generate dates we don't care about.
        # Here we set the max `until` argument for the rrule.
        if self.end_date is None:
            # self.end_date from the spec could be None to define infinite dates.
            # There has to be a limit, so substitute None with end_date argument.
            rrule_end = end_date
        else:
            # Substitute if spec_end_date > end_date
            spec_end_date = dp.parse(self.end_date)
            rrule_end = end_date if spec_end_date > end_date else spec_end_date

        """
        Specify "last day of month" when self.day_of_month would exclude certain months.

        See this StackOverflow answer for discussion of the issue.
        https://stackoverflow.com/questions/38328313/dateutils-rrule-returns-dates-that-2-months-apart/38555283#38555283
        """
        day_of_month = self.day_of_month
        if day_of_month in [29, 30, 31]:
            """
            Specify "last day of the month" by passing bymonthday=-1 to the rrule generator, thereby including 
            months like February where self.day_of_month would be "out of bounds".
            
            TODO Fix edge cases 
    
            This solution still leaves edge cases where, for example:
    
            day_of_month = 29
            October has 31 days
            Date generated as 2021-10-31
            More accurate would be 2021-10-29
            """
            day_of_month = -1
        rr = dr.rrule(
            frequency_map.get(self.frequency),
            dtstart=rrule_start,
            until=rrule_end,
            interval=self.interval,
            byweekday=weekday_map.get(self.day_of_week),
            bymonthday=day_of_month
        )
        dates = list(rr)
        # Filter start dates. End dates were limited in rrule
        dates = [d for d in dates if d >= start_date]
        return dates


@attr.define(kw_only=True)
class Transaction:
    transaction_id: str
    account_id: str
    date: str
    amount: float
    name: str


@attr.define(kw_only=True)
class Transfer:
    direction: str
    account_id: int


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
class AccountMap:
    accounts: dict = attr.ib(factory=dict)

    def add_account(self, account):
        self.accounts[account.account_id] = account

    def get_account(self, account_id):
        account = self.accounts.get(account_id, None)
        if account is None:
            raise AccountNotFoundException(f'account not found: {account_id}')
        return account

    def add_transactions(self, transactions):
        for t in transactions:
            account = self.get_account(t.account_id)
            account.add_transaction(t)


@attr.define(kw_only=True)
class ScheduledTransaction:
    transaction_id: str = attr.ib()
    account_id: int = attr.ib()
    name: str = attr.ib()
    amount: Union[float, dict] = attr.ib()
    type: str = attr.ib()
    date_spec: DateSpec = attr.ib()
    transfer: Union[Transfer, None] = attr.ib()

    @classmethod
    def from_spec(cls, account_id, transaction_id, spec):
        transfer = None if spec['transfer'] is None else Transfer(direction=spec['transfer']['direction'],
                                                                  account_id=spec['transfer']['account_id'])
        st = ScheduledTransaction(transaction_id=transaction_id, account_id=account_id,
                                  name=spec['name'], amount=spec['amount'], type=spec['type'],
                                  date_spec=DateSpec.from_spec(spec['date_spec']), transfer=transfer)
        return st

    def generate_transactions(self, start_date, end_date):
        """
        Generate transactions

        Note that this process may generate transactions for any other account

        :param start_date: str
        :param end_date: str
        :return: list
        """
        transactions = []
        if type(self.amount) == dict:
            return transactions
        dates = self.date_spec.generate_dates(start_date, end_date)
        for d in dates:
            if self.type == 'transfer':
                transactions.extend(self.create_transfer(d))
            if self.type == 'income':
                transactions.extend(self.create_credit(d))
            if self.type == 'expense':
                transactions.extend(self.create_debit(d))
        return transactions

    def create_transfer(self, date):
        transactions = []
        # determine sending and receiving account
        if self.transfer.direction == 'to':
            sending_account_id = self.account_id
            receiving_account_id = self.transfer.account_id
        elif self.transfer.direction == 'from':
            sending_account_id = self.transfer.account_id
            receiving_account_id = self.account_id
        # debit sending account
        transactions.append(
            Transaction(transaction_id=self.transaction_id, account_id=sending_account_id, date=date,
                        amount=-abs(self.amount), name=self.name)
        )
        # credit receiving account
        transactions.append(
            Transaction(transaction_id=self.transaction_id, account_id=receiving_account_id, date=date,
                        amount=abs(self.amount), name=self.name)
        )
        return transactions

    def create_credit(self, date):
        return [Transaction(transaction_id=self.transaction_id, account_id=self.account_id, date=date,
                            amount=abs(self.amount), name=self.name)]

    def create_debit(self, date):
        return [Transaction(transaction_id=self.transaction_id, account_id=self.account_id, date=date,
                            amount=-abs(self.amount), name=self.name)]


@attr.define(kw_only=True)
class Chart:
    name: str = attr.ib()
    type: str = attr.ib()
    accounts: list = attr.ib()


@attr.define(kw_only=True)
class Projector:
    spec: dict = attr.ib(factory=dict)
    start_date: str = attr.ib(factory=str)
    end_date: str = attr.ib(factory=str)
    accounts: AccountMap = attr.ib()

    @classmethod
    def from_spec(cls, spec, start_date, end_date):
        accounts = AccountMap()
        for account_id, account_spec in spec['accounts'].items():
            accounts.add_account(Account(account_id=account_id, name=account_spec['name'],
                                         start_date=start_date, balance=account_spec['balance']))
        Projector.load_transactions(accounts, start_date, end_date, spec)
        return Projector(spec=spec, start_date=start_date, end_date=end_date, accounts=accounts)

    @classmethod
    def load_transactions(cls, accounts, start_date, end_date, spec):
        for account_id, account_spec in spec['accounts'].items():
            if account_spec['scheduled_transactions']:
                for trans_id, trans in account_spec['scheduled_transactions'].items():
                    st = ScheduledTransaction.from_spec(account_id, trans_id, trans)
                    accounts.add_transactions(st.generate_transactions(start_date, end_date))

    def get_account(self, account_id):
        return self.accounts.get_account(account_id)

    def get_charts(self):
        charts = []
        for chart in self.spec['chart_spec']:
            accounts = list(
                map(
                    lambda a: dict(
                        name=self.get_account(a).name,
                        df=self.get_account(a).get_running_balance_grouped()), chart['account_ids']
                )
            )
            charts.append(Chart(name=chart['name'], type=chart['type'], accounts=accounts))
        return charts
