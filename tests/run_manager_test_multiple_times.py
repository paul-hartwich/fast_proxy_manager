import unittest
import os
import sys

# Add the project directory to the sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'can_of_proxy'))

# Import the test module
from tests import proxy_data_manager_1, proxy_data_manager_2

if __name__ == "__main__":  # fast test to check if big problems exist, it does not cover all cases
    for _ in range(500):
        suite = unittest.defaultTestLoader.loadTestsFromModule(proxy_data_manager_1)
        result = unittest.TextTestRunner().run(suite)
        if not result.wasSuccessful():
            break

    for _ in range(500):
        suite = unittest.defaultTestLoader.loadTestsFromModule(proxy_data_manager_2)
        result = unittest.TextTestRunner().run(suite)
        if not result.wasSuccessful():
            break
