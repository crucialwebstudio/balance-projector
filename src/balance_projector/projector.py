from datetime import datetime
import dateutil.rrule as dr
import dateutil.parser as dp
import attr

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
class RunningBalance:
    transaction: Transaction
    balance: float


@attr.define(kw_only=True)
class Projector:
    scheduled_transactions = attr.ib(factory=list)
    transaction_map = attr.ib()

    @transaction_map.default
    def default_transaction_map(self):
        return {}

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

    def get_transaction_map(self):
        if len(self.transaction_map) > 0:
            return self.transaction_map

        for st in self.scheduled_transactions:
            self.group_transactions(st.generate_transactions())

        return self.transaction_map

    def group_transactions(self, transactions):
        for trans in transactions:
            if self.transaction_map.get(trans.account_id, None) is None:
                self.transaction_map[trans.account_id] = [
                    trans
                ]
            else:
                self.transaction_map[trans.account_id].append(trans)

    def project(self, account_id, starting_balance, start_date, end_date):
        # initialize list of balances to return
        balances = []

        # initialize current balance
        current_balance = starting_balance

        start = dp.parse(start_date)
        end = dp.parse(end_date)

        # get transactions for this account
        transactions = self.get_transaction_map().get(account_id, [])

        # sort transactions by date
        transactions.sort(key=lambda x: x.date)

        for t in transactions:
            if start <= t.date <= end:
                # apply transaction to current balance
                current_balance = current_balance + t.amount
                balances.append(RunningBalance(transaction=t, balance=current_balance))

        return balances
