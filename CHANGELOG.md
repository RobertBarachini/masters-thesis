# Commits from local repository

Public repository has been reinitialized to decrease bloat. Here are the commit messages from the local repository up to the reinitialization.

- 2024-05-05 Create data science process pipeline specific to the thesis
- 2024-05-03 Fix typo in data science diagram
- 2024-05-03 Create data science process pipeline
- 2024-05-02 Create generic data acquisition process diagram
- 2024-05-02 Update HICP notebooks
- 2024-04-14 Update location visualizations
- 2024-04-03 Add GFLOPS to abbreviations
- 2024-04-02 Update date event about sanctions
- 2024-04-02 Fix event date for ChatGPT release
- 2024-04-02 Add note for Word bug in find and replace
- 2024-04-01 Add slovenian translations to abbreviations
- 2024-04-01 Fix year in TRW2
- 2024-03-31 Create abbreviations for the thesis
- 2024-03-31 Fix Python environment file syntax error
- 2024-03-17 Create diagram for the ETL process and the system of indicators
- 2024-03-16 Merge visualizations of all domains
- 2024-03-16 Add some statistics to category_analysis_clean
- 2024-03-15 Update merge_images to show a single legend
- 2024-03-15 Implement notebook for automatically arranging category visualizations per domain into a 2x2 grid
- 2024-03-14 Update graphic in category_analysis
- 2024-03-14 Update exclusion-list for smaller backups
- 2024-03-14 Update notebooks for thesis writing purposes
- 2024-03-13 Generate and store visualization for different imputation methods
- 2024-03-13 Add and generate product history and category visualizations for the thesis
- 2024-03-12 Update RAM requirements
- 2024-03-12 Finalize category_analysis_clean
- 2024-03-12 Create category_analysis_clean for product, category, and domain analysis
- 2024-03-12 Update category_analysis
- 2024-03-10 Finalize sectors_industries
- 2024-03-10 Update events
- 2024-03-10 Slight update to crypto_plots_index and validate results
- 2024-03-10 Finalize crypto_plots_index
- 2024-03-09 Update events and finance_df_utils
- 2024-03-09 Update CPI process
- 2024-03-05 Further improve processing of product price histories, add index adjustments, inflation adjustments, ...
- 2024-03-05 Update category analysis with np.convolve smoothing
- 2024-03-03 Update category_analysis for Amazon products
- 2024-03-03 Create alternative index notebook for Amazon products
- 2024-03-03 Create events
- 2024-03-03 Fix plot label for all market performance from price to index
- 2024-03-03 Update sectors_industries to use the updated finance utils and CPI adjustments
- 2024-03-03 Drop NaN values after resampling in get_grouped_df
- 2024-03-02 Update finance_df_utils
- 2024-03-02 Add CPI adjustments to crypto plots
- 2024-03-02 Implement cpi_adjust utility
- 2024-03-02 Rename cpi-process to cpi_process
- 2024-03-01 Re-commit CPI notebooks
- 2024-03-01 Create functions to use CPI data to adjust dataframes for inflation
- 2024-02-28 Create currency pairs processing and plotting notebook
- 2024-02-27 Update cpi and inflation notebooks
- 2024-02-25 Create automatic text analysis with OpenAI LLM
- 2024-02-25 Update text-exploration-parsed keywords and resampling
- 2024-02-25 Add article and word character counts to text-exploration
- 2024-02-20 Update text-exploration-parsed
- 2024-02-19 Update text-exploration to use pre-tokenized articles
- 2024-02-19 Create cpi and inflation notebooks
- 2024-02-16 Update covid plots
- 2024-02-12 Update merge_incidence_population
- 2024-02-10 Create alternative Keepa category analysis notebook
- 2024-01-30 Process article tokens and create an ngram index for search and plotting search term frequencies
- 2024-01-28 Start work on text mining articles
- 2024-01-28 Create notebook to merge Covid and population data and plot it
- 2024-01-28 Implement notebook for generating crypto plots
- 2024-01-28 Add drawio extension
- 2024-01-27 Make some small adjustments to plots
- 2024-01-27 Upgrade visualizations for finance charts and generate all Yahoo finance sectors, industries aggregate charts
- 2024-01-26 Create utility function for calculating trends and plotting stocks and similar data
- 2024-01-24 Update yahoo sector plots
- 2024-01-24 Update stocks analysis and plots
- 2024-01-24 Create analysis notebook for Yahoo stocks
- 2024-01-23 Update geo visualization for company data
- 2024-01-23 Update scraper_companies to read sector and industry from profile for Yahoo finance
- 2024-01-22 Merge Yahoo sectors companies with geo data and plot with plotly
- 2024-01-22 Add geocoding data from Google API
- 2024-01-21 Create a diagram summarizing the data acquisition process
- 2024-01-18 Add HICP database and plot Personal Computers index from Eurostat
- 2024-01-18 Add total number of countries to World Bank population notebook
- 2024-01-17 Fetch population data from World Bank
- 2024-01-17 Fetch Covid data from WHO
- 2024-01-10 Create geopy supported script for adding company geo data from Yahoo profile info
- 2024-01-08 Update Keepa jupyter notebook for statistics of downloaded data for all domains
- 2024-01-08 Update IMF weo and dataflows exploration
- 2024-01-02 Create IMF World Economic Outlook Database downloader, fix encoding issues, convert csv to dictionary and make it queryable then display some examples
- 2023-12-31 Implement IMF API
- 2023-12-31 Create scraper for currency exchange rates from Yahoo Finance
- 2023-12-31 Update archive exclusion-list
- 2023-12-31 Improve efficiency of backup script by applying exclusion rules directly in 7z and skip creating a copy of the project folder
- 2023-12-31 Add data/scraped/cnet/articles/html to purge list in backup script
- 2023-12-31 Add fails count to cnet article parser
- 2023-12-30 Create parser for Cnet article html files
- 2023-12-30 Add a function to print failed tasks while the scheduler is running
- 2023-12-30 Create cnet article parser
- 2023-12-30 Create article_downloader_worker for cnet which is controller by scheduler.py
- 2023-12-30 Create Cnet article indexer and downloader
- 2023-12-29 Write scraper for Yahoo finance companies profiles
- 2023-12-28 Write scraper for Yahoo stocks for each company in sectors
- 2023-12-27 Create scraper for Yahoo Finance sectors and their industries and their companies list
- 2023-12-16 Update VS Code settings
- 2023-12-05 Create a project backup script to automate daily backups
- 2023-12-04 Implement a scraper for crypto CSV data from Yahoo
- 2023-12-04 Create Yahoo crypto crawler to create an index
- 2023-12-04 Simplify wrapper return type annotation
- 2023-12-04 Streamline category analysis
- 2023-11-29 Change reviews and rating to use the avg30 smoothed window
- 2023-11-29 Update logic for plotting reviews and rating and also fix bug with cutoff date
- 2023-11-29 Create a way to process all product categories and get trends for an Amazon domain just once and storing results in numpy binary objects
- 2023-11-28 Test different combinations for plotting
- 2023-11-28 Streamline plotting for category trends
- 2023-11-28 Add minimum count of datapoints for each csv key in a product to be eligible to be added to trends
- 2023-11-28 Create a way to analyze and visualize price trends for an entire category of products
- 2023-11-27 Change get_trends so that we keep the sum of all values for a specific value type for a specific day
- 2023-11-27 Create keepa_analysis_utils which hosts a list of functions from notebooks that will be used to generate trend data and visualizations
- 2023-11-27 Start work on Keepa category_analysis
- 2023-11-27 Update workspace cspell words
- 2023-11-25 Idk why I have to commit this again - I already did with this version
- 2023-11-25 Write categories and products json for domain 1
- 2023-11-25 Create gitignore for generated files from and for keepa analysis
- 2023-11-25 Construct product categories from product types and subcategories for analysis
- 2023-11-25 product_category_analysis checkpoint
- 2023-11-25 Checkpoint
- 2023-11-25 Checkpoint for product_category_analysis again
- 2023-11-25 Checkpoint for product_category_analysis
- 2023-11-25 Create product analysis with different imputation methods
- 2023-11-25 Create imputation methods comparison visualization
- 2023-11-25 Update product_category_analysis
- 2023-11-23 Add domain_id to logging for each product iteration
- 2023-11-23 Fix bug in log_settings
- 2023-11-23 Improve api_products_downloader to iterate over multiple domains for all products
- 2023-11-21 Ran api_result_analysis on updated file list
- 2023-11-20 Rerunning product_search_analysis after finishing the camel search
- 2023-11-20 Rerunning api_results_analysis after finishing the camel search
- 2023-11-20 Improve product_category_analysis
- 2023-11-19 Create product_category_analysis for Keepa product objects
- 2023-11-18 Add newline to each search iteration to make it more readable
- 2023-11-18 Fix type_text return type in selenium_utils
- 2023-11-18 Use new utility for quicker installation of uBlock Origin
- 2023-11-18 Write a utility for downloading and installing uBlock Origin from local storage in selenium_utils
- 2023-11-18 Replace race order so that LOCATOR_HIGH_VOLUME_OF_SEARCHES has priority over LOCATOR_INCLUDE_NOT_IN_STOCK when both are present
- 2023-11-18 Fix some logic in try_getting_results
- 2023-11-18 Refactor try_getting_results in indexer_passive to include a simpler retry logic
- 2023-11-18 Update Mamba setup instructions in README.md
- 2023-11-18 Implement a way to move errored files in api_result_analysis to trash using the new utility
- 2023-11-18 Removed retries from request in api_products_downloader
- 2023-11-18 Add retries and timeout option to requests in api_products_downloader
- 2023-11-18 Move pip dependencies from README.md to environment.yml
- 2023-11-18 Add Jupyter extension to extensions.json and add notebookFileRoot to be workspaceFolder in project settings.json
- 2023-11-18 Add .trash to gitignore
- 2023-11-18 Implement trash utility to make it possible to "delete" files safely with recovery options
- 2023-11-18 Add some more stats to Keepa api_result_analysis notebook
- 2023-11-17 Add quick Keepa api downloaded results analysis
- 2023-11-17 Swap file write and wait order in api_products_downloader
- 2023-11-17 Update api_products_downloader path and logger then validate a sample product response parsed csv
- 2023-11-17 Fix log path
- 2023-11-17 Implement Keepa API products downloader
- 2023-11-17 Remove scraper_products - not needed
- 2023-11-17 Update product_search_analysis and api_investiogation_clean
- 2023-11-17 Improve camel html search page parsing and analysis
- 2023-11-16 Idk why it didn't save before xd
- 2023-11-16 Clean up dedicated functions for interacting with Keepa API in api_investigation_clean.ipynb
- 2023-11-16 Add example to generic_utils.py
- 2023-11-16 Write html analysis tool for camel product search scraper
- 2023-11-16 Create working get_element_by_race in selenium_utils
- 2023-11-16 Create alternative pangoly index product list generator
- 2023-11-16 Update camel search indexer
- 2023-11-14 Create passive scraping indexer for Camel product search
- 2023-11-14 Update selenium utils
- 2023-11-14 Update Pangoly index analysis
- 2023-11-14 Update settings
- 2023-11-14 Replace Python deprecated yapf formatter with an extension
- 2023-11-13 Implement Keepa diret API access for product searches
- 2023-11-12 Continue with Keepa API investigation
- 2023-11-12 Update Camel cv-demo Notebook for thesis visualizations
- 2023-11-12 Remove thunder-client from repo
- 2023-11-01 Add merge_stocks function to visualization in Yahoo
- 2023-10-31 Implement custom visualizations for stock-like data with plotly
- 2023-10-29 Implement scraper for Yahoo Finance stocks
- 2023-10-29 Implement Yahoo Finance crawler and symbol similarity visualization
- 2023-10-28 Update logger class with custom methods for info, error, debug, warning and critical
- 2023-10-28 Commit changes for Keepa API investigation, fuzzy string matching and testing proxies
- 2023-05-05 Implement a way to pause and resume the scheduler
- 2023-05-05 Implement scheduler_data_analyzer
- 2023-05-05 Start work on camel indexer
- 2023-05-03 Add type annotations, clean up prints in chart_to_data
- 2023-05-03 Refactor, extend and simplify chart_to_data actual
- 2023-05-03 Refactor, extend and simplify chart_to_data
- 2023-05-03 Implement chart_to_data library
- 2023-05-01 Implement cv-demo to extract line chart data from images
- 2023-05-01 Start implementation of line chart data reconstruction from image
- 2023-04-30 Optimize scraper_worker.py for pangoly
- 2023-04-29 Implement proxy library, add geonode proxy provider
- 2023-04-28 Add rate limiting check to worker
- 2023-04-28 Implement task scheduler, add logging, improve worker
- 2023-04-24 Add logger to pangoly scraper_indexer
- 2023-04-24 Extend logger with Logger class for convenience
- 2023-04-24 Implement logger and pangoly indexer and scraping worker
- 2023-04-18 Implement browsermob-proxy support
- 2023-04-17 Implement Selenium driver
- 2023-04-11 Write some utilities for processing data
- 2023-04-06 Set up project for Python development
- 2023-04-06 Init repo
