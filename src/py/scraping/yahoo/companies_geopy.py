import os
import sys
import json
import time
# from geopy.geocoders import Nominatim
from geopy.geocoders import GoogleV3
from typing import Tuple

# Project imports
sys.path.append(os.getcwd())
from src.py.utils.logger import Logger

# Globals
path_index = "data/scraped/yahoo/sectors/index_stocks.json"
output_path_root = "data/scraped/yahoo"
script_path = os.path.dirname(os.path.realpath(__file__))
stop_path = os.path.join(script_path,
                         "stop")  # if this file exists, stop scraping
index = []
fails = []
logger = Logger({
    "filepath":
        os.path.join(*[output_path_root, "logs", "companies_geopy.log"]),
    "level":
        "DEBUG",
})
user_agent = "Thesis/Barachini"  # Nominatim requires a "custom" user agent
# minimum_time_per_iteration = 1.0  # requires no more than 1 request per second
# Google's default limit is 3000 requests per minute (50 per second)
minimum_time_per_iteration = (1.0 / 50.0) * 2  # 25 requests per second
# geolocator = Nominatim(user_agent=user_agent)
geolocator = GoogleV3(api_key=os.environ["GOOGLE_MAPS_PLATFORM_API_KEY"])
# geo_field_name = "geo"
geo_field_name = "geo_google"


def save_index():
	'''
		Saves the index to a file
	'''
	logger.info(f"Saving index...")
	with open(path_index, "w") as f:
		json.dump(index, f, indent=2)
	logger.info(f"Index saved.")


def load_index():
	'''
		Loads the index from a file
	'''
	global index
	logger.info(f"Loading index from '{path_index}'...")
	if not os.path.exists(path_index):
		logger.error(f"Index file not found: '{path_index}'")
		sys.exit(1)
	with open(path_index, "r") as f:
		index = json.load(f)
		logger.info(f"Index loaded successfully ({len(index)} companies).")


def get_geodata(address: str) -> Tuple[dict, None] | Tuple[None, str]:
	'''
		Returns a dict with the geodata for the given address
	'''
	try:
		address = address.replace("\n", ", ")
		location = geolocator.geocode(address)
		assert location is not None, "Location is None"
		address = location.address  # type: ignore
		latitude = location.latitude  # type: ignore
		longitude = location.longitude  # type: ignore
		country = address.split(",")[-1].strip()
		result = {
		    "address": address,
		    "latitude": latitude,
		    "longitude": longitude,
		    "country": country,
		}
		return result, None
	except Exception as e:
		return None, str(e)


def wait_iteration(time_start: float):
	'''
		Waits for the minimum time per iteration
	'''
	time_end = time.time()
	time_elapsed = time_end - time_start
	if time_elapsed < minimum_time_per_iteration:
		wait_time = minimum_time_per_iteration - time_elapsed + 0.05
		time.sleep(wait_time)
		logger.info(f"Time iteration: {time_elapsed:.2f} (waited {wait_time:.2f})")
	else:
		logger.info(f"Time iteration: {time_elapsed:.2f}")
	logger.info("")


def add_data():
	logger.info("Adding data...")
	time_start_total = time.time()
	for i, company in enumerate(index):
		if os.path.exists(stop_path):
			logger.info("Stop file found, gracefully stopping...")
			logger.info("")
			break
		time_start_loop = time.time()
		try:
			logger.info(f"Company {i+1}/{len(index)} ({company['symbol']})")
			if geo_field_name in company["profile"]:
				logger.info("Already has geo data, skipping...")
				logger.info("")
				continue
			# Get geodata
			logger.info("Getting geodata...")
			geodata, error = get_geodata(company["profile"]["address"])
			if error is not None:
				logger.error(f"Unable to get geodata: '{error}'")
				fails.append((company, error))
				wait_iteration(time_start_loop)
				continue
			# Add geodata to company
			company["profile"][geo_field_name] = geodata
			wait_iteration(time_start_loop)
		except Exception as e:
			logger.error(f"Error getting geodata: '{e}'")
			fails.append((company, str(e)))
			wait_iteration(time_start_loop)
			continue
	time_end_total = time.time()
	logger.info("")
	save_index()
	logger.info(
	    f"Total time elapsed: {time_end_total - time_start_total:.2f} seconds")


def print_fails():
	if len(fails) > 0:
		logger.info(f"The following symbols failed to scrape ({len(fails)}):")
		for fail in fails:
			company, error = fail
			logger.info(f"  - {company['symbol']}: '{error}'")


def main():
	load_index()
	add_data()
	print_fails()


if __name__ == "__main__":
	main()
	logger.info("Done!")
