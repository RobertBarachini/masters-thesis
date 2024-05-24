# Utility for processing data

import os
import sys
import pandas as pd
from typing import Optional

sys.path.append(os.getcwd())
from src.py.utils.generic_utils import wrapper

# Constants
supported_extensions = {
    "csv": "csv",
    "feather": "feather",
    "parquet": "parquet",
    "pickle": "pickle",
    "pkl": "pickle"
}
supported_formats = set(supported_extensions.values())


def read_file_to_df(file_path: str,
                    file_format: Optional[str]) -> pd.DataFrame:
	"""
	Reads a file to a pandas DataFrame

	Args:
		file_path (str): Path to the file
		file_format (Optional[str]): Format of the file (csv, feather, parquet, pickle) - if not provided, it will be guessed from the extension. It takes precedence over the extension.
	
	Returns:
		pd.DataFrame: DataFrame with the data
	"""
	print(f"Reading file to DataFrame")
	extension = os.path.splitext(file_path)[1].lower().replace(".", "")
	if file_format is None:
		if extension not in supported_extensions:
			raise Exception(f"Extension '{extension}' not supported")
		file_format = supported_extensions[extension]
	if file_format not in supported_formats:
		raise Exception(f"Format '{file_format}' not supported")
	if file_format == "csv":
		return pd.read_csv(file_path)
	if file_format == "feather":
		return pd.read_feather(file_path)
	if file_format == "parquet":
		return pd.read_parquet(file_path)
	if file_format == "pickle":
		return pd.read_pickle(file_path)
	raise Exception(f"Format '{file_format}' not supported")


def convert_file_to_format(
    file_path_source: str,
    file_path_destination: str,
    file_format: str,
    delete_source: Optional[bool] = False) -> pd.DataFrame:
	"""
	Converts a file to a given format (csv, feather, parquet, pickle)
	"""
	print(f"Converting file '{file_path_source}' to format '{file_format}'")
	df, err = wrapper(read_file_to_df, file_path_source, None)
	if err:
		print(f"Error: {err}")
		raise err
	assert df is not None
	if file_format not in supported_formats:
		raise Exception(f"Format '{file_format}' not supported")
	if file_format == "csv":
		df.to_csv(file_path_destination)
	elif file_format == "feather":
		df.to_feather(file_path_destination)
	elif file_format == "parquet":
		df.to_parquet(file_path_destination)
	elif file_format == "pickle":
		df.to_pickle(file_path_destination)
	else:
		raise Exception(f"Format '{file_format}' not supported")
	if delete_source == None:
		delete_source = False
	# TODO: Fix this
	# if delete_source == True:
	# 	os.remove(file_path_source)
	return df


def convert_files_to_format(
    source_dir: str,
    destination_dir: Optional[str],
    file_format: str,
    delete_source: Optional[bool] = False) -> dict[str, bool]:
	"""
	Converts all files in a directory to a given format (csv, feather, parquet, pickle)
	"""
	print(f"Converting files to format '{file_format}'")
	new_extension = f"{file_format}"
	if destination_dir in set([None, ""]):
		destination_dir = source_dir
	assert (destination_dir)
	if not os.path.exists(source_dir):
		raise Exception(f"Source directory '{source_dir}' does not exist")
	if not os.path.exists(destination_dir):
		os.makedirs(destination_dir)
	files = os.listdir(source_dir)
	files_converted = {}
	for file in files:
		file_path_source = os.path.join(source_dir, file)
		file_path_destination = os.path.join(
		    destination_dir, f"{os.path.splitext(file)[0]}.{new_extension}")
		if file_path_source == file_path_destination:
			continue
		_, err = wrapper(convert_file_to_format, file_path_source,
		                 file_path_destination, file_format, delete_source)
		if err:
			files_converted[file] = False
		else:
			files_converted[file] = True
	return files_converted


def main() -> None:
	"""
	Main function - used to invoke the script from the command line and call the other functions with the appropriate arguments
	"""
	cmd_arguments = sys.argv[1:]
	if len(cmd_arguments) < 2:
		print("Not enough arguments")
		return
	method, *args = cmd_arguments
	if method == "convert_file_to_format":
		file_path_source, file_path_destination, file_format, delete_source = args
		delete_source = bool(delete_source)
		res, err = wrapper(convert_file_to_format, file_path_source,
		                   file_path_destination, file_format, delete_source)
		if err:
			print(f"Error: {err}")
	elif method == "convert_files_to_format":
		source_dir, destination_dir, file_format, delete_source = args
		delete_source = bool(delete_source)
		res, err = wrapper(convert_files_to_format, source_dir, destination_dir,
		                   file_format, delete_source)
		if err:
			print(f"Error: {err}")
		else:
			print(f"Files converted: {res}")


if __name__ == "__main__":
	main()
	print("ALL DONE!")
