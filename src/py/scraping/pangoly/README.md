# Instructions

Use `scraper_indexer.py` to index the site. It creates a file `data/scraped/pangoly/index.json` with an index for all of the products for each of the selected categories. The script is fault tolerant and can be run multiple times. It will only add new products to the index. If you want to re-index everything, delete the `index.json` file.

Use `scraper_handler.py` to do the scraping. It provisions workers (individual processes) based on the `index.json` file. Each worker `scraper_worker.py` scrapes a product page and saves the data to a file in `data/scraped/pangoly/<product_hierarchy>/<product_key>.json`.

# Run

Make sure to inspect all of the settings and intermediate outputs before running anything.

1. Index the site: `python src/py/scraping/pangoly/scraper_indexer.py`
2. Generate the task list using `src/py/scraping/pangoly/index.ipynb`
3. Scrape using the task scheduler to provision workers: `python src/py/utils/scheduler/scheduler.py -c src/py/scraping/pangoly/scheduler_config.json`

Scraper for an individual product is `src/py/scraping/pangoly/scraper_worker.py`. It can be run directly for testing purposes (change `DEBUG_MODE = True` in the file)
