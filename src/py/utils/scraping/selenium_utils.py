import os
import time
import requests
import platform
import random
from typing import Optional, Tuple, Union
from dotenv import load_dotenv
# Selenium
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
# from selenium.webdriver import ChromeOptions, FirefoxOptions, Chrome, Firefox, FirefoxProfile, DesiredCapabilities
from selenium.webdriver import ChromeOptions, FirefoxOptions, Chrome, FirefoxProfile, DesiredCapabilities
from seleniumwire.webdriver import Firefox
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.common.exceptions import TimeoutException

# Load environment variables
load_dotenv()

BROWSERS = {
    "chrome": Chrome,
    "firefox": Firefox,
}

DEFAULT_BROWSER = "firefox"

DRIVER_SERVICE_LOG_PATH = "logs"

ublock_origin_url_firefox = "https://addons.mozilla.org/firefox/downloads/file/4188488/ublock_origin-1.53.0.xpi"
extension_path = "~/Downloads/ublock_origin-1.53.0.xpi"
extension_path = os.path.expanduser(extension_path)


def add_generic_options(options: Union[ChromeOptions, FirefoxOptions]) -> None:
	"""Add the generic options to the browser."""
	# options.add_argument("--headless")
	options.add_argument("--disable-gpu")
	# options.add_argument("--incognito")
	options.add_argument("--disable-infobars")
	options.add_argument("--disable-blink-features=AutomationControlled")
	options.add_argument("--disable-extensions")


def get_options_chrome() -> ChromeOptions:
	"""Get the Chrome options."""
	options = ChromeOptions()
	# Add generic options
	add_generic_options(options)
	# Add Chrome specific options
	# TODO: Add Chrome specific options
	return options


def get_options_firefox() -> FirefoxOptions:
	"""Get the Firefox options."""
	options = FirefoxOptions()
	# Add generic options
	add_generic_options(options)
	# Add Firefox specific options
	# TODO: Add Firefox specific options
	return options


def init_driver_chrome(options: Optional[ChromeOptions] = None,
                       proxy: Optional[str] = None) -> Chrome:
	"""Initialize the Selenium driver."""
	if options is None:
		options = get_options_chrome()
	if proxy is not None:
		options.add_argument(f"--proxy-server={proxy}")
	driver = Chrome(options=options)
	return driver


def init_driver_firefox(options: Optional[FirefoxOptions] = None,
                        proxy: Optional[str] = None,
                        profile: Optional[FirefoxProfile] = None) -> Firefox:
	"""Initialize the Selenium driver."""
	if options is None:
		options = get_options_firefox()
	if profile is None:
		profile = FirefoxProfile()
	firefox_bin_path = os.getenv("FIREFOX_BIN_PATH")
	if firefox_bin_path is None:
		# Try and find the binary based on OS
		os_name = platform.system()
		if os_name == "Linux":
			firefox_bin_path = "/usr/bin/firefox"
	driver_bin_path = os.getenv("GECKODRIVER_BIN_PATH")
	if driver_bin_path is None:
		# Try and find the binary based on OS
		os_name = platform.system()
		if os_name == "Linux":
			driver_bin_path = "/usr/local/bin/geckodriver"
	log_path = os.path.join(DRIVER_SERVICE_LOG_PATH, "geckodriver.log")
	assert driver_bin_path is not None
	service = FirefoxService(driver_bin_path, log_path=log_path)
	assert firefox_bin_path is not None
	# Create profile
	# profile = FirefoxProfile()
	# Additional options
	options.binary_location = firefox_bin_path
	# Create capabilities
	capabilities = options.to_capabilities()
	# if proxy is not None:
	# 	firefox_proxy = {
	# 	    "proxyType": "MANUAL",
	# 	    "httpProxy": proxy,
	# 	    "sslProxy": proxy,
	# 	    "noProxy": []
	# 	}
	# 	capabilities["proxy"] = firefox_proxy
	# profile = FirefoxProfile()
	# profile.set_preference("dom.webdriver.enabled", False)
	# profile.set_preference('useAutomationExtension', False)
	# profile.update_preferences()
	# capabilities = DesiredCapabilities.FIREFOX
	# driver = Firefox(options=options, service=service, capabilities=capabilities)
	options.profile = profile
	driver = Firefox(options=options, service=service)
	return driver


def init_driver(
    browser_name: Optional[str] = None,
    options: Optional[Union[ChromeOptions, FirefoxOptions]] = None,
    proxy: Optional[str] = None,
    profile: Optional[FirefoxProfile] = None) -> Union[Chrome, Firefox]:
	"""Initialize the Selenium driver."""

	if browser_name is None:
		browser_name = DEFAULT_BROWSER
	if browser_name not in BROWSERS.keys():
		raise ValueError(
		    f"Browser name {browser_name} does not exist. Must be one of {BROWSERS.keys()}"
		)
	if browser_name == "chrome":
		return init_driver_chrome(options=options, proxy=proxy)  # type: ignore
	elif browser_name == "firefox":
		return init_driver_firefox(options=options, proxy=proxy,
		                           profile=profile)  # type: ignore
	else:
		raise ValueError(f"This option is not yet supported: {browser_name}")


def test_init_driver():
	"""Test the init_driver function."""
	driver = init_driver()
	driver.get("https://www.google.com")
	print(f"Title: {driver.title}")
	driver.close()


def get_element_by(
    driver: Union[Chrome, Firefox],
    locator: tuple,
    timeout: float = 5.0,
    poll_frequency: float = 0.01,
    retries: int = 0,
) -> Union[Tuple[WebElement, None], Tuple[None, Exception]]:
	"""Returns a list of elements that match the locator."""
	for i in range(retries + 1):
		try:
			elements = WebDriverWait(
			    driver, timeout, poll_frequency=poll_frequency).until(
			        # EC.visibility_of_element_located(locator))  # type: WebElement
			        EC.presence_of_element_located(locator))
			return elements, None
		except Exception as e:
			# print(f"Error: {e}")
			if i == retries:
				return None, e
	return None, TimeoutException(
	    f"Could not find element with locator: '{locator}'")


def get_element_by_race(
    driver: Chrome | Firefox,
    locators: list[tuple],
    timeout: float = 5.0,
    poll_frequency: float = 0.01,
    retries: int = 0,
) -> Tuple[Tuple[WebElement, int], None] | Tuple[None, Exception]:
	"""Returns a list of elements that match the locator."""
	for retry in range(retries + 1):
		time_start = time.time()
		while time.time() - time_start < timeout:
			for i in range(len(locators)):
				try:
					result, err = get_element_by(driver=driver,
					                             locator=locators[i],
					                             timeout=poll_frequency,
					                             poll_frequency=poll_frequency,
					                             retries=0)
					if result:
						return (result, i), None
				except Exception as e:
					# print(f"Error: {e}")
					pass
	return None, TimeoutException(
	    f"Could not find element with locator: '{locators}'")


def type_text(element: WebElement,
              text: str,
              wait_min: float = 0.067,
              wait_max: float = 0.238) -> Optional[str]:
	"""Types the text into the element."""
	try:
		for char in text:
			element.send_keys(char)
			random_time = random.uniform(wait_min, wait_max)
			time.sleep(random_time)
		return None
	except Exception as e:
		return str(e)


def test_get_element():
	"""Test the get_element function."""
	a = init_driver()
	a.get("https://www.google.com")
	print(f"Title: {a.title}")
	# Try by using CSS_SELECTOR
	GOOGLE_IMG = (
	    By.CSS_SELECTOR,
	    "body > div.L3eUgb > div.o3j99.LLD4me.yr19Zb.LS8OJ > div > img")
	el, err = get_element_by(a, GOOGLE_IMG, timeout=5.0, poll_frequency=0.1)
	if err:
		print(f"Error: {err}")
	else:
		assert el
		print(f"Img src (CSS_SELECTOR): {el.get_attribute('src')}")
	# Try by using XPATH
	GOOGLE_IMG = (By.XPATH, "/html/body/div[1]/div[2]/div/img")
	el, err = get_element_by(a, GOOGLE_IMG, timeout=5.0, poll_frequency=0.1)
	if err:
		print(f"Error: {err}")
	else:
		assert el
		print(f"Img src (XPATH): {el.get_attribute('src')}")
	a.close()


def test_selemiumwire_requests():
	driver = init_driver_firefox()
	driver.get("https://www.google.com")
	print(f"Title: {driver.title}")
	requests = driver.requests
	for request in requests:
		if request.response:
			print(request.url, request.response.status_code,
			      request.response.headers['Content-Type'])
	# Clear requests
	del driver.requests
	driver.close()


def test_request_interceptor(request):
	"""Test the request interceptor."""
	print(f"Request: {request.url}")


def test_response_interceptor(request, response):
	"""Test the response interceptor."""
	print(f"Response: {response.status_code}")


def test_seleniumwire_interceptors():
	driver = init_driver_firefox()
	driver.request_interceptor = test_request_interceptor
	driver.response_interceptor = test_response_interceptor
	driver.get("https://www.google.com")
	print(f"Title: {driver.title}")
	# Example clearing interceptors
	del driver.request_interceptor
	del driver.response_interceptor
	driver.close()


def download_ublockorigin_firefox() -> None:
	"""
		Downloads uBlock Origin on Firefox.
	"""
	if not os.path.exists(extension_path):
		print("Downloading uBlock Origin")
		response = requests.get(ublock_origin_url_firefox)
		print("Downloaded uBlock Origin")
		with open(extension_path, "wb") as f:
			print(f"Writing uBlock Origin to {extension_path}")
			f.write(response.content)
			print("Done writing uBlock Origin")


def install_ublockorigin_firefox(driver: Firefox) -> None:
	"""
		Installs uBlock Origin on Firefox.
	"""
	download_ublockorigin_firefox()
	print("Installing uBlock Origin")
	driver.install_addon(extension_path, temporary=True)
	print("Installed uBlock Origin")


if __name__ == "__main__":
	# print("test_init_driver")
	# test_init_driver()
	print("test_get_element")
	test_get_element()
	# print("test_selemiumwire_requests")
	# test_selemiumwire_requests()
	# print("test_seleniumwire_interceptors")
	# test_seleniumwire_interceptors()
	print("ALL DONE")
