# Responsible for finding similar companies from Yahoo Finance

import os
import sys
import json
import time
import random
from typing import Tuple
import requests
import bs4 as bs
from datetime import datetime
from collections import deque

# TODO: fix some symbols not being crawled - requests.get("https://finance.yahoo.com/quote/IMOS", timeout=10)

# Project imports
sys.path.append(os.getcwd())
from src.py.utils.logger import Logger

# Globals
symbol_entrypoint = "ASML"  # NVDA, ASML
url_root = "https://finance.yahoo.com"
script_path = os.path.dirname(os.path.realpath(__file__))
index_path = os.path.join(script_path, "index.json")
stop_path = os.path.join(script_path,
                         "stop")  # if this file exists, stop crawling
output_path_root = "data/scraped/yahoo"
time_format = "%Y-%m-%dT%H:%M:%S.%f%z"
index = {}
crawl_queue = deque()
crawl_count_limit = 100
fails = {}
logger = Logger({
    "filepath": os.path.join(*[output_path_root, "logs", "crawler.log"]),
    "level": "DEBUG",
})
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
cookie_path = os.path.join(script_path, "cookie")
cookie = ""


def wait_random(lower: float = 1.0, upper: float = 3.0) -> None:
	'''
		Waits a random amount of time
	'''
	if lower > upper:
		lower, upper = upper, lower
	wait_time = random.uniform(lower, upper)
	logger.info(f"Waiting for '{wait_time}' seconds...")
	time.sleep(wait_time)


def get_default_symbol_object(symbol: str) -> dict:
	'''
		Returns a default symbol object for the crawler
	'''
	symbol_object = {
	    "symbol": symbol,
	    "title": "",
	    "exchange": "",
	    "created_at": datetime.now().astimezone().strftime(time_format),
	    "updated_at": datetime.now().astimezone().strftime(time_format),
	    "url_quote": "",
	    "url_history": "",
	    "crawl_index": 0,  # which successful crawl was this
	    "is_crawled": False,
	    # "is_similar": False, # this will be analyzed later
	    # "is_recommended": False, # this will be analyzed later
	    "similar": {},
	    "recommended": {},
	    "company_profile": {},
	}
	return symbol_object


def get_default_index() -> dict:
	'''
		Returns a default index for the crawler
	'''
	index = {
	    "metadata": {
	        "created_at": datetime.now().astimezone().strftime(time_format),
	        "updated_at": datetime.now().astimezone().strftime(time_format),
	        "symbols_crawled": 0,
	    },
	    "queue": [],
	    "symbols": {
	        symbol_entrypoint: get_default_symbol_object(symbol_entrypoint),
	    },
	    "fails": {},
	}
	return index


def load_index(index_path: str = index_path) -> dict:
	'''
		Loads the index from a file
	'''
	index = {}
	if not os.path.exists(index_path):
		logger.info("Index file does not exist, creating a new one...")
		index = get_default_index()
	else:
		logger.info("Index file exists, loading it...")
		with open(index_path, "r", encoding="utf-8") as f:
			index = json.load(f)
	# If symbol_entrypoint is not in index, add it
	# as we can load the old index with a new symbol_entrypoint
	# Example: we want to expand the index with a new symbol_entrypoint
	# and its similar and recommended symbols
	if symbol_entrypoint not in index["symbols"]:
		logger.info(
		    f"Symbol entrypoint '{symbol_entrypoint}' not in index, adding it...")
		index["symbols"][symbol_entrypoint] = get_default_symbol_object(
		    symbol_entrypoint)
		logger.info("Updating index metadata...")
		# Update metadata
		index["metadata"]["updated_at"] = datetime.now().astimezone().strftime(
		    time_format)
	# Save index
	logger.info("Saving index...")
	save_index(index)
	return index


def save_index(index: dict, index_path: str = index_path) -> None:
	'''
		Saves the index to a file
	'''
	with open(index_path, "w") as f:
		json.dump(index, f, indent='\t', default=str)


def get_crawl_queue(index: dict) -> deque:
	'''
		Returns a queue of symbols to crawl
	'''
	queue = deque()
	# for symbol in index["symbols"]:
	# 	if not index["symbols"][symbol]["is_crawled"]:
	# 		queue.append(symbol)
	index_queue = index["queue"]
	for symbol in index_queue:
		queue.append(symbol)
	if symbol_entrypoint not in queue:
		queue.appendleft(symbol_entrypoint)
	return queue


def load_cookie(cookie_path: str) -> str:
	'''
		Loads cookie from a file
	'''
	cookie = ""
	logger.info(f"Loading cookie from '{cookie_path}'...")
	if os.path.exists(cookie_path):
		with open(cookie_path, "r") as f:
			cookie = f.read()
	else:
		logger.info(f"cookie file does not exist - using empty string...")
	return cookie


# Returns res string, null if no error and null, error if error
def get_quote_page(symbol: str) -> Tuple[str, None] | Tuple[None, str]:
	'''
		Returns the quote page contents for a symbol
	'''
	url = f"{url_root}/quote/{symbol}"
	logger.info(f"Getting quote page for '{symbol}' from '{url}'...")
	# res = requests.get(url,
	#                    timeout=10,
	#                    headers={
	#                        "User-Agent": user_agent,
	#                        "Cookie": cookie
	#                    })
	res = requests.get(url, timeout=10)
	if res.status_code != 200:
		err_msg = f"Error getting quote page for '{symbol}'! (Status code: {res.status_code})"
		return None, err_msg
	return res.text, None


def process_quote_page(
    symbol: str, quote_page: str) -> Tuple[dict, None] | Tuple[None, str]:
	'''
		Processes the quote page contents
	'''
	# We should only return an object if there are no errors
	try:
		soup = bs.BeautifulSoup(quote_page, "html.parser")
		logger.info(f"Processing quote page for '{symbol}'...")
		symbol_object = index["symbols"].get(symbol, None)
		if symbol_object is None:
			logger.info(
			    f"Symbol '{symbol}' not in index, creating a new object for it...")
			symbol_object = get_default_symbol_object(symbol)
		if symbol_object["is_crawled"]:
			err_msg = f"Symbol '{symbol}' already crawled, skipping..."
			return None, err_msg
		# Get title
		logger.info(f"Getting title...")
		title = soup.find("h1").text  # type: ignore
		# Get exchange
		logger.info(f"Getting exchange...")
		exchange = soup.find("div", {
		    "id": "quote-header-info"
		}).find(  # type: ignore
		    "div",
		    {  # type: ignore
		        "class": "C($tertiaryColor)"
		    }).text  # type: ignore
		# Get quote url
		logger.info(f"Getting quote url...")
		quote_url = f"{url_root}/quote/{symbol}"
		# Get history url
		logger.info(f"Getting history url...")
		history_url = f"{url_root}/quote/{symbol}/history"
		# Get similar
		logger.info(f"Getting similar symbols...")
		similar_symbols = soup.find("section", {
		    "id": "similar-by-symbol"
		}).find("table").find_all("tr")  # type: ignore
		similar_symbols = similar = [
		    row.find_all("td")[0].find("a").text
		    for row in similar_symbols
		    if len(row.find_all("td")) > 0
		]
		similar_symbols = [
		    similar_symbol.strip() for similar_symbol in similar_symbols
		]
		similar = {}
		for similar_symbol in similar_symbols:
			similar[similar_symbol] = similar_symbol
		# Get recommended
		logger.info(f"Getting recommended symbols...")
		recommended_symbols = soup.find("section", {
		    "id": "recommendations-by-symbol"
		}).find("table").find_all("tr")  # type: ignore
		recommended_symbols = [
		    row.find_all("td")[0].find("a").text
		    for row in recommended_symbols
		    if len(row.find_all("td")) > 0
		]
		recommended_symbols = [
		    recommended_symbol.strip()
		    for recommended_symbol in recommended_symbols
		]
		recommended = {}
		for recommended_symbol in recommended_symbols:
			recommended[recommended_symbol] = recommended_symbol
		# Get company profile
		logger.info(f"Getting company profile...")
		company_profile = soup.find("div", {
		    "class": "Mb(25px)"
		}).find_all("p")  # type: ignore
		description = company_profile[0]
		details = company_profile[1]
		description_decoded = description.encode_contents().decode("utf-8")
		details_decoded = details.encode_contents().decode("utf-8")
		website = description.find("a", {"title": "Company Profile"})["href"]
		country = description_decoded.split("<br/>")[-3]  # [2]
		details_spans = details.find_all("span")
		sector = details_spans[1].text
		industry = details_spans[3].text
		employees = details_spans[5].text
		company_profile = {
		    "website": website,
		    "country": country,
		    "sector": sector,
		    "industry": industry,
		    "employees": employees,
		    "raw": {
		        "description": description_decoded,
		        "details": details_decoded,
		    }
		}
		# Update symbol object
		logger.info(f"Updating symbol object...")
		symbol_object["title"] = title
		symbol_object["exchange"] = exchange
		symbol_object["url_quote"] = quote_url
		symbol_object["url_history"] = history_url
		symbol_object["similar"] = similar
		symbol_object["recommended"] = recommended
		symbol_object["company_profile"] = company_profile
		symbol_object["is_crawled"] = True
		symbol_object["crawl_index"] = index["metadata"]["symbols_crawled"] + 1
		symbol_object["updated_at"] = datetime.now().astimezone().strftime(
		    time_format)
		return symbol_object, None
	except Exception as e:
		err_msg = f"Error processing quote page for '{symbol}'! ({json.dumps(e, indent='  ', default=str)})"
		return None, err_msg


def handle_fail(symbol: str, repeat: bool = False) -> None:
	'''
		Handles a failed symbol
	'''
	global fails
	global index
	global crawl_queue
	if repeat:
		logger.info(
		    f"Repeating symbol: '{symbol}' - putting it at the end of the queue..."
		)
		crawl_queue.append(symbol)
	# Update fails
	logger.info(f"Updating fails...")
	if symbol not in fails:
		fails[symbol] = 0
	fails[symbol] = fails[symbol] + 1
	# Update index fails
	logger.info(f"Updating index fails...")
	index["fails"] = fails
	# Update index metadata
	logger.info(f"Updating index metadata...")
	index["metadata"]["updated_at"] = datetime.now().astimezone().strftime(
	    time_format)
	# Save index
	logger.info(f"Saving index...")
	save_index(index)
	logger.info("")


def crawl() -> None:
	'''
		Responsible for crawling the queue
	'''
	global index
	global crawl_queue
	global fails
	while len(crawl_queue) > 0:
		if index["metadata"]["symbols_crawled"] >= crawl_count_limit:
			logger.info(
			    f"Symbols crawled limit reached ({crawl_count_limit}), stopping...")
			break
		if os.path.exists(stop_path):
			logger.info(f"Stop file found, stopping...")
			break
		symbol = crawl_queue.popleft()
		logger.info(f"Crawling symbol: '{symbol}'")
		quote_page, err_msg = get_quote_page(symbol)
		# Sleep for a random amount of time - regardless of error
		wait_random(1.0, 3.0)
		if err_msg:
			logger.error(err_msg)
			handle_fail(symbol, repeat=False)  #repeat=True)
			# Ask user if they want to continue or not
			# This is to avoid getting blocked by Yahoo
			# user_input = input("Continue? (y/n): ")
			# if user_input.lower() != "y":
			# 	break
			continue
		assert quote_page is not None
		# Process quote page
		symbol_object, err_process = process_quote_page(symbol, quote_page)
		if err_process:
			logger.error(err_process)
			handle_fail(symbol, repeat=False)
			continue
		assert symbol_object is not None
		# Update index
		index["symbols"][symbol] = symbol_object
		# Update crawl queue with symbols from similar and recommended
		logger.info(f"Updating crawl queue...")
		symbols_similar = symbol_object["similar"]
		symbols_recommended = symbol_object["recommended"]
		symbols_to_enqueue = {}
		symbols_to_enqueue.update(
		    symbols_similar)  # NOTE: should we only use similar?
		symbols_to_enqueue.update(symbols_recommended)
		for symbol_to_enqueue in symbols_to_enqueue:
			if (symbol_to_enqueue not in index["symbols"] or
			    index["symbols"][symbol_to_enqueue]["is_crawled"]
			    == False) and symbol_to_enqueue not in crawl_queue:
				crawl_queue.append(symbol_to_enqueue)
		# Update index queue
		logger.info(f"Updating index queue...")
		index_queue = list(crawl_queue)
		index["queue"] = index_queue
		# Update index metadata
		logger.info(f"Updating index metadata...")
		index["metadata"]["updated_at"] = datetime.now().astimezone().strftime(
		    time_format)
		index["metadata"][
		    "symbols_crawled"] = index["metadata"]["symbols_crawled"] + 1
		# Save index
		logger.info(f"Saving index...")
		save_index(index)
		logger.info(f"Done crawling symbol: '{symbol}'")
		logger.info("")


def main() -> None:
	'''
		Main function
	'''
	global index
	global crawl_queue
	global cookie
	global fails
	index = load_index()
	fails = index["fails"]
	crawl_queue = get_crawl_queue(index)
	logger.info(f"Crawl queue: {crawl_queue}")
	cookie = load_cookie(cookie_path)
	crawl()
	fails_text = json.dumps(fails, indent='\t')
	logger.info(f"Fails:\n{fails_text}")


if __name__ == "__main__":
	main()
	print("Done!")