import unittest
import os
import sys

# Add the project directory to the sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'can_of_proxy'))

# Import the test module
from tests import test_proxy_data_manager

if __name__ == "__main__":  # fast test to check if big problems exist, it does not cover all cases
    for _ in range(500):
        suite = unittest.defaultTestLoader.loadTestsFromModule(test_proxy_data_manager)
        result = unittest.TextTestRunner().run(suite)
        if not result.wasSuccessful():
            break
