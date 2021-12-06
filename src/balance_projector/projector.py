import attr
import pandas as pd
from datetime import datetime
import dateutil.rrule as dr
import dateutil.parser as dp

pd.options.mode.chained_assignment = None    # no warning message and no exception is raised

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
class Projector:
    scheduled_transactions = attr.ib(factory=list)

    @classmethod
    def from_spec(cls, spec):
        scheduled_transactions = []
        for param in spec['scheduled_transactions']:
            date_spec = DateSpec.from_spec(param['date_spec'])
            transfer = None if param['transfer'] is None else Transfer(direction=param['transfer']['direction'],
                                                                       account_id=param['transfer']['account_id'])
            st = ScheduledTransaction(account_id=param['account_id'], name=param['name'], amount=param['amount'],
                                      type=param['type'], date_spec=date_spec, transfer=transfer)

            scheduled_transactions.append(st)
        return cls(scheduled_transactions=scheduled_transactions)

    def get_transactions(self):
        transactions = []
        for st in self.scheduled_transactions:
            transactions.extend(st.generate_transactions())
        return transactions

    def get_transactions_data_frame(self):
        df = pd.DataFrame.from_records(list(map(attr.asdict, self.get_transactions())))
        df = df.sort_values(by=['date', 'name'],
                            ascending=True,
                            ignore_index=True)
        return df

    def filter(self, account_id, start_date, end_date):
        df = self.get_transactions_data_frame()
        start = dp.parse(start_date)
        end = dp.parse(end_date)

        # filter transactions
        mask = (df['account_id'] == account_id) & ((df['date'] >= start) & (df['date'] <= end))
        filtered = df[mask]
        return filtered
