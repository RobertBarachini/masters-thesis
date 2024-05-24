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

# Globals
debug = False
if debug is True:
	sys.argv = [
	    sys.argv[0], "54a81ab5-de2b-410c-8615-222d817e04f9",
	    "aaxa-p7-plus-with-solar-projector-review-tv-off-the-grid"
	]
script_path = os.path.dirname(os.path.realpath(__file__))
output_path_root = "data/scraped/cnet/articles/html"
article_id = ""
article_slug = ""
logger = Logger({"typeinit": True})
logger = Logger({
    "filepath":
        os.path.join(
            *["data/scraped/cnet", "logs", "tasks", f"{sys.argv[1]}.log"]),
    "level":
        "DEBUG",
})
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
session = requests.Session()
session.headers.update({"User-Agent": user_agent})


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
		logger.error(f"Got exception: {e}")
		return None, f"Got exception: {e}"


def download_article():
	'''
		Downloads an article
	'''
	output_path = os.path.join(output_path_root, f"{article_id}.html")
	if os.path.exists(output_path):
		logger.info(f"Article '{article_id}' already exists. Skipping...")
		return
	if not os.path.exists(output_path_root):
		os.makedirs(output_path_root)
	url = f"https://www.cnet.com/news/{article_slug}"
	logger.info(f"Downloading article '{article_id}'...")
	data, error = get_data(url)
	if error is not None:
		logger.error(f"Failed to download article '{article_id}'!")
		sys.exit(1)
	assert data is not None
	with open(output_path, "w", encoding="utf-8") as f:
		f.write(data)
	logger.info(f"Downloaded article and saved it.")


def load_args():
	if len(sys.argv) != 3:
		logger.error("Received invalid number of arguments!")
		sys.exit(1)
	global article_id, article_slug
	article_id = sys.argv[1]
	article_slug = sys.argv[2]
	logger.info("Received arguments:")
	logger.info(f"Article ID: '{article_id}'")
	logger.info(f"Article slug: '{article_slug}'")


def main():
	'''
		Main entrypoint
	'''
	logger.info("Starting...")
	load_args()
	download_article()


if __name__ == "__main__":
	main()
	logger.info("Done.")
