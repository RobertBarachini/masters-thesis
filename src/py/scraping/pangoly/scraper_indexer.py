from __future__ import annotations
import os
import sys
import json
import time
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
import brotli
import gzip
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
final_output_path = os.path.join(path_output_root, "index.json")
WEBDRIVER_BROWSER = os.getenv("WEBDRIVER_BROWSER")
all_data = {}
driver: TypeWebDriver = None  # type: ignore
pangoly_base_url = "https://pangoly.com"
# walk_categories_limiter:
# Select which categories to walk in advance
# Key: category key
# Value: number of pages to walk (-1 for no limit)
# Set to None to walk all categories
# walk_categories_limiter = {"cpu": 3}
# walk_categories_limiter = {"psu": -1}
walk_categories_limiter = {
    "motherboard": -1,
    "cpu": -1,
    "ram": -1,
    "vga": -1,
    "ssd": -1,
    "hdd": -1,
    "external-storage": -1,
    "monitor": -1,
    "mouse": -1,
    "keyboard": -1,
    "cpu-cooler": -1,
    "wireless-network-adapter": -1,
    "laptop": -1,
}

# Init logger (same path as index.json but index.log)
logger = Logger({
    "filepath": os.path.join(path_output_root, "index.log"),
    "level": "DEBUG",
})


def init_all_data():
	# Add metadata
	all_data["metadata"] = {
	    "created_at":
	        datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
	    "updated_at":
	        datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
	}
	# Get all categories
	all_data["categories"] = get_categories()


def init():
	global driver
	global all_data
	# Log all constants and globals
	logger.say(f"Starting scraper_indexer.py with options:")
	logger.say(f"path_output_root: '{path_output_root}'")
	logger.say(f"final_output_path: '{final_output_path}'")
	logger.say(f"pangoly_base_url: '{pangoly_base_url}'")
	logger.say(f"WEBDRIVER_BROWSER: '{WEBDRIVER_BROWSER}'")
	logger.say(
	    f"walk_categories_limiter: {json.dumps(walk_categories_limiter, indent=2, sort_keys=True, default=str)}"
	)
	logger.say("")

	# Init driver
	driver = init_driver(WEBDRIVER_BROWSER)  # type: ignore
	# driver.request_interceptor = request_interceptor
	# driver.response_interceptor = response_interceptor

	# Check if the file already exists and load all_data from it
	if os.path.exists(final_output_path):
		logger.say(f"Loading all_data from '{final_output_path}' to continue")
		with open(final_output_path, "r", encoding="utf-8") as f:
			all_data = json.load(f)
	else:
		# Init all_data
		logger.say(f"Initializing all_data and starting from scratch")
		init_all_data()


def close():
	global driver
	try:
		driver.quit()
	except Exception as e:
		logger.say(f"Exception while quitting the driver: {e}")


def save_data():
	# Save all_data to file
	# logger.say(f"Saving all_data to '{final_output_path}'")
	if not os.path.exists(path_output_root):
		os.makedirs(path_output_root)
	with open(final_output_path, "w", encoding="utf-8") as f:
		json.dump(all_data, f, indent="\t")


def walk_category(category_key: str):
	if walk_categories_limiter is not None and category_key not in walk_categories_limiter:
		logger.say(f"\nSkipping category '{category_key}' (not in limiter)\n")
		return
	logger.say(f"\nCATEGORY: {category_key}\n")
	# Local locators
	LOCATOR_PRODUCTS_GRID = (
	    By.CSS_SELECTOR,
	    "body > div.container > div > div.col-xs-12.col-sm-9.content-wrapper > div.row.products-grid.wrapper-box"
	)
	LOCATOR_NO_MORE_PRODUCTS = (
	    By.CSS_SELECTOR,
	    "body > div.container > div > div.col-xs-12.col-sm-9.content-wrapper > div:nth-child(4) > div"
	)
	category_obj = all_data["categories"][category_key]
	product_links = {}
	products_count = 0
	if "products" in category_obj and category_obj["products"]:
		product_links = category_obj["products"]
		products_count = int(
		    len(product_links) - (len(product_links) / category_obj["last_page"])
		)  # 12 products per page + we repeat the last page
	current_page = 1
	if "last_page" in category_obj:
		current_page = category_obj[
		    "last_page"]  # + 1 is not good - we want to recheck the last page anyways and the operations below are idempotent
	hard_limit = 100  # default: 100, -1 for no limit
	if walk_categories_limiter is not None and category_key in walk_categories_limiter:
		hard_limit = walk_categories_limiter[category_key]
	while True:
		# Check if we reached the hard limit
		if hard_limit != -1 and current_page > hard_limit:
			break
		page_url = f"{pangoly_base_url}/en/browse/{category_key}?page={current_page}"
		category_obj["last_page"] = current_page
		logger.say(f"Page {current_page}: {page_url}")
		driver.get(page_url)
		# Get products grid
		el_products_grid, err = get_element_by(
		    driver,  # type: ignore
		    LOCATOR_PRODUCTS_GRID)
		if err:
			logger.say(f"Error: {err}")
			break
		assert el_products_grid
		# Get product links
		el_products = el_products_grid.find_elements(By.CLASS_NAME,
		                                             "productItemLink")
		for i_product, el_product in enumerate(el_products):
			url = f"{el_product.get_attribute('href')}"
			products_count += 1
			logger.say(f"  {i_product + 1}. / {products_count}: {url}")
			product_key = url.split("/")[-1]
			product_links[product_key] = url
		current_page += 1
		# Update metadata
		category_obj["updated_at"] = datetime.now().astimezone().strftime(
		    "%Y-%m-%dT%H:%M:%S.%f%z")
		# Save data
		category_obj["products"] = product_links
		save_data()  # TODO: update only every n pages
	# Update metadata
	category_obj["updated_at"] = datetime.now().astimezone().strftime(
	    "%Y-%m-%dT%H:%M:%S.%f%z")
	# Save data
	category_obj["products"] = product_links
	save_data()


def walk_categories(categories_data: dict):
	for category_key, category_data in categories_data.items():
		walk_category(category_key)


def get_categories() -> dict:
	# Local locators
	LOCATOR_PRODUCTS_GRID = (
	    By.CSS_SELECTOR,
	    "body > div.container > div > div.col-xs-12.col-sm-9.content-wrapper > div"
	)

	# Get categories
	driver.get(f"{pangoly_base_url}/en/browse")

	# Get categories
	el_categories_grid, err = get_element_by(
	    driver,  # type: ignore
	    LOCATOR_PRODUCTS_GRID)
	if err:
		logger.say(f"Error: {err}")
		exit(1)
	assert el_categories_grid
	el_categories = el_categories_grid.find_elements(By.CLASS_NAME,
	                                                 "productItemCategory")
	# Get categories data
	categories_data = {}
	for category in el_categories:
		category_data = {}
		category_data["name"] = category.get_attribute("textContent").strip()
		el_a = category.find_element(By.TAG_NAME, "a")
		url = f"{el_a.get_attribute('href')}"
		category_data["url"] = url
		category_key = url.split("/")[-1]
		logger.say(f"'{category_key}': {url}")
		category_data["products"] = None
		category_data["created_at"] = datetime.now().astimezone().strftime(
		    "%Y-%m-%dT%H:%M:%S.%f%z")
		category_data["updated_at"] = datetime.now().astimezone().strftime(
		    "%Y-%m-%dT%H:%M:%S.%f%z")
		categories_data[category_key] = category_data
	return categories_data


def main():
	# Init
	init()
	# Walk categories
	walk_categories(all_data["categories"])
	# Update metadata
	all_data["metadata"]["updated_at"] = datetime.now().astimezone().strftime(
	    "%Y-%m-%dT%H:%M:%S.%f%z")
	# Save data
	save_data()
	# Close everything
	close()


if __name__ == '__main__':
	main()
	logger.say("ALL DONE")