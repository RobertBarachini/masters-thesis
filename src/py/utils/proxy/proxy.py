import os
import time
import json
import random
import subprocess
from typing import Optional
import requests
import concurrent.futures

# Constants and global variables
default_provider = "geonode"
default_protocols = ["http", "https", "socks4", "socks5"]
filepath_geonode_dict = "src/py/utils/proxy/geonode/proxylist.json"


def run_geonode_update_list() -> subprocess.Popen:
	'''
		Runs the update_list.py script
	'''
	process = subprocess.Popen(
	    ["python", "src/py/utils/proxy/geonode/update_list.py"],
	    stdout=subprocess.PIPE,
	    stderr=subprocess.PIPE,
	    shell=False,
	    universal_newlines=True)
	return process


# TODO: launch a process in the background and just read the file if it exists
# if it doesn't exist wait for up to 20 seconds (poll rate = 0.1s) and then proceed
# quicker (0.007 seconds vs 1.382 seconds) but may get the outdated list the first time around
# maybe also check the info file to see when the list was last updated and still wait for the process to finish
# if it was updated less than 60 minutes ago
def get_geonode_list() -> Optional[list]:
	'''
		Returns a list of proxies from geonode.com
	'''
	if os.path.exists(filepath_geonode_dict):
		# just read the file
		geonode_data = {}
		with open(filepath_geonode_dict, "r") as f:
			geonode_data = json.load(f)
		# start the process and don't wait for it to finish so it
		# tries to update the list in the background
		process = run_geonode_update_list()
		# return the list of proxies
		return geonode_data["data"]
	# run update_list.py to ensure that the list is up to date
	process = run_geonode_update_list()
	# wait for the process to finish
	process.wait()
	# if there is no file, return None
	if not os.path.exists(filepath_geonode_dict):
		return None
	# load the file
	geonode_data = {}
	with open(filepath_geonode_dict, "r") as f:
		geonode_data = json.load(f)
	# return the list of proxies
	return geonode_data["data"]


def match_protocols(proxy_protocols: list, accepted_protocols: list) -> bool:
	'''
		Checks if the any proxy protocols match the any accepted protocols
	'''
	for protocol in proxy_protocols:
		if protocol in accepted_protocols:
			return True
	return False


def get_geonode_proxies(count: int = 1,
                        protocols: list = ["http", "https"]) -> Optional[list]:
	'''
		Gets a select number of appropriate proxies from the list of geonode proxies
	'''
	# get the list of proxies
	geonode_list = get_geonode_list()
	if geonode_list is None:
		return None
	# filter out by protocols
	geonode_list = [
	    proxy for proxy in geonode_list
	    if match_protocols(proxy["protocols"], protocols)
	]
	# filter out by latency (1000 ms)
	geonode_list = [proxy for proxy in geonode_list if proxy["latency"] < 1000]
	if len(geonode_list) == 0:
		return None
	# from the list pick count proxies at random
	geonode_list = random.sample(geonode_list, min(count, len(geonode_list)))
	# return the list of proxies
	return geonode_list


def test_get_geonode_proxies():
	'''
		Tests the get_geonode_proxies function
	'''
	print(f"Getting 10 proxies from geonode.com...")
	time_start = time.time()
	proxies = get_geonode_proxies(10)
	time_end = time.time()
	if proxies is None:
		print("Could not get proxies from geonode.com")
	else:
		print(
		    f"Got {len(proxies)} proxies from geonode.com in {round(time_end - time_start, 3)} seconds"
		)


# This is the more generic function that will be used to get proxies when importing this module
def get_proxies(count: int = 1,
                protocols: list = default_protocols,
                provider: str = default_provider) -> Optional[list]:
	'''
		Gets a select number of appropriate proxies from the list of proxies for the specified provider
	'''
	# TODO: standardize the fileds of a proxy object in the list:
	# ip, port, ... most common fields + some extra for the provider
	# TODO: async call to multiple providers and return select one, otherwise return any available
	if provider == "geonode":
		return get_geonode_proxies(count, protocols=protocols)


def test_get_proxies():
	'''
		Tests the get_proxies function
	'''
	print(f"Getting 10 proxies")
	time_start = time.time()
	proxies = get_proxies(10)
	time_end = time.time()
	if proxies is None:
		print("Could not get proxies")
	else:
		print(
		    f"Got {len(proxies)} proxies in {round(time_end - time_start, 3)} seconds"
		)


def make_request(url: str, proxy: dict, timeout: float = 5.0) -> Optional[int]:
	'''
		Makes a request to the specified url using the specified proxy
	'''
	proxies = {}
	# if "http" in proxy["protocols"]:
	# 	proxies["http"] = f"http://{proxy['ip']}:{proxy['port']}"
	# if "https" in proxy["protocols"]:
	# 	proxies["https"] = f"https://{proxy['ip']}:{proxy['port']}"
	proxies["http"] = f"http://{proxy['ip']}:{proxy['port']}"
	# proxies["https"] = f"https://{proxy['ip']}:{proxy['port']}"
	try:
		response = requests.get(url, proxies=proxies, timeout=timeout)
		print(f"Text:\n{response.text}")
		return response.status_code
	except Exception as e:
		print(f"Error making request to '{url}' using proxy {proxy}: {e}")
		return None


# TODO: track proxy stats: how often it's used, latency, number of requests, successes, failures, etc.
def get_working_proxy(
    test_url: str,
    expected_status_code: int = 200,
    timeout: float = 5.0,
    count: int = 5,  # number of proxies to try
    protocols: list = default_protocols,
    provider: str = default_provider) -> Optional[dict]:
	'''
		Gets a random working proxy from the list of proxies for the specified provider
	'''
	# get the list of proxies
	proxies = get_proxies(count, provider=provider, protocols=protocols)
	if proxies is None:
		return None
	# in parallel make requests to the test_url using each proxy and save the results in a list
	results = []
	with concurrent.futures.ThreadPoolExecutor(max_workers=count) as executor:
		time_start = time.time()
		results = executor.map(
		    lambda proxy: make_request(test_url, proxy, timeout), proxies)
		time_end = time.time()
		print(
		    f"Made {count} requests in {round(time_end - time_start, 3)} seconds")
		for result in results:
			print(result)
		a = 0
	# filter out the proxies that did not return the expected status code


def test_get_working_proxy():
	'''
		Tests the get_working_proxy function
	'''
	print(f"Getting a working proxy")
	time_start = time.time()
	url = "https://pangoly.com/en/"
	proxy = get_working_proxy(url,
	                          200,
	                          5.0,
	                          5,
	                          protocols=["socks5"],
	                          provider="geonode")
	time_end = time.time()
	if proxy is None:
		print("Could not get working proxy")
	else:
		print(
		    f"Got working proxy {proxy} in {round(time_end - time_start, 3)} seconds"
		)


def get_public_ip(proxy: Optional[dict] = None) -> Optional[str]:
	'''
		Gets the public IP of the machine
	'''
	try:
		proxies = {}
		if proxy is not None:
			proxies["http"] = f"http://{proxy['ip']}:{proxy['port']}"
			proxies["https"] = f"https://{proxy['ip']}:{proxy['port']}"
		response = requests.get("https://api.ipify.org",
		                        proxies=proxies,
		                        timeout=2.0)
		return response.text
	except Exception as e:
		# print(f"Error getting public IP: {e}")
		return None


def is_proxy_anonymus(proxy: dict, public_ip: str) -> bool:
	'''
		Checks if the specified proxy is anonymus
	'''
	proxied_ip = get_public_ip(proxy)
	if proxied_ip is None:
		print(f"Could not get proxied IP for proxy with _id = '{proxy['_id']}'")
		return False
	return proxied_ip != public_ip


def get_anonymous_proxies_geonode() -> Optional[list]:
	'''
		Gets a list of anonymous proxies from geonode.com
	'''
	proxies = get_geonode_list()
	if proxies is None:
		return None
	public_ip = get_public_ip()
	if public_ip is None:
		return None
	print(f"Public IP: {public_ip}")
	anonymous_proxies = []
	for i, proxy in enumerate(proxies):
		print(f"Checking proxy {i + 1} of {len(proxies)}")
		is_anonymous = is_proxy_anonymus(proxy, public_ip)
		if is_anonymous:
			print(f"Proxy with _id = '{proxy['_id']}' is anonymous")
			anonymous_proxies.append(proxy)
		else:
			print(f"Proxy with _id = '{proxy['_id']}' is NOT anonymous")
	# save to file (same as filepath_geonode_dict but replace .json with _anonymous.json)
	filepath = filepath_geonode_dict.replace(".json", "_anonymous.json")
	with open(filepath, "w") as f:
		json.dump(proxies, f, indent=2)
	return anonymous_proxies


def test_get_anonymous_proxies_geonode():
	'''
		Tests the get_anonymous_proxies_geonode function
	'''
	print(f"Getting anonymous proxies from geonode.com")
	time_start = time.time()
	proxies = get_anonymous_proxies_geonode()
	time_end = time.time()
	if proxies is None:
		print("Could not get proxies from geonode.com")
	else:
		print(
		    f"Got {len(proxies)} anonymous proxies from geonode.com in {round(time_end - time_start, 3)} seconds"
		)


if __name__ == "__main__":
	# test_get_geonode_proxies()
	# test_get_proxies()
	# test_get_working_proxy()
	test_get_anonymous_proxies_geonode()
	print("ALL DONE")