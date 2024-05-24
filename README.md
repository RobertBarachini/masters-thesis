# Master's thesis project: Data science for understanding the global semiconductor shortage

TODO: Abstract

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
