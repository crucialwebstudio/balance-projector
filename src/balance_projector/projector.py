import attr
import pandas as pd
from datetime import datetime
import dateutil.rrule as dr
import dateutil.parser as dp
from .exceptions import AccountNotFoundException

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
    balance: float = attr.ib()
    transactions: list = attr.ib(factory=list)

    @classmethod
    def from_spec(cls, account_id, spec):
        return cls(account_id=account_id, name=spec['name'], balance=spec['balance'])

    def add_transaction(self, transaction):
        if transaction.account_id != self.account_id:
            raise Exception('Invalid account id')
        self.transactions.append(transaction)

    def generate_transactions_data_frame(self):
        data = list(map(attr.asdict, self.transactions))
        df = pd.DataFrame(data, columns=['account_id', 'date', 'amount', 'name'])
        df = df.sort_values(by=['date', 'name'],
                            ascending=True,
                            ignore_index=True)
        return df

    def get_running_balance(self):
        trans_df = self.generate_transactions_data_frame()
        return self.apply_running_balance(self.balance, trans_df)

    def get_running_balance_grouped(self):
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
class ScheduledTransaction:
    transaction_id: str
    account_id: int
    name: str
    amount: float
    type: str
    date_spec: DateSpec
    transfer: Transfer = None

    def generate_transactions(self, start_date, end_date):
        transactions = []
        is_transfer = self.type == 'transfer'
        is_credit = self.type == 'income'
        is_debit = self.type == 'expense'
        dates = self.date_spec.generate_dates(start_date, end_date)
        for d in dates:
            if is_transfer:
                transactions.extend(self.create_transfer(d))
            if is_credit:
                transactions.extend(self.create_credit(d))
            if is_debit:
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
    accounts: dict = attr.ib()
    transactions: list = attr.ib()
    chart_spec: dict = attr.ib()

    @classmethod
    def from_spec(cls, spec, start_date, end_date):
        account_map = {}
        transactions = []
        for account_id, account_spec in spec['accounts'].items():
            account = Account.from_spec(account_id, account_spec)
            account_map[account.account_id] = account
            if account_spec['scheduled_transactions']:
                for trans_id, trans in account_spec['scheduled_transactions'].items():
                    transfer = None if trans['transfer'] is None else Transfer(direction=trans['transfer']['direction'],
                                                                               account_id=trans['transfer'][
                                                                                   'account_id'])
                    st = ScheduledTransaction(transaction_id=trans_id, account_id=account_id, name=trans['name'],
                                              amount=trans['amount'], type=trans['type'],
                                              date_spec=DateSpec.from_spec(trans['date_spec']), transfer=transfer)

                    """
                    NOTE: Due to transfers, a ScheduledTransaction can generate a Transaction for any other account.
                    # So transactions generated by st.generate_transactions() MAY not belong to the account in the 
                    # current iteration.
                    """
                    transactions.extend(st.generate_transactions(start_date, end_date))

        # one last iteration to add transactions to the account
        for t in transactions:
            account = account_map.get(t.account_id, None)
            if account is None:
                raise AccountNotFoundException(
                    f'Account not found for transaction: account_id: {t.account_id}, transaction_id: {t.transaction_id}')
            account.add_transaction(t)

        return cls(accounts=account_map, transactions=transactions, chart_spec=spec['chart_spec'])

    def get_account(self, account_id):
        account = self.accounts.get(account_id, None)
        if account is None:
            raise AccountNotFoundException(f'account not found: {account_id}')
        return account

    def get_charts(self):
        charts = []
        for chart in self.chart_spec:
            accounts = list(
                map(
                    lambda a: dict(
                        name=self.get_account(a).name,
                        df=self.get_account(a).get_running_balance_grouped()), chart['account_ids']
                )
            )
            charts.append(Chart(name=chart['name'], type=chart['type'], accounts=accounts))
        return charts
