from typing import Union

import attr

from .datespec import DateSpec


@attr.define(kw_only=True)
class Transfer:
    direction: str
    account_id: int


@attr.define(kw_only=True)
class Transaction:
    transaction_id: str = attr.ib()
    account_id: str = attr.ib()
    date: str = attr.ib()
    amount: float = attr.ib()
    name: str = attr.ib()
    type: str = attr.ib()


@attr.define(kw_only=True)
class CCBalanceAmount:
    account_id: dict = attr.ib()
    index: int = attr.ib()

    @classmethod
    def from_spec(cls, spec, index):
        instructions = spec['cc_balance']
        return CCBalanceAmount(account_id=instructions['account_id'], index=index)


@attr.define(kw_only=True)
class CCTransaction(Transaction):
    amount: CCBalanceAmount = attr.ib()
    transfer: Union[Transfer, None] = attr.ib()


@attr.define(kw_only=True)
class ScheduledTransactions:
    plain: list = attr.ib(factory=list)
    cc: list = attr.ib(factory=list)

    @classmethod
    def from_spec(cls, spec, start_date, end_date):
        transactions = []
        for account_id, account_spec in spec['accounts'].items():
            if account_spec['scheduled_transactions']:
                for trans_id, trans in account_spec['scheduled_transactions'].items():
                    st = ScheduledTransaction.from_spec(account_id, trans_id, trans)
                    transactions.extend(st.generate_transactions(start_date, end_date))
        plain = [t for t in transactions if type(t).__name__ == 'Transaction']
        cc = [t for t in transactions if type(t).__name__ == 'CCTransaction']
        return ScheduledTransactions(plain=plain, cc=cc)


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

        This process may generate transactions for any other account

        :param start_date: str
        :param end_date: str
        :return: list
        """
        transactions = []
        dates = self.date_spec.generate_dates(start_date, end_date)
        for i, d in enumerate(dates):
            transactions.extend(self.create_transaction(i, d, self.amount))
        return transactions

    def create_transaction(self, index, date, amount):
        if type(amount) == dict:
            return self.create_cc_trans(index, date, amount)
        if self.type == 'transfer':
            return self.create_transfer(date, amount)
        if self.type == 'income':
            return self.create_credit(date, amount)
        if self.type == 'expense':
            return self.create_debit(date, amount)

    def create_transfer(self, date, amount):
        transactions = []
        # determine sending and receiving account
        if self.transfer.direction == 'to':
            sending_account_id = self.account_id
            receiving_account_id = self.transfer.account_id
        elif self.transfer.direction == 'from':
            sending_account_id = self.transfer.account_id
            receiving_account_id = self.account_id
        else:
            raise ValueError(f'Transfer direction must be one of "to", "from". Received: {self.transfer.direction}')
        # debit sending account
        transactions.append(
            Transaction(transaction_id=self.transaction_id, type=self.type, account_id=sending_account_id, date=date,
                        amount=-abs(amount), name=self.name)
        )
        # credit receiving account
        transactions.append(
            Transaction(transaction_id=self.transaction_id, type=self.type, account_id=receiving_account_id, date=date,
                        amount=abs(amount), name=self.name)
        )
        return transactions

    def create_credit(self, date, amount):
        return [Transaction(transaction_id=self.transaction_id, type=self.type, account_id=self.account_id, date=date,
                            amount=abs(amount), name=self.name)]

    def create_debit(self, date, amount):
        return [Transaction(transaction_id=self.transaction_id, type=self.type, account_id=self.account_id, date=date,
                            amount=-abs(amount), name=self.name)]

    def create_cc_trans(self, index, date, amount):
        return [CCTransaction(transaction_id=self.transaction_id, type=self.type, account_id=self.account_id, date=date,
                              amount=CCBalanceAmount.from_spec(amount, index), name=self.name, transfer=self.transfer)]
