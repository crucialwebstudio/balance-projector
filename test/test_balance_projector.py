import datetime
import unittest
from parameterized import parameterized
from test.helpers import FixtureHelper, DebugHelper
import pandas as pd
import numpy as np
from balance_projector.projector import Account, ScheduledTransaction, DateSpec, Transfer, Transaction, Projector
from balance_projector.exceptions import OutOfBoundsException


class TestAccount(unittest.TestCase):
    def test_balance_date_out_of_range(self):
        account = Account(account_id='checking', name='Checking', start_date='2022-01-01', balance=1000)
        account.add_transactions([
            Transaction(transaction_id='bi_weekly_transfer', account_id='checking',
                        date=datetime.datetime(2022, 1, 14, 0, 0), amount=-250.0, name='Savings'),
            Transaction(transaction_id='bi_weekly_transfer', account_id='checking',
                        date=datetime.datetime(2022, 1, 28, 0, 0), amount=-250.0, name='Savings')
        ])
        # before start_date of the account
        self.assertRaises(OutOfBoundsException, account.get_balance, '2021-12-31')

    def test_no_transactions_returns_current_balance(self):
        account = Account(account_id='checking', name='Checking', start_date='2022-01-01', balance=1000)
        self.assertEqual(account.get_balance('2022-01-14'), 1000)

    def test_no_transactions_lt_balance_date_returns_current_balance(self):
        account = Account(account_id='checking', name='Checking', start_date='2022-01-01', balance=1000)
        account.add_transactions([
            Transaction(transaction_id='bi_weekly_transfer', account_id='checking',
                        date=datetime.datetime(2022, 1, 14, 0, 0), amount=-250.0, name='Savings'),
            Transaction(transaction_id='bi_weekly_transfer', account_id='checking',
                        date=datetime.datetime(2022, 1, 28, 0, 0), amount=-250.0, name='Savings')
        ])
        self.assertEqual(account.get_balance('2022-01-05'), 1000)

    def test_get_balance_for_date(self):
        account = Account(account_id='checking', name='Checking', start_date='2022-01-01', balance=1000)
        account.add_transactions([
            Transaction(transaction_id='bi_weekly_transfer', account_id='checking',
                        date=datetime.datetime(2022, 1, 14, 0, 0), amount=-250.0, name='Savings'),
            Transaction(transaction_id='bi_weekly_transfer', account_id='checking',
                        date=datetime.datetime(2022, 1, 28, 0, 0), amount=-250.0, name='Savings')
        ])
        self.assertEqual(account.get_balance('2022-01-05'), 1000)
        self.assertEqual(account.get_balance('2022-01-14'), 750)
        self.assertEqual(account.get_balance('2022-01-15'), 750)
        self.assertEqual(account.get_balance('2022-01-16'), 750)
        self.assertEqual(account.get_balance('2022-01-28'), 500)
        self.assertEqual(account.get_balance('2025-01-01'), 500)

    def test_add_previous_transaction_updates_balance(self):
        account = Account(account_id='checking', name='Checking', start_date='2022-01-01', balance=7500)
        account.add_transactions([
            Transaction(transaction_id='bi_weekly_transfer', account_id='checking',
                        date=datetime.datetime(2022, 1, 14, 0, 0), amount=-250.0, name='Savings'),
            Transaction(transaction_id='bi_weekly_transfer', account_id='checking',
                        date=datetime.datetime(2022, 1, 28, 0, 0), amount=-250.0, name='Savings')
        ])
        self.assertEqual(account.get_balance('2022-01-05'), 7500)
        self.assertEqual(account.get_balance('2022-01-14'), 7250)
        self.assertEqual(account.get_balance('2022-01-15'), 7250)
        self.assertEqual(account.get_balance('2022-01-16'), 7250)
        self.assertEqual(account.get_balance('2022-01-28'), 7000)
        self.assertEqual(account.get_balance('2025-01-01'), 7000)
        account.add_transaction(
            Transaction(transaction_id='mountain_bike', account_id='checking',
                        date=datetime.datetime(2022, 1, 18, 0, 0), amount=-1000, name='Mountain Bike'))
        self.assertEqual(account.get_balance('2022-01-05'), 7500)
        self.assertEqual(account.get_balance('2022-01-14'), 7250)
        self.assertEqual(account.get_balance('2022-01-15'), 7250)
        self.assertEqual(account.get_balance('2022-01-16'), 7250)
        self.assertEqual(account.get_balance('2022-01-28'), 6000)
        self.assertEqual(account.get_balance('2025-01-01'), 6000)


class TestDates(unittest.TestCase):
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
                {
                    'start_date': '2021-11-05',
                    'end_date':   '2022-11-05'
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
                {
                    'start_date': '2021-11-05',
                    'end_date':   '2022-11-05'
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
                {
                    'start_date': '2021-11-05',
                    'end_date':   '2022-11-05'
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
                {
                    'start_date': '2021-11-05',
                    'end_date':   '2021-11-05'
                },
                [
                    datetime.datetime(2021, 11, 5, 0, 0)
                ]
        )
    ])
    def test_create_dates_fixed(self, name, spec, date_filter, expected):
        datespec = DateSpec.from_spec(spec)
        actual = datespec.generate_dates(start_date=date_filter['start_date'], end_date=date_filter['end_date'])
        self.assertEqual(actual, expected)

    @parameterized.expand([
        (
                # Every Month on the 31st
                "monthly_31st_fixed",
                {
                    'start_date':   '2021-11-05',
                    'end_date':     '2022-11-05',
                    'frequency':    'monthly',
                    'interval':     1,
                    'day_of_week':  None,
                    'day_of_month': 31
                },
                {
                    'start_date': '2022-01-01',
                    'end_date':   '2022-06-30'
                },
                [
                    datetime.datetime(2022, 1, 31, 0, 0, 0),
                    datetime.datetime(2022, 2, 28, 0, 0, 0),
                    datetime.datetime(2022, 3, 31, 0, 0, 0),
                    datetime.datetime(2022, 4, 30, 0, 0, 0),
                    datetime.datetime(2022, 5, 31, 0, 0, 0),
                    datetime.datetime(2022, 6, 30, 0, 0, 0)
                ]
        ),
        (
                # Every Month on the 30th
                "monthly_30th_infinite",
                {
                    'start_date':   '2021-11-05',
                    'end_date':     None,
                    'frequency':    'monthly',
                    'interval':     1,
                    'day_of_week':  None,
                    'day_of_month': 30
                },
                {
                    'start_date': '2022-01-01',
                    'end_date':   '2022-06-30'
                },
                [
                    datetime.datetime(2022, 1, 31, 0, 0, 0),
                    datetime.datetime(2022, 2, 28, 0, 0, 0),
                    datetime.datetime(2022, 3, 31, 0, 0, 0),
                    datetime.datetime(2022, 4, 30, 0, 0, 0),
                    datetime.datetime(2022, 5, 31, 0, 0, 0),
                    datetime.datetime(2022, 6, 30, 0, 0, 0)
                ]
        )
    ])
    def test_create_dates_filtered(self, name, spec, date_filter, expected):
        datespec = DateSpec.from_spec(spec)
        actual = datespec.generate_dates(start_date=date_filter['start_date'], end_date=date_filter['end_date'])
        self.assertEqual(actual, expected)


class TestProjector(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_transactions_data_frame(self):
        spec = FixtureHelper.get_spec_fixture()
        projector = Projector.from_spec(spec, '2022-01-01', '2022-12-31')
        checking_df = projector.get_account('checking').get_transactions_df()
        taxable_df = projector.get_account('taxable_brokerage').get_transactions_df()
        # DebugHelper.pprint(checking_df)

        # Spot-check some rows
        mask = ((checking_df['date'] > '2022-02-01') & (checking_df['date'] < '2022-02-28'))
        t = checking_df[mask]
        # DebugHelper.pprint(t)
        np.testing.assert_array_equal(
            t.to_numpy(),
            pd.DataFrame(
                [
                    {
                        'account_id': 'checking', 'date': datetime.datetime(2022, 2, 11, 0, 0, 0), 'amount': -100.00,
                        'name':       'Freedom Fund'
                    },
                    {
                        'account_id': 'checking', 'date': datetime.datetime(2022, 2, 11, 0, 0, 0), 'amount': 2500.00,
                        'name':       'Paycheck'
                    },
                    {
                        'account_id': 'checking', 'date': datetime.datetime(2022, 2, 25, 0, 0, 0), 'amount': -100.00,
                        'name':       'Freedom Fund'
                    },
                    {
                        'account_id': 'checking', 'date': datetime.datetime(2022, 2, 25, 0, 0, 0), 'amount': 2500.00,
                        'name':       'Paycheck'
                    }
                ]
            ).to_numpy()
        )

        mask = ((taxable_df['date'] > '2022-02-01') & (taxable_df['date'] < '2022-02-28'))
        t = taxable_df[mask]
        # DebugHelper.pprint(t)
        np.testing.assert_array_equal(
            t.to_numpy(),
            pd.DataFrame(
                [
                    {
                        'account_id': 'taxable_brokerage', 'date': datetime.datetime(2022, 2, 11, 0, 0, 0),
                        'amount':     100.00,
                        'name':       'Freedom Fund'
                    },
                    {
                        'account_id': 'taxable_brokerage', 'date': datetime.datetime(2022, 2, 25, 0, 0, 0),
                        'amount':     100.00,
                        'name':       'Freedom Fund'
                    }
                ]
            ).to_numpy()
        )


if __name__ == "__main__":
    unittest.main()
