# Methods from https://datahelp.imf.org/knowledgebase/articles/667681-using-json-restful-web-service

import requests
from typing import Tuple, Optional

# Globals
url_base = "http://dataservices.imf.org/REST/SDMX_JSON.svc"
max_timeout = 30


def get_data(
    url: str,
    params: Optional[dict] = None) -> Tuple[dict, None] | Tuple[None, str]:
	'''
		Makes a request and returns JSON data for the given url
	'''
	try:
		if params is None:
			params = {}
		response = requests.get(url, params=params, timeout=max_timeout)
		if response.status_code != 200:
			return None, f"Error: Status code {response.status_code} != 200"
		if "application/json" not in response.headers["content-type"].lower():
			return None, f"Error: Content type is not JSON"
		return response.json(), None
	except Exception as e:
		return None, f"Exception: {e}"


def get_data_flow() -> Tuple[dict, None] | Tuple[None, str]:
	'''
		1.1 Dataflow Method
		
		Dataflow method returns the list of the datasets, registered for the Data Service.
		
		In order to obtain the data use the following request: 

		http://dataservices.imf.org/REST/SDMX_JSON.svc/Dataflow
	'''
	url = f"{url_base}/Dataflow"
	return get_data(url)


def get_data_structure(
    database_id: str) -> Tuple[dict, None] | Tuple[None, str]:
	'''
		1.2 DataStructure Method
		
		DataStructure method returns the structure of the dataset.

		In order to obtain the data use the following request:

		http://dataservices.imf.org/REST/SDMX_JSON.svc/DataStructure/{database ID}
	'''
	url = f'{url_base}/DataStructure/{database_id}'
	return get_data(url)


def get_compact_data(database_id: str, frequency: str, dimension1: list[str],
                     dimension2: list[str], start_period: str,
                     end_period: str) -> Tuple[dict, None] | Tuple[None, str]:
	'''
		1.3 CompactData Method
		
		CompactData method returns the compact data message.

		In order to obtain the data use the following request:

		http://dataservices.imf.org/REST/SDMX_JSON.svc/CompactData/{database ID}/{frequency}.{item1 from
		dimension1}+{item2 from dimension1}+{item N from dimension1}.{item1 from
		dimension2}+{item2 from dimension2}+{item M from dimension2}?startPeriod={start
		date}&endPeriod={end date}
	'''
	params = {
	    "startPeriod": start_period,
	    "endPeriod": end_period,
	}
	url = f"{url_base}/CompactData/{database_id}/{frequency}."
	for item in dimension1:
		url += f"{item}+"
	url += "."
	for item in dimension2:
		url += f"{item}+"
	return get_data(url, params)


def get_metadata_structure(
    database_id: str) -> Tuple[dict, None] | Tuple[None, str]:
	'''
		1.4 MetadataStructure Method
		
		MetadataStructure method returns the metadata structure of the dataset.
		
		In order to obtain the data use the following request:

		http://dataservices.imf.org/REST/SDMX_JSON.svc/MetadataStructure/{database ID}
	'''
	url = f"{url_base}/MetadataStructure/{database_id}"
	return get_data(url)


def get_generic_metadata(
    database_id: str, frequency: str, dimension1: list[str],
    dimension2: list[str], start_period: str,
    end_period: str) -> Tuple[dict, None] | Tuple[None, str]:
	'''
		1.5 GenericMetadata Method
		
		GenericMetadata method returns the generic metadata message.
		
		In order to obtain the data use the following request:

		http://dataservices.imf.org/REST/SDMX_JSON.svc/GenericMetadata/{database ID}/{item1 from
		dimension1}+{item2 from dimension1}+{item N from dimension1}.{item1 from
		dimension2}+{item2 from dimension2}+{item M from dimension2}?startPeriod={start
		date}&endPeriod={end date}
	'''
	params = {
	    "startPeriod": start_period,
	    "endPeriod": end_period,
	}
	url = f"{url_base}/CompactData/{database_id}/{frequency}."
	for item in dimension1:
		url += f"{item}+"
	url += "."
	for item in dimension2:
		url += f"{item}+"
	return get_data(url, params)


def get_code_list(database_id: str,
                  code_list_id: str) -> Tuple[dict, None] | Tuple[None, str]:
	'''
		1.6 CodeList Method

		GetCodeList method returns the description of CodeLists
		
		In order to obtain the data use the following request:

		http://dataservices.imf.org/REST/SDMX_JSON.svc/CodeList/{codelist code}_{database ID}
	'''
	url = f"{url_base}/CodeList/{code_list_id}_{database_id}"
	return get_data(url)


def get_max_series_in_result() -> Tuple[dict, None] | Tuple[None, str]:
	'''
		1.7 MaxSeriesInResult Method

		GetMaxSeriesInResult method returns the maximum number of time series that can be returned by CompactData.
		
		In order to obtain the data use the following request:

		http://dataservices.imf.org/REST/SDMX_JSON.svc/GetMaxSeriesInResult
	'''
	url = f"{url_base}/GetMaxSeriesInResult"
	return get_data(url)
