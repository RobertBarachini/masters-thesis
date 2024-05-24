import os
import sys
import json
import time
import random
from urllib.parse import quote
from datetime import datetime
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from seleniumwire.request import Request, Response
from seleniumwire.webdriver import Remote as TypeWebDriver, FirefoxProfile

load_dotenv()

# Project imports
sys.path.append(os.getcwd())
from src.py.utils.scraping.selenium_utils import init_driver, get_element_by, get_options_firefox, type_text, get_element_by_race, install_ublockorigin_firefox
from src.py.utils.logger import Logger

# Constants
script_location = os.path.dirname(os.path.realpath(__file__))
profile_name_path = os.path.join(
    *[script_location, "firefox_profile_yahoo.txt"])
domain = "finance.yahoo.com"
main_page_url = "https://finance.yahoo.com/sectors"
all_sectors_data = {}
output_path_root = "data/scraped/yahoo/sectors"
all_sectors_data_path = os.path.join(*[output_path_root, "all_sectors.json"])
WEBDRIVER_BROWSER = os.getenv("WEBDRIVER_BROWSER")
logger = Logger({"typeinit": True})
driver: TypeWebDriver = None  # type: ignore
is_waiting_for_response = False
blocked_domains = [
    # Main page
    "https://m.media-amazon.com",
    "https://cmp.inmobi.com",
    "doubleclick.net",
    "amazon-adsystem.com",
    "lijit.com",
    "cdn.adfirst.media",
    "cmp.quantcast.com",
    # "s.yimg.com/oa/build/css/",
    # "finance.yahoo.com/assets/_app/immutable/assets/",
    # "s.yimg.com/cv/apiv2/finance/fonts/",
    # "s.yimg.com/ok/u/assets/img/",
    # "s.yimg.com/uc/finance/dd-site/modules/css/",
    "googletagservices",
    ".woff",
    ".woff2",
    # ".svg",
    # ".webp",
    # ".gif",
    # ".png",
    "streamer.finance"
]

# Locators
LOCATOR_COOKIES = (By.CSS_SELECTOR, "button.btn:nth-child(5)")
# All sectors
LOCATOR_SECTORS_SECTORS_COUNT = (
    By.CSS_SELECTOR,
    "#nimbus-app > section > section > section > article > section.top.svelte-17rbjcy > section.svelte-e2k9sg > div.block.svelte-e2k9sg > div.content.col.svelte-e2k9sg > div:nth-child(1) > div.value.svelte-e2k9sg"
)
LOCATOR_SECTORS_INDUSTRIES_COUNT = (
    By.CSS_SELECTOR,
    "#nimbus-app > section > section > section > article > section.top.svelte-17rbjcy > section.svelte-e2k9sg > div.block.svelte-e2k9sg > div.content.col.svelte-e2k9sg > div:nth-child(2) > div.value.svelte-e2k9sg"
)
LOCATOR_SECTORS_MARKET_CAP = (
    By.CSS_SELECTOR,
    "#nimbus-app > section > section > section > article > section.top.svelte-17rbjcy > section.svelte-e2k9sg > div.block.svelte-e2k9sg > div.content.col.svelte-e2k9sg > div:nth-child(3) > div.value.svelte-e2k9sg"
)
LOCATOR_VISUAL_BREAKDOWN_TABLE_BODY = (
    By.CSS_SELECTOR,
    "#nimbus-app > section > section > section > article > section.top.svelte-17rbjcy > section:nth-child(2) > div > div > div:nth-child(1) > div > div.tableContainer.svelte-vatrz8 > table > tbody"
)
# Sector
LOCATOR_SECTOR_MARKET_CAP = (
    By.CSS_SELECTOR,
    "#nimbus-app > section > section > section > article > section.top.svelte-tkxuml > div > section > div.block.svelte-e2k9sg > div.content.col.svelte-e2k9sg > div:nth-child(1) > div.value.svelte-e2k9sg"
)
LOCATOR_SECTOR_INDUSTRY_WEIGHT = (
    By.CSS_SELECTOR,
    "#nimbus-app > section > section > section > article > section.top.svelte-tkxuml > div > section > div.block.svelte-e2k9sg > div.content.col.svelte-e2k9sg > div:nth-child(2) > div.value.svelte-e2k9sg"
)
LOCATOR_SECTOR_INDUSTRIES_COUNT = (
    By.CSS_SELECTOR,
    "#nimbus-app > section > section > section > article > section.top.svelte-tkxuml > div > section > div.block.svelte-e2k9sg > div.content.col.svelte-e2k9sg > div:nth-child(3) > div.value.svelte-e2k9sg"
)
LOCATOR_SECTOR_COMPANIES_COUNT = (
    By.CSS_SELECTOR,
    "#nimbus-app > section > section > section > article > section.top.svelte-tkxuml > div > section > div.block.svelte-e2k9sg > div.content.col.svelte-e2k9sg > div:nth-child(4) > div.value.svelte-e2k9sg"
)
LOCATOR_VISUAL_BREAKDOWN_TABLE_BODY_SECTOR = (
    By.CSS_SELECTOR, "table.svelte-vatrz8 > tbody:nth-child(2)")
# Industry
LOCATOR_INDUSTRY_MARKET_CAP = (
    By.CSS_SELECTOR,
    "#nimbus-app > section > section > section > article > section.top.svelte-tkxuml > div > section > div.block.svelte-e2k9sg > div.content.col.svelte-e2k9sg > div:nth-child(1) > div.value.svelte-e2k9sg"
)
LOCATOR_INDUSTRY_INDUSTRY_WEIGHT = (
    By.CSS_SELECTOR,
    "#nimbus-app > section > section > section > article > section.top.svelte-tkxuml > div > section > div.block.svelte-e2k9sg > div.content.col.svelte-e2k9sg > div:nth-child(2) > div.value.svelte-e2k9sg"
)
LOCATOR_INDUSTRY_COMPANIES_COUNT = (
    By.CSS_SELECTOR,
    "#nimbus-app > section > section > section > article > section.top.svelte-tkxuml > div > section > div.block.svelte-e2k9sg > div.content.col.svelte-e2k9sg > div:nth-child(3) > div.value.svelte-e2k9sg"
)
LOCATOR_INDUSTRY_EMPLOYEES_COUNT = (
    By.CSS_SELECTOR,
    "#nimbus-app > section > section > section > article > section.top.svelte-tkxuml > div > section > div.block.svelte-e2k9sg > div.content.col.svelte-e2k9sg > div:nth-child(4) > div.value.svelte-e2k9sg"
)
LOCATOR_INDUSTRY_COMPANIES_LINK = (
    By.CSS_SELECTOR,
    "#nimbus-app > section > section > section > article > section.container.svelte-ekgvwx > header > div > a"
)
# Companies
LOCATOR_PREDEFINED_SCREENER_TABLE_BODY = (
    By.CSS_SELECTOR,
    "#scr-res-table > div.Ovx\\(a\\).Ovx\\(h\\)--print.Ovy\\(h\\).W\\(100\\%\\) > table > tbody"
)


def ask_to_continue(default: bool = False):
	'''
	Asks the user if they want to resume the scraping
	'''
	global is_waiting_for_response
	resume_query = "y/N"
	if default:
		resume_query = "Y/n"
	is_waiting_for_response = True
	can_resume = input(f"Do you want to resume the scraping? ({resume_query}): ")
	is_waiting_for_response = False
	if can_resume.lower() == "y":
		return True
	elif can_resume.lower() == "n":
		return False
	else:
		return default


def wait_n_seconds(n: float):
	'''
	Waits for x seconds
	'''
	global is_waiting_for_response
	logger.info(f"Waiting for {n} seconds...")
	is_waiting_for_response = True
	time.sleep(n)
	is_waiting_for_response = False


def request_interceptor(request: Request):
	'''
	Intercepts the request and modifies it.
	'''
	# if "woff" in request.url:
	# 	print(f"> Request URL: {request.url}")
	for domain in blocked_domains:
		if domain in request.url:
			# logger.info(f"Blocking domain request: {request.url}")
			request.abort()
			# request.response = Response(
			#     request_id=request.id,
			#     body="",
			#     status_code=200,
			#     headers={},
			#     request=request,
			#     encoding="utf-8",
			# )
			return
	# block requests that have images
	content_type = request.headers.get("Content-Type")
	# print(content_type)
	if content_type:
		# print(f"content_type: {content_type}")
		if "image" in content_type or "audio" in content_type or "video" in content_type:
			# logger.info(f"Blocking image request: {request.url}")
			request.abort()


def response_interceptor(request: Request, response: Response):
	'''
	Intercepts the response and modifies it.
	'''
	# if response.status_code == 429:
	# 	logger.warning(
	# 	    f"\nWARNING!!! Rate limited (status code 429)! Confirm/wait to continue..."
	# 	)
	# 	# save the data
	# 	# can_continue = ask_to_continue(True)
	# 	wait_n_seconds(random.uniform(60, 120))
	if domain not in str(request.url):
		return
	if response.status_code == 429:
		logger.warning(
		    f"\nWARNING!!! Rate limited (status code 429)! Confirm/wait to continue..."
		)
		logger.info(f"Request URL: {request.url}")
		# save the data
		# can_continue = ask_to_continue(True)
		wait_n_seconds(random.uniform(10, 20))
		return
	# if response.status_code != 200:
	# 	logger.warning(f"\nResponse status code: {response.status_code}")
	# 	# can_continue = ask_to_continue(True)


def get_profile_path_firefox() -> str:
	'''
		Gets the path from the profile name
	'''
	profile_path = "/tmp/firefox_profile_thesis_yahoo"
	try:
		with open(profile_name_path, "r") as f:
			profile_path = f.read()
	except Exception as e:
		logger.info(f"File does not exist! ({profile_name_path})")
	return profile_path


def load_profile_firefox() -> FirefoxProfile:
	'''
		Loads a persisted profile
	'''
	profile_path = get_profile_path_firefox()
	try:
		logger.info(f"Loading profile from {profile_path}...")
		profile = FirefoxProfile(profile_path)
		logger.info(f"Loaded profile! - path:{profile.path}")  
		return profile
	except Exception as e:
		logger.error(f"Error: {e}")
		profile = FirefoxProfile()
		logger.info(f"Profile path: {profile.path}")
		profile.set_preference("permissions.default.image", 2)
		profile.update_preferences()
		logger.info("Created new profile!")
		# Save profile path to file
		with open(profile_name_path, "w") as f:
			f.write(str(profile.path))
		return profile


def init_driver_local():
	'''
	Initializes the driver
	'''
	global driver
	# Init driver
	logger.info(f"Initializing driver ({WEBDRIVER_BROWSER})...")
	options = get_options_firefox()
	options.headless = False
	options.set_capability("pageLoadStrategy", "eager")
	profile = load_profile_firefox()
	driver = init_driver(WEBDRIVER_BROWSER, options,
	                     profile=profile)  # type: ignore
	driver.request_interceptor = request_interceptor
	driver.response_interceptor = response_interceptor
	logger.info("Initialized driver!")
	get_ublock_origin()
	navigate_to_main_page()
	# Check the current page load strategy
	current_strategy = driver.capabilities["pageLoadStrategy"]
	logger.info(f"Current page load strategy: {current_strategy}")
	# Execute JavaScript to get performance timing information
	performance_timing = driver.execute_script(
	    "return window.performance.timing;")
	# convert all values from unix milliseconds to datetime
	performance_timing = {
	    key: datetime.fromtimestamp(value / 1000.0)
	    for key, value in performance_timing.items()
	}
	logger.info(
	    f"Performance timing:{json.dumps(performance_timing, indent=2, default=str)}"
	)
	accept_cookies()


def init_logger():
	'''
	Initializes the logger
	'''
	global logger
	logger = Logger({
	    "filepath": os.path.join(*["logs", "yahoo", "sectors.log"]),
	    "level": "DEBUG",
	})


def init():
	init_logger()
	init_driver_local()


def wait_indefinitely():
	while True:
		time.sleep(0.05)


def navigate_to_main_page():
	logger.info("Navigating to main page...")
	driver.get(main_page_url)


def accept_cookies():
	# Wait for cookies
	logger.info("Waiting for cookies...")
	cookies_button, cookies_button_err = get_element_by(
	    driver=driver,  # type: ignore
	    locator=LOCATOR_COOKIES,
	    timeout=20.0,
	    poll_frequency=0.1,
	    retries=0)
	if cookies_button_err:
		logger.error(f"Error: {cookies_button_err}")
	else:
		assert cookies_button
		logger.info("Clicking cookies button...")
		cookies_button.click()
		logger.info("Accepted cookies!")


def get_ublock_origin():
	# driver.get("https://addons.mozilla.org/en-US/firefox/addon/ublock-origin/")
	logger.info("Installing uBlock Origin...")
	install_ublockorigin_firefox(driver)  # type: ignore
	logger.info("Installed uBlock Origin...")
	# logger.info("Press continue when ready...")
	# can_continue = ask_to_continue(True)


def save_all_sectors_data():
	'''
	Saves the all sectors data
	'''
	global all_sectors_data
	logger.info("Saving all sectors data...")
	with open(all_sectors_data_path, "w") as f:
		json.dump(all_sectors_data, f, indent=2)
	logger.info("Saved all sectors data!")


def get_sectors() -> dict:
	'''
	Gets the sectors
	'''
	global all_sectors_data
	logger.info("Getting sectors...")
	all_sectors_data = {
	    "name": "All Sectors",
	    "url": main_page_url,
	    "date_created": datetime.utcnow().isoformat(),
	    "stats": {
	        "sectors_count": None,
	        "industries_count": None,
	        "market_cap": None,
	    },
	    "sectors": [],
	}
	# If url of the driver is not the main page, navigate to it
	if domain not in driver.current_url:
		navigate_to_main_page()
	# Get statistics (from header)
	sectors_count, sectors_count_err = get_element_by(
	    driver=driver,  # type: ignore
	    locator=LOCATOR_SECTORS_SECTORS_COUNT,
	    timeout=5.0,
	    poll_frequency=0.1,
	    retries=0)
	if sectors_count_err:
		logger.error(f"sectors_count_err: {sectors_count_err}")
	else:
		assert sectors_count
		sectors_count = sectors_count.text
		logger.info(f"Sectors count: {sectors_count}")
		all_sectors_data["stats"]["sectors_count"] = sectors_count
	industries_count, industries_count_err = get_element_by(
	    driver=driver,  # type: ignore
	    locator=LOCATOR_SECTORS_INDUSTRIES_COUNT,
	    timeout=5.0,
	    poll_frequency=0.1,
	    retries=0)
	if industries_count_err:
		logger.error(f"industries_count_err: {industries_count_err}")
	else:
		assert industries_count
		industries_count = industries_count.text
		logger.info(f"Industries count: {industries_count}")
		all_sectors_data["stats"]["industries_count"] = industries_count
	market_cap, market_cap_err = get_element_by(
	    driver=driver,  # type: ignore
	    locator=LOCATOR_SECTORS_MARKET_CAP,
	    timeout=5.0,
	    poll_frequency=0.1,
	    retries=0)
	if market_cap_err:
		logger.error(f"market_cap_err: {market_cap_err}")
	else:
		assert market_cap
		market_cap = market_cap.text
		logger.info(f"Market cap: {market_cap}")
		all_sectors_data["stats"]["market_cap"] = market_cap
	# Get sectors
	# Get table body
	table_body, table_body_err = get_element_by(
	    driver=driver,  # type: ignore
	    locator=LOCATOR_VISUAL_BREAKDOWN_TABLE_BODY,
	    timeout=5.0,
	    poll_frequency=0.1,
	    retries=0)
	if table_body_err:
		logger.error(f"table_body_err: {table_body_err}")
	else:
		assert table_body
		# Get rows
		rows = table_body.find_elements(By.TAG_NAME, "tr")
		logger.info(f"Found {len(rows)} rows!")
		# Iterate through rows
		for i, row in enumerate(rows):
			# Get columns
			cols = row.find_elements(By.TAG_NAME, "td")
			# Get sector name
			sector_name = cols[0].text
			logger.info(f"sector_name: {sector_name}")
			# Get sector url
			sector_url = f"https://finance.yahoo.com/sectors/{sector_name.lower().replace(' ', '-')}"
			logger.info(f"sector_url: {sector_url}")
			# Get market weight
			market_weight = cols[1].text
			logger.info(f"market_weight: {market_weight}")
			# Get day return
			day_return = cols[2].text
			logger.info(f"day_return: {day_return}")
			# Get YTD return
			ytd_return = cols[3].text
			logger.info(f"ytd_return: {ytd_return}")
			if i == 0:  # first row is all sectors
				all_sectors_data["stats"]["market_weight"] = market_weight
				all_sectors_data["stats"]["day_return"] = day_return
				all_sectors_data["stats"]["ytd_return"] = ytd_return
			else:
				sector_data = {
				    "name": sector_name,
				    "url": sector_url,
				    "stats": {
				        "market_cap": None,
				        "industry_weight": None,
				        "industries_count": None,
				        "companies_count": None,
				        "market_weight": market_weight,
				        "day_return": day_return,
				        "ytd_return": ytd_return,
				    },
				    "industries": [],
				}
				all_sectors_data["sectors"].append(sector_data)
	save_all_sectors_data()
	return all_sectors_data


def load_all_sectors_data():
	'''
	Loads the all sectors data
	'''
	global all_sectors_data
	logger.info("Loading all sectors data...")
	if os.path.exists(all_sectors_data_path):
		with open(all_sectors_data_path, "r") as f:
			all_sectors_data = json.load(f)
			logger.info("Loaded all sectors data!")
	else:
		logger.info(
		    f"File for all sectors data does not exist! ({all_sectors_data_path}) - starting from scratch!"
		)
		get_sectors()


def get_sector(sector: dict) -> dict:
	'''
	Gets the sector data
	'''
	driver.get(sector["url"])
	# Get statistics (from header)
	market_cap, market_cap_err = get_element_by(
	    driver=driver,  # type: ignore
	    locator=LOCATOR_SECTOR_MARKET_CAP,
	    timeout=5.0,
	    poll_frequency=0.1,
	    retries=0)
	if market_cap_err:
		logger.error(f"market_cap_err: {market_cap_err}")
	else:
		assert market_cap
		market_cap = market_cap.text
		logger.info(f"Market cap: {market_cap}")
		sector["stats"]["market_cap"] = market_cap
	industry_weight, industry_weight_err = get_element_by(
	    driver=driver,  # type: ignore
	    locator=LOCATOR_SECTOR_INDUSTRY_WEIGHT,
	    timeout=5.0,
	    poll_frequency=0.1,
	    retries=0)
	if industry_weight_err:
		logger.error(f"industry_weight_err: {industry_weight_err}")
	else:
		assert industry_weight
		industry_weight = industry_weight.text
		logger.info(f"Industry weight: {industry_weight}")
		sector["stats"]["industry_weight"] = industry_weight
	industries_count, industries_count_err = get_element_by(
	    driver=driver,  # type: ignore
	    locator=LOCATOR_SECTOR_INDUSTRIES_COUNT,
	    timeout=5.0,
	    poll_frequency=0.1,
	    retries=0)
	if industries_count_err:
		logger.error(f"industries_count_err: {industries_count_err}")
	else:
		assert industries_count
		industries_count = industries_count.text
		logger.info(f"Industries count: {industries_count}")
		sector["stats"]["industries_count"] = industries_count
	companies_count, companies_count_err = get_element_by(
	    driver=driver,  # type: ignore
	    locator=LOCATOR_SECTOR_COMPANIES_COUNT,
	    timeout=5.0,
	    poll_frequency=0.1,
	    retries=0)
	if companies_count_err:
		logger.error(f"companies_count_err: {companies_count_err}")
	else:
		assert companies_count
		companies_count = companies_count.text
		logger.info(f"Companies count: {companies_count}")
		sector["stats"]["companies_count"] = companies_count
	# Get industries
	# Get table body
	table_body, table_body_err = get_element_by(
	    driver=driver,  # type: ignore
	    locator=LOCATOR_VISUAL_BREAKDOWN_TABLE_BODY_SECTOR,
	    timeout=5.0,
	    poll_frequency=0.1,
	    retries=0)
	if table_body_err:
		logger.error(f"table_body_err: {table_body_err}")
	else:
		assert table_body
		# Get rows
		rows = table_body.find_elements(By.TAG_NAME, "tr")
		logger.info(f"Found {len(rows)} rows!")
		# Iterate through rows
		for i, row in enumerate(rows):
			# Get columns
			cols = row.find_elements(By.TAG_NAME, "td")
			# Get industry name
			industry_name = cols[0].text
			logger.info(f"industry_name: {industry_name}")
			# Get industry url
			industry_url = f"{sector['url']}/{industry_name.lower().replace(' ', '-').replace('---', '-')}"
			# industry_url = f"https://finance.yahoo.com/industries/{industry_name.lower().replace(' ', '-').replace('---', '-')}"
			logger.info(f"industry_url: {industry_url}")
			# Get market weight
			market_weight = cols[1].text
			logger.info(f"market_weight: {market_weight}")
			# Get day return
			day_return = cols[2].text
			logger.info(f"day_return: {day_return}")
			# Get YTD return
			ytd_return = cols[3].text
			logger.info(f"ytd_return: {ytd_return}")
			if i == 0:
				sector["stats"]["market_weight"] = market_weight
				sector["stats"]["day_return"] = day_return
				sector["stats"]["ytd_return"] = ytd_return
			else:
				industry_data = {
				    "name": industry_name,
				    "url": industry_url,
				    "stats": {
				        "market_cap": None,
				        "industry_weight": None,
				        "companies_count": None,
				        "employees_count": None,
				        "market_weight": market_weight,
				        "day_return": day_return,
				        "ytd_return": ytd_return,
				    },
				    "companies": [],
				}
				sector["industries"].append(industry_data)
	save_all_sectors_data()
	return sector


def get_industry(industry: dict) -> dict:
	'''
	Gets the industry data
	'''
	driver.get(industry["url"])
	# Get statistics (from header)
	market_cap, market_cap_err = get_element_by(
	    driver=driver,  # type: ignore
	    locator=LOCATOR_INDUSTRY_MARKET_CAP,
	    timeout=5.0,
	    poll_frequency=0.1,
	    retries=0)
	if market_cap_err:
		logger.error(f"market_cap_err: {market_cap_err}")
	else:
		assert market_cap
		market_cap = market_cap.text
		logger.info(f"Market cap: {market_cap}")
		industry["stats"]["market_cap"] = market_cap
	industry_weight, industry_weight_err = get_element_by(
	    driver=driver,  # type: ignore
	    locator=LOCATOR_INDUSTRY_INDUSTRY_WEIGHT,
	    timeout=5.0,
	    poll_frequency=0.1,
	    retries=0)
	if industry_weight_err:
		logger.error(f"industry_weight_err: {industry_weight_err}")
	else:
		assert industry_weight
		industry_weight = industry_weight.text
		logger.info(f"Industry weight: {industry_weight}")
		industry["stats"]["industry_weight"] = industry_weight
	companies_count, companies_count_err = get_element_by(
	    driver=driver,  # type: ignore
	    locator=LOCATOR_INDUSTRY_COMPANIES_COUNT,
	    timeout=5.0,
	    poll_frequency=0.1,
	    retries=0)
	if companies_count_err:
		logger.error(f"companies_count_err: {companies_count_err}")
	else:
		assert companies_count
		companies_count = companies_count.text
		logger.info(f"Companies count: {companies_count}")
		industry["stats"]["companies_count"] = companies_count
	employees_count, employees_count_err = get_element_by(
	    driver=driver,  # type: ignore
	    locator=LOCATOR_INDUSTRY_EMPLOYEES_COUNT,
	    timeout=5.0,
	    poll_frequency=0.1,
	    retries=0)
	if employees_count_err:
		logger.error(f"employees_count_err: {employees_count_err}")
	else:
		assert employees_count
		employees_count = employees_count.text
		logger.info(f"Employees count: {employees_count}")
		industry["stats"]["employees_count"] = employees_count
	companies_link_element, companies_link_element_err = get_element_by(
	    driver=driver,  # type: ignore
	    locator=LOCATOR_INDUSTRY_COMPANIES_LINK,
	    timeout=5.0,
	    poll_frequency=0.1,
	    retries=0)
	if companies_link_element_err:
		logger.error(f"companies_link_element_err: {companies_link_element_err}")
	else:
		assert companies_link_element
		companies_link = companies_link_element.get_attribute("href")
		logger.info(f"Companies link: {companies_link}")
		industry["companies_link"] = companies_link
	save_all_sectors_data()
	return industry


def get_industry_companies(industry: dict) -> dict:
	'''
	Gets the industry companies
	'''
	# driver.get(industry["companies_link"])
	# ?count=100&offset=0
	companies_per_page = 100
	loop_limit = 10 * companies_per_page
	for offset in range(0, loop_limit, companies_per_page):
		# Get 100 companies
		companies_link = f"{industry['companies_link']}?count={companies_per_page}&offset={offset}"
		logger.info(f"Getting companies from {companies_link}...")
		driver.get(companies_link)
		# Get table body
		table_body, table_body_err = get_element_by(
		    driver=driver,  # type: ignore
		    locator=LOCATOR_PREDEFINED_SCREENER_TABLE_BODY,
		    timeout=5.0,
		    poll_frequency=0.1,
		    retries=0)
		if table_body_err:
			logger.error(f"table_body_err: {table_body_err}")
			break
		else:
			assert table_body
			# Get rows
			rows = table_body.find_elements(By.TAG_NAME, "tr")
			logger.info(f"Found {len(rows)} rows!")
			# Iterate through rows
			for j, row in enumerate(rows):
				company = {}
				# Get columns
				cols = row.find_elements(By.TAG_NAME, "td")
				# Get company name
				company_symbol = cols[0].text
				company["symbol"] = company_symbol
				# Get company url
				company_url = cols[0].find_element(By.TAG_NAME,
				                                   "a").get_attribute("href")
				company["url"] = company_url
				# Get company name
				company_name = cols[1].text
				company["name"] = company_name
				# Get company price (interday)
				company_price_interday = cols[2].text
				company["price_interday"] = company_price_interday
				# Get price change
				company_price_change = cols[3].text
				company["change"] = company_price_change
				# Get price change percentage
				company_price_change_percentage = cols[4].text
				company["change_percentage"] = company_price_change_percentage
				# Get volume
				company_volume = cols[5].text
				company["volume"] = company_volume
				# Get average volume (3 months)
				company_average_volume_3_months = cols[6].text
				company["average_volume_3_months"] = company_average_volume_3_months
				# Get market cap
				company_market_cap = cols[7].text
				company["market_cap"] = company_market_cap
				# Get PE ratio (TTM)
				company_pe_ratio_ttm = cols[8].text
				company["pe_ratio_ttm"] = company_pe_ratio_ttm
				logger.info(f"Company {offset + j + 1}: {company}")
				industry["companies"].append(company)
			if len(rows) < companies_per_page:
				logger.info(
				    f"Reached the end of the companies list! ({len(rows)} < {companies_per_page})"
				)
				break
	save_all_sectors_data()
	return industry


def fill_data():
	'''
	Fills the all_sectors_data with data for each sector
	'''
	# 1. Iterate through sectors
	# 2. Get sector data
	# 3. Get industries
	# 4. Iterate through industries
	# 5. Get industry data
	# 6. Get companies
	for i, sector in enumerate(all_sectors_data["sectors"]):
		if "complete" in sector:
			logger.info(
			    f"Skipping sector {sector['name']} {i + 1}/{len(all_sectors_data['sectors'])}..."
			)
			continue
		logger.info(
		    f"Getting data for sector {sector['name']} {i + 1}/{len(all_sectors_data['sectors'])}..."
		)
		# Get sector data
		get_sector(sector)
		# Get industries
		for j, industry in enumerate(sector["industries"]):
			if "complete" in industry:
				logger.info(
				    f"Skipping industry {industry['name']} {j + 1}/{len(sector['industries'])}..."
				)
				continue
			logger.info(
			    f"Getting data for industry {industry['name']} {j + 1}/{len(sector['industries'])}..."
			)
			# Get industry data
			get_industry(industry)
			# Get companies
			get_industry_companies(industry)
			industry["complete"] = True
		sector["complete"] = True
	all_sectors_data["complete"] = True
	save_all_sectors_data()


def main():
	if not os.path.exists(output_path_root):
		os.makedirs(output_path_root)
	init()
	load_all_sectors_data()
	fill_data()


def turn_off_driver():
	'''
	Turns off the driver
	'''
	global driver
	# driver.close()
	driver.quit()


if __name__ == "__main__":
	main()
	# wait_indefinitely()  # for debug
	turn_off_driver()
	logger.say("Done!")
