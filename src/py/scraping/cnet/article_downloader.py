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
script_path = os.path.dirname(os.path.realpath(__file__))
stop_path = os.path.join(script_path, "article_downloader_stop")
index_path = "data/scraped/cnet/index_articles.json"
output_path_root = "data/scraped/cnet/articles/html"
index = {}
fails = []
logger = Logger({
    "filepath":
        os.path.join(*[
            "data/scraped/cnet", "logs", "scraper_cnet_article_downloader.log"
        ]),
    "level":
        "DEBUG",
})
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
session = requests.Session()
session.headers.update({"User-Agent": user_agent})


def load_index():
	'''
		Loads the index from a file
	'''
	global index
	logger.info(f"Loading index from '{index_path}'...")
	if not os.path.exists(index_path):
		logger.info(
		    "Index file does not exist. Try running article_indexer.py first.")
		sys.exit(1)
	with open(index_path, "r", encoding="utf-8") as f:
		index = json.load(f)
	logger.info("Loaded index from file.")


def wait_random(lower: float = 1.0, upper: float = 3.0) -> None:
	'''
		Waits a random amount of time
	'''
	if lower > upper:
		lower, upper = upper, lower
	wait_time = random.uniform(lower, upper)
	logger.info(f"Waiting for '{round(wait_time, 3)}' seconds...")
	time.sleep(wait_time)


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
				wait_random(10.0, 30.0)
			return None, f"Got status code {response.status_code}!"
		return response.text, None
	except Exception as e:
		logger.error(f"Got exception: {e}")
		return None, f"Got exception: {e}"


def download_article(article_id: str, url: str, output_path: str):
	'''
		Downloads an article
	'''
	logger.info(f"Downloading article '{article_id}'...")
	data, error = get_data(url)
	if error is not None:
		logger.error(f"Failed to download article '{article_id}'!")
		fails.append(article_id)
		return
	assert data is not None
	with open(output_path, "w", encoding="utf-8") as f:
		f.write(data)
	logger.info(f"Downloaded article and saved it.")


def download_articles():
	'''
		Downloads the articles
	'''
	logger.info("Downloading articles...")
	logger.info(f"")
	count = 0
	downloaded_this_run = 0
	time_start_all = time.time()
	for article_id, article in index["articles"].items():
		if os.path.exists(stop_path):
			logger.info(
			    f"Elapsed time total: {round(time.time() - time_start_all, 3)}s")
			logger.info("Stop file found. Safely stopping.")
			sys.exit(0)
		count += 1
		output_path = os.path.join(output_path_root, f"{article_id}.html")
		if os.path.exists(output_path):
			logger.info(
			    f"{count + 1}/{len(index['articles'])} - Article '{article_id}' already exists."
			)
			logger.info("")
			continue
		time_start_article = time.time()
		logger.info(f"{count + 1}/{len(index['articles'])}...")
		slug = article["slug"]
		url = f"https://www.cnet.com/news/{slug}"
		download_article(article_id, url, output_path)
		# wait_random(1.0, 3.0)
		downloaded_this_run += 1
		logger.info(
		    f"Avg. time per article: {round((time.time() - time_start_all) / downloaded_this_run, 3)}s ({downloaded_this_run} articles downloaded this run)"
		)
		logger.info(
		    f"Elapsed time article: {round(time.time() - time_start_article, 3)}s")
		logger.info("")
	logger.info("Downloaded articles.")
	logger.info(f"Elapsed time total: {round(time.time() - time_start_all, 3)}s")
	logger.info("")


def main():
	'''
		Main entrypoint
	'''
	load_index()
	if not os.path.exists(output_path_root):
		os.makedirs(output_path_root)
	download_articles()
	if len(fails) > 0:
		logger.info(f"Failed to download {len(fails)} articles:")
		for fail in fails:
			logger.info(f"  - '{fail}'")
	logger.info(f"Fails ({len(fails)}): {fails}")


if __name__ == "__main__":
	main()
	logger.info("Done.")
