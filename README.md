# El País Opinion Scraper & Translator

This repository contains Deliverable 1 for the BrowserStack Customer Engineer technical assessment. It is a Python-based Selenium WebDriver script that scrapes the top five articles from the El País Opinion section, translates the titles from Spanish to English using a third-party API, and calculates the frequency of repeated words across the translated headers.

## Prerequisites
* Python 3.8+
* Google Chrome browser installed locally
* Active [BrowserStack Automate](https://automate.browserstack.com/) account
* Active [RapidAPI](https://rapidapi.com/) account (for Google Translate API)

## Installation
It is recommended to use an isolated Python virtual environment to prevent dependency conflicts.

```bash
# Create and activate the virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install required dependencies and the BrowserStack SDK
pip install -r requirements.txt
pip install browserstack-sdk
