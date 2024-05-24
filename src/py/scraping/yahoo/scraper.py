# Scraper for Yahoo Finance

# Generic instructions if you want to get a single CSV file
# 1. Go to Yahoo Finance
# 2. Search for a stock
# 3. Click on Historical Data
# 4. Set the date range
# 5. Click Apply
# 6. Click Download button or open developer tools and inspect the button to get the CSV link

# Just query this:
# https://query1.finance.yahoo.com/v7/finance/download/NVDA?period1=1540771200&period2=1698451200&interval=1d&events=history&includeAdjustedClose=true
# replace the symbol as needed - this is last 5 years of daily data for NVDA (Nvidia)

import os
import random
import sys
import json
import time
from typing import Tuple
import requests
from datetime import datetime, timezone

# Project imports
sys.path.append(os.getcwd())
from src.py.utils.logger import Logger

# Globals
date_start = "2018-10-29 00:00:00"
date_end = "2023-10-28 00:00:00"
url_root = "https://query1.finance.yahoo.com/v7/finance/download"
script_path = os.path.dirname(os.path.realpath(__file__))
index_path = os.path.join(script_path, "index.json")
stop_path = os.path.join(script_path,
                         "stop")  # if this file exists, stop scraping
output_path_root = "data/scraped/yahoo"
csv_path_root = os.path.join(output_path_root, "stocks")
time_format = "%Y-%m-%dT%H:%M:%S.%f%z"
symbols = []
fails = []
logger = Logger({
    "filepath": os.path.join(*[output_path_root, "logs", "scraper.log"]),
    "level": "DEBUG",
})
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"


def get_date_from_epoch(epoch: int) -> str:
	# return in UTC
	return datetime.utcfromtimestamp(epoch).strftime('%Y-%m-%d %H:%M:%S')


def get_epoch_from_date(date: str) -> int:
	# get epoch in UTC
	# convert date to UTC - use timezone.utc
	return round(
	    datetime.strptime(
	        date, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).timestamp())


# Epoch tests
# print(get_date_from_epoch(get_epoch_from_date("2018-10-29 00:00:00")))
# print(get_date_from_epoch(1540771200))
# print(get_date_from_epoch(get_epoch_from_date("2023-10-28 00:00:00")))
# print(get_date_from_epoch(1698451200))


def load_index(index_path: str = index_path) -> dict:
	'''
		Loads the index from a file
	'''
	index = {}
	if not os.path.exists(index_path):
		logger.error(
		    f"Index file '{index_path}' does not exist! Try running the crawler first."
		)
		sys.exit(1)
	with open(index_path, "r", encoding="utf-8") as f:
		index = json.load(f)
	logger.info("Loaded index from file.")
	return index


def set_symbols(use_queue: bool = True,
                use_fails: bool = True,
                use_similar: bool = True,
                use_recommended: bool = True) -> list:
	'''
		Returns a list of symbols to scrape from the index
	'''
	global symbols
	symbols_unique = {}
	symbols_list = []
	logger.info("Setting symbols to scrape...")
	index = load_index()
	logger.info("Getting symbols from 'symbols' key...")
	# symbols_index = index["symbols"].keys()
	# sort symbols_index by index["symbols"][symbol]["crawl_index"] descending
	symbols_index = sorted(
	    index["symbols"].keys(),
	    key=lambda symbol: index["symbols"][symbol]["crawl_index"],
	    reverse=False)
	symbols_index_count = 0
	for symbol in symbols_index:
		if symbol in symbols_unique:
			continue
		symbols_list.append(symbol)
		symbols_index_count += 1
		symbols_unique[symbol] = True
	logger.info(f"Got '{symbols_index_count}' symbols from index.")
	if use_queue:
		logger.info("Getting symbols from 'queue' key...")
		symbols_queue = index["queue"]
		symbols_queue_count = 0
		for symbol in symbols_queue:
			if symbol in symbols_unique:
				continue
			symbols_list.append(symbol)
			symbols_queue_count += 1
			symbols_unique[symbol] = True
		logger.info(f"Got '{symbols_queue_count}' symbols from queue.")
	if use_fails:
		logger.info("Getting symbols from 'fails' key...")
		symbols_fails = index["fails"]
		symbols_fails_count = 0
		for symbol in symbols_fails:
			if symbol in symbols_unique:
				continue
			symbols_list.append(symbol)
			symbols_fails_count += 1
			symbols_unique[symbol] = True
		logger.info(f"Got '{symbols_fails_count}' symbols from fails.")
	if use_similar:
		logger.info("Getting symbols from 'similar' keys for each symbol...")
		symbols_similar_count = 0
		for symbol in index["symbols"]:
			for symbol_similar in index["symbols"][symbol]["similar"]:
				if symbol_similar in symbols_unique:
					continue
				symbols_list.append(symbol_similar)
				symbols_similar_count += 1
				symbols_unique[symbol_similar] = True
		logger.info(f"Got '{symbols_similar_count}' symbols from similar.")
	if use_recommended:
		logger.info("Getting symbols from 'recommended' keys for each symbol...")
		symbols_recommended_count = 0
		for symbol in index["symbols"]:
			for symbol_recommended in index["symbols"][symbol]["recommended"]:
				if symbol_recommended in symbols_unique:
					continue
				symbols_list.append(symbol_recommended)
				symbols_recommended_count += 1
				symbols_unique[symbol_recommended] = True
		logger.info(f"Got '{symbols_recommended_count}' symbols from recommended.")
	symbols = symbols_list
	logger.info(f"Set '{len(symbols)}' symbols to scrape.")
	logger.info(f"Symbols: {symbols}")
	return symbols


def wait_random(lower: float = 1.0, upper: float = 3.0) -> None:
	'''
		Waits a random amount of time
	'''
	if lower > upper:
		lower, upper = upper, lower
	wait_time = random.uniform(lower, upper)
	logger.info(f"Waiting for '{wait_time}' seconds...")
	time.sleep(wait_time)


def get_csv(symbol: str) -> Tuple[str, None] | Tuple[None, str]:
	'''
		Returns a tuple of (csv, error)
	'''
	logger.info(f"Getting CSV for '{symbol}'...")
	try:
		date_start_epoch = get_epoch_from_date(date_start)
		date_end_epoch = get_epoch_from_date(date_end)
		url = f"{url_root}/{symbol}?period1={date_start_epoch}&period2={date_end_epoch}&interval=1d&events=history&includeAdjustedClose=true"
		logger.info(f"URL: '{url}'")
		response = requests.get(url, timeout=10, headers={"User-Agent": user_agent})
		if response.status_code != 200:
			err_msg = f"Bad status code '{response.status_code}'"
			return None, err_msg
		csv = response.text
		return csv, None
	except Exception as e:
		err_msg = f"Error converting date to epoch: '{e}'"
		return None, err_msg


def scrape():
	'''
		Scrapes the data
	'''
	logger.info("Scraping Yahoo Finance...")
	logger.info(f"Date range: '{date_start}' to '{date_end}'")
	logger.info(f"CSV path root: '{csv_path_root}'")
	if not os.path.exists(csv_path_root):
		logger.info(f"Creating CSV path root: '{csv_path_root}'...")
		os.makedirs(csv_path_root)
	logger.info("")
	for symbol in symbols:
		if os.path.exists(stop_path):
			logger.info(f"Stop file '{stop_path}' exists! Stopping...")
			logger.info("")
			break
		csv_path = os.path.join(csv_path_root, f"{symbol}.csv")
		if os.path.exists(csv_path):
			logger.info(f"CSV file '{csv_path}' already exists! Skipping...")
			logger.info("")
			continue
		logger.info(f"Scraping '{symbol}'...")
		csv, error = get_csv(symbol)
		wait_random(1.0, 3.0)
		if error:
			logger.error(f"Error scraping '{symbol}': '{error}'")
			fails.append(symbol)
			continue
		assert csv is not None
		logger.info(f"Successfully scraped '{symbol}'!")
		logger.info(f"Writing CSV to '{csv_path}'...")
		with open(csv_path, "w", encoding="utf-8") as f:
			f.write(csv)
		logger.info(f"Successfully wrote CSV to '{csv_path}'!")
		logger.info("")


def print_fails():
	if len(fails) > 0:
		logger.info(f"The following symbols failed to scrape ({len(fails)}):")
		for fail in fails:
			logger.info(f"  - {fail}")


def main():
	logger.info("Starting Yahoo Finance scraper...")
	set_symbols()
	scrape()
	print_fails()
	logger.info("Done scraping Yahoo Finance!")


if __name__ == "__main__":
	main()
	logger.info("Done!")