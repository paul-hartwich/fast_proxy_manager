import unittest
import os
import sys

# Add the project directory to the sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'can_of_proxy'))

# Import the test module
from tests import proxy_data_manager_1, proxy_data_manager_2, proxy_data_manager_3, test_file_ops


def run_test(test_module, run_times: int):
    for _ in range(run_times):
        suite = unittest.defaultTestLoader.loadTestsFromModule(test_module)
        result = unittest.TextTestRunner().run(suite)
        if not result.wasSuccessful():
            break


if __name__ == "__main__":
    times_testing = 50
    # checks all main modules and tests them 50 times
    # Errors can still happen, but it's a good way to check if the code is stable
    run_test(test_file_ops, times_testing)

    run_test(proxy_data_manager_1, times_testing)
    run_test(proxy_data_manager_2, times_testing)
    run_test(proxy_data_manager_3, times_testing)
