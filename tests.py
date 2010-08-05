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

if __name__ == "__main__":
    if 'LINODE_API_KEY' not in os.environ:
        os.environ['LINODE_API_KEY'] = getpass('Enter API Key: ')
    unittest.main()
