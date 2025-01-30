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
            return test_module.__name__, None  # Return immediately if a test fails
    average_time = total_time / run_times
    return test_module.__name__, average_time


if __name__ == "__main__":
    n = 25
    test_modules = [test_file_ops, proxy_data_manager_1, proxy_data_manager_2, proxy_data_manager_3,
                    proxy_data_manager_4, test_can, test_auto_can]
    results = []

    for test_module in test_modules:
        module_name, average_time = run_test(test_module, n)
        if average_time is None:
            print(f"Test failed in module: {module_name}")
            break
        results.append((module_name, average_time))

    for module_name, average_time in results:
        print(f"Average time per run for {module_name}: {average_time:.6f} seconds")
