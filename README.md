# FIU Class Scraper

### Overview
fiu-class-scraper is a Python script designed to scrape and download class information for the current semester at Florida International University (FIU). Specifically, it's set up to retrieve undergraduate class data from the Modesto A. Maidique Campus (MMDC). The script accesses FIU's public class search website, navigates through different departments, and extracts detailed information about each class, including class name, time, location, instructors, dates, and campus.

### Features
- Automated scraping of class data from FIU's public class search portal.
- Ability to run in a headless mode for faster execution.
- Extracts detailed class information.
- Outputs data in a CSV format for easy use and analysis.

### Prerequisites
Before you begin, ensure you have met the following requirements:

- You have installed Python 3.x.
- You have a basic understanding of Python and web scraping.
- You have Firefox installed on your machine (required for the Selenium Firefox webdriver).

### Installation
- Clone the repo:
```bash
git clone https://github.com/yourusername/fiu-class-scraper.git
```
- Navigate to the project directory
```bash
cd fiu-class-scraper
```

- Install selenium
```bash
pip install selenium
```

### Usage
To run the script, execute the following command in your terminal:
```bash
python fiu_class_scraper.py
```

You will be prompted to choose whether to run the program in headless mode. Answer Y for yes or n for no. The script will then automatically navigate through the class search website, select the appropriate filters, and begin scraping data.

### Output
The scraped data will be saved in a file named class_data.csv in the project directory. This file includes the following fields: class name, time, location, instructors, dates, and campus.

### Customization
The script is currently set up for undergraduate classes at MMDC, but it can be modified for different campuses or academic levels. You can adjust the selection criteria in the script to meet your specific needs.