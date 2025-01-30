import unittest
import os
import sys
import time

# Add the project directory to the sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'can_of_proxy'))

# Import the test module
from tests import proxy_data_manager_1, proxy_data_manager_2, proxy_data_manager_3, proxy_data_manager_4, test_file_ops, \
    test_can, test_auto_can


def run_test(test_module, run_times: int):
    total_time = 0
    for _ in range(run_times):
        start_time = time.time()
        suite = unittest.defaultTestLoader.loadTestsFromModule(test_module)
        result = unittest.TextTestRunner().run(suite)
        end_time = time.time()
        total_time += (end_time - start_time)
        if not result.wasSuccessful():
            break
    average_time = total_time / run_times
    return test_module.__name__, average_time


if __name__ == "__main__":
    n = 25
    results = [run_test(test_file_ops, n), run_test(proxy_data_manager_1, n), run_test(proxy_data_manager_2, n),
               run_test(proxy_data_manager_3, n), run_test(proxy_data_manager_4, n), run_test(test_can, n),
               run_test(test_auto_can, n)]
    # checks all main modules and tests them n times
    # Errors can still happen, but it's a good way to check if the code is stable

    for module_name, average_time in results:
        print(f"Average time per run for {module_name}: {average_time:.6f} seconds")
