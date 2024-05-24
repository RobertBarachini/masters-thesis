import os
import re
import sys
import json
import time
import random
from bs4 import BeautifulSoup as bs

# TODO: use fuzzy matching to match titles

# Globals
index = {}
override = False
shuffle_html_files = True
path_index = "data/scraped/cnet/index_articles.json"
path_data_root = "data/scraped/cnet/articles"
path_html = os.path.join(path_data_root, "html")
path_parsed = os.path.join(path_data_root, "parsed")
script_path = os.path.dirname(os.path.realpath(__file__))
stopfile_path = os.path.join(script_path, "article_parser_stop")
html_files = []
fails = []


def load_index():
	global index
	if not os.path.exists(path_index):
		print("Index file not found. Run the indexer first.")
		sys.exit(1)
	with open(path_index, "r") as f:
		index = json.load(f)
	print(f"Got {len(index['articles'])} articles in index")


def load_filenames():
	global html_files
	html_files = os.listdir(path_html)
	if shuffle_html_files is True:
		random.shuffle(html_files)
	print(f"Got {len(html_files)} html files from '{path_html}'")


def remove_tags(soup, tagnames: list):
	for tag in soup([tagnames]):
		tag.decompose()


def process_paragraph(p):
	res_text = p.text
	res_text = res_text.replace("\n", " ")
	res_text = res_text.replace("\xa0", " ")
	res_text = res_text.strip()
	res_text = re.sub(r"\s+", " ", res_text)
	return res_text


def parse_file(filepath: str):
	'''
		Parses a single html file and extracts the article content.
	'''
	global fails
	article_id = filepath.split(".")[0]
	try:
		path_output = os.path.join(path_parsed, filepath.replace(".html", ".txt"))
		if override == False and os.path.exists(path_output):
			print(f"File '{filepath}' already parsed. Skipping...")
			print("")
			return
		# print(f"Parsing file '{filepath}'")
		article_text = ""
		with open(os.path.join(path_html, filepath), "r") as f:
			article_text = f.read()
		article = index["articles"][article_id]
		soup = bs(article_text, "html.parser")
		# Remove unwanted tags
		unwanted_tags = [
		    "script", "style", "symbol", "svg", "path", "figure", "picture"
		]
		remove_tags(soup, unwanted_tags)
		title = soup.find("title").text.replace(  # type: ignore
		    " - CNET", "").strip()
		if title != article["title"]:
			print(f"WARNING: Title mismatch: '{title}' != '{article['title']}'")
			print("")
			return
		# Extract article content
		article_div = soup.find("div", {"id": f"page-article-{article_id}"})
		article_body_div = article_div.find(  # type: ignore
		    "div", {"class": "c-pageArticle_body"})  # type: ignore
		article_content_div = article_body_div.find(  # type: ignore
		    "div",
		    {"class": lambda x: x and "c-ShortcodeContent" in x})  # type: ignore
		paragraphs = article_content_div.find_all(  # type: ignore
		    "p", recursive=True)
		print(f"Found {len(paragraphs)} paragraphs")
		paragraphs_processed = list(map(process_paragraph, paragraphs))
		article_text = "\n\n".join(paragraphs_processed)
		word_count = len(article_text.split(" "))
		print(f"Word count: {word_count}")
		# Write to file
		with open(path_output, "w") as f:
			f.write(article_text)
		print(f"Successfully parsed file.")
		print("")
	except Exception as e:
		print(f"Error parsing file '{filepath}': {e}")
		print("")
		fails.append((article_id, e))
		return


def parse_all():
	'''
		Parses all html files in the html folder.
	'''
	print("Parsing all files...")
	print("")
	count_parsed = 0
	time_start = time.time()
	for i, html_filepath in enumerate(html_files):
		if os.path.exists(stopfile_path):
			print("Stopfile found. Stopping...")
			break
		path_output = os.path.join(path_parsed,
		                           html_filepath.replace(".html", ".txt"))
		if override == False and os.path.exists(path_output):
			print(
			    f"[{i+1}/{len(html_files)}] File '{html_filepath}' already parsed. Skipping..."
			)
			print("")
			continue
		print(f"[{i+1}/{len(html_files)}] Parsing file '{html_filepath}'")
		parse_file(html_filepath)
		count_parsed += 1
		if i % 100 == 0:
			time_elapsed = time.time() - time_start
			average_time = time_elapsed / count_parsed
			articles_left = len(html_files) - count_parsed
			time_left = articles_left * average_time
			print(f"Avg. time per article: {average_time}s ({time_left}s left)")
			# print(f"Time elapsed: {time_elapsed}")
			print("")
	count_successful = len(html_files) - len(fails)
	print(
	    f"Successfully parsed {count_successful}/{len(html_files)} ({round(count_successful/len(html_files)*100, 3)} %)"
	)
	print(f"Total time elapsed: {time.time() - time_start}s")
	print("")
	if len(fails) > 0:
		print(f"Failed files ({len(fails)}):")
		for fail in fails:
			print(f"  - {fail[0]}: {fail[1]}")
		print("")


def main():
	load_index()
	load_filenames()
	parse_all()


if __name__ == "__main__":
	main()
	print("Done!")
