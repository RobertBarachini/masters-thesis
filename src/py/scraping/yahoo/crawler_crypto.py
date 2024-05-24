import os
import sys
import json
import time
import random
import requests
from typing import Tuple
from bs4 import BeautifulSoup
from datetime import datetime

# Project imports
sys.path.append(os.getcwd())
from src.py.utils.generic_utils import wrapper

# Example url: "https://finance.yahoo.com/crypto?count=100&offset=0

base_url = "https://finance.yahoo.com/crypto"
count = 100  # number of items per page
offset = 0  # item offset
path_output = "data/scraped/yahoo/crypto/index.json"
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"


def get_page(url: str,
             offset: int = 0,
             count: int = 100) -> Tuple[str, None] | Tuple[None, Exception]:
	'''
	Get the HTML page from the given url
	:param url: Url to get the page from
	:param offset: Offset for the url
	:param count: Count for the url
	:return: HTML page as string
	'''
	params = {'count': count, 'offset': offset}
	headers = {'User-Agent': user_agent}
	response, error = wrapper(requests.get, url, params=params, headers=headers)
	if error:
		return None, error
	assert response is not None
	if response.status_code != 200:
		return None, Exception(f"Status code {response.status_code}")
	return response.text, None


def scrape_page(page_index: int) -> Tuple[list, None] | Tuple[None, Exception]:
	'''
	Scrape the given page index
	Returns a list of urls
	'''
	page, error = get_page(base_url, offset=page_index * count, count=count)
	if error:
		return None, error
	assert page is not None
	# Get div with id=scr-res-table
	soup = BeautifulSoup(page, 'html.parser')
	div = soup.find('div', {'id': 'scr-res-table'})
	# Get all <a> tags where data-test="quoteLink"
	if div is None:
		return None, Exception("Could not find div with id=scr-res-table")
	a_tags = div.find_all('a', {'data-test': 'quoteLink'})  # type: ignore
	urls = []
	for a_tag in a_tags:
		urls.append(a_tag['href'])
	return urls, None


def save_results(urls: list, time_start: datetime):
	'''
	Saves results to file
	'''
	time_end = datetime.now()
	if not os.path.exists(os.path.dirname(path_output)):
		os.makedirs(os.path.dirname(path_output))
	output_object = {
	    "time_start": str(time_start),
	    "time_end": str(time_end),
	    "urls": urls,
	}
	with open(path_output, 'w') as f:
		json.dump(output_object, f, indent=2)


def scrape_all():
	'''
	Scrape all pages
	'''
	time_start = datetime.now()
	print(f"Starting scraping at {time_start}")
	all_urls = []
	for page_index in range(
	    100
	):  # set to some "big" number like 100 - realistically there are only 89 pages if count=100
		time.sleep(random.uniform(0.5, 1.5))
		loop_start = time.time()
		print(f"Scraping page {page_index}")
		urls, error = scrape_page(page_index)
		if error:
			print(f"Error scraping page {page_index}: {error}")
			print()
			continue
		assert urls is not None
		all_urls.extend(urls)
		if len(urls) != count:
			print(
			    f"Finished scraping page {page_index} - last page reached, exiting loop"
			)
			print()
			break
		loop_end = time.time()
		print(
		    f"Finished scraping page {page_index} in {loop_end - loop_start} seconds"
		)
		print()
		if page_index % 5 == 0:
			print(f"Saving results to file")
			save_results(all_urls, time_start)
			print(f"Finished saving results to file")
			print()
	time_end = datetime.now()
	print(
	    f"Scraped {len(all_urls)} urls in {(time_end - time_start).total_seconds} seconds"
	)
	print()
	print("Writing finished results to a file")
	save_results(all_urls, time_start)
	print("Finished writing to file")


def main():
	scrape_all()


if __name__ == "__main__":
	main()
	print("ALL DONE!")
