from __future__ import annotations
import os
import sys
import json
import time
import random
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
import brotli
from selenium.webdriver.common.by import By
from seleniumwire.request import Request, Response
from seleniumwire.webdriver import Remote as TypeWebDriver

load_dotenv()

# Project imports
sys.path.append(os.getcwd())
from src.py.utils.scraping.selenium_utils import init_driver, get_element_by
from src.py.utils.logger import Logger

#
##  Constants and globals
#
path_output_root = "data/scraped/pangoly"
WEBDRIVER_BROWSER = os.getenv("WEBDRIVER_BROWSER")
pangoly_base_url = "https://pangoly.com"
total_response_count = 0
time_limit_per_region = 5.0  # seconds (decimal)
all_data = {}  # All the data from the page
driver: TypeWebDriver = None  # type: ignore
product_name = ""
logger = Logger({"typeinit": True})  # placeholder variable for type hinting
DEBUG_MODE = False  # set to true to use a default product name without having to set it from the command line
# Global locators
LOCATOR_COOKIES_ACCEPT_BUTTON = (
    By.CSS_SELECTOR,
    "#qc-cmp2-ui > div.qc-cmp2-footer.qc-cmp2-footer-overlay.qc-cmp2-footer-scrolled > div > button.css-1ga3yq3"
)


def get_product_name() -> str:
	'''
	Reads the product name from the command line.
	'''
	# debug_mode_name = "amd-ryzen-7-2700x"
	# debug_mode_name = "amd-ryzen-5-3600"
	# debug_mode_name = "gigabyte-geforce-rtx-2060-super-gaming-oc-white-8g"
	debug_mode_name = "amd-ryzen-5-7600"
	if DEBUG_MODE:
		return debug_mode_name
	args = sys.argv[1:]
	product_name = ""
	if len(args) > 0:
		# we expect just one argument anyways so this solves the accidental space problem
		product_name = "".join(args)
	else:
		print(f"Usage: python path/to/scraper_worker.py <product_name>")
		print(
		    f"Example: python src/py/scraping/pangoly/scraper_worker.py {debug_mode_name}"
		)
		exit(1)
	return product_name


def save_data():
	logger.say("Saving data")
	final_output_path = os.path.join(
	    path_output_root,
	    "/".join(all_data["pages"]["product"]["hierarchy"][:-1]))
	if not os.path.exists(final_output_path):
		os.makedirs(final_output_path)
	# Save one without indentation
	filename = f"{product_name}.json"
	filepath = os.path.join(final_output_path, filename)
	logger.say(f"Saving to '{filepath}'")
	with open(filepath, "w", encoding="utf-8") as f:
		json.dump(all_data, f)
	logger.say("Done saving data")


def request_interceptor(request: Request):
	'''
	Intercepts the request and modifies it.
	'''
	if "price-chart" in str(request.url):
		request.url = str(request.url).replace("range=90", "range=7300")
	if "trend-history" in str(request.url):
		pass
		# request.url = str(request.url).replace("range=90", "range=7300")


# TODO - Add a generic body resolver to selenium_utils.py
#        (based on header try to decompress/decode body -> base64, gzip, brotli, etc.)
#        ... or get disable_encofing option to work
def response_interceptor(request: Request, response: Response):
	'''
	Intercepts the response and modifies it.
	'''
	# Uncomment prints and add watch expressions to debugger
	# when inspecting requests and responses
	# Debugger watch for inspection:
	# - request.url
	# - response.body
	# - body
	# - body_json
	# - total_response_count
	# global total_response_count
	# total_response_count += 1
	# body = None
	# try:
	# 	body = response.body.decode("utf-8")
	# except Exception as e:
	# 	pass
	# try:
	# 	assert request.response
	# 	body = brotli.decompress(request.response.body).decode("utf-8")
	# except Exception as e:
	# 	pass
	# if body:
	# 	# logger.say(f"Body length: {len(body)}")
	# 	try:
	# 		body_json = json.loads(body)
	# 		# logger.say(f"Body JSON ({request.url}): {body_json}")
	# 	except Exception as e:
	# 		pass

	# Check if we are rate limited (response code 429)
	if response.status_code == 429:
		# logger.say(f"Rate limited! Sleeping for 5 minutes...")
		# time.sleep(300)
		# logger.say(f"Done sleeping, continuing...")
		logger.say(f"Rate limited! Exiting...", level="error")
		# save the data
		save_data()
		exit(202)


def init():
	'''
	Initializes the driver
	'''
	global driver
	# Init driver
	logger.say(f"Initializing driver ({WEBDRIVER_BROWSER})...")
	driver = init_driver(WEBDRIVER_BROWSER)  # type: ignore
	driver.request_interceptor = request_interceptor
	driver.response_interceptor = response_interceptor


def close():
	'''
	Closes the driver
	'''
	global driver
	try:
		driver.quit()
	except Exception as e:
		logger.say(f"Exception while quitting the driver: {e}")


def decompress_brotli(data: bytes) -> str:
	'''
	Decompresses the brotli compressed data.
	'''
	return brotli.decompress(data).decode("utf-8")


# TODO: Make more generic to try to decode/parse the body based on headers
#       and move to utils
def get_body_str_brotli(request: Request) -> Optional[str]:
	'''
	Extracts the body from the request.
	'''
	try:
		if request.response:
			decoded_body = decompress_brotli(request.response.body)
			return decoded_body
	except Exception as e:
		logger.say(f"Exception while parsing body: {e}")
	return None


def get_region_data(region_info) -> dict:
	# TODO add more metadata to the region data
	# mabye request specific to price_chart and trend_history
	# and creation dates and such
	logger.say(f"Getting region data for {region_info['name']}...")
	region_data = {}
	region_data["metadata"] = {
	    "info":
	        region_info,
	    "url":
	        driver.current_url,
	    "created_at":
	        datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S.%f%z")
	}
	extracted_data = {"price_chart": None, "trend_history": None}
	region_data["datapoints"] = extracted_data
	datapoints_needed = len(extracted_data.keys())
	time_start = time.time()
	# loop over driver.requests and check if we have all the data
	# stop when we have all the data or when we reach time_limit_per_region
	logger.say(f"Waiting for {datapoints_needed} datapoints...")
	while datapoints_needed > 0 and time.time(
	) - time_start < time_limit_per_region:
		for request in driver.requests:
			if "price-chart" in str(request.url):
				logger.say(f"Found price-chart request: {request.url}")
				datapoints_needed -= 1
				decoded_body = get_body_str_brotli(request)
				if request.response:
					logger.say(f"Response status code: {request.response.status_code}")
				if decoded_body:
					logger.say(f"Body successfully decoded. Length: {len(decoded_body)}")
					logger.say(f"Loading body as JSON...")
					body_json = json.loads(decoded_body)
					logger.say(f"Body successfully loaded as JSON.")
					# TODO clean up the data
					extracted_data["price_chart"] = {  # type: ignore
					    "created_at":
					        datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S.%f%z"
					                                            ),
					    "data":
					        body_json
					}
			if "trend-history" in str(request.url):
				logger.say(f"Found trend-history request: {request.url}")
				datapoints_needed -= 1
				decoded_body = get_body_str_brotli(request)
				if request.response:
					logger.say(f"Response status code: {request.response.status_code}")
				if decoded_body:
					logger.say(f"Body successfully decoded. Length: {len(decoded_body)}")
					logger.say(f"Loading body as JSON...")
					body_json = json.loads(decoded_body)
					logger.say(f"Body successfully loaded as JSON.")
					LOCATOR_TREND_HISTORY_TITLE = (
					    By.CSS_SELECTOR,
					    "body > div.container > div > div.col-xs-12.col-sm-9.content-wrapper > div.row.wrapper-box > div.col-xxs.col-xs-12 > h3"
					)
					trend_history_title = None
					el_tend_history_title, err = get_element_by(
					    driver, LOCATOR_TREND_HISTORY_TITLE)  # type: ignore
					if err:
						logger.say(f"Error while getting trend history title: {err}",
						           level="error")
					else:
						assert el_tend_history_title
						trend_history_title = el_tend_history_title.get_attribute(
						    "textContent")
						logger.say(f"Got trend history title: {trend_history_title}")
					# try getting the title of the trend graph
					# TODO clean up the data
					extracted_data["trend_history"] = {  # type: ignore
					    "created_at":
					        datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S.%f%z"
					                                            ),
					    "title":
					        trend_history_title,
					    "data":
					        body_json
					}
		time.sleep(0.1)
	logger.say(
	    f"Finished waiting for datapoints. Got {len(extracted_data.keys()) - datapoints_needed}/{len(extracted_data.keys())} datapoints."
	)
	logger.say(f"Done getting region data for {region_info['name']}.")
	# Save page source
	return region_data


# TODO: test no history for ryzen 1700, GB region: https://pangoly.com/en/price-history/amd-ryzen-7-1700x?st=UK
def scrape_page_history(url: str):
	time_start = time.time()
	# Local locators
	LOCATOR_CHANGE_REGION = (
	    By.CSS_SELECTOR,
	    # "body > div.container > div > div.col-xs-12.col-sm-9.content-wrapper > div:nth-child(2) > div.col-md-8.col-xs-12 > div.text-right > a"
	)
	LOCATOR_LIST_GROUP = (
	    By.CSS_SELECTOR,
	    # "#store-dialog > div > div > div.modal-body.modal-regions > div") # This one works if we clicked on (change region) button first
	    "#store-dialog > div > div > div.modal-body.modal-regions > div")
	LOCATOR_CHANGE_REGION_ALT = (
	    By.CSS_SELECTOR,
	    "body > div.container > div > div.col-xs-12.col-sm-9.content-wrapper > div:nth-child(4) > div.col-md-7.col-xs-12.product-info.product-info-2 > div:nth-child(4) > div > div > a"
	)
	# class="cl-effect cl-regions dropdown open"
	LOCATOR_REGIONS_TOPBAR = (By.CLASS_NAME, "cl-regions")

	# DON'T REINIT - messes up the regions
	# Reinstantiate driver
	# init()
	page_history = {}
	all_data["pages"]["history"] = page_history

	# Clear previous requests
	del driver.requests

	# Go to page
	logger.say(f"Going to page: {url}")
	driver.get(url)

	# THIS IS MORE ROBUST NOW BUT STILL NOT PERFECT - using just LOCATOR_LIST_GROUP which is the same for multiple cases
	# # TODO - What to wait for - universally (if trend missing, if history missing, etc.)
	# # Wait for change region button to appear
	# logger.say("Waiting for change region button to appear...")
	# el_change_region, err = get_element_by(
	#     driver,  # type: ignore
	#     LOCATOR_CHANGE_REGION)
	# if err:
	# 	logger.say(f"Error while getting change region button: {err}", level="error")
	# 	el_change_region, err = get_element_by(
	# 	    driver,  # type: ignore
	# 	    LOCATOR_CHANGE_REGION_ALT)
	# 	if err:
	# 		logger.say(
	# 		    f"Error while getting alternative change region button: {err}", level="error")
	# 		return
	# 	return
	# assert el_change_region

	# Get list group of regions
	logger.say("Getting list group of regions...")
	el_list_group, err = get_element_by(
	    driver,  # type: ignore
	    LOCATOR_LIST_GROUP)
	# el_list_group, err = get_element_by(
	#     driver,  # type: ignore
	#     (By.CLASS_NAME, "list-group"))
	if err:
		logger.say(f"Error while getting list group: {err}", level="error")
		return
	assert el_list_group

	# Get all <a> elements in the list group
	logger.say("Getting all <a> elements in the list group...")
	el_list_group_a = el_list_group.find_elements(By.TAG_NAME, "a")
	# Iterate over all <a> elements
	region_links = {}
	page_history["region_links"] = region_links
	# active_key determines which region is active
	# we already have the data for the active region in request
	active_key = ""
	logger.say("Getting region links and currency data...")
	for el_a in el_list_group_a:
		# Get data-store attribute
		data_store = el_a.get_attribute("data-store")
		# Check if it has class "active"
		classes = el_a.get_attribute("class")
		if "active" in classes:
			active_key = data_store
		el_strong = el_a.find_element(By.TAG_NAME, "strong")
		region_name = el_strong.get_attribute("textContent").strip()
		el_em = el_a.find_element(By.TAG_NAME, "em")
		currency_text = el_em.get_attribute("textContent")
		currency_code, currency_symbol = currency_text.split(" ")
		region_links[data_store] = {
		    "name": region_name,
		    "key": data_store,
		    "currency": {
		        "code": currency_code.strip(),
		        "symbol": currency_symbol.strip()
		    }
		}

	# Iterate over all regions
	# TODO: clean up their JSON -> unix float to int, ...
	page_history["regions"] = {}
	logger.say("Getting current page region data...")
	page_history["regions"][active_key] = get_region_data(
	    region_links[active_key])
	save_data()
	logger.say("Getting other regions data...")
	for region_key, region_data in region_links.items():
		time.sleep(random.uniform(0.1, 0.35))
		logger.say(f"Region key: '{region_key}' ({region_data['name']})")
		if region_key == active_key:
			logger.say(f"Skipping active region: '{region_key}'")
			continue
		new_url = f"{url.split('=')[0]}={region_key}"
		logger.say(f"Going to new url: '{new_url}'")
		# Clear requests for new region
		del driver.requests
		# Go to new url
		driver.get(new_url)
		# Wait for change region button to appear
		# el_change_region, err = get_element_by(
		#     driver, LOCATOR_CHANGE_REGION)  # type: ignore
		# if err:
		# 	logger.say(f"Error while getting change region button: {err}", level="error")
		# 	continue
		# assert el_change_region
		# Get region data
		# Wait for LOCATOR_LIST_GROUP
		el_list_group_loop, err = get_element_by(
		    driver,  # type: ignore
		    LOCATOR_LIST_GROUP)
		if err:
			logger.say(f"Error while getting list group: {err}", level="error")
			continue
		assert el_list_group_loop
		region_data = get_region_data(region_data)
		page_history["regions"][region_key] = region_data
		# save_data()
	logger.say(f"Done getting region data in {time.time() - time_start} seconds")


def scrape_page_product(url: str):
	time_start = time.time()
	# Local locators
	LOCATOR_TITLE = (
	    By.CSS_SELECTOR,
	    "body > div.container > div > div.col-xs-12.col-sm-9.content-wrapper > div:nth-child(1) > div > div.col-md-7.col-xs-12.product-info.product-info-2.pull-right > h2"
	)
	LOCATOR_TAIL_LINKS = (
	    By.CSS_SELECTOR,
	    "body > div.container > div > div.col-xs-12.col-sm-9.content-wrapper > div:nth-child(1) > div > div.col-md-5.col-xs-12 > ul"
	)
	LOCALTOR_SPECIFICATIONS_OVERVIEW = (
	    By.CSS_SELECTOR,
	    "body > div.container > div > div.col-xs-12.col-sm-9.content-wrapper > div:nth-child(3) > div > table"
	)
	LOCATOR_HIERARCHY = (
	    By.CSS_SELECTOR,
	    "body > div.container > div > div.col-xs-12.col-sm-9.content-wrapper > div:nth-child(1) > div > ol"
	)
	LOCATOR_REGIONS_DROPDOWN = (
	    By.CSS_SELECTOR,
	    "body > div.pangoly-top > div.navbar.navbar-default.navbar-static-top > div > div.navbar-collapse.collapse > ul > li.cl-effect.cl-regions.dropdown"
	)
	LOCATOR_REGION_DOWNDOWN_GLOBAL_US = (
	    By.CSS_SELECTOR,
	    "body > div.pangoly-top > div.navbar.navbar-default.navbar-static-top > div > div.navbar-collapse.collapse > ul > li.cl-effect.cl-regions.dropdown.open > ul > li:nth-child(1) > a"
	)
	# Reinitialize driver
	init()
	# Accept cookies and choose default active region (US (global))
	driver.get(pangoly_base_url)
	# Get Cookies accept button
	logger.say("Waiting for cookies accept button")
	el_cookies_accept, err = get_element_by(
	    driver, LOCATOR_COOKIES_ACCEPT_BUTTON)  # type: ignore
	if err:
		logger.say(f"Error while waiting for cookies accept button: {err}",
		           level="error")
	else:
		assert el_cookies_accept
		el_cookies_accept.click()
	# Select US (global) region
	logger.say("Waiting for regions dropdown")
	el_regions_dropdown, err = get_element_by(
	    driver, LOCATOR_REGIONS_DROPDOWN)  # type: ignore
	if err:
		logger.say(f"Error while waiting for regions dropdown: {err}",
		           level="error")
	else:
		assert el_regions_dropdown
		el_regions_dropdown.click()
		logger.say("Waiting for US (global) region selection")
		el_region_us_global, err = get_element_by(
		    driver, LOCATOR_REGION_DOWNDOWN_GLOBAL_US)  # type: ignore
		if err:
			logger.say(
			    f"Error while waiting for US (global) region selection: {err}",
			    level="error")
		else:
			assert el_region_us_global
			el_region_us_global.click()
	# Start actual data portion
	page_product = {}
	all_data["pages"]["product"] = page_product
	# Go to page
	logger.say(f"Going to page: '{url}'")
	driver.get(url)
	# Wait for the page to load
	# Get product title
	logger.say("Waiting for title element")
	el_title, err = get_element_by(driver, LOCATOR_TITLE)  # type: ignore
	if err:
		logger.say(f"Error while waiting for the title: {err}", level="error")
		page_product["title"] = None
	else:
		assert el_title
		page_product["title"] = el_title.text
	# Get hierarchy
	logger.say("Waiting for hierarchy element")
	el_hierarchy, err = get_element_by(driver, LOCATOR_HIERARCHY)  # type: ignore
	if err:
		logger.say(f"Error while waiting for the hierarchy: {err}", level="error")
		page_product["hierarchy"] = None
	else:
		assert el_hierarchy
		# get li elements
		logger.say("Getting hierarchy li elements")
		el_hierarchy_lis = el_hierarchy.find_elements(By.TAG_NAME, "li")
		# get their text contents
		logger.say("Getting hierarchy li text contents")
		page_product["hierarchy"] = [
		    el_hierarchy_li.get_attribute("textContent").replace("=�", "").replace(
		        "🖥", "").strip().replace(" ", "-")
		    for el_hierarchy_li in el_hierarchy_lis
		]
	# Get tail links
	logger.say("Waiting for tail links element")
	el_tail_links, err = get_element_by(
	    driver,  # type: ignore
	    LOCATOR_TAIL_LINKS)
	if err:
		logger.say(f"Error while waiting for the tail links: {err}", level="error")
		page_product["tail_links"] = None
	else:
		assert el_tail_links
		page_product["tail_links"] = {}
		logger.say("Waiting for tail links strong elements")
		strong_elements = el_tail_links.find_elements(By.TAG_NAME, "strong")
		logger.say("Getting tail links strong elements")
		for strong_element in strong_elements:
			text = strong_element.text
			href = strong_element.find_element(By.XPATH, "..").get_attribute("href")
			page_product["tail_links"][text] = href
	# Get specifications overview
	logger.say("Waiting for specifications overview element")
	el_specifications_overview, err = get_element_by(
	    driver,  # type: ignore
	    LOCALTOR_SPECIFICATIONS_OVERVIEW)
	if err:
		logger.say(f"Error while waiting for the specifications overview: {err}")
		page_product["specifications"] = None
	else:
		assert el_specifications_overview
		page_product["specifications"] = {}
		logger.say("Getting specifications overview tr elements")
		tr_elements = el_specifications_overview.find_elements(By.TAG_NAME, "tr")
		for tr_element in tr_elements:
			td_elements = tr_element.find_elements(By.TAG_NAME, "td")
			if len(td_elements) == 2:
				spec_key = td_elements[0].text
				span_res = td_elements[1].find_elements(By.TAG_NAME, "span")
				# if span_res is [] then we get spec_value from the text of td_elements[1]
				spec_value = td_elements[1].text
				if len(span_res) > 0:
					span_element = span_res[0]
					spec_value = span_element.text
					# if there is a span element check it's title="Yes" or "No" - substitute the icon-ok or icon-remove
					if span_element:
						if span_element.get_attribute("title") == "Yes":
							spec_value = True
						elif span_element.get_attribute("title") == "No":
							spec_value = False
				page_product["specifications"][spec_key] = spec_value
	# Get page source
	logger.say("Getting page source")
	page_product["source"] = driver.page_source
	logger.say(f"Done with product page in {time.time() - time_start} seconds")


# def main(product_name: str):
def main():
	time_start = time.time()
	# Get product name from command line
	global product_name
	product_name = get_product_name()
	# Init logger path_output_root + logs + products + product_name + .log
	global logger
	logger = Logger({
	    "filepath":
	        os.path.join(
	            *[path_output_root, "logs", "products", f"{product_name}.log"]),
	    "level":
	        "DEBUG",
	})
	if product_name == "":
		logger.say("Please specify a product name", level="error")
		exit(1)
	logger.say(f"Product name: '{product_name}'")
	# Add metadata
	all_data["metadata"] = {
	    "created_at":
	        datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
	    "updated_at":
	        datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
	    "product_name":
	        product_name,
	}
	# Init pages
	all_data["pages"] = {}
	# Scrapes separate pages for a given product
	logger.say("Scraping product page")
	scrape_page_product(f"{pangoly_base_url}/en/product/{product_name}?st=US")
	save_data()
	time.sleep(random.uniform(0.1, 0.5))
	logger.say("Scraping price history page")
	scrape_page_history(
	    f"{pangoly_base_url}/en/price-history/{product_name}?st=US")
	# save_data()
	logger.say("Done scraping pages")
	# Update metadata
	all_data["metadata"]["updated_at"] = datetime.now().astimezone().strftime(
	    "%Y-%m-%dT%H:%M:%S.%f%z")
	# Save data
	save_data()
	# Close everything
	logger.say("Closing driver")
	close()
	logger.say(f"Total runtime: {time.time() - time_start} seconds")


if __name__ == '__main__':
	# Run main for the product name
	main()
	logger.say("ALL DONE")
