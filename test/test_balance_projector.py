import datetime
import unittest
from parameterized import parameterized
from test.helpers import FixtureHelper, DebugHelper
import pandas as pd
import numpy as np
from balance_projector.projector import ScheduledTransaction, DateSpec, Transfer, Transaction, Projector


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
                {
                    'start_date': '2021-11-05',
                    'end_date': '2022-11-05'
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
    def test_create_dates(self, name, spec, date_filter, expected):
        datespec = DateSpec.from_spec(spec)
        actual = datespec.generate_dates(start_date=date_filter['start_date'], end_date=date_filter['end_date'])
        self.assertEqual(actual, expected)

    @parameterized.expand([
        (
                "bi_weekly_transfer",
                {
                    'account_id': 'checking',
                    'name':       'Savings',
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
                        'account_id': 'savings'
                    }
                },
                [
                    Transaction(transaction_id='bi_weekly_transfer', account_id='checking',
                                date=datetime.datetime(2022, 1, 14, 0, 0), amount=-250.0, name='Savings'),
                    Transaction(transaction_id='bi_weekly_transfer', account_id='savings',
                                date=datetime.datetime(2022, 1, 14, 0, 0), amount=250.0, name='Savings'),
                    Transaction(transaction_id='bi_weekly_transfer', account_id='checking',
                                date=datetime.datetime(2022, 1, 28, 0, 0), amount=-250.0, name='Savings'),
                    Transaction(transaction_id='bi_weekly_transfer', account_id='savings',
                                date=datetime.datetime(2022, 1, 28, 0, 0), amount=250.0, name='Savings'),
                    Transaction(transaction_id='bi_weekly_transfer', account_id='checking',
                                date=datetime.datetime(2022, 2, 11, 0, 0), amount=-250.0, name='Savings'),
                    Transaction(transaction_id='bi_weekly_transfer', account_id='savings',
                                date=datetime.datetime(2022, 2, 11, 0, 0), amount=250.0, name='Savings'),
                    Transaction(transaction_id='bi_weekly_transfer', account_id='checking',
                                date=datetime.datetime(2022, 2, 25, 0, 0), amount=-250.0, name='Savings'),
                    Transaction(transaction_id='bi_weekly_transfer', account_id='savings',
                                date=datetime.datetime(2022, 2, 25, 0, 0), amount=250.0, name='Savings'),
                    Transaction(transaction_id='bi_weekly_transfer', account_id='checking',
                                date=datetime.datetime(2022, 3, 11, 0, 0), amount=-250.0, name='Savings'),
                    Transaction(transaction_id='bi_weekly_transfer', account_id='savings',
                                date=datetime.datetime(2022, 3, 11, 0, 0), amount=250.0, name='Savings'),
                    Transaction(transaction_id='bi_weekly_transfer', account_id='checking',
                                date=datetime.datetime(2022, 3, 25, 0, 0), amount=-250.0, name='Savings'),
                    Transaction(transaction_id='bi_weekly_transfer', account_id='savings',
                                date=datetime.datetime(2022, 3, 25, 0, 0), amount=250.0, name='Savings'),
                    Transaction(transaction_id='bi_weekly_transfer', account_id='checking',
                                date=datetime.datetime(2022, 4, 8, 0, 0), amount=-250.0, name='Savings'),
                    Transaction(transaction_id='bi_weekly_transfer', account_id='savings',
                                date=datetime.datetime(2022, 4, 8, 0, 0), amount=250.0, name='Savings'),
                    Transaction(transaction_id='bi_weekly_transfer', account_id='checking',
                                date=datetime.datetime(2022, 4, 22, 0, 0), amount=-250.0, name='Savings'),
                    Transaction(transaction_id='bi_weekly_transfer', account_id='savings',
                                date=datetime.datetime(2022, 4, 22, 0, 0), amount=250.0, name='Savings'),
                    Transaction(transaction_id='bi_weekly_transfer', account_id='checking',
                                date=datetime.datetime(2022, 5, 6, 0, 0), amount=-250.0, name='Savings'),
                    Transaction(transaction_id='bi_weekly_transfer', account_id='savings',
                                date=datetime.datetime(2022, 5, 6, 0, 0), amount=250.0, name='Savings'),
                    Transaction(transaction_id='bi_weekly_transfer', account_id='checking',
                                date=datetime.datetime(2022, 5, 20, 0, 0), amount=-250.0, name='Savings'),
                    Transaction(transaction_id='bi_weekly_transfer', account_id='savings',
                                date=datetime.datetime(2022, 5, 20, 0, 0), amount=250.0, name='Savings'),
                    Transaction(transaction_id='bi_weekly_transfer', account_id='checking',
                                date=datetime.datetime(2022, 6, 3, 0, 0), amount=-250.0, name='Savings'),
                    Transaction(transaction_id='bi_weekly_transfer', account_id='savings',
                                date=datetime.datetime(2022, 6, 3, 0, 0), amount=250.0, name='Savings'),
                    Transaction(transaction_id='bi_weekly_transfer', account_id='checking',
                                date=datetime.datetime(2022, 6, 17, 0, 0), amount=-250.0, name='Savings'),
                    Transaction(transaction_id='bi_weekly_transfer', account_id='savings',
                                date=datetime.datetime(2022, 6, 17, 0, 0), amount=250.0, name='Savings')
                ]
        ),
        (
                "one_time_credit",
                {
                    'account_id': 'checking',
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
                    Transaction(transaction_id='one_time_credit', account_id='checking',
                                date=datetime.datetime(2022, 5, 15, 0, 0), amount=500.00, name='Craigslist Sale')
                ]
        ),
        (
                "one_time_debit",
                {
                    'account_id': 'checking',
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
                    Transaction(transaction_id='one_time_debit', account_id='checking',
                                date=datetime.datetime(2022, 5, 15, 0, 0), amount=-1299.99, name='Mountain Bike')
                ]
        )
    ])
    def test_create_transactions(self, test_name, param, expected):
        transfer = None if param['transfer'] is None else Transfer(direction=param['transfer']['direction'],
                                                                   account_id=param['transfer']['account_id'])
        tr = ScheduledTransaction(transaction_id=test_name, account_id=param['account_id'], name=param['name'],
                                  amount=param['amount'],
                                  type=param['type'], date_spec=DateSpec.from_spec(param['date_spec']),
                                  transfer=transfer)
        actual = tr.generate_transactions('2022-01-01', '2022-12-31')
        self.assertEqual(actual, expected)

    def test_get_transactions_data_frame(self):
        spec = FixtureHelper.get_spec_fixture()
        projector = Projector.from_spec(spec, '2022-01-01', '2022-12-31')
        checking_df = projector.get_account('checking').generate_transactions_data_frame()
        taxable_df = projector.get_account('taxable_brokerage').generate_transactions_data_frame()
        # DebugHelper.pprint(checking_df)

        """
        Spot-check some rows
        """
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
