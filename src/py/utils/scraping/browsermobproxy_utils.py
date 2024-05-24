import os
import sys
from typing import Optional
from browsermobproxy import Server
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.getcwd())
from src.py.utils.scraping.selenium_utils import init_driver

BROWSERMOBPROXY_BIN_PATH = os.getenv("BROWSERMOBPROXY_BIN_PATH")
WEBDRIVER_BROWSER = os.getenv("WEBDRIVER_BROWSER")
assert BROWSERMOBPROXY_BIN_PATH is not None


def init_server(executable_path: Optional[str] = None,
                options: Optional[dict] = None) -> Server:
	"""Starts the browsermob proxy server.

		Args:
				executable_path: The path to the browsermob-proxy executable.
				options: The options to pass to the server.

		Returns:
				The server object.
		"""
	# TODO use envs as default fallback for ports
	if options is None:
		options = {}
	if "port" not in options:
		options["port"] = 20123
	# if "log_path" not in options:
	if "existing_proxy_port_to_use" not in options:
		options["existing_proxy_port_to_use"] = 21123
	server = Server(BROWSERMOBPROXY_BIN_PATH)
	server.start()
	return server


def test_init_server():
	server = init_server()
	proxy = server.create_proxy()
	driver = init_driver(WEBDRIVER_BROWSER, proxy=proxy.proxy)
	hmm = proxy.new_har('some_key_for_pageref',
	                    options={
	                        'captureHeaders': True,
	                        'captureContent': True
	                    })
	driver.get("https://www.youtube.com/")
	import time
	time.sleep(5)
	har = proxy.har
	har_data = har['log']['entries']
	server.stop()
	driver.quit()


# test_init_server()