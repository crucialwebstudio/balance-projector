import attr
import pandas as pd
from datetime import datetime
import dateutil.rrule as dr
import dateutil.parser as dp

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
        return cls(**spec)

    def generate_dates(self):
        start = dp.parse(self.start_date)
        end = dp.parse(self.end_date)

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
            dtstart=start,
            until=end,
            interval=self.interval,
            byweekday=weekday_map.get(self.day_of_week),
            bymonthday=day_of_month
        )
        dates = list(rr)

        return dates


@attr.define(kw_only=True)
class Transaction:
    account_id: int
    date: str
    amount: float
    name: str


@attr.define(kw_only=True)
class Transfer:
    direction: str
    account_id: int


@attr.define(kw_only=True)
class Account:
    account_id: int = attr.ib()
    name: str = attr.ib()
    balance: float = attr.ib()
    transactions: list = attr.ib(factory=list)

    @classmethod
    def from_spec(cls, spec):
        return cls(account_id=spec['account_id'], name=spec['name'], balance=spec['balance'])

    def add_transaction(self, transaction):
        if transaction.account_id != self.account_id:
            raise Exception('Invalid account id')
        self.transactions.append(transaction)

    def generate_transactions_data_frame(self):
        # TODO Handle empty dataframes
        df = pd.DataFrame.from_records(list(map(attr.asdict, self.transactions)))
        df = df.sort_values(by=['date', 'name'],
                            ascending=True,
                            ignore_index=True)
        return df

    def get_running_balance(self, start_date, end_date):
        trans_df = self.generate_transactions_data_frame()
        # filter transactions
        start = dp.parse(start_date)
        end = dp.parse(end_date)
        mask = ((trans_df['date'] >= start) & (trans_df['date'] <= end))
        filtered = trans_df[mask]
        return self.apply_running_balance(self.balance, filtered)

    def get_running_balance_grouped(self, start_date, end_date):
        trans_df = self.get_running_balance(start_date, end_date)
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
    account_id: int
    name: str
    amount: float
    type: str
    date_spec: DateSpec
    transfer: Transfer = None

    def generate_transactions(self):
        transactions = []
        is_transfer = self.type == 'transfer'
        is_credit = self.type == 'income'
        is_debit = self.type == 'expense'
        dates = self.date_spec.generate_dates()
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
            Transaction(account_id=sending_account_id, date=date, amount=-abs(self.amount), name=self.name)
        )
        # credit receiving account
        transactions.append(
            Transaction(account_id=receiving_account_id, date=date, amount=abs(self.amount), name=self.name)
        )

        return transactions

    def create_credit(self, date):
        return [Transaction(account_id=self.account_id, date=date, amount=abs(self.amount), name=self.name)]

    def create_debit(self, date):
        return [Transaction(account_id=self.account_id, date=date, amount=-abs(self.amount), name=self.name)]


@attr.define(kw_only=True)
class Chart:
    name: str = attr.ib()
    type: str = attr.ib()
    accounts: list = attr.ib()


@attr.define(kw_only=True)
class Projector:
    accounts: dict = attr.ib()
    chart_spec: dict = attr.ib()

    @classmethod
    def from_spec(cls, spec):
        account_map = {}
        for account_spec in spec['accounts']:
            account = Account.from_spec(account_spec)
            account_map[account.account_id] = account
        for param in spec['scheduled_transactions']:
            date_spec = DateSpec.from_spec(param['date_spec'])
            transfer = None if param['transfer'] is None else Transfer(direction=param['transfer']['direction'],
                                                                       account_id=param['transfer']['account_id'])
            st = ScheduledTransaction(account_id=param['account_id'], name=param['name'], amount=param['amount'],
                                      type=param['type'], date_spec=date_spec, transfer=transfer)
            for tr in st.generate_transactions():
                # NOTE: Due to transfers, a ScheduledTransaction can generate a Transaction for any other account.
                # So we get account_id from each generated transaction
                account = account_map.get(tr.account_id)
                # add transaction to account
                account.add_transaction(tr)

        return cls(accounts=account_map, chart_spec=spec['chart_spec'])

    def get_account(self, account_id):
        return self.accounts.get(account_id)

    def get_charts(self, start_date, end_date):
        charts = []
        for chart in self.chart_spec:
            accounts = list(
                map(
                    lambda a: dict(
                        name=self.get_account(a).name,
                        df=self.get_account(a).get_running_balance_grouped(
                            start_date.strftime(DATE_FORMAT),
                            end_date.strftime(DATE_FORMAT)
                        )), chart['account_ids']
                )
            )
            charts.append(Chart(name=chart['name'], type=chart['type'], accounts=accounts))
        return charts
