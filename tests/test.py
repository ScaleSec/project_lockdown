# -*- coding: utf-8 -*-

import unittest


class ExampleTestCases(unittest.TestCase):
    """test case"""

    def test_check_test(self):
        self.assertTrue(True)
    
if __name__ == '__main__':
    unittest.main()