# Scraper for Yahoo Finance currencies (exchange rates)

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
date_start = "2010-01-01 00:00:00"
date_end = "2023-12-27 00:00:00"
time_format = "%Y-%m-%d %H:%M:%S"
override_index = False  # if True, overrides the index every time
output_path_root = "data/scraped/yahoo"
path_index = os.path.join(*[output_path_root, "currencies", "index.json"])
path_csv_root = os.path.join(*[output_path_root, "currencies", "csv"])
url_base = "https://finance.yahoo.com"
url_currencies = f"{url_base}/currencies/"
index = {}
fails = []
logger = Logger({
    "filepath":
        os.path.join(*[output_path_root, "logs", "scraper_currencies.log"]),
    "level":
        "DEBUG",
})
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
session = requests.Session()
session.headers.update({"User-Agent": user_agent})


def get_date_from_epoch(epoch: int) -> str:
	# return in UTC
	return datetime.utcfromtimestamp(epoch).strftime(time_format)


def get_epoch_from_date(date: str) -> int:
	# get epoch in UTC
	# convert date to UTC - use timezone.utc
	return round(
	    datetime.strptime(date,
	                      time_format).replace(tzinfo=timezone.utc).timestamp())


def get_data(url: str) -> Tuple[str, None] | Tuple[None, str]:
	'''
		Gets the data from the given url
	'''
	logger.info(f"Getting data from '{url}'...")
	try:
		response = session.get(url, timeout=30)
		if response.status_code != 200:
			logger.error(f"Got status code {response.status_code}!")
			if response.status_code == 429:
				logger.error(
				    "Too many requests. RATE LIMIT EXCEEDED. Try again later.")
			return None, f"Got status code {response.status_code}!"
		return response.text, None
	except Exception as e:
		# logger.error(f"Got exception: {e}")
		return None, f"Got exception: {e}"


def save_index() -> None:
	'''
		Saves the index to a file
	'''
	if not os.path.exists(os.path.dirname(path_index)):
		os.makedirs(os.path.dirname(path_index))
	logger.info(f"Saving index to '{path_index}'...")
	with open(path_index, "w") as f:
		json.dump(index, f, indent=2)
	logger.info(f"Saved index.")


def fill_index():
	'''
		Fills the index with the currencies
	'''
	global index
	if os.path.exists(path_index) and not override_index:
		logger.info(f"Loading index from '{path_index}'...")
		with open(path_index, "r") as f:
			index = json.load(f)
		logger.info(f"Loaded index with {len(index)} currencies.")
		return
	index = {}
	logger.info("Filling index...")
	data, err = get_data(url_currencies)
	if err is not None:
		logger.error(f"Got error while getting index response: {err}")
		logger.info("Exiting...")
		sys.exit(1)
	assert data is not None
	soup = bs(data, "html.parser")
	# get section id="yfin-list"
	section = soup.find("section", {"id": "yfin-list"})
	assert section is not None
	table = section.find("table", {"class": "W(100%)"})  # type: ignore
	assert table is not None
	tbody = table.find("tbody")  # type: ignore
	assert tbody is not None
	rows = tbody.find_all("tr")  # type: ignore
	assert rows is not None
	for row in rows:
		currency = {}
		cols = row.find_all("td")
		assert cols is not None
		symbol = cols[0].find("a").text.strip()
		currency["symbol"] = symbol
		link = cols[0].find("a")["href"]
		currency["link"] = link
		name = cols[1].text.replace("/", "-").strip()
		currency["name"] = name
		last_price = cols[2].text.strip()
		currency["last_price"] = last_price
		index[name] = currency
		logger.info(
		    f"Added currency '{name}' to index.\n{json.dumps(currency, indent=2)}")
	logger.info(f"Filled index with {len(index)} currencies.")
	save_index()


def scrape():
	'''
		Scrapes the data
	'''
	time_start = time.time()
	logger.info("Scraping Yahoo Finance for currency exchange rates...")
	logger.info(f"CSV path root: '{path_csv_root}'")
	logger.info(f"Date range: '{date_start}' to '{date_end}'")
	date_start_epoch = get_epoch_from_date(date_start)
	date_end_epoch = get_epoch_from_date(date_end)
	if not os.path.exists(path_csv_root):
		os.makedirs(path_csv_root)
	logger.info("")
	for i, name in enumerate(index):
		currency = index[name]
		time_start_symbol = time.time()
		csv_path = os.path.join(path_csv_root, f"{name}.csv")
		if os.path.exists(csv_path):
			logger.info(
			    f"[{i + 1}/{len(index)}] CSV file '{csv_path}' already exists! Skipping..."
			)
			logger.info("")
			continue
		logger.info(f"[{i + 1}/{len(index)}] Scraping '{name}'...")
		url = f"https://query1.finance.yahoo.com/v7/finance/download/{currency['symbol']}?period1={date_start_epoch}&period2={date_end_epoch}&interval=1d&events=history&includeAdjustedClose=true"
		csv, error = get_data(url)
		if error:
			logger.error(f"Error scraping '{name}': '{error}'")
			logger.info("")
			fails.append((name, error))
			continue
		assert csv is not None
		with open(csv_path, "w") as f:
			f.write(csv)
		logger.info(f"Saved CSV to '{csv_path}'")
		time_end_symbol = time.time()
		time_elapsed_symbol = time_end_symbol - time_start_symbol
		logger.info(
		    f"Scraped '{name}' in '{round(time_elapsed_symbol, 3)}' seconds.")
		logger.info("")
	time_end = time.time()
	time_elapsed = time_end - time_start
	logger.info(f"Scraped all currencies in '{round(time_elapsed, 3)}' seconds.")
	logger.info("")
	if len(fails) > 0:
		logger.info(f"The following currencies failed to scrape ({len(fails)}):")
		for fail in fails:
			logger.info(f"  - {fail}")


def main():
	fill_index()
	scrape()


if __name__ == "__main__":
	main()
	logger.info("Done!")
