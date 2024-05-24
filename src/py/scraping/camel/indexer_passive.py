import os
import sys
import json
import time
import random
from urllib.parse import quote
from datetime import datetime
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from seleniumwire.request import Request, Response
from seleniumwire.webdriver import Remote as TypeWebDriver

# NOTE: it's useful to open the CamelCamelCamel website in a browser and make a manual search if you're being rate limited
#       this will allow you to solve the captcha and continue the scraping - rate limit detection is also implemented but will halt the scraping

load_dotenv()

# Project imports
sys.path.append(os.getcwd())
from src.py.utils.scraping.selenium_utils import init_driver, get_element_by, get_options_firefox, type_text, get_element_by_race, install_ublockorigin_firefox
from src.py.utils.logger import Logger

# Constants
output_path_root = "data/scraped/camel/search"
filepath_product_list = "data/scraped/pangoly/product_list.txt"
domain = "camelcamelcamel.com"
WEBDRIVER_BROWSER = os.getenv("WEBDRIVER_BROWSER")
logger = Logger({"typeinit": True})
driver: TypeWebDriver = None  # type: ignore
LOCATOR_COOKIES = (By.CSS_SELECTOR, ".css-47sehv")
LOCATOR_SEARCH_BAR = (By.CSS_SELECTOR, "#sq")
LOCATOR_SEARCH_RESULTS = (By.CSS_SELECTOR,
                          "#content > div.grid-x.grid-margin-x.search_results")
LOCATOR_INCLUDE_NOT_IN_STOCK = (By.CSS_SELECTOR,
                                "#content > form:nth-child(9) > input.button")
LOCATOR_HIGH_VOLUME_OF_SEARCHES = (By.CSS_SELECTOR, ".alert-callout-border")
LOCATOR_SINGLE_PRODUCT = (
    By.CSS_SELECTOR,
    "div.grid-x:nth-child(12) > div:nth-child(1) > h3:nth-child(1) > a:nth-child(1)"
)  # when a product search returns a single product page directly
LOCATOR_CLOUFLARE_CHALLENGE = (By.CSS_SELECTOR, "#challenge-running"
                              )  # id="challenge-running"
is_waiting_for_response = False
blocked_domains = [
    # Main page
    "https://m.media-amazon.com",
    # "https://assets.camelcamelcamel.com", # need this for app.js...
    "https://assets.camelcamelcamel.com/live-assets/favicon",
    "https://camelcamelcamel.com/afm.js",
    "https://cmp.inmobi.com",
    "https://camelcamelcamel.com/camelfarm",
    "doubleclick.net",
    "amazon-adsystem.com",
    "lijit.com",
    "cdn.adfirst.media",
    # Additional on product page
    "cmp.quantcast.com",
]


def ask_to_continue(default: bool = False):
	'''
	Asks the user if they want to resume the scraping
	'''
	global is_waiting_for_response
	resume_query = "y/N"
	if default:
		resume_query = "Y/n"
	is_waiting_for_response = True
	can_resume = input(f"Do you want to resume the scraping? ({resume_query}): ")
	is_waiting_for_response = False
	if can_resume.lower() == "y":
		return True
	elif can_resume.lower() == "n":
		return False
	else:
		return default


def wait_n_seconds(n: float):
	'''
	Waits for x seconds
	'''
	logger.info(f"Waiting for {n} seconds...")
	is_waiting_for_response = True
	time.sleep(n)
	is_waiting_for_response = False


def request_interceptor(request: Request):
	'''
	Intercepts the request and modifies it.
	'''
	# if "price-chart" in str(request.url):
	# 	request.url = str(request.url).replace("range=90", "range=7300")
	# if "trend-history" in str(request.url):
	# 	pass
	# 	# request.url = str(request.url).replace("range=90", "range=7300")
	a = 0
	# if "https://m.media-amazon.com" in request.url:
	# 	# logger.info(f"Blocking Amazon request: {request.url}")
	# 	request.abort()
	for domain in blocked_domains:
		if domain in request.url:
			# logger.info(f"Blocking domain request: {request.url}")
			request.abort()
	# block requests that have images
	content_type = request.headers.get("Content-Type")
	# print(content_type)
	if content_type:
		if "image" in content_type or "audio" in content_type or "video" in content_type:
			# logger.info(f"Blocking image request: {request.url}")
			request.abort()


def response_interceptor(request: Request, response: Response):
	'''
	Intercepts the response and modifies it.
	'''
	# if response.status_code == 429:
	# 	logger.warning(
	# 	    f"\nWARNING!!! Rate limited (status code 429)! Confirm/wait to continue..."
	# 	)
	# 	# save the data
	# 	# can_continue = ask_to_continue(True)
	# 	wait_n_seconds(random.uniform(60, 120))
	if domain not in str(request.url):
		return
	if response.status_code == 429:
		logger.warning(
		    f"\nWARNING!!! Rate limited (status code 429)! Confirm/wait to continue..."
		)
		logger.info(f"Request URL: {request.url}")
		# save the data
		# can_continue = ask_to_continue(True)
		wait_n_seconds(random.uniform(10, 20))
		return
	# if response.status_code != 200:
	# 	logger.warning(f"\nResponse status code: {response.status_code}")
	# 	# can_continue = ask_to_continue(True)


def init_driver_local():
	'''
	Initializes the driver
	'''
	global driver
	# Init driver
	logger.say(f"Initializing driver ({WEBDRIVER_BROWSER})...")
	options = get_options_firefox()
	options.headless = False
	driver = init_driver(WEBDRIVER_BROWSER, options)  # type: ignore
	driver.request_interceptor = request_interceptor
	driver.response_interceptor = response_interceptor


def init_logger():
	'''
	Initializes the logger
	'''
	global logger
	logger = Logger({
	    "filepath": os.path.join(*["logs", "camel", "indexer_passive.log"]),
	    "level": "DEBUG",
	})


def save_page_to_file(product_name: str, page_source: str):
	'''
	Saves the page to a file
	'''
	output_path = os.path.join(*[output_path_root, f"{product_name}.html"])
	logger.say(f"Saving page to file '{output_path}'...")
	with open(output_path, "w") as f:
		f.write(page_source)
	logger.say(f"Saved page")


def type_search_bar(product_name: str):
	logger.info("Typing in search bar...")
	# Sanitize product name
	product_name = product_name.strip().replace("-", " ")
	# Search for product
	# click on search bar
	search_bar, search_bar_err = get_element_by(
	    driver=driver,  # type: ignore
	    locator=LOCATOR_SEARCH_BAR,
	    timeout=10.0,
	    poll_frequency=0.1,
	    retries=0)
	if search_bar_err:
		logger.error(f"Error: {search_bar_err}")
	assert search_bar
	search_bar.click()
	# click ctrl + a
	search_bar.send_keys(Keys.CONTROL, "a")
	# click backspace
	search_bar.send_keys(Keys.BACKSPACE)
	# type product name
	search_type_text_err = type_text(search_bar, product_name, 0.0446, 0.118)
	if search_type_text_err:
		logger.error(f"Error: {search_type_text_err}")
	# search
	logger.info("Searching...")
	search_bar.send_keys(Keys.ENTER)
	search_bar.send_keys(Keys.ENTER)


def try_getting_results(retries: int = 2):
	'''
		Function for controlling the driver and returning when the results are ready
		or when there is a block
	'''
	logger.info("Trying to get results...")
	race_locators = [
	    LOCATOR_SEARCH_RESULTS, LOCATOR_HIGH_VOLUME_OF_SEARCHES,
	    LOCATOR_INCLUDE_NOT_IN_STOCK, LOCATOR_SINGLE_PRODUCT,
	    LOCATOR_CLOUFLARE_CHALLENGE
	]
	race_result, race_result_err = get_element_by_race(
	    driver=driver,  # type: ignore
	    locators=race_locators,
	    timeout=10.0,
	    poll_frequency=0.01,
	    retries=0)
	if race_result_err:
		logger.error(f"Something unexpected happened - no elements returned!")
		can_continue = ask_to_continue(True)
		if not can_continue:
			logger.warning("Chose to stop the scraping!")
			raise Exception("Chose to stop the scraping!")
		return
	assert race_result
	race_element, race_index = race_result
	if race_index == 0:  # got search results
		logger.info(f"Got search results!")
		return  # we can save the page without any issues
	elif race_index == 2:  # try clicking not in stock products
		logger.info(f"Got not in stock page!")
		# only do at max 1 retry
		if retries > 1:
			retries = 1
		if retries == 1:
			# try clicking the button after a short delay
			time.sleep(random.uniform(0.124, 0.359))
			race_element.click()
			logger.info(f"Retrying to get results 1 time...")
			try_getting_results(retries=0)
		return
	elif race_index == 1:  # got high volume of searches
		logger.warning(f"Got WARNING!!! High volume of searches!")
		# can_continue = ask_to_continue(True)
		logger.info(f"Retries left: {retries}")
		if retries > 0:
			sleep_time = random.uniform(10, 20)
			logger.info(f"Sleeping for {sleep_time} seconds...")
			time.sleep(sleep_time)
			logger.info(f"Refreshing the page to see if we get the results...")
			driver.refresh()
			try_getting_results(retries - 1)
		return
	elif race_index == 3:  # was redirected to product page directly - single result
		logger.info(f"Got a single result!")
		return
	elif race_index == 4:  # got cloudflare challenge
		logger.warning(
		    f"WARNING!!! Cloudflare challenge! NEED TO SOLVE IT! - try to see if you get results manually before continuing!"
		)
		can_continue = ask_to_continue(True)
		return
	else:  # impossible
		pass


def search_product(product_name: str):
	'''
	Searches for a product
	'''
	type_search_bar(product_name)
	time.sleep(random.uniform(0.124, 0.359))
	try_getting_results()


def wait_indefinitely():
	while True:
		time.sleep(0.05)


def init():
	init_logger()
	init_driver_local()


def navigate_to_main_page():
	logger.info("Navigating to main page...")
	driver.get("https://camelcamelcamel.com")


def accept_cookies():
	# Wait for cookies
	logger.info("Waiting for cookies...")
	cookies_button, cookies_button_err = get_element_by(
	    driver=driver,  # type: ignore
	    locator=LOCATOR_COOKIES,
	    timeout=5.0,
	    poll_frequency=0.1,
	    retries=0)
	if cookies_button_err:
		logger.error(f"Error: {cookies_button_err}")
	else:
		assert cookies_button
		cookies_button.click()
		logger.info("Accepted cookies!")


def load_product_list() -> list:
	'''
	Loads the product list
	'''
	if not os.path.exists(filepath_product_list):
		logger.error(f"File '{filepath_product_list}' does not exist!")
		raise Exception(f"File '{filepath_product_list}' does not exist!")
	products = []
	with open(filepath_product_list, "r") as f:
		products = f.read()
	# split by newline
	products = products.split("\n")
	# remove empty strings
	products = list(filter(lambda x: x != "", products))
	return products


def search_products():
	# products = ["Razer Viper Ultimate", "razer deathadder", "nvidia rtx 3080"]
	logger.info("Loading product list...")
	products = load_product_list()
	logger.info(f"Loaded {len(products)} products!")
	for i, product_title in enumerate(products):
		time_start = time.time()
		logger.info(
		    f"Searching for product {i + 1}/{len(products)}: {product_title}")
		while is_waiting_for_response:
			time.sleep(0.1)
		try:
			product_path = os.path.join(*[output_path_root, f"{product_title}.html"])
			if os.path.exists(product_path):
				logger.info(f"Product '{product_title}' already exists! Skipping...")
				continue
			logger.info(f"Resetting the page to home")
			driver.get(
			    "https://camelcamelcamel.com"
			)  # reset the page to reduce the chance of getting stale elements
			search_product(product_title)
			page_source = driver.page_source
			save_page_to_file(product_title, page_source)
			time_to_sleep = random.uniform(1.234 * 1, 2.234 * 1)
			logger.info(f"Sleeping for {time_to_sleep} seconds...")
			time.sleep(time_to_sleep)
		except Exception as e:
			logger.error(f"Error searching for product: {e}")
			if "context has been discarded" in str(e):
				logger.warning("Context has been discarded!")
				# set new context in tab 0
				driver.switch_to.window(driver.window_handles[0])
				# refresh the page
				driver.refresh()
			can_continue = ask_to_continue(True)
			if not can_continue:
				logger.warning("Chose to stop the scraping!")
				break
		time_end = time.time()
		time_elapsed = time_end - time_start
		logger.info(
		    f"Iteration {i + 1}/{len(products)} took {time_elapsed} seconds")
		logger.info("")


def get_ublock_origin():
	# driver.get("https://addons.mozilla.org/en-US/firefox/addon/ublock-origin/")
	logger.info("Installing uBlock Origin...")
	install_ublockorigin_firefox(driver)  # type: ignore
	logger.info("Installed uBlock Origin...")
	# logger.info("Press continue when ready...")
	# can_continue = ask_to_continue(True)


def main():
	if not os.path.exists(output_path_root):
		os.makedirs(output_path_root)
	init()
	get_ublock_origin()
	navigate_to_main_page()
	accept_cookies()
	search_products()


def turn_off_driver():
	'''
	Turns off the driver
	'''
	global driver
	driver.close()


if __name__ == "__main__":
	main()
	# wait_indefinitely()  # for debug
	turn_off_driver()
	logger.say("Done!")
