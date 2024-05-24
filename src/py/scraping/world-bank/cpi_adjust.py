import os
import pandas as pd
from datetime import datetime
from typing import Optional

path_cpi = "data/scraped/world-bank/cpi.csv"
df_cpi = pd.DataFrame()  # just init to satisfy type checker


def load_cpi(filepath: str = path_cpi) -> pd.DataFrame:
	'''
		Loads the CPI data from the CSV file.
	'''
	if not os.path.exists(filepath):
		raise FileNotFoundError(
		    f"File not found: '{filepath}'. Try running cpi.iypnb first.")
	df = pd.read_csv(filepath, skipfooter=5, engine="python", na_values="..")
	for col in df.columns:
		if "[" in col:
			new_col = col.split("[")[0].strip()
			df = df.rename(columns={col: new_col})
	df = df.drop(columns=["Series Name", "Series Code"])
	return df


def transpose_cpi(df: pd.DataFrame) -> pd.DataFrame:
	'''
		Transposes the dataframe and sets the index to the year.
	'''
	df = df.set_index("Country Code")
	df = df.drop(columns=["Country Name"])
	df = df.T
	df.index = pd.to_datetime(df.index)
	return df


def get_ratio(df: pd.DataFrame) -> pd.DataFrame:
	'''
		Converts the CPI values to ratios (0-1).
	'''
	df = df / 100
	return df


def add_missing_years(df: pd.DataFrame) -> pd.DataFrame:
	'''
		Adds rows for missing years and fills them with the last known value.
	'''
	current_year = datetime.now().year
	years = df.index.year.unique()  # type: ignore
	last_year = years[-1]
	# get last row values
	last_known = df.loc[df.index.year == last_year].iloc[0]  # type: ignore
	for year in range(last_year + 1, current_year + 1):
		# for each missing year, add a new row with the last known value of all columns in last known
		new_index = pd.Timestamp(datetime(year, 1, 1))
		df.loc[new_index] = last_known  # type: ignore
	# sort by index
	df = df.sort_index()
	return df


def fill_missing_dates(df: pd.DataFrame) -> pd.DataFrame:
	'''
		Fills missing dates between years with last valid row.
	'''
	df = df.asfreq("D")
	# NOTE: a more complete approach would be to exclude actual NaN (missing years) values
	#       for specific countries, however for our purposes, the result is the same
	df = df.fillna(method="ffill")
	return df


def fill_missing_dates_interpolate(df: pd.DataFrame) -> pd.DataFrame:
	'''
		Fills missing dates using linear interpolation.
	'''
	df = df.asfreq("D")
	# df = df.interpolate(method="time")
	# use linear interpolation to fill all missing values
	df = df.interpolate(method="linear")
	return df


def get_cpi_df_processed(filepath: str = path_cpi,
                         jagged: bool = False) -> pd.DataFrame:
	'''
		Returns the processed CPI dataframe which is used for adjusting for inflation.
	'''
	df_cpi = load_cpi(filepath)
	df_cpi = transpose_cpi(df_cpi)
	df_cpi = get_ratio(df_cpi)
	df_cpi = add_missing_years(df_cpi)
	if jagged:
		df_cpi = fill_missing_dates(df_cpi)
	else:
		df_cpi = fill_missing_dates_interpolate(df_cpi)
	return df_cpi


def adjust_for_inflation(df: pd.DataFrame,
                         country: str,
                         columns: Optional[list] = None) -> pd.DataFrame:
	'''
		Adjusts numerical values in the dataframe for inflation using the CPI for the given country.
	'''
	# NOTE: df_cpi has already been divided by 100
	# Make a copy of the dataframe
	df = df.copy()
	# Get the CPI for the country
	cpi = df_cpi[country]  # type: ignore
	# # Get the year component of the index
	# years = df.index.year
	# # Get the CPI for the year
	# cpi = cpi[years]
	# Adjust the prices for inflation
	# df = df / cpi

	# df = df.div(cpi, axis=0, fill_value=None)
	if columns is not None:
		df[columns] = df[columns].div(cpi, axis=0, fill_value=None)
	else:
		df = df.div(cpi, axis=0, fill_value=None)
	return df


def initialize_cpi(filepath: str = path_cpi,
                   jagged: bool = False,
                   date_cutoff: Optional[str] = None):
	'''
		Initializes the CPI data by loading the data from the CSV file and processing it.
	'''
	global df_cpi
	df_cpi = get_cpi_df_processed(filepath, jagged)
	if date_cutoff:
		df_cpi = df_cpi[df_cpi.index >= date_cutoff]
