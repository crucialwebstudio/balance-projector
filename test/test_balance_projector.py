import unittest
from parameterized import parameterized
from test.helpers import FixtureHelper, DebugHelper
import datetime
from balance_projector.projector import ScheduledTransaction, DateSpec, Transfer, Transaction, Projector, \
    RunningBalance


class TestProjector(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @parameterized.expand([
        (
                # Every Month on the 31st
                "monthly_31st",
                {
                    'start_date':   '2021-11-05',
                    'end_date':     '2022-11-05',
                    'frequency':    'monthly',
                    'interval':     1,
                    'day_of_week':  None,
                    'day_of_month': 31
                },
                [
                    datetime.datetime(2021, 11, 30, 0, 0, 0),
                    datetime.datetime(2021, 12, 31, 0, 0, 0),
                    datetime.datetime(2022, 1, 31, 0, 0, 0),
                    datetime.datetime(2022, 2, 28, 0, 0, 0),
                    datetime.datetime(2022, 3, 31, 0, 0, 0),
                    datetime.datetime(2022, 4, 30, 0, 0, 0),
                    datetime.datetime(2022, 5, 31, 0, 0, 0),
                    datetime.datetime(2022, 6, 30, 0, 0, 0),
                    datetime.datetime(2022, 7, 31, 0, 0, 0),
                    datetime.datetime(2022, 8, 31, 0, 0, 0),
                    datetime.datetime(2022, 9, 30, 0, 0, 0),
                    datetime.datetime(2022, 10, 31, 0, 0, 0)
                ]
        ),
        (
                # Every Month on the 30th
                "monthly_30th",
                {
                    'start_date':   '2021-11-05',
                    'end_date':     '2022-11-05',
                    'frequency':    'monthly',
                    'interval':     1,
                    'day_of_week':  None,
                    'day_of_month': 30
                },
                [
                    datetime.datetime(2021, 11, 30, 0, 0, 0),
                    datetime.datetime(2021, 12, 31, 0, 0, 0),
                    datetime.datetime(2022, 1, 31, 0, 0, 0),
                    datetime.datetime(2022, 2, 28, 0, 0, 0),
                    datetime.datetime(2022, 3, 31, 0, 0, 0),
                    datetime.datetime(2022, 4, 30, 0, 0, 0),
                    datetime.datetime(2022, 5, 31, 0, 0, 0),
                    datetime.datetime(2022, 6, 30, 0, 0, 0),
                    datetime.datetime(2022, 7, 31, 0, 0, 0),
                    datetime.datetime(2022, 8, 31, 0, 0, 0),
                    datetime.datetime(2022, 9, 30, 0, 0, 0),
                    datetime.datetime(2022, 10, 31, 0, 0, 0)
                ]
        ),
        (
                # every other Friday
                "every_other_friday",
                {
                    'start_date':   '2021-11-05',
                    'end_date':     '2022-11-05',
                    'frequency':    'weekly',
                    'interval':     2,
                    'day_of_week':  'fri',
                    'day_of_month': None
                },
                [
                    datetime.datetime(2021, 11, 5, 0, 0),
                    datetime.datetime(2021, 11, 19, 0, 0),
                    datetime.datetime(2021, 12, 3, 0, 0),
                    datetime.datetime(2021, 12, 17, 0, 0),
                    datetime.datetime(2021, 12, 31, 0, 0),
                    datetime.datetime(2022, 1, 14, 0, 0),
                    datetime.datetime(2022, 1, 28, 0, 0),
                    datetime.datetime(2022, 2, 11, 0, 0),
                    datetime.datetime(2022, 2, 25, 0, 0),
                    datetime.datetime(2022, 3, 11, 0, 0),
                    datetime.datetime(2022, 3, 25, 0, 0),
                    datetime.datetime(2022, 4, 8, 0, 0),
                    datetime.datetime(2022, 4, 22, 0, 0),
                    datetime.datetime(2022, 5, 6, 0, 0),
                    datetime.datetime(2022, 5, 20, 0, 0),
                    datetime.datetime(2022, 6, 3, 0, 0),
                    datetime.datetime(2022, 6, 17, 0, 0),
                    datetime.datetime(2022, 7, 1, 0, 0),
                    datetime.datetime(2022, 7, 15, 0, 0),
                    datetime.datetime(2022, 7, 29, 0, 0),
                    datetime.datetime(2022, 8, 12, 0, 0),
                    datetime.datetime(2022, 8, 26, 0, 0),
                    datetime.datetime(2022, 9, 9, 0, 0),
                    datetime.datetime(2022, 9, 23, 0, 0),
                    datetime.datetime(2022, 10, 7, 0, 0),
                    datetime.datetime(2022, 10, 21, 0, 0),
                    datetime.datetime(2022, 11, 4, 0, 0)
                ]
        ),
        (
                # One-time
                "one_time",
                {
                    'start_date':   '2021-11-05',
                    'end_date':     '2021-11-05',
                    'frequency':    'daily',
                    'interval':     1,
                    'day_of_week':  None,
                    'day_of_month': None
                },
                [
                    datetime.datetime(2021, 11, 5, 0, 0)
                ]
        )
    ])
    def test_create_dates(self, name, param, expected):
        datespec = DateSpec.from_spec(param)
        actual = datespec.generate_dates()
        self.assertEqual(actual, expected)

    @parameterized.expand([
        (
                "bi_weekly_transfer",
                {
                    'account_id': 1,
                    'name':       'Roth IRA',
                    'amount':     250.00,
                    'type':       'transfer',
                    'date_spec':  {
                        'start_date':   '2022-01-01',
                        'end_date':     '2022-06-30',
                        'frequency':    'weekly',
                        'interval':     2,
                        'day_of_week':  'fri',
                        'day_of_month': None
                    },
                    'transfer':   {
                        'direction':  'to',
                        'account_id': 2
                    }
                },
                [
                    Transaction(account_id=1, date=datetime.datetime(2022, 1, 14, 0, 0), amount=-250.0,
                                name='Roth IRA'),
                    Transaction(account_id=2, date=datetime.datetime(2022, 1, 14, 0, 0), amount=250.0, name='Roth IRA'),
                    Transaction(account_id=1, date=datetime.datetime(2022, 1, 28, 0, 0), amount=-250.0,
                                name='Roth IRA'),
                    Transaction(account_id=2, date=datetime.datetime(2022, 1, 28, 0, 0), amount=250.0, name='Roth IRA'),
                    Transaction(account_id=1, date=datetime.datetime(2022, 2, 11, 0, 0), amount=-250.0,
                                name='Roth IRA'),
                    Transaction(account_id=2, date=datetime.datetime(2022, 2, 11, 0, 0), amount=250.0, name='Roth IRA'),
                    Transaction(account_id=1, date=datetime.datetime(2022, 2, 25, 0, 0), amount=-250.0,
                                name='Roth IRA'),
                    Transaction(account_id=2, date=datetime.datetime(2022, 2, 25, 0, 0), amount=250.0, name='Roth IRA'),
                    Transaction(account_id=1, date=datetime.datetime(2022, 3, 11, 0, 0), amount=-250.0,
                                name='Roth IRA'),
                    Transaction(account_id=2, date=datetime.datetime(2022, 3, 11, 0, 0), amount=250.0, name='Roth IRA'),
                    Transaction(account_id=1, date=datetime.datetime(2022, 3, 25, 0, 0), amount=-250.0,
                                name='Roth IRA'),
                    Transaction(account_id=2, date=datetime.datetime(2022, 3, 25, 0, 0), amount=250.0, name='Roth IRA'),
                    Transaction(account_id=1, date=datetime.datetime(2022, 4, 8, 0, 0), amount=-250.0, name='Roth IRA'),
                    Transaction(account_id=2, date=datetime.datetime(2022, 4, 8, 0, 0), amount=250.0, name='Roth IRA'),
                    Transaction(account_id=1, date=datetime.datetime(2022, 4, 22, 0, 0), amount=-250.0,
                                name='Roth IRA'),
                    Transaction(account_id=2, date=datetime.datetime(2022, 4, 22, 0, 0), amount=250.0, name='Roth IRA'),
                    Transaction(account_id=1, date=datetime.datetime(2022, 5, 6, 0, 0), amount=-250.0, name='Roth IRA'),
                    Transaction(account_id=2, date=datetime.datetime(2022, 5, 6, 0, 0), amount=250.0, name='Roth IRA'),
                    Transaction(account_id=1, date=datetime.datetime(2022, 5, 20, 0, 0), amount=-250.0,
                                name='Roth IRA'),
                    Transaction(account_id=2, date=datetime.datetime(2022, 5, 20, 0, 0), amount=250.0, name='Roth IRA'),
                    Transaction(account_id=1, date=datetime.datetime(2022, 6, 3, 0, 0), amount=-250.0, name='Roth IRA'),
                    Transaction(account_id=2, date=datetime.datetime(2022, 6, 3, 0, 0), amount=250.0, name='Roth IRA'),
                    Transaction(account_id=1, date=datetime.datetime(2022, 6, 17, 0, 0), amount=-250.0,
                                name='Roth IRA'),
                    Transaction(account_id=2, date=datetime.datetime(2022, 6, 17, 0, 0), amount=250.0, name='Roth IRA')
                ]
        ),
        (
                "one_time_credit",
                {
                    'account_id': 1,
                    'name':       'Craigslist Sale',
                    'amount':     500.00,
                    'type':       'income',
                    'date_spec':  {
                        'start_date':   '2022-05-15',
                        'end_date':     '2022-05-15',
                        'frequency':    'daily',
                        'interval':     1,
                        'day_of_week':  None,
                        'day_of_month': None
                    },
                    'transfer':   None
                },
                [
                    Transaction(account_id=1, date=datetime.datetime(2022, 5, 15, 0, 0), amount=500.00,
                                name='Craigslist Sale')
                ]
        ),
        (
                "one_time_debit",
                {
                    'account_id': 1,
                    'name':       'Mountain Bike',
                    'amount':     1299.99,
                    'type':       'expense',
                    'date_spec':  {
                        'start_date':   '2022-05-15',
                        'end_date':     '2022-05-15',
                        'frequency':    'daily',
                        'interval':     1,
                        'day_of_week':  None,
                        'day_of_month': None
                    },
                    'transfer':   None
                },
                [
                    Transaction(account_id=1, date=datetime.datetime(2022, 5, 15, 0, 0), amount=-1299.99,
                                name='Mountain Bike')
                ]
        )
    ])
    def test_create_transactions(self, name, param, expected):
        transfer = None if param['transfer'] is None else Transfer(direction=param['transfer']['direction'],
                                                                   account_id=param['transfer']['account_id'])
        tr = ScheduledTransaction(account_id=param['account_id'], name=param['name'], amount=param['amount'],
                                  type=param['type'], date_spec=DateSpec.from_spec(param['date_spec']),
                                  transfer=transfer)
        actual = tr.generate_transactions()
        self.assertEqual(actual, expected)

    def test_projector(self):
        spec = FixtureHelper.get_yaml('balance_projector.yml')
        projector = Projector.from_spec(spec)
        actual = projector.project(1, 2000.00, '2021-11-01', '2021-12-31')
        # DebugHelper.pprint(actual)

        expected = [
            RunningBalance(
                transaction=Transaction(account_id=1, date=datetime.datetime(2021, 11, 5, 0, 0), amount=2500.0,
                                        name='Paycheck'), balance=4500.0),
            RunningBalance(
                transaction=Transaction(account_id=1, date=datetime.datetime(2021, 11, 5, 0, 0), amount=-222.22,
                                        name='Roth IRA'), balance=4277.78),
            RunningBalance(
                transaction=Transaction(account_id=1, date=datetime.datetime(2021, 11, 19, 0, 0), amount=2500.0,
                                        name='Paycheck'), balance=6777.78),
            RunningBalance(
                transaction=Transaction(account_id=1, date=datetime.datetime(2021, 11, 19, 0, 0), amount=-222.22,
                                        name='Roth IRA'), balance=6555.5599999999995),
            RunningBalance(
                transaction=Transaction(account_id=1, date=datetime.datetime(2021, 12, 3, 0, 0), amount=2500.0,
                                        name='Paycheck'), balance=9055.56),
            RunningBalance(
                transaction=Transaction(account_id=1, date=datetime.datetime(2021, 12, 3, 0, 0), amount=-222.22,
                                        name='Roth IRA'), balance=8833.34),
            RunningBalance(
                transaction=Transaction(account_id=1, date=datetime.datetime(2021, 12, 17, 0, 0), amount=2500.0,
                                        name='Paycheck'), balance=11333.34),
            RunningBalance(
                transaction=Transaction(account_id=1, date=datetime.datetime(2021, 12, 17, 0, 0), amount=-222.22,
                                        name='Roth IRA'), balance=11111.12),
            RunningBalance(
                transaction=Transaction(account_id=1, date=datetime.datetime(2021, 12, 31, 0, 0), amount=2500.0,
                                        name='Paycheck'), balance=13611.12),
            RunningBalance(
                transaction=Transaction(account_id=1, date=datetime.datetime(2021, 12, 31, 0, 0), amount=-222.22,
                                        name='Roth IRA'), balance=13388.900000000001)
        ]
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
