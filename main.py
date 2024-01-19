import time
import re
import csv

from selenium import webdriver
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

url = "https://pslinks.fiu.edu/psc/cslinks/EMPLOYEE/CAMP/c/COMMUNITY_ACCESS.CLASS_SEARCH.GBL&FolderPath=PORTAL_ROOT_OBJECT.HC_CLASS_SEARCH_GBL&IsFolder=false&IgnoreParamTempl=FolderPath,IsFolder"

with open('class_data.csv', 'w', newline='') as csvfile:
  fieldnames = ['class name', 'time', 'location', 'instructors', 'dates', 'campus']
  writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
  writer.writeheader()
  
  # let user choose to run program headless
  opts = Options()
  opts.add_argument("-headless") if input("Run program headless? (Y/n)\n").lower() == 'y' else None
  driver = Firefox(options=opts)
  wait = WebDriverWait(driver, 20)
  
  print("Launching initial load to get all departments.")
  driver.get(url)
  print("Load complete. Getting departments.")

  # loop through departments
  dept_select_element = wait.until(EC.element_to_be_clickable((By.ID, 'SSR_CLSRCH_WRK_ACAD_ORG$2')))
  dept_select = Select(dept_select_element)
  dept_names = list(map(lambda x : x.get_attribute("innerHTML").replace("&amp;", "&"), dept_select.options))[1:]
  print("Departments retrieved. Beggining scrape... \n\n")
  for index, dept in enumerate(dept_names):
    print("Loading web page...")
    driver.get(url)
    print("=> Page loaded")
    
    print(f"\n===> Current department: {dept} | {index+1} out of {len(dept_names)} <=== \n")
    # select department
    dept_select_element = wait.until(EC.element_to_be_clickable((By.ID, 'SSR_CLSRCH_WRK_ACAD_ORG$2')))
    dept_select = Select(dept_select_element)
    dept_select.select_by_visible_text(dept)
    
    # set location to main campus
    print("==> Selecting campus")
    location_select_element = wait.until(EC.element_to_be_clickable((By.ID, 'SSR_CLSRCH_WRK_CAMPUS$0')))
    location_select = Select(location_select_element)
    location_select.select_by_visible_text('Modesto A. Maidique Campus')  # select main campus
    print("==> Campus selected")
    
    # narrow search results to undergrad,
    print("==> Selecting undergrad")
    time.sleep(1)
    career_select_element = wait.until(EC.element_to_be_clickable((By.ID, 'SSR_CLSRCH_WRK_ACAD_CAREER$5')))
    career_select = Select(career_select_element)
    career_select.select_by_visible_text('Undergraduate')
    print("==> Undergrad selected")
    
    print("==> Clicking search button for ")
    search_button_element = wait.until(EC.element_to_be_clickable((By.ID, 'CLASS_SRCH_WRK2_SSR_PB_CLASS_SRCH')))
    search_button_element.click()
    print("==> Search button clicked")
    
    # edge cases: page has more than 50, or page has 0.
    print("==> Page loaded. Checking for edge cases.")
    try:
      # wait for either the "no results" message. the "more than 50 entries" warning, or element that signals page load
      time.sleep(2)
      WebDriverWait(driver, 10).until(
        lambda d: d.find_elements(By.ID, 'DERIVED_CLSMSG_ERROR_TEXT') or # no results
                  d.find_elements(By.ID, '#ICSave') or # more than 50 
                  d.find_elements(By.ID, 'win0divSSR_CLSRSLT_WRK_GROUPBOX1') # page loaded
      )
      no_results_elements = driver.find_elements(By.ID, 'DERIVED_CLSMSG_ERROR_TEXT')
      search_warning_element = driver.find_elements(By.ID, '#ICSave')
      
      if len(no_results_elements) > 0:
        print(no_results_elements)
        print(f"==> No results found for department: {dept}")
        continue  # Skip to the next department
      
      # check for more than 50 warning and click ok if present
      elif len(search_warning_element) > 0:
        print("===> More than 50 entries warning detected, clicking OK.")
        driver.find_element(By.ID, '#ICSave').click()
        WebDriverWait(driver, 10).until(
          EC.staleness_of(search_warning_element[0])
        )
      else: print("==> Page loaded...")
    except TimeoutException:
      print("===> Timed out waiting for page to load or detect messages.")
      exit()

    # find number of entries
    num_entries = 0
    num_sections_text = driver.find_element(By.CLASS_NAME, 'PSGROUPBOXLABEL').text

    # Use regular expression to extract the number from the text
    match = re.search(r'\d+', num_sections_text)
    if match:
        num_entries = int(match.group())
    else:
        num_entries = 0  # Default to 0 if no number is found

    print(f"Number of class sections found: {num_entries}")

    class_data = []
    for i in range(num_entries):  
      entry = {}
      # extracting each piece of information
      name_parent = driver.find_element(By.ID, f"win0divSSR_CLSRCH_MTG1${i}")
      entry['class name'] = name_parent.find_element(By.TAG_NAME, "div").text
      entry['time'] = driver.find_element(By.ID, f'MTG_DAYTIME${i}').text
      entry['location'] = driver.find_element(By.ID, f'MTG_ROOM${i}').text
      entry['instructors'] = driver.find_element(By.ID, f'MTG_INSTR${i}').text
      entry['dates'] = driver.find_element(By.ID, f'MTG_TOPIC${i}').text
      entry['campus'] = driver.find_element(By.ID, f'DERIVED_CLSRCH_DESCR${i}').text
      # check if class is online by time being TBA. no need to add
      online = entry['time'] == 'TBA'
      if online: continue
      class_data.append(entry)
    
    # write data to csv
    try:
      for entry in class_data: writer.writerow(entry)
      print(f"==> All classes in {dept} have been written to csv")
    except (RuntimeError, TypeError, NameError):
      user_input = input("An error occured writing to file. Exit program? (Y/n)")
      if user_input.lower() == "Y": exit()
    
  # close the browser
  driver.quit()