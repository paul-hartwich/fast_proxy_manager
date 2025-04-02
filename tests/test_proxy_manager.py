import unittest
import logging
import functools
from functools import partial
from ineedproxy import Manager, Fetch, ProxyDict

times_tested = 1


def repeat_test(times):
    def decorator(test_method):
        @functools.wraps(test_method)
        async def wrapper(self, *args, **kwargs):
            for i in range(times):
                try:
                    await test_method(self, *args, **kwargs)
                    await self.asyncTearDown()  # Clean up after each iteration
                    await self.asyncSetUp()  # Set up for next iteration
                except Exception as e:
                    raise AssertionError(f"Failed on iteration {i + 1}/{times}: {str(e)}")

        return wrapper

    return decorator


logging.getLogger("fast_proxy_manager").setLevel(logging.INFO)


class TestProxyManager(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        """Set up a fresh ProxyManager before each test."""
        proxy_url = "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=json"
        self.manager = await Manager(fetching_method=[partial(Fetch.custom, proxy_url)], data_file=None,
                                     auto_fetch_proxies=False)

        test_data = [
            ProxyDict(url="http://123.123.123.123:1", country="US", anonymity="elite"),
            ProxyDict(url="http://123.123.123.123:2", country="US", anonymity="elite"),
            ProxyDict(url="http://123.123.123.123:3", country="US", anonymity="elite"),
            ProxyDict(url="http://123.123.123.123:3", country="US", anonymity="elite"),
            ProxyDict(url="http://123.123.123.123:4", country="US", anonymity="transparent"),
        ]
        self.manager.data_manager.add_proxy(test_data, remove_duplicates=True)
        self.assertEqual(len(self.manager), 4)

    async def asyncTearDown(self):
        self.manager.data_manager.rm_all_proxies()

    @repeat_test(times=times_tested)
    async def test_fetch_proxies(self):
        await self.manager.fetch_proxies(test_proxies=False)
        self.assertGreater(len(self.manager.data_manager), 4)

    @repeat_test(times=times_tested)
    async def test_proxy_removal(self):
        self.manager.data_manager.rm_proxy(0)
        self.assertEqual(len(self.manager), 3)
        self.assertEqual(self.manager.data_manager.proxies[0]["url"], "http://123.123.123.123:2")

    @repeat_test(times=times_tested)
    async def test_fails_in_row_rm(self):
        # Set properties on the Manager instance
        self.manager.data_manager.allowed_fails_in_row = 3
        self.manager.data_manager.fails_without_check = 100

        self.assertEqual(len(self.manager), 4)

        # Store proxy URL and initial proxies
        proxy_url = await self.manager.get_proxy()
        initial_proxies = [p['url'] for p in self.manager.data_manager.proxies]

        # Check consecutive failures
        self.manager.feedback_proxy(success=False)
        self.assertEqual(len(self.manager), 4)
        self.manager.feedback_proxy(success=False)
        self.assertEqual(len(self.manager), 4)
        self.manager.feedback_proxy(success=False)
        self.assertEqual(len(self.manager), 4)
        self.manager.feedback_proxy(success=False)
        self.assertEqual(len(self.manager), 3)

        # Verify the failed proxy was removed
        current_proxies = [p['url'] for p in self.manager.data_manager.proxies]
        self.assertNotIn(proxy_url, current_proxies,
                         "Failed proxy should have been removed")

        # Verify other proxies remain
        remaining_count = 0
        for url in initial_proxies:
            if url != proxy_url:
                self.assertIn(url, current_proxies,
                              f"Proxy {url} should still be present")
                remaining_count += 1
        self.assertEqual(remaining_count, 3)

    @repeat_test(times=times_tested)
    async def test_fail_ratio_rm1(self):
        self.manager.data_manager.allowed_fails_in_row = 100
        self.manager.data_manager.fails_without_check = 2
        self.manager.data_manager.percent_failed_to_remove = 0.5

        initial_proxies = self.manager.data_manager.proxies.copy()
        first_proxy_url = await self.manager.get_proxy()

        for _ in range(2):
            self.manager.feedback_proxy(success=False)
            self.assertEqual(len(self.manager), 4)

        self.manager.feedback_proxy(success=False)
        self.assertEqual(len(self.manager), 3)

        remaining_proxies = self.manager.data_manager.proxies
        self.assertNotIn(first_proxy_url, [p['url'] for p in remaining_proxies])

    @repeat_test(times=times_tested)
    async def test_fail_ratio_rm2(self):
        self.manager.data_manager.allowed_fails_in_row = 100
        self.manager.data_manager.fails_without_check = 2
        self.manager.data_manager.percent_failed_to_remove = 0.5

        initial_proxies = self.manager.data_manager.proxies.copy()
        first_proxy_url = await self.manager.get_proxy()

        for _ in range(4):
            self.manager.feedback_proxy(success=True)
        self.assertEqual(len(self.manager), 4)

        # Add failures until ratio triggers removal
        for i in range(5):
            self.manager.feedback_proxy(success=False)
            if i < 4:
                self.assertEqual(len(self.manager), 4)
            else:
                self.assertEqual(len(self.manager), 3)

        # Verify the failed proxy was removed
        remaining_proxies = self.manager.data_manager.proxies
        self.assertNotIn(first_proxy_url, [p['url'] for p in remaining_proxies])

    @repeat_test(times=times_tested)
    async def test_get_proxy(self):
        # Clear and set up initial proxies
        self.manager.data_manager.rm_all_proxies()

        # Add first proxy
        first_proxy = ProxyDict(url="http://123.123.123.123:1", country="US", anonymity="elite")
        self.manager.data_manager.add_proxy([first_proxy])
        self.assertEqual(len(self.manager), 1)

        # Test single proxy behavior
        proxy = await self.manager.get_proxy()
        self.assertEqual(str(proxy), "http://123.123.123.123:1")
        self.assertEqual(self.manager.data_manager.last_proxy_index, 0)

        # Test repeated call with single proxy
        proxy = await self.manager.get_proxy()
        self.assertEqual(str(proxy), "http://123.123.123.123:1")
        self.assertEqual(self.manager.data_manager.last_proxy_index, 0)

        # Add second proxy
        second_proxy = ProxyDict(url="http://123.123.123.123:2", country="US", anonymity="elite")
        self.manager.data_manager.add_proxy([second_proxy])
        self.assertEqual(len(self.manager), 2)

        # Test alternating behavior
        previous_index = self.manager.data_manager.last_proxy_index
        for i in range(10):
            proxy = await self.manager.get_proxy()
            current_index = self.manager.data_manager.last_proxy_index

            # Verify index alternates between 0 and 1
            self.assertNotEqual(current_index, previous_index)
            self.assertTrue(0 <= current_index <= 1)

            # Verify URL matches index
            expected_url = f"http://123.123.123.123:{current_index + 1}"
            self.assertEqual(proxy, expected_url)

            previous_index = current_index


if __name__ == "__main__":
    unittest.main()
