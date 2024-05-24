'''
	Library for converting CamelCamelCamel line chart image to data

	It uses OpenCV and Tessaract to find axis, gridlines, labels,
	and aproximated data points which form the line chart.

	This is the optimized algorithm from cv-demo.ipynb

	The main function you might be interested in is get_image_data(img)
	which takes an image and returns a dict with all the extracted data
'''

# TODO: make inverse functions - from values to pixels (for later (visual) verification of the extracted data)
# TODO: make validation functions - check if the extracted data is correct (visual verification - plot select extracted data on the image)

# imports
import time
import re
from datetime import datetime, timedelta
from typing import Optional, Union
import cv2 as cv
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
import pytesseract
from pytesseract import Output

# Global variables and constants
months = set([
    'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'nov', 'dec'
])
color_axis = (51, 51, 51)
color_gridline_major = (221, 221, 221)
color_gridline_minor = (245, 245, 245)
color_line_amazon = (99, 168, 94)
color_line_new = (0, 51, 204)
color_line_used = (204, 51, 0)
color_price_highest = (194, 68, 68)
color_price_lowest = (119, 195, 107)
confidence = 80  # pytesseract confidence level

#
'''
	Helper functions and utilities
'''


def clean_str(s: str) -> str:
	'''
		Remove all non-alphanumeric characters from a string.
	'''
	s_clean = s.replace(' ', '')
	s_clean = s_clean.strip()
	s_clean = s_clean.lower()
	s_clean = re.sub('[^0-9a-zA-Z]+', '', s_clean)
	return s_clean


def show(img: np.ndarray, figsize: Optional[tuple] = None):
	'''
		Shows image in a matplotlib window
	'''
	if figsize is None:
		w = img.shape[1]
		h = img.shape[0]
		a = w / h
		figsize = (12, 12 / a)
	plt.figure(figsize=figsize)
	plt.imshow(img)


def load_image(filepath: str) -> np.ndarray:
	# loads image from filepath
	img = cv.cvtColor(cv.imread(filepath), cv.COLOR_BGR2RGB)
	return img


def mask_image(img: np.ndarray,
               color: tuple,
               color_range: Optional[tuple] = None) -> np.ndarray:
	'''
		Returns a masked image where only the pixels of the specified color are kept.
		If two colors are specified, the pixels between the two colors are kept.
	'''
	img_copy = img.copy()
	if color_range is None:
		color_range = color
	img_masked = cv.inRange(img_copy, np.array(color), np.array(color_range))
	return img_masked


# Key algo for getting chart line coordinates
def get_vertical_pixel_indices(img: np.ndarray, line_color: tuple) -> list:
	'''
		Returns a list (length is same as img) where each element is a an index
		of the center of the first and last non-zero pixel in the column (vertical pixel line)
		If no non-zero pixel if found in a column the element at that index equals -1.

		Useful for getting the averaged coordinates of the chart line.
		Example: element in list at index 3 has a value of 5 -> (3, 5) ; (x, y) ; (width_i, height_i) of the image
		The coordinate system for images starts at the top left corner of the image.
	'''
	img_copy = img.copy()
	# Mask the image to only keep the line color
	img_masked = mask_image(img_copy, line_color)
	vertical_pixel_indices = []
	# transpose the array to make it easier to loop through each column (now row)
	# loop through each row
	for i, row in enumerate(img_masked.T):
		# Find the indices of the non-zero elements
		nz_indices = np.nonzero(row)[0]
		# If there are no non-zero elements, add -1 to the list
		if len(nz_indices) == 0:
			vertical_pixel_indices.append(-1)
			continue
		# Find the first and last non-zero indices
		first_nz_index = nz_indices[0]
		last_nz_index = nz_indices[-1]
		# Find the average of the first and last non-zero indices
		avg_nz_index = (first_nz_index + last_nz_index) / 2
		# Get the integer part of the average index
		avg_nz_index = int(avg_nz_index)
		# Add the average index to the list
		vertical_pixel_indices.append(avg_nz_index)
	# return the list
	return vertical_pixel_indices


def get_line_indices_generic(img: np.ndarray,
                             is_horizontal: bool,
                             color: tuple,
                             match_threshold: float = 0.2) -> list:
	'''
		Find the indices of the lines in the image.
		Returns tuples of (index, match_count) where match_count is
		the number of pixels in that line that match the specified color.
	'''
	# mask the image
	img_mask = mask_image(img, color)
	# show(img_mask)
	scanline = None
	# generate scanline
	if is_horizontal:
		scanline = np.logical_not(np.zeros(img_mask.shape[1]))
	else:
		scanline = np.logical_not(np.zeros(img_mask.shape[0]))
	matches_indices = []
	# loop through each row and use logical and to find the number of matches
	img_mask = img_mask if is_horizontal else img_mask.T
	for i, row in enumerate(img_mask):
		match_count = np.sum(np.logical_and(row, scanline))
		match_ratio = match_count / img_mask.shape[1]
		if match_ratio > match_threshold:
			matches_indices.append((i, match_count))
	return matches_indices


def line_indice_tuples_to_list(line_indice_tuples: list) -> list:
	'''
		Converts a list of tuples of (index, match_count) to a list of indices.
	'''
	return [t[0] for t in line_indice_tuples]


def get_line_indices_best_matches(matches_indices: list) -> list:
	'''
		Returns the indices of the lines with the highest number of matches.
	'''
	max_matches = max(matches_indices, key=lambda x: x[1])[1]
	indices = []
	for i, match_count in matches_indices:
		if match_count == max_matches:
			indices.append(i)
	return indices


def get_consecutive_elements(arr: Union[list, np.ndarray]) -> list:
	'''
		Returns a list of lists where each list contains consecutive elements (assuming ascending order) from the input array.
	'''
	consecutive_lists = []
	current_list = [arr[0]]
	for i in range(1, len(arr)):
		if arr[i] == arr[i - 1] + 1:
			current_list.append(arr[i])
		else:
			consecutive_lists.append(current_list)
			current_list = [arr[i]]
	consecutive_lists.append(current_list)
	return consecutive_lists


def merge_consecutive_elements(arr: list) -> list:
	'''
		Returns a list where each element is the average of the elements in the corresponding list in the input array.
	'''
	merged_list = []
	for els in arr:
		merged_list.append(int(np.average(els)))
	return merged_list


def tesseract_data_object_to_list_of_objects(data: dict) -> list:
	'''
		Convert the tesseract data object to a list of objects.
	'''
	data_list = []
	for i in range(len(data["text"])):
		el = {}
		for k in data:
			el[k] = data[k][i]
		data_list.append(el)
	return data_list


# arr = np.array([33, 34, 100, 101, 102, 105, 108])
# consecutive_lists = get_consecutive_elements(arr)
# print(consecutive_lists)
# merged_list = merge_consecutive_elements(consecutive_lists)
# print(merged_list)

#
'''
	Core functions
'''


def get_axis_locations(img: np.ndarray, color: tuple = color_axis) -> tuple:
	'''
			Returns the x and y axis locations of the image.
		'''
	# Get x axis location
	x_indices = get_line_indices_generic(img, True, color, 0.2)
	x_indices_best = get_line_indices_best_matches(x_indices)
	x_indices_consecutive = get_consecutive_elements(x_indices_best)
	x_indices_merged = merge_consecutive_elements(x_indices_consecutive)
	x_index = int(np.average(x_indices_merged))
	# Get y axis location
	y_indices = get_line_indices_generic(img, False, color, 0.2)
	y_indices_best = get_line_indices_best_matches(y_indices)
	y_indices_consecutive = get_consecutive_elements(y_indices_best)
	y_indices_merged = merge_consecutive_elements(y_indices_consecutive)
	y_index = int(np.average(y_indices_merged))
	return x_index, y_index


def get_major_grid_locations(img: np.ndarray,
                             color: tuple = color_gridline_major) -> tuple:
	'''
		Find the locations of vertical and horizontal major gridlines in the image.
	'''
	lines_horizontal = get_line_indices_generic(img, True, color, 0.2)
	lines_horizontal = line_indice_tuples_to_list(lines_horizontal)
	lines_horizontal_consecutive = get_consecutive_elements(lines_horizontal)
	lines_horizontal_merged = merge_consecutive_elements(
	    lines_horizontal_consecutive)
	lines_vertical = get_line_indices_generic(img, False, color, 0.2)
	lines_vertical = line_indice_tuples_to_list(lines_vertical)
	lines_vertical_consecutive = get_consecutive_elements(lines_vertical)
	lines_vertical_merged = merge_consecutive_elements(
	    lines_vertical_consecutive)
	return lines_horizontal_merged, lines_vertical_merged


def get_rightmost_minor_gridline(img: np.ndarray,
                                 color: tuple = color_gridline_minor) -> int:
	'''
		Find the location of the rightmost minor gridline in the image.
		Also serves as the right side of the bounding box for the graph (line chart).
	'''
	# Get all of the minor gridlines (vertical)
	lines_x = get_line_indices_generic(img, False, color, 0.2)
	lines_x = line_indice_tuples_to_list(lines_x)
	# Get the rightmost minor gridline
	rightmost_minor_gridline = max(lines_x)
	return rightmost_minor_gridline


def get_max_price_index(img: np.ndarray,
                        color: tuple = color_price_highest) -> int:
	'''
		Returns the index of the horizonal line representing the highest price.
	'''
	possible_indices = get_line_indices_generic(img, True, color, 0.2)
	possible_indices_best = get_line_indices_best_matches(possible_indices)
	possible_indices_consecutive = get_consecutive_elements(
	    possible_indices_best)
	possible_indices_merged = merge_consecutive_elements(
	    possible_indices_consecutive)
	max_price_index = int(np.average(possible_indices_merged))
	return max_price_index


def get_min_price_index(img: np.ndarray,
                        color: tuple = color_price_lowest) -> int:
	'''
		Returns the index of the horizonal line representing the lowest price.
	'''
	possible_indices = get_line_indices_generic(img, True, color, 0.2)
	possible_indices_best = get_line_indices_best_matches(possible_indices)
	possible_indices_consecutive = get_consecutive_elements(
	    possible_indices_best)
	possible_indices_merged = merge_consecutive_elements(
	    possible_indices_consecutive)
	min_price_index = int(np.average(possible_indices_merged))
	return min_price_index


def get_y_axis_label_candidates(candidates: list) -> list:
	'''
		Find the y axis label candidates.
	'''
	# find the y axis label candidates
	y_axis_label_candidates = []
	for candidate in candidates:
		# get the text from the candidate
		text = candidate['text']
		if "$" in text and "." not in text:
			y_axis_label_candidates.append(candidate)
	return y_axis_label_candidates


def get_x_axis_month_label_candidates(candidates: list) -> list:
	'''
		Find the x axis month label candidates.
	'''
	# find the x axis month label candidates
	x_axis_month_label_candidates = []
	for candidate in candidates:
		# get the text from the candidate
		text = candidate['text']
		if clean_str(text) in months:
			x_axis_month_label_candidates.append(candidate)
	return x_axis_month_label_candidates


def get_month_labels_y_location(candidates: list) -> int:
	'''
		Find the y axis location of the month labels. Used for determining x axis year label candidates.
	'''
	y_locations = {}
	for candidate in candidates:
		y = str(candidate['top'])
		if y not in y_locations:
			y_locations[y] = []
		y_locations[y].append(candidate)
	# y_location is the key with the most values
	y_location = int(max(y_locations, key=lambda k: len(y_locations[k])))
	# return the y location of the month labels
	return y_location


def get_x_axis_year_label_candidates(candidates: list,
                                     y_location: int) -> list:
	'''
		Find the x axis year label candidates.
	'''
	# find the x axis year label candidates
	x_axis_year_label_candidates = []
	for candidate in candidates:
		# get the text from the candidate
		text = candidate['text']
		# get the y location from the candidate
		y = candidate['top']
		# if the text is a digit and the y location is near (3 pixels + or -) the y location of the month labels
		if text.isdigit() and abs(y - y_location) <= 3:
			x_axis_year_label_candidates.append(candidate)
	return x_axis_year_label_candidates


def get_text_data(img: np.ndarray) -> dict:
	'''
		Get the text data from the image.
	'''
	img_copy = img.copy()
	gray = cv.cvtColor(img_copy, cv.COLOR_BGR2GRAY)
	# show(gray)
	text_data = pytesseract.image_to_data(
	    gray, output_type=Output.DICT,
	    config='--psm 6 --oem 3')  # currently the best
	return text_data


def filter_text_data(text_data: dict, confidence: int = confidence) -> list:
	# make a copy of the text data
	text_data_copy = text_data.copy()
	# convert the tesseract data object to a list of objects
	text_data_copy = tesseract_data_object_to_list_of_objects(text_data_copy)
	# filter out the non-text boxes
	text_data_copy = [b for b in text_data_copy if b['text'].strip() != '']
	# filter out the boxes with low confidence
	text_data_copy = [b for b in text_data_copy if int(b['conf']) > confidence]
	# return the filtered text data
	return text_data_copy


def match_x_axis_label_candidates_with_gridlines(
    x_axis_label_candidates: list, grid_x_locations: list) -> list:
	'''
		Tries matching the x axis label candidates center with the closest gridline.
	'''
	matches = []
	biggest_distance = 5  # the horizontal distance between the center of the label and the gridline
	for candidate in x_axis_label_candidates:
		center = candidate['left'] + (candidate['width'] / 2)
		closest_gridline = min(grid_x_locations, key=lambda x: abs(x - center))
		if abs(center - closest_gridline) < biggest_distance:
			matches.append((candidate, closest_gridline))
	return matches


def match_y_axis_label_candidates_with_gridlines(
    y_axis_label_candidates: list, grid_y_locations: list) -> list:
	'''
		Tries matching the y axis label candidates center with the closest gridline.
	'''
	matches = []
	biggest_distance = 5  # the vertical distance between the center of the label and the gridline
	for candidate in y_axis_label_candidates:
		center = candidate['top'] + (candidate['height'] / 2)
		closest_gridline = min(grid_y_locations, key=lambda y: abs(y - center))
		if abs(center - closest_gridline) < biggest_distance:
			matches.append((candidate, closest_gridline))
	return matches


# function to calculate the timestamp of a given x axis pixel (coordinate system starts from top left)
def calculate_timestamp_from_x_axis_pixel(
    gridline_pair: tuple, pixel_x: int,
    x_seconds_per_pixel: float) -> datetime:
	'''
		Returns the timestamp of a given x axis pixel in relation to the selected gridline pair axis using x_seconds_per_pixel.
	'''
	gridline = gridline_pair[1]
	gridline_timestamp = datetime(year=int(gridline_pair[0]['text']),
	                              month=1,
	                              day=1)
	pixels_diff = pixel_x - gridline
	seconds_from_gridline = pixels_diff * x_seconds_per_pixel
	td = timedelta(seconds=seconds_from_gridline)
	timestamp_at_pixel_x = gridline_timestamp + td
	return timestamp_at_pixel_x


# function to calculate the value of a given y axis pixel (coordinate system starts from top left)
def calculate_value_from_y_axis_pixel(gridline_pair: tuple, pixel_y: int,
                                      y_dollars_per_pixel: float) -> float:
	'''
		Returns the value of a given y axis pixel in relation to the selected gridline pair axis using y_dollars_per_pixel.
	'''
	gridline = gridline_pair[1]
	gridline_value = float(clean_str(gridline_pair[0]['text']))
	# pixels_diff = pixel_y - gridline
	pixels_diff = gridline - pixel_y  # invert the y axis - images start from top left
	dollars_from_gridline = pixels_diff * y_dollars_per_pixel
	sum_total = gridline_value + dollars_from_gridline
	return sum_total


def mask_image_bounding_box(img: np.ndarray, left: int, top: int, right: int,
                            bottom: int) -> np.ndarray:
	'''
		Masks the image with a bounding box.
	'''
	img_copy = img.copy()
	mask = np.zeros(img_copy.shape[:2], dtype=np.uint8)
	mask[top:bottom, left:right] = 255
	masked_img = cv.bitwise_and(img_copy, img_copy, mask=mask)
	# show(masked_img)
	return masked_img


# This is the ultimate function that converts the chart image to data
# TODO: write 'jsdoc' for this function - all that it returns in a dict
# TODO: make "validation" methods to check if the data is correct
def get_image_data(img: np.ndarray, line_color: tuple) -> dict:
	'''
		Extracts data from CamelCamelCamel line chart image
	'''
	img_copy = img.copy()
	data = {}  # extracted data

	# Get axis locations
	x_axis_location, y_axis_location = get_axis_locations(img_copy)
	# should I use location or position or index or something else
	# naming was made on the fly and is not consistent
	data["x_axis_location"] = x_axis_location
	data["y_axis_location"] = y_axis_location

	# Get rightmost minor gridline location
	rightmost_minor_gridline = get_rightmost_minor_gridline(img_copy)
	data["rightmost_minor_gridline"] = rightmost_minor_gridline

	# Get min and max price indices
	min_price_index = get_min_price_index(img_copy)
	max_price_index = get_max_price_index(img_copy)
	data["min_price_index"] = min_price_index
	data["max_price_index"] = max_price_index

	# Get gridlines
	grid_y_locations, grid_x_locations = get_major_grid_locations(img_copy)
	grid_x_locations = merge_consecutive_elements(
	    get_consecutive_elements(grid_x_locations))
	grid_y_locations = merge_consecutive_elements(
	    get_consecutive_elements(grid_y_locations))
	# Append the x axis to the gridlines as well
	grid_y_locations.append(x_axis_location)
	data["gridlines_vertical_indices"] = grid_x_locations
	data["gridlines_horizonal_indices"] = grid_y_locations

	# get text from image
	text_data = get_text_data(img_copy)
	text_data_filtered = filter_text_data(text_data)
	data["text_data"] = text_data_filtered

	# get y axis labels
	y_axis_label_candidates = get_y_axis_label_candidates(text_data_filtered)
	y_axis_labels = [candidate['text'] for candidate in y_axis_label_candidates]
	data["y_axis_labels"] = y_axis_labels

	# get x axis labels
	x_month_candidates = get_x_axis_month_label_candidates(text_data_filtered)
	x_month_y_location = get_month_labels_y_location(x_month_candidates)
	x_axis_candidates = get_x_axis_year_label_candidates(text_data_filtered,
	                                                     x_month_y_location)
	x_axis_labels = [candidate['text'] for candidate in x_axis_candidates]
	data["x_axis_labels"] = x_axis_labels

	# Get the matches between the labels and the vertical gridlines of the x axis
	grid_x_matches = match_x_axis_label_candidates_with_gridlines(
	    x_axis_candidates, grid_x_locations)
	data["grid_x_matches"] = grid_x_matches

	# Get the matches between the labels and the horizontal gridlines of the y axis
	grid_y_matches = match_y_axis_label_candidates_with_gridlines(
	    y_axis_label_candidates, grid_y_locations)
	data["grid_y_matches"] = grid_y_matches

	# Get the extreme values for the most accurate calculations
	x_pair_smallest = min(grid_x_matches, key=lambda x: x[1])
	x_pair_largest = max(grid_x_matches, key=lambda x: x[1])
	y_pair_smallest = min(grid_y_matches, key=lambda y: y[1])
	y_pair_largest = max(grid_y_matches, key=lambda y: y[1])
	data["x_pair_smallest"] = x_pair_smallest
	data["x_pair_largest"] = x_pair_largest
	data["y_pair_smallest"] = y_pair_smallest
	data["y_pair_largest"] = y_pair_largest

	# Calculate the x and y axis pixel to value ratio (resolution)s
	x_smallest_timestamp = datetime(year=int(x_pair_smallest[0]['text']),
	                                month=1,
	                                day=1)
	x_largest_timestamp = datetime(year=int(x_pair_largest[0]['text']),
	                               month=1,
	                               day=1)
	data["x_smallest_timestamp"] = x_smallest_timestamp
	data["x_largest_timestamp"] = x_largest_timestamp
	# calculate the y axis resolution
	y_smallest_value = float(clean_str(y_pair_smallest[0]['text']))
	y_largest_value = float(clean_str(y_pair_largest[0]['text']))
	data["y_smallest_value"] = y_smallest_value
	data["y_largest_value"] = y_largest_value

	# calculate different in x and y axis
	x_axis_difference_value = (x_largest_timestamp -
	                           x_smallest_timestamp).total_seconds()
	y_axis_difference_value = abs(y_largest_value - y_smallest_value)
	# calculate the difference in pixels between the extreme values
	x_axis_difference_pixels = abs(x_pair_largest[1] - x_pair_smallest[1])
	y_axis_difference_pixels = abs(y_pair_largest[1] - y_pair_smallest[1])
	data["x_axis_difference_value"] = x_axis_difference_value
	data["y_axis_difference_value"] = y_axis_difference_value
	data["x_axis_difference_pixels"] = x_axis_difference_pixels
	data["y_axis_difference_pixels"] = y_axis_difference_pixels
	x_seconds_per_pixel = x_axis_difference_value / x_axis_difference_pixels
	y_dollars_per_pixel = y_axis_difference_value / y_axis_difference_pixels
	data["x_seconds_per_pixel"] = x_seconds_per_pixel
	data["y_dollars_per_pixel"] = y_dollars_per_pixel

	# Validation purposes
	# TODO: improve this with min + max lines and stuff
	# After automatically processing images, we can manually check if the
	# validity of the results
	#
	# # draw a horizontal line at the y axis label location
	# cv.line(img_copy, (0, int(x_axis_location)),
	#         (img_copy.shape[1], int(x_axis_location)), (255, 0, 0), 2)
	# # draw a vertical line at the x axis label location
	# cv.line(img_copy, (int(y_axis_location), 0),
	#         (int(y_axis_location), img_copy.shape[0]), (255, 0, 0), 2)
	# # draw a vertical cyan line at the rightmost_minor_gridline
	# cv.line(img_copy, (int(rightmost_minor_gridline), 0),
	#         (int(rightmost_minor_gridline), img_copy.shape[0]), (0, 255, 255), 2)
	# # draw gridlines
	# for x in grid_x_locations:
	# 	cv.line(img_copy, (int(x), 0), (int(x), img_copy.shape[0]), (0, 255, 0), 1)
	# for y in grid_y_locations:
	# 	cv.line(img_copy, (0, int(y)), (img_copy.shape[1], int(y)), (0, 255, 0), 1)
	# # in magenta draw the x axis label candidates
	# for candidate in x_axis_candidates:
	# 	cv.rectangle(img_copy, (candidate['left'], candidate['top']),
	# 	             (candidate['left'] + candidate['width'],
	# 	              candidate['top'] + candidate['height']), (255, 0, 255), 1)
	# # in magenta draw the y axis label candidates
	# for candidate in y_axis_label_candidates:
	# 	cv.rectangle(img_copy, (candidate['left'], candidate['top']),
	# 	             (candidate['left'] + candidate['width'],
	# 	              candidate['top'] + candidate['height']), (255, 0, 255), 1)

	# Caulculate the timestamp and value of the x and y axis - for later validation purposes
	time_of_y_axis = calculate_timestamp_from_x_axis_pixel(
	    x_pair_smallest, y_axis_location, x_seconds_per_pixel)
	value_of_x_axis = calculate_value_from_y_axis_pixel(y_pair_smallest,
	                                                    x_axis_location,
	                                                    y_dollars_per_pixel)
	data["time_of_y_axis"] = time_of_y_axis
	data["value_of_x_axis"] = value_of_x_axis

	# Mask the image to ensure we only get the data portion of the line chart
	masked_img = mask_image_bounding_box(img_copy, y_axis_location,
	                                     y_pair_smallest[1],
	                                     rightmost_minor_gridline,
	                                     x_axis_location)
	data["bounding_box"] = {
	    "left": y_axis_location,
	    "top": y_pair_smallest[1],
	    "right": rightmost_minor_gridline,
	    "bottom": x_axis_location
	}

	# Get vertical pixes indices from the image (aproximate points on the line chart)
	vertical_pixel_indices = get_vertical_pixel_indices(masked_img, line_color)
	# calculate x and y values for each pixel
	extracted_data = []
	for y, x in enumerate(vertical_pixel_indices):
		if x == -1:
			# extracted_data.append((-1, -1))
			continue
		val_at_pixel_y = calculate_value_from_y_axis_pixel(y_pair_smallest, x,
		                                                   y_dollars_per_pixel)
		val_at_pixel_x = calculate_timestamp_from_x_axis_pixel(
		    x_pair_smallest, y, x_seconds_per_pixel)
		extracted_data.append((val_at_pixel_x, val_at_pixel_y))
	data["extracted_data"] = extracted_data

	# Get xs and ys for plotting
	xs = [x[0] for x in extracted_data]
	ys = [x[1] for x in extracted_data]
	data["plot_data"] = {
	    "xs": xs,
	    "ys": ys,
	}

	# Return the extracted data
	return data


def print_image_data(data: dict):
	'''
		Prints the data extracted from the image
	'''
	x_axis_location = data["x_axis_location"]
	y_axis_location = data["y_axis_location"]
	print(f"x axis location: {x_axis_location}")
	print(f"y axis location: {y_axis_location}")
	rightmost_minor_gridline = data["rightmost_minor_gridline"]
	print(
	    f"rightmost minor gridline location (right side of the bounding box): {rightmost_minor_gridline}"
	)
	min_price_index = data["min_price_index"]
	max_price_index = data["max_price_index"]
	print(f"min price index: {min_price_index}")
	print(f"max price index: {max_price_index}")
	grid_x_locations = data["gridlines_vertical_indices"]
	grid_y_locations = data["gridlines_horizonal_indices"]
	print(f"grid x locations: {grid_x_locations}")
	print(f"grid y locations: {grid_y_locations}")
	x_axis_labels = data["x_axis_labels"]
	y_axis_labels = data["y_axis_labels"]
	print(f"x axis labels: {x_axis_labels}")
	print(f"y axis labels: {y_axis_labels}")
	grid_x_matches = data["grid_x_matches"]
	print("x axis label matches to gridline positions:")
	for match in grid_x_matches:
		print(
		    f"{match[0]['text']}: {match[0]['left'] + match[0]['width'] / 2} -> {match[1]}"
		)
	grid_y_matches = data["grid_y_matches"]
	print("y axis label matches to gridline positions:")
	for match in grid_y_matches:
		print(
		    f"{match[0]['text']}: {match[0]['top'] + match[0]['height'] / 2} -> {match[1]}"
		)
	x_pair_smallest = data["x_pair_smallest"]
	x_pair_largest = data["x_pair_largest"]
	print(
	    f"smallest x value: {x_pair_smallest[0]['text']} @ {x_pair_smallest[1]}")
	print(f"largest x value: {x_pair_largest[0]['text']} @ {x_pair_largest[1]}")
	y_pair_smallest = data["y_pair_smallest"]
	y_pair_largest = data["y_pair_largest"]
	print(
	    f"smallest y value: {y_pair_smallest[0]['text']} @ {y_pair_smallest[1]}")
	print(f"largest y value: {y_pair_largest[0]['text']} @ {y_pair_largest[1]}")
	x_smallest_timestamp = data["x_smallest_timestamp"]
	x_largest_timestamp = data["x_largest_timestamp"]
	print(f"smallest x timestamp: {x_smallest_timestamp}")
	print(f"largest x timestamp: {x_largest_timestamp}")
	y_smallest_value = data["y_smallest_value"]
	y_largest_value = data["y_largest_value"]
	print(f"smallest y value: {y_smallest_value} $")
	print(f"largest y value: {y_largest_value} $")
	x_axis_difference_value = data["x_axis_difference_value"]
	x_axis_difference_pixels = data["x_axis_difference_pixels"]
	print(
	    f"x axis difference: {x_axis_difference_value} seconds per {x_axis_difference_pixels} pixels"
	)
	y_axis_difference_value = data["y_axis_difference_value"]
	y_axis_difference_pixels = data["y_axis_difference_pixels"]
	print(
	    f"y axis difference: {y_axis_difference_value} $ per {y_axis_difference_pixels} pixels"
	)
	x_seconds_per_pixel = data["x_seconds_per_pixel"]
	y_dollars_per_pixel = data["y_dollars_per_pixel"]
	print(
	    f"1 pixel on x axis is {x_seconds_per_pixel} seconds ({x_seconds_per_pixel / 86400} days)"
	)
	print(f"1 pixel on y axis is {y_dollars_per_pixel} $")

	print(f"pixel of x axis: {y_axis_location}")
	print(f"pixel of y axis: {x_axis_location}")
	time_of_y_axis = data["time_of_y_axis"]
	value_of_x_axis = data["value_of_x_axis"]
	print(f"timestamp of x axis: {time_of_y_axis}")
	print(f"value of y axis: {value_of_x_axis} $")
	print(f"bounding box: {data['bounding_box']}")
	print(
	    f"data points: {len(data['plot_data']['xs'])} vertical pixels out of {len(data['extracted_data'])}"
	)


def plot_image_data(data: dict, title: Optional[str] = None) -> Figure:
	'''
		Plots the data extracted from the image
	'''
	if title is None:
		title = "Reverse engineered chart"
	xs = data["plot_data"]["xs"]
	ys = data["plot_data"]["ys"]
	# for i, (x, y) in enumerate(zip(xs, ys)):
	# 	print(f"{i + 1}. ({x} , {y})")
	# Create new figure
	fig = plt.figure()
	# Add subplot
	ax = fig.add_subplot(1, 1, 1)
	# Plot the data
	ax.plot(xs, ys)
	# Set the title
	ax.set_title(title)
	# Set the labels
	ax.set_xlabel('Date')
	ax.set_ylabel('Price')
	# Set the grid
	ax.grid()
	# Set the size
	fig.set_size_inches(12 * 2, 9)
	# Return the figure
	return fig


def main():
	filepath_sample_image = "data/scraped/camel/charts/camelcamelcamel-B07B428M7F.png"
	img = load_image(filepath_sample_image)
	time_start = time.time()
	data = get_image_data(img, color_line_new)
	time_end = time.time()
	# Print the data
	print_image_data(data)
	print(f"Time elapsed: {time_end - time_start} seconds")
	# Plot the data
	fig = plot_image_data(data)
	# Save the figure
	fig.savefig(
	    'data/scraped/camel/charts/camelcamelcamel-B07B428M7F-reconstructed.png')


if __name__ == "__main__":
	main()
	print("ALL DONE")