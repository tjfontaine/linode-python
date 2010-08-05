import api
import unittest
import os
from getpass import getpass

class ApiTest(unittest.TestCase):

    def setUp(self):
        self.linode = api.Api(os.environ['LINODE_API_KEY'])

    def testAvailLinodeplans(self):
        available_plans = self.linode.avail_linodeplans()
        self.assertTrue(isinstance(available_plans, list))

    def testEcho(self):
        test_parameters = {'FOO': 'bar', 'FIZZ': 'buzz'}
        response = self.linode.test_echo(**test_parameters)
        self.assertTrue('FOO' in response)
        self.assertTrue('FIZZ' in response)
        self.assertEqual(test_parameters['FOO'], response['FOO'])
        self.assertEqual(test_parameters['FIZZ'], response['FIZZ'])

if __name__ == "__main__":
    if 'LINODE_API_KEY' not in os.environ:
        os.environ['LINODE_API_KEY'] = getpass('Enter API Key: ')
    unittest.main()
