# Master's thesis project: Data science for understanding the global semiconductor shortage

In recent years, starting in 2020 and lasting throughout 2023 we’ve been dealing with a global semiconductor, or as some call it, chip shortage, which affected many industries, automotive being one of the most affected, as well as end consumers. A complex set of events, starting with the COVID-19 pandemic, created conditions which resulted in temporary drops in production, logistics issues, increased demand, and decreases in supply which have been reflected in the shortage of many electronics components, products, as well as issues in other fields. As we followed the situation unfold throughout the years, we decided to use different data science techniques to analyse various data sources, process the data, create visualizations, and interpret them in the context of events related to the chip shortage, how they correlate with one another and how they could be used to create a system which uses these and other data sources as indicators to autonomously follow trend changes, track events, issue warnings, and help in the decision making process at company or government level to help adapt to events, detect threats, reduce their negative consequences or reduce harm in the event of another crisis, like the pandemic or the chip shortage. We sourced the data using techniques like web scraping, using APIs, and downloading aggregate statistics. Using preliminary research and iterative development, we narrowed down potential data sources and picked some of the main ones. First, we focused on sourcing electronics histories and generating electronics price trends. This was the toughest part of the research as there were many technical and other limitations, such as bot restrictions and artificial paywalls. We also created a technique for reverse engineering data from images of time series plots using computer vision and optical character recognition. We also sourced company data as well as their stock histories which were used to generate trends by industry and by sector. We used geo data to plot relevant company clusters. Cryptocurrency market data was used to explain a part of the shortage as well. World data and statistics were obtained from sites like the World Bank, WHO, IMF, and Eurostat. These were used in conjunction with other data. Population data was merged with COVID-19 incidence numbers to help explain regional events. News articles were sourced to generate relevant search term frequencies using a custom-made n-gram search engine. We also created a novel approach which uses generative AI and large language models to automate data analytics using textual data. After concluding analysis and interpretation of the results we created a proposal for a system of indicators which used newly gained understanding of the chip shortage as well as various data science techniques and system design knowledge. Although there were many challenges, most of which are described in the thesis, we managed to realize all the initially set research goals. Using extensive domain research, combined with various data science techniques and knowledge from other fields, we managed to obtain a better understanding of the chip shortage and help explain some of its causes, properties, and consequences as well as create a codebase which can be used to create more generalized solutions or products and continue research in the spirit of open source.

# Project setup

## General instructions

TODO

## Environment variables

Most of the variables are stored in the `.env` file. The file is not included in the repository, so you will have to create it yourself. The file should be located in the root of the project. You can use the `.env-template.env` file as a template.

```sh
# Copy the template file
cp .env-template.env .env
# Edit the file
nano .env
```

Certain variables (such as secrets) should be stored outside of this repo altogether. These variables should be stored in a separate .env file (e.g. `~/.env`). The variables should be exported in the `.bashrc` file.

Example (choose the location / name of the file yourself):

1. Open the .bashrc file:
   > nano ~/.bashrc
2. Add the following line to the end of the file:
   > . ~/.env
3. Save the file and exit
4. Open the .env file:
   > nano ~/.env
5. Add the following lines to the end of the file (add your own values for each key):

   ```sh
   export AWS_ACCESS_KEY_ID=""
   export AWS_SECRET_ACCESS_KEY=""
   ```

6. Save the file and exit
7. Reload the .bashrc file:
   > source ~/.bashrc

## VS Code

TODO

## Python

It is suggested you use a Conda / Mamba virtual environment for this project. Mamba is preferred over Conda, as it is faster.

### Mamba

This section covers the installation of Mamba, a faster alternative to Conda. Most of the commands are the same as for Conda.

Download and install Mamba:

```sh
# Download the Mamba installer (Mambaforge)
wget "https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-$(uname)-$(uname -m).sh"
# Install Mambaforge
chmod +x Mambaforge-$(uname)-$(uname -m).sh
bash Mambaforge-$(uname)-$(uname -m).sh
# Remove the installer
rm Mambaforge-$(uname)-$(uname -m).sh
```

To make VS Code happy, you will also have to select interpreter when prompted (usually seen at the bottom of the screen when editing a Python file). Select the interpreter in `~/mambaforge/envs/thesis/bin/python`.

Create a virtual environment:

```sh
# Create a Conda environment from the environment.yml file at src/py/environment.yml
mamba env create -f src/py/environment.yml
# Activate the environment
mamba activate thesis
# Deactivate the environment
mamba deactivate
```

Common Conda commands:

```sh
# List all environments
mamba env list
# Remove the environment
mamba env remove -n thesis
# Install a package in the specific environment
mamba install -n thesis <package>
# Remove a package from the specific environment
mamba remove -n thesis <package>
# List installed packages in select environment
mamba list -n thesis
```

### Guidelines

Style guide is defined in `./src/py/.style.yapf` and enforced by `yapf` (Google style guide with some customizations).

You can format code blocks in Jupyter notebooks using the `yapf` extension:

TODO:

```sh
# Install the extension
mamba install -n thesis -c conda-forge jupyter_contrib_nbextensions
# Enable the extension
jupyter contrib nbextension install --user
# Enable the yapf extension
jupyter nbextension enable yapf
```

It is also recommended you use type annotations in the code.

## WebDriver

The WebDriver is used to automate the browser. It is used in the `src/py/utils/scraping/selenium` module.

### ChromeDriver

My local version is `112.0.5615.49`, running on Chromium 112 on Kubuntu 22.04. If you are using a different version, you will need to download the correct version of the ChromeDriver. You can find the correct version of the ChromeDriver [here](https://chromedriver.chromium.org/downloads).

Setup:

```sh
# Download the ChromeDriver
wget https://chromedriver.storage.googleapis.com/112.0.5615.49/chromedriver_linux64.zip
# Unzip the ChromeDriver
unzip chromedriver_linux64.zip -d /tmp
# Move the ChromeDriver to the bin folder
sudo mv /tmp/chromedriver /usr/local/bin
sudo mv /tmp/LICENSE.chromedriver /usr/local/bin
# Remove the zip file
rm chromedriver_linux64.zip
```

### GeckoDriver

Minimum required Firefox version is 133.0.

Setup:

```sh
# Download the GeckoDriver
wget https://github.com/mozilla/geckodriver/releases/download/v0.33.0/geckodriver-v0.33.0-linux64.tar.gz
# Unzip the GeckoDriver
tar -xvzf geckodriver-v0.33.0-linux64.tar.gz -C /tmp
# Move the GeckoDriver to the bin folder
sudo mv /tmp/geckodriver /usr/local/bin
# Remove the zip file
rm geckodriver-v0.33.0-linux64.tar.gz
```

## Tessaract

Tessaract is used to extract text from images.

Setup:

```sh
sudo apt install tesseract-ocr -y
sudo apt install libtesseract-dev -y
```

# Maintenance

## Jupyter cleanup

You can run `find . -type f -name "*.ipynb" -exec nbstripout {} \;` within the `masters-thesis` directory to remove the outputs, metadata, and execution counts from all Jupyter notebooks. You can also set it up to run automatically before each commit.
