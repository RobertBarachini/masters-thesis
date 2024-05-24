# Simplified scraper for Yahoo Finance companies using the index_stocks.json file
# It adds company profile data to the index_stocks.json file
# https://finance.yahoo.com/quote/MSFT/profile

# Scraper for Yahoo Finance

import os
import random
import sys
import json
import time
from typing import Tuple
import requests
from datetime import datetime, timezone
from bs4 import BeautifulSoup as bs

# Project imports
sys.path.append(os.getcwd())
from src.py.utils.logger import Logger

# Globals
script_path = os.path.dirname(os.path.realpath(__file__))
index_path = "data/scraped/yahoo/sectors/index_stocks.json"
stop_path = os.path.join(script_path,
                         "stop")  # if this file exists, stop scraping
output_path_root = "data/scraped/yahoo"
index = {}
fails = []
logger = Logger({
    "filepath":
        os.path.join(
            *[output_path_root, "logs", "scraper_company_profiles.log"]),
    "level":
        "DEBUG",
})
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
session = requests.Session()
session.headers.update({"User-Agent": user_agent})


def load_index(index_path: str = index_path) -> dict:
	'''
		Loads the index from a file
	'''
	index = {}
	if not os.path.exists(index_path):
		logger.error(
		    f"Index file '{index_path}' does not exist! Try running the sectors.py script first."
		)
		sys.exit(1)
	with open(index_path, "r", encoding="utf-8") as f:
		index = json.load(f)
	logger.info("Loaded index from file.")
	return index


def save_index(index_path: str = index_path) -> None:
	'''
		Saves the index to a file
	'''
	logger.info(f"Saving index to '{index_path}'...")
	with open(index_path, "w", encoding="utf-8") as f:
		json.dump(index, f, indent=2)
	logger.info(f"Successfully saved index to '{index_path}'!")


def set_index() -> dict:
	'''
		Returns the index dictionary with companies list
	'''
	global index
	logger.info("Setting the index to scrape...")
	index = load_index()
	return index


def wait_random(lower: float = 1.0, upper: float = 3.0) -> None:
	'''
		Waits a random amount of time
	'''
	if lower > upper:
		lower, upper = upper, lower
	wait_time = random.uniform(lower, upper)
	logger.info(f"Waiting for '{round(wait_time, 3)}' seconds...")
	time.sleep(wait_time)


def get_profile_page(symbol: str) -> Tuple[str, None] | Tuple[None, str]:
	'''
		Returns a tuple of (csv, error)
	'''
	logger.info(f"Getting profile page for '{symbol}'...")
	try:
		url = f"https://finance.yahoo.com/quote/{symbol}/profile"
		logger.info(f"URL: '{url}'")
		# response = requests.get(url,
		#                         timeout=10,
		#                         headers={"User-Agent": user_agent})
		response = session.get(url, timeout=10)
		if session.cookies.get_dict() == {}:
			session.cookies.update(response.cookies)
		if response.status_code != 200:
			err_msg = f"Bad status code '{response.status_code}'"
			return None, err_msg
		csv = response.text
		return csv, None
	except Exception as e:
		err_msg = f"Error converting date to epoch: '{e}'"
		return None, err_msg


def get_profile_data(
    profile_page: str) -> Tuple[dict, None] | Tuple[None, str]:
	'''
		Returns company data from profile page (location, employees, etc.)
	'''
	logger.info("Getting company data from profile page...")
	try:
		profile_data = {}
		soup = bs(profile_page, "html.parser")
		# element_profile_container = soup.find("div",
		#                                       {"class": "asset-profile-container"})
		# assert element_profile_container is not None
		element_profile_info = soup.select_one("div[data-test='qsp-profile']")
		assert element_profile_info is not None
		element_ps = element_profile_info.find_all("p")
		element_address_contact = element_ps[0]
		element_sector_industry = element_ps[1]
		element_sector_industry_spans = element_sector_industry.find_all("span")
		profile_data["sector"] = element_sector_industry_spans[1].text.replace(
		    "\t", "").replace("\xa0", "").strip()
		profile_data["industry"] = element_sector_industry_spans[3].text.replace(
		    "\t", "").replace("\xa0", "").strip()
		all_links = element_address_contact.find_all("a", href=True)
		website = None
		phone_number = None
		if len(all_links) == 1:
			link_text = all_links[0].text.strip()
			if "http" in link_text:
				website = link_text
			else:
				phone_number = link_text
		elif len(all_links) == 2:
			phone_number = all_links[0].text.strip().replace(" ", "").replace(
			    "-", "").replace("\t", "").replace("\n", "").replace("+", "")
			website = all_links[1].text.strip()
		else:
			logger.error(f"Unexpected number of links: '{len(all_links)}'")
			return None, "Unexpected number of links"
		profile_data["website"] = website
		profile_data["phone_number"] = phone_number
		# remove all links from the address/contact section
		for a in all_links:
			a.extract()
		address = element_address_contact.decode_contents().strip().replace(
		    "<br/>", "\n").replace("\t", "").strip()
		profile_data["address"] = address
		employees = None
		split_parts = element_sector_industry.text.lower().strip().replace(
		    "\n",
		    "").replace("\t", "").replace("\xa0", "").replace(" ", "").replace(
		        ".", "").replace(",", "").split("fulltimeemployees:")
		if len(split_parts) == 2:
			employees = split_parts[1].strip()
		else:
			logger.error(f"Unexpected number of parts: '{len(split_parts)}'")
			return None, "Unexpected number of parts"
		profile_data["employees"] = employees
		logger.info(f"Profile data successfully parsed: '{profile_data}'")
		return profile_data, None
	except Exception as e:
		err_msg = f"Error getting company data from profile page: '{e}'"
		return None, err_msg


def scrape():
	'''
		Scrapes the data
	'''
	time_start = time.time()
	logger.info("Scraping Yahoo Finance for company profile data...")
	logger.info(f"Index path: '{index_path}'")
	logger.info("")
	for i, company in enumerate(index):
		symbol = company["symbol"]
		time_start_symbol = time.time()
		if os.path.exists(stop_path):
			logger.info(f"Stop file '{stop_path}' exists! Stopping...")
			logger.info("")
			break
			# if "profile" in company and "industry" in company[
			#     "profile"] and "sector" in company["profile"]:
		if "profile" in company:
			logger.info(f"Profile already exists for '{symbol}'! Skipping...")
			logger.info("")
			continue
		logger.info(f"Scraping '{symbol}' ({i + 1}/{len(index)})...")
		profile_page, error = get_profile_page(symbol)
		wait_random(0.5, 1.0)
		if error:
			logger.error(f"Error getting the page for symbol '{symbol}': '{error}'")
			fails.append((symbol, error))
			continue
		assert profile_page is not None
		profile_data, error = get_profile_data(profile_page)
		if error:
			logger.error(f"Error scraping the page for symbol '{symbol}': '{error}'")
			fails.append((symbol, error))
			continue
		assert profile_data is not None
		company["profile"] = profile_data
		# if "profile" not in company:
		# 	company["profile"] = profile_data
		# else:
		# 	company["profile"]["sector"] = profile_data["sector"]
		# 	company["profile"]["industry"] = profile_data["industry"]
		logger.info(f"Successfully scraped '{symbol}'!")
		# save_index()
		time_end_symbol = time.time()
		logger.info(
		    f"Time elapsed for '{symbol}': '{time_end_symbol - time_start_symbol}' seconds"
		)
		logger.info("")
	time_end = time.time()
	logger.info(f"Time elapsed total: '{time_end - time_start}' seconds")
	logger.info("")
	save_index()


def print_fails():
	if len(fails) > 0:
		logger.info(f"The following symbols failed to scrape ({len(fails)}):")
		for fail in fails:
			# logger.info(f"  - {fail}")
			logger.info(f"  - {fail[0]}: '{fail[1]}'")


def main():
	logger.info("Starting Yahoo Finance scraper...")
	set_index()
	scrape()
	print_fails()
	logger.info("Done scraping Yahoo Finance!")


if __name__ == "__main__":
	main()
	logger.info("Done!")
