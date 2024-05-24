# How to

## Sequential download

1. Run article_indexer.py
2. Run article_downloader.py

## Parallel download

1. Run article_indexer.py
2. Generate the task list using `src/py/scraping/cnet/article_downloader_tasks.ipynb`
3. Run `python src/py/utils/scheduler/scheduler.py -c src/py/scraping/cnet/scheduler_config.json`

Feel free to adjust the settings in `scheduler_config.json` to your liking.

It's useful to run `article_downloader.py` after the scheduler concludes to download any articles that were missed as its more efficient with startup.
