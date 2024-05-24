# Script responsible for updating the list of proxies from geonode.com
# If the list was updated less than an hour ago, it will not update it again

import os
import sys
import json
import requests
import time

# Project imports
sys.path.append(os.getcwd())
from src.py.utils.logger import Logger

# Sourced from https://geonode.com/free-proxy-list
geonode_list_url = "https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=speed&sort_type=asc&anonymityLevel=elite&anonymityLevel=anonymous"
geonode_output_path = "src/py/utils/proxy/geonode/proxylist.json"
info_filepath = "src/py/utils/proxy/geonode/update_list.json"
info = {}

# Load logger
logger = Logger({"filepath": "logs/geonode/update_list.log", "level": "DEBUG"})


def save_info():
	'''
		Saves the info file
	'''
	logger.say(f"Saving info file to '{info_filepath}'")
	with open(info_filepath, "w") as f:
		json.dump(info, f, indent="\t")
	logger.say(f"Successfully saved info file: {info}")


def load_info() -> dict:
	'''
		Loads the info file
	'''
	global info
	if not os.path.exists(info_filepath):
		logger.say(f"Info file does not exist - creating it with default values")
		info = {
		    "last_updated": 0,
		}
		save_info()
	else:
		logger.say(f"Loading info file from '{info_filepath}'")
		with open(info_filepath, "r") as f:
			info = json.load(f)
		logger.say(f"Successfully loaded info file: {info}")
	return info


def get_geonode_proxies(url: str = geonode_list_url) -> dict:
	'''
		Returns a list of proxies from geonode.com
	'''
	logger.say(f"Getting proxies from '{url}'")
	response = requests.get(
	    url,
	    timeout=60,
	    # User agent is required to get a response...
	    headers={
	        "User-Agent":
	            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
	    })
	logger.say(f"Response: {response.status_code}")
	if response.status_code != 200:
		logger.say(f"Failed to get proxies from '{url}'")
		sys.exit(1)
	logger.say(f"Loading response as JSON")
	proxies = json.loads(response.text)
	logger.say(f"Successfully loaded response as JSON")
	return proxies


def save_geonode_proxies(proxies: dict, path: str = geonode_output_path):
	'''
		Saves a list of proxies to a file
	'''
	logger.say(f"Saving proxies to '{path}'")
	with open(path, "w") as f:
		json.dump(proxies, f)
	logger.say(f"Successfully saved proxies to {path}")


if __name__ == "__main__":
	# Load info file
	load_info()
	# Check if we need to update
	if time.time() - info["last_updated"] < 3600 and os.path.exists(
	    geonode_output_path):
		logger.say(
		    f"Geonode proxies were updated less than an hour ago - skipping update"
		)
		sys.exit(0)
	# Get proxies
	proxies = get_geonode_proxies()
	# Save proxies
	save_geonode_proxies(proxies)
	# Update info file
	info["last_updated"] = time.time()
	save_info()
	logger.say(f"Successfully updated geonode proxies")