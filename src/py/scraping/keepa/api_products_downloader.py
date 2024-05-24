import os
import sys
import json
import time
import requests
from datetime import datetime
from typing import Optional, Tuple

# Project imports
sys.path.append(os.getcwd())
from src.py.utils.generic_utils import wrapper
from src.py.utils.logger import Logger

#
'''
	Constants and global variables
'''
path_parsed_products = "data/scraped/camel/parsed-products.json"
path_output_root = "data/keepa/products/domains"
api_key = os.environ.get('KEEPA_API_KEY')
api_url = "https://api.keepa.com"
domains = [1, 3, 2]  # list of domain IDs to retrieve products for
logger = Logger({"typeinit": True})
min_tokens = 5  # minimum number of tokens needed to ensure we can make a full request - used to calculate wait time
# in our case 1 request consumes 1-2 tokens, so 5 gives us a margin of 2 extra requests which ensures
# we always have enough tokens to make a full request


def get_token_status() -> Tuple[dict, None] | Tuple[None, Exception]:
	'''
		Retrieves token status from Keepa API

		More info: https://keepa.com/#!discuss/t/retrieve-token-status/1305
	'''
	response, err = wrapper(requests.get,
	                        f"{api_url}/token",
	                        params={"key": api_key})
	if err:
		return None, err
	assert response is not None
	if response.status_code == 200:
		return response.json(), None
	return None, Exception(f"Error: {response.status_code}")


def get_products_reponse(
    asin: str,
    domain_id: int,
    stats: Optional[Tuple[str, str]] = ("2011-01-01", "2025-01-01"),
    history: bool = True,
    rating: bool = True) -> Tuple[dict, None] | Tuple[None, Exception]:
	'''
		Retrieves product information from Keepa API

		More info: https://keepa.com/#!discuss/t/request-products/110

		Args:
			asin: Amazon Standard Identification Number
			domain_id: Amazon domain ID - Valid values: [ 1: com | 2: co.uk 231 | 3: de | 4: fr | 5: co.jp | 6: ca | 8: it | 9: es | 10: in | 11: com.mx ]
			stats: Include product statistics
			history: Include product price history
			rating: Include product rating history
		Returns:
			Product information
	'''
	params = {
	    "key": api_key,
	    "domain": domain_id,
	    "asin": asin,
	    "history": 1 if history is True else 0,
	    "rating": 1 if rating is True else 0
	}
	if stats:
		params["stats"] = f"{stats[0]},{stats[1]}"
	# response, err = wrapper(requests.get, f"{api_url}/product", params=params)
	# timeout 60 seconds, retry 3 times
	response, err = wrapper(requests.get,
	                        f"{api_url}/product",
	                        params=params,
	                        timeout=60)
	# TODO: implement retries
	if err:
		return None, err
	assert response is not None
	if response.status_code == 200:
		response_json = response.json()
		return response_json, None
	return None, Exception(f"Error: {response.status_code}")


def init_logger():
	'''
	Initializes the logger
	'''
	global logger
	logger = Logger({
	    "filepath":
	        os.path.join(
	            *["data", "keepa", "logs", "api_products_downloader.log"]),
	    "level":
	        "DEBUG",
	})


def get_products_json() -> dict:
	'''
		Retrieves parsed products JSON
	'''
	with open(path_parsed_products, "r") as f:
		return json.load(f)


def check_requirements():
	if api_key is None:
		err_msg = "Error: KEEPA_API_KEY environment variable not set"
		logger.error(err_msg)
		raise Exception(err_msg)
	if not os.path.exists(path_parsed_products):
		err_msg = f"Error: File '{path_parsed_products}' not found"
		logger.error(err_msg)
		raise Exception(err_msg)


def log_settings():
	logger.info(f"")
	logger.info(f"Settings:")
	logger.info(f"  path_parsed_products: '{path_parsed_products}'")
	logger.info(f"  path_output_root: '{path_output_root}'")
	logger.info(f"  api_url: '{api_url}'")
	logger.info(f"  domains: '{domains}'")
	logger.info(f"  min_tokens: '{min_tokens}'")
	logger.info(f"")


def init():
	init_logger()
	log_settings()
	check_requirements()
	logger.info("Init done.")


def get_info_object(product_response: dict) -> dict:
	'''
		Retrieves the info object from the product response
	'''
	info_obj = {}
	for k, v in product_response.items():
		if k != "products":
			info_obj[k] = v
	if "products" in product_response:
		if product_response["products"]:
			info_obj["products_count"] = len(product_response["products"])
		else:
			info_obj["products_count"] = 0
	return info_obj


def get_wait_time(info_object: dict, min_tokens: int = min_tokens) -> int:
	'''
		Retrieves the wait time in milliseconds
	'''
	timestamp = info_object["timestamp"]
	tokens_left = info_object["tokensLeft"]
	refill_in = info_object["refillIn"]  # milliseconds, maximum is 60000
	refill_rate = info_object["refillRate"]
	wait_till = timestamp + refill_in
	tokens_left += refill_rate
	refill_in = 60000
	max_iterations = 10
	iterations = 0
	while tokens_left < min_tokens:
		tokens_left += refill_rate
		wait_till += refill_in
		iterations += 1
		if iterations >= max_iterations:
			logger.warning(
			    f"Max iterations reached in get_wait_time: {max_iterations} - check if this is correct"
			)
			break
	safety_margin = 1000  # milliseconds to wait after refill (just in case our clocks are not in sync)
	return wait_till - timestamp + safety_margin


def get_all(domain_id: int):
	'''
		Retrieves all products information from Keepa API
	'''
	logger.info(
	    f"Retrieving all specified products from Keepa API for domain_id={domain_id}"
	)
	# Create output directory for specified domain
	path_output_domain = os.path.join(path_output_root, f"{domain_id}")
	if not os.path.exists(path_output_domain):
		logger.info(f"Creating directory: '{path_output_domain}'")
		os.makedirs(path_output_domain)
	# Retrieve all products
	logger.info(f"Retrieving product definitions from '{path_parsed_products}'")
	products = get_products_json()
	logger.info(f"Retrieved {len(products)} product definitions")
	logger.info("")
	for i, asin in enumerate(products):
		time_start = time.time()
		logger.info(
		    f"Processing product {i + 1} of {len(products)} for domain_id={domain_id}"
		)
		path_product = os.path.join(path_output_domain, f"{asin}.json")
		if os.path.exists(path_product):
			logger.info(f"Product '{asin}' already processed - skipping")
			continue
		product_definition = products[asin]
		logger.info(
		    f"Product definition: {json.dumps(product_definition, indent=2)}")
		product_response, err = get_products_reponse(asin,
		                                             domain_id,
		                                             history=True,
		                                             rating=True)
		if err:
			logger.error(f"Error: {err}")
			with open(path_product, "w") as f:
				logger.info(f"Writing empty product response to '{path_product}'")
				err_json = {"error": str(err)}
				json.dump(err_json, f)
				logger.info(f"Done writing empty product response")
				logger.info(f"Sleeping for 60 seconds")
				time.sleep(60)
				logger.info("")
			continue
		assert product_response is not None
		info_obj = get_info_object(product_response)
		logger.info(f"Info object: {json.dumps(info_obj, indent=2)}")
		with open(path_product, "w") as f:
			logger.info(f"Writing product response to '{path_product}'")
			json.dump(product_response, f)  #, indent=2)
			logger.info(f"Done writing product response")
		wait_time = 0
		if info_obj["tokensLeft"] < min_tokens:
			wait_time = get_wait_time(info_obj)
			datetime_at_restart = datetime.fromtimestamp((info_obj["timestamp"] /
			                                              1000) + (wait_time / 1000))
			logger.info(
			    f"Waiting {wait_time} milliseconds for tokens to refill - resuming at {datetime_at_restart}"
			)
			time.sleep(wait_time / 1000)
		time_end = time.time()
		time_elapsed = time_end - time_start
		logger.info(
		    f"Processing time for product '{asin}': {time_elapsed} seconds ; {wait_time} milliseconds of which was waiting for tokens to refill"
		)
		logger.info("")


def get_all_domains():
	'''
		Iterates over all specified domains and retrieves all products information from Keepa API for each domain
	'''
	for domain_id in domains:
		get_all(domain_id)


def main():
	init()
	get_all_domains()


if __name__ == "__main__":
	main()
	logger.info(f"All done!")
