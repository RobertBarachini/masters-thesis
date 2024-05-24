import os
import sys
import json
import time
import random
from typing import Tuple
import requests
from datetime import datetime, timezone

# Project imports
sys.path.append(os.getcwd())
from src.py.utils.logger import Logger

# Project imports
year_start = 2019
year_end = 2023
limit = 2000
script_path = os.path.dirname(os.path.realpath(__file__))
index_path = "data/scraped/cnet/index_articles.json"
apikey_path = os.path.join(script_path, "apikey")
apikey = ""
stop_path = os.path.join(script_path,
                         "stop")  # if this file exists, stop scraping
output_path_root = "data/scraped/cnet"
index = {}
fails = []
logger = Logger({
    "filepath":
        os.path.join(
            *[output_path_root, "logs", "scraper_cnet_article_indexer.log"]),
    "level":
        "DEBUG",
})
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
session = requests.Session()
session.headers.update({"User-Agent": user_agent})


def load_apikey():
	'''
		Loads the API key from a file
	'''
	global apikey
	logger.info(f"Loading API key from '{apikey_path}'...")
	if not os.path.exists(apikey_path):
		logger.error(
		    f"API key file '{apikey_path}' does not exist! Make a request manually and save the API key from network tab to the file."
		)
		sys.exit(1)
	with open(apikey_path, "r", encoding="utf-8") as f:
		apikey = f.read().strip()
		session.headers.update({"apiKey": apikey})
	logger.info("Loaded API key from file.")


def load_index():
	'''
		Loads the index from a file
	'''
	global index
	logger.info(f"Loading index from '{index_path}'...")
	if not os.path.exists(index_path):
		logger.info("Index file does not exist. Creating new index...")
		index = {
		    "metadata": {
		        "created": datetime.now(timezone.utc).isoformat(),
		        "last_updated": datetime.now(timezone.utc).isoformat(),
		    },
		    "articles": {},
		    "state": {
		        "year": year_start,
		        "year_start": year_start,
		        "year_end": year_end,
		        "limit": limit,
		        "offset": 0,
		    }
		}
	else:
		with open(index_path, "r", encoding="utf-8") as f:
			index = json.load(f)
		logger.info("Loaded index from file.")


def save_index() -> None:
	'''
		Saves the index to a file
	'''
	logger.info(f"Saving index to '{index_path}'...")
	with open(index_path, "w", encoding="utf-8") as f:
		# json.dump(index, f)  #, indent=2)
		json.dump(index, f, indent=2)
	logger.info("Saved index to file.")


def get_data(url: str) -> Tuple[dict, None] | Tuple[None, str]:
	'''
		Gets the data from the given url
	'''
	logger.info(f"Getting data from '{url.split('&apiKey=')[0]}'...")
	try:
		response = session.get(url, timeout=60)
		if response.status_code != 200:
			logger.error(f"Got status code {response.status_code}!")
			return None, f"Got status code {response.status_code}!"
		return response.json(), None
	except Exception as e:
		logger.error(f"Got exception: {e}")
		return None, f"Got exception: {e}"


def wait_random(lower: float = 1.0, upper: float = 3.0) -> None:
	'''
		Waits a random amount of time
	'''
	if lower > upper:
		lower, upper = upper, lower
	wait_time = random.uniform(lower, upper)
	logger.info(f"Waiting for '{round(wait_time, 3)}' seconds...")
	time.sleep(wait_time)


def fill_index():
	'''
		Fills the index with articles
	'''
	logger.info("Filling the index with articles...")
	logger.info(f"Current state: {json.dumps(index['state'], indent=2)}")
	logger.info("")
	limit = index["state"]["limit"]
	start_at_year = index["state"]["year"]
	start_at_offset = index["state"]["offset"]
	for year in range(start_at_year, index["state"]["year_end"] + 1):
		logger.info(f"Scraping year '{year}'...")
		logger.info("")
		index["state"]["year"] = year
		offset = start_at_offset
		while True:
			time_start = time.time()
			if os.path.exists(stop_path):
				logger.info(f"Stop file '{stop_path}' exists. Stopping scraping...")
				save_index()
				sys.exit(0)
			logger.info(
			    f"Scraping year '{year}' with offset '{offset}' and limit '{limit}'..."
			)
			url = f"https://bender.cnetstatic.com/api/neutron/sitemaps/cnet/articles/year/{year}/web?limit={limit}&offset={offset}&apiKey={apikey}"
			data, err = get_data(url)
			if err is not None:
				logger.error(f"Got error: {err}")
				save_index()
				sys.exit(1)
			assert data is not None
			num_items = data["meta"]["numOfItems"]
			logger.info(f"Got '{num_items}' articles.")
			for article in data["data"]["items"]:
				index["articles"][article["id"]] = article
			index["state"]["offset"] = offset
			index["state"]["last_updated"] = datetime.now(timezone.utc).isoformat()
			logger.info(f"Total articles: '{len(index['articles'])}'")
			# save_index() # takes too long
			wait_random()
			logger.info(
			    f"Total time: '{round(time.time() - time_start, 3)}' seconds")
			logger.info("")
			if data["links"]["next"]["href"] is None:
				logger.info("No more articles. Moving to next year...")
				logger.info("")
				break
			offset += limit
		start_at_offset = 0
	save_index()
	logger.info("Successfully filled the index with articles!")


def main():
	load_apikey()
	load_index()
	fill_index()


if __name__ == "__main__":
	main()
	logger.info("Done!")
