import os
import json
from datetime import datetime, timedelta
from typing import Tuple
import numpy as np
import numpy.typing as npt
from keepa.interface import keepa_minutes_to_time, parse_csv


def load_result_object(path: str) -> dict:
	'''
		Loads the result object from a path.
	'''
	result_object = json.load(open(path))
	return result_object


def get_root_key(key: str) -> str:
	'''
		Returns the root key of a key.
		Example: "AMAZON" is the root key of "AMAZON_time"
	'''
	if key.endswith("_time"):
		return key[:-5]
	if key.startswith("df_"):
		return key[3:]
	return key


# TODO: should we clean -1 values as well?
def clean_nan_values(
    values: npt.NDArray[np.float64], dates: npt.NDArray[np.datetime64]
) -> Tuple[npt.NDArray[np.float64], npt.NDArray[np.datetime64]]:
	'''
		Removes all NaN values from the pair of arrays, keeping the dates and values in sync.
	'''
	if len(values) != len(dates):
		raise ValueError('Length of values and dates must be equal.')
	nan_values_mask = np.isnan(values)
	# nan_dates_mask = np.isnan(dates)
	# nan_mask = np.logical_or(nan_values_mask, nan_dates_mask)
	nan_mask = nan_values_mask
	values_clean: npt.NDArray[np.float64] = values[~nan_mask]
	dates_clean: npt.NDArray[np.datetime64] = dates[~nan_mask]
	return values_clean, dates_clean


def organize_csv(
    parsed_csv: dict
) -> dict[str, Tuple[npt.NDArray[np.float64], npt.NDArray[np.datetime64]]]:
	'''
		Organizes the keys into price / other data categories and returns an object
		Example mapping: "AMAZON": (np.ndarray[np.float64], "dates": np.ndarray[np.datetime64])
		where the first element of the tuple is the values (example: price) array and the second element is the dates array.
	'''
	organized: dict[str, Tuple[npt.NDArray[np.float64],
	                           npt.NDArray[np.datetime64]]] = {}
	dict_organized: dict[str, dict[str, npt.NDArray[np.float64] |
	                               npt.NDArray[np.datetime64]]] = {}
	# Organize
	for k, v in parsed_csv.items():
		root_key = get_root_key(k)
		if root_key not in dict_organized:
			dict_organized[root_key] = {}
		if k.endswith("_time"):  # if it's a date array
			dates_array: npt.NDArray[np.datetime64] = v
			dict_organized[root_key]["dates"] = dates_array
		# if k.startswith("df_"): # idk if we need this since we got values and dates
		# 	organized[root_key]["df"] = v
		if not k.endswith("_time") and not k.startswith(
		    "df_"):  # if it's a value array
			values_array: npt.NDArray[np.float64] = v
			dict_organized[root_key]["values"] = values_array
	# Convert to organized (dict to tuple)
	for k, v in dict_organized.items():
		values_array: npt.NDArray[np.float64] = v["values"]  # type: ignore
		dates_array: npt.NDArray[np.datetime64] = v["dates"]  # type: ignore
		organized[k] = (values_array, dates_array)
	# Clean NaN values
	for k in organized:
		organized[k] = clean_nan_values(organized[k][0], organized[k][1])
	return organized


def print_organized_csv(
    organized_csv: dict[str, Tuple[npt.NDArray[np.float64],
                                   npt.NDArray[np.datetime64]]]):
	'''
		Prints the organized csv in a readable format.
	'''
	print(f"Organized csv:")
	for k, v in organized_csv.items():
		# print the key and types of the v tuple elements
		first_element_value = v[0][0] if len(v[0]) > 0 else None
		last_element_value = v[0][-1] if len(v[0]) > 0 else None
		first_element_date = v[1][0] if len(v[0]) > 0 else None
		last_element_date = v[1][-1] if len(v[0]) > 0 else None
		print(f"{k}:")
		print(f"    values: {type(v[0])} ; shape: {v[0].shape}")
		print(f"        first value: {first_element_value}")
		print(f"        last value: {last_element_value}")
		print(f"    dates:  {type(v[1])} ; shape: {v[1].shape}")
		print(f"        first date: {first_element_date}")
		print(f"        last date: {last_element_date}")
		print()


def get_clean_date(date: datetime) -> datetime:
	'''
		Returns a copy of the datetime object, only keeping the year, month and day.
	'''
	dt = datetime.replace(date, hour=0, minute=0, second=0, microsecond=0)
	return dt


# arr_values is a numpy array of prices
def discretize(
    arr_values: npt.NDArray[np.float64], arr_dates: npt.NDArray[np.datetime64]
) -> Tuple[npt.NDArray[np.float64], npt.NDArray[np.datetime64]]:
	'''
		Converts all dates in a time series to only keep the year, month and day,
		choosing the most recent consecutive date and discarding all others.
	'''
	if len(arr_values) != len(arr_dates):
		raise ValueError('Length of arr_values and arr_dates must be equal.')
	arr_dates_discrete = []
	arr_values_discrete = []
	for i in range(len(arr_values)):
		if i == len(arr_values) - 1:
			arr_dates_discrete.append(get_clean_date(arr_dates[i]))
			arr_values_discrete.append(arr_values[i])
			break
		date = get_clean_date(arr_dates[i])
		value = arr_values[i]
		date_next = get_clean_date(arr_dates[i + 1])
		if date != date_next:
			arr_dates_discrete.append(date)
			arr_values_discrete.append(value)
	return np.array(arr_values_discrete), np.array(arr_dates_discrete)


def discretize_smart(
    arr_values: npt.NDArray[np.float64], arr_dates: npt.NDArray[np.datetime64]
) -> Tuple[npt.NDArray[np.float64], npt.NDArray[np.datetime64]]:
	'''
		Similar to discretize, but trying to fill the gaps in the time series by
		using the first data point within a day as the value to impute the previous day if missing.
		The dates must be consecutive to impute.
		The last data point within the day is used for that specific day.
	'''
	if len(arr_values) != len(arr_dates):
		raise ValueError('Length of arr_values and arr_dates must be equal.')
	arr_dates_discrete = []
	arr_values_discrete = []
	same_date_groups = []
	# group the same dates
	for i in range(len(arr_values)):
		date = get_clean_date(arr_dates[i])
		value = arr_values[i]
		if i == 0:
			same_date_groups.append([(date, value)])
			continue
		if date == same_date_groups[-1][-1][0]:
			if len(same_date_groups[-1]) == 1:
				same_date_groups[-1].append((date, value))
				continue
			same_date_groups[-1][-1] = (date, value)
			continue
		same_date_groups.append([(date, value)])
	# impute the gaps where possible
	for group in same_date_groups:
		if len(group) == 1:
			arr_dates_discrete.append(group[0][0])
			arr_values_discrete.append(group[0][1])
			continue
		lower_date_yesterday = group[0][0] - timedelta(days=1)
		if len(arr_dates_discrete) == 0 or arr_dates_discrete[
		    -1] != lower_date_yesterday:  # date check condition (can make it more strict by checking the time as well)
			arr_dates_discrete.append(lower_date_yesterday)
			arr_values_discrete.append(group[0][1])
		arr_dates_discrete.append(group[-1][0])
		arr_values_discrete.append(group[-1][1])
	return np.array(arr_values_discrete), np.array(arr_dates_discrete)


def discretize_csv_smart(
    organized_csv: dict[str, Tuple[npt.NDArray[np.float64],
                                   npt.NDArray[np.datetime64]]]
) -> dict[str, Tuple[npt.NDArray[np.float64], npt.NDArray[np.datetime64]]]:
	'''
		Discretizes the organized csv using the discretize_smart function.
		Runs the all time series keys through the discretize_smart function and
		returns the discretized organized csv.
	'''
	for k, v in organized_csv.items():
		organized_csv[k] = discretize_smart(v[0], v[1])
	return organized_csv


def get_trends(
    organized_csv: dict[str, Tuple[npt.NDArray[np.float64],
                                   npt.NDArray[np.datetime64]]],
    trends: dict[str, dict[np.datetime64, npt.NDArray[np.float64]]] = {},
    minimum_datapoints: int = -1
) -> Tuple[dict[str, dict[np.datetime64, npt.NDArray[np.float64]]], list[str]]:
	'''
		Returns the trends of the organized csv.
		
		It is a meta-object which is transformed from organized_csv into a dict of dicts for
		more efficient adding of products (organized_csv object contains product time series) to the trends.

		Example trends object:
		trends = {
			"AMAZON": {
				"2021-01-01": [2.5, 2],
				"2021-01-02": [6.2, 3],
				...
			},
			"RATING": {
				"2021-01-02": [4.2, 3],
				...
			},
			"COUNT_REVIEWS": {
				"2021-01-02": [2324, 3],
				...
			},
			...
		}

		Correction for below: all values at index 0 in array for a specific day are summed, not averaged.

		"AMAZON": "2021-01-01": [2.5, 2], means that the summed price of 2 products on 2021-01-01 was 2.5
		This is done, so that we can easily add more products to the trends object and also get the average values
		for certain trend keys, for example, the total number of reviews on "2021-01-01" is 2324 * 3 = 6972.
		As trend keys can be used as averages, other as accumulators, some as something else,
		we can also use more array elements in the value array, for example, [2.5, 2, -0.2] could indicate a price percentage change from the previous day.
		The specifics will be determined throughout analysis.
		
		New products can be added as we can calculate the new average value (Amazon price, for example) by multiplying the old average value by the old number of products,
		adding the new value to it and dividing by the new number of products, then updating the number of products.
	'''
	skipped_product_keys = []  # these do not have enough datapoints
	for trend_type, trend_data in organized_csv.items():
		values = trend_data[0]
		dates = trend_data[1]
		if minimum_datapoints != -1 and len(values) < minimum_datapoints:
			skipped_product_keys.append(trend_type)
			continue
		if trend_type not in trends:
			trends[trend_type] = {}
		for i, d in enumerate(dates):
			if d not in trends[trend_type]:
				trends[trend_type][d] = np.array([0, 0])
			trends[trend_type][d][0] += values[i]
			trends[trend_type][d][1] += 1
	return trends, skipped_product_keys


def get_timeseries_from_trends(
    trends: dict[str, dict[np.datetime64, npt.NDArray[np.float64]]],
    trend_key: str,
    operation: str = "average"
) -> Tuple[npt.NDArray[np.float64], npt.NDArray[np.datetime64]]:
	'''
		Returns a tuple of values and dates for a specific trend key.
	'''
	if operation not in ["average", "sum", "count"]:
		raise ValueError(f"Invalid operation: {operation}")
	trend = trends[trend_key]
	trend_keys = np.array(list(trend.keys()))
	min_date = min(trend_keys)
	max_date = max(trend_keys)
	values = np.array([])
	dates = np.array([])
	current_date = min_date
	while current_date <= max_date:
		if current_date in trend:
			if operation == "average":
				values = np.append(values,
				                   trend[current_date][0] / trend[current_date][1])
			if operation == "sum":
				values = np.append(values, trend[current_date][0])
			if operation == "count":  # number of instances of a trend key for a specific date
				values = np.append(values, trend[current_date][1])
			dates = np.append(dates, current_date)
		current_date += timedelta(days=1)
	return values, dates


def remove_outliers(
    values: npt.NDArray[np.float64],
    dates: npt.NDArray[np.datetime64],
    max_std_multiplier: float = 2
) -> Tuple[npt.NDArray[np.float64], npt.NDArray[np.datetime64]]:
	'''
		Removes all outliers from the given values and dates.

		Returns a new tuple of values and dates without outliers.
	'''
	if len(values) == 0:
		return values, dates
	# Compute the mean and standard deviation of the values
	mean = np.mean(values)
	std = np.std(values)
	# Compute the lower and upper bounds
	lower_bound = mean - max_std_multiplier * std
	upper_bound = mean + max_std_multiplier * std
	if lower_bound < 0:
		lower_bound = 0
	# Remove all outliers
	values_new = np.array([])
	dates_new = np.array([])
	for i, value in enumerate(values):
		if value >= lower_bound and value <= upper_bound:
			values_new = np.append(values_new, value)
			dates_new = np.append(dates_new, dates[i])
	return values_new, dates_new


def remove_outliers_csv(
    csv: dict[str, Tuple[npt.NDArray[np.float64], npt.NDArray[np.datetime64]]],
    max_std_multiplier: float = 2
) -> dict[str, Tuple[npt.NDArray[np.float64], npt.NDArray[np.datetime64]]]:
	'''
		Removes all outliers from the given csv.

		Returns a new csv without outliers.
	'''
	csv_new = {}
	for key in csv:
		values, dates = csv[key]
		values_new, dates_new = remove_outliers(values, dates, max_std_multiplier)
		csv_new[key] = (values_new, dates_new)
	return csv_new


class CustomEncoder(json.JSONEncoder):
	'''
		Used to serialize np.datetime64 objects.
	'''

	def default(self, obj):
		if isinstance(obj, np.datetime64):
			return str(obj)
		if isinstance(obj, np.ndarray):
			return obj.tolist()
		return json.JSONEncoder.default(self, obj)


###### "TESTS" ######


def test_get_trends():
	path_sample_product = "data/keepa/products/domains/1/B0B7CPSN2K.json"
	result_object = json.load(open(path_sample_product))
	product = result_object["products"][0]
	organized_csv = organize_csv(parse_csv(product["csv"]))
	discretize_csv_smart(organized_csv)
	trends, skipped_product_keys = get_trends(organized_csv)
	# Run it again with the same product - averaged values should be the same, number of products should be 2
	trends, skipped_product_keys = get_trends(organized_csv, trends)
	a = 0
	# Save trends to date/keepa/trends_test.json, default=str is used to serialize np.datetime64
	# json_string = json.dumps(trends, indent=2, sort_keys=True, cls=CustomEncoder)
	# path_trends = "data/keepa/trends_test.json"
	# os.makedirs(os.path.dirname(path_trends), exist_ok=True)
	# with open(path_trends, "w") as f:
	# 	f.write(json_string)


def test_discretize_smart():
	print("Test discretize_smart")
	values = np.array([1, 2, 3, 4, 5, 6])
	dates = np.array([
	    datetime(2023, 11, 18, 10),  # solo can be added
	    datetime(2023, 11, 20, 10),  # next 3 elements are the same date
	    datetime(2023, 11, 20, 11),  #
	    datetime(
	        2023, 11, 20, 12
	    ),  # the last element is added for sure, first of the same is added if it does not overwrite the last element - OK
	    datetime(2023, 11, 21, 10),  # next 2 elements are the same
	    datetime(
	        2023, 11, 21, 11
	    ),  # last element is added for sure, the first once can't be as it  overlaps with the last element date
	])
	# expected: [1, 2, 4, 6]
	#           [2023-11-18, 2023-11-19, 2023-11-20, 2023-11-21]
	values_discrete, dates_discrete = discretize_smart(values, dates)
	for v, d in zip(values_discrete, dates_discrete):
		print(f"{v}, {d}")
	print()
	print("Test discretize_smart 2")
	values = np.array([1, 2, 3, 4])
	dates = np.array([
	    datetime(2023, 11, 18, 10),
	    datetime(2023, 11, 18, 11),
	    datetime(2023, 11, 20, 10),
	    datetime(2023, 11, 20, 11),
	])
	# expected: [1, 2, 3, 4]
	#           [2023-11-17, 2023-11-18, 2023-11-19, 2023-11-20]
	values_discrete, dates_discrete = discretize_smart(values, dates)
	for v, d in zip(values_discrete, dates_discrete):
		print(f"{v}, {d}")


def test_print_organized_csv():
	path_sample_product = "data/keepa/products/domains/1/B0B7CPSN2K.json"
	result_object = json.load(open(path_sample_product))
	product = result_object["products"][0]
	organized_csv = organize_csv(parse_csv(product["csv"]))
	print_organized_csv(organized_csv)


def test_get_timeseries_from_trends():
	path_sample_product = "data/keepa/products/domains/1/B0B7CPSN2K.json"
	result_object = json.load(open(path_sample_product))
	product = result_object["products"][0]
	organized_csv = organize_csv(parse_csv(product["csv"]))
	discretize_csv_smart(organized_csv)
	trends, _ = get_trends(organized_csv)
	values, dates = get_timeseries_from_trends(trends, "AMAZON")
	print(f"Got {len(values)} values and {len(dates)} dates")


if __name__ == "__main__":
	# test_print_organized_csv()
	# test_get_trends()
	# test_discretize_smart()
	test_get_timeseries_from_trends()
