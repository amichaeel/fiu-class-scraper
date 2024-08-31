import time
import re
import csv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains

# Constants
URL = "https://pslinks.fiu.edu/psc/cslinks/EMPLOYEE/CAMP/c/COMMUNITY_ACCESS.CLASS_SEARCH.GBL?FolderPath=PORTAL_ROOT_OBJECT.CO_EMPLOYEE_SELF_SERVICE.HC_CLASS_SEARCH_GBL&IsFolder=false&IgnoreParamTempl=FolderPath,IsFolder&PortalActualURL=https%3a%2f%2fpslinks.fiu.edu%2fpsc%2fcslinks%2fEMPLOYEE%2fCAMP%2fc%2fCOMMUNITY_ACCESS.CLASS_SEARCH.GBL&PortalContentURL=https%3a%2f%2fpslinks.fiu.edu%2fpsc%2fcslinks%2fEMPLOYEE%2fCAMP%2fc%2fCOMMUNITY_ACCESS.CLASS_SEARCH.GBL&PortalContentProvider=CAMP&PortalCRefLabel=Class%20Search&PortalRegistryName=EMPLOYEE&PortalServletURI=https%3a%2f%2fpslinks.fiu.edu%2fpsp%2fcslinks%2f&PortalURI=https%3a%2f%2fpslinks.fiu.edu%2fpsc%2fcslinks%2f&PortalHostNode=CAMP&NoCrumbs=yes&PortalKeyStruct=yes"
IFRAME_ID = 'ptifrmtgtframe'
FALL_TERM = 'Fall Term 2024'
CAMPUS_NAME = "Modesto A. Maidique Campus"
CLASS_DATA_FILE = 'class_data.csv'

# Flags
EXCESS = False
INIT = True
HEADLESS = None

def init_webdriver(headless=True):
    opts = webdriver.ChromeOptions()
    if headless:
        opts.add_argument("-headless")
    return webdriver.Chrome(options=opts)

def get_department_names(dept_select):
    options = dept_select.options[1:]
    dept_names = []
    
    for i, option in enumerate(options):
        try:
            dept_name = option.text
            print(dept_name)
            dept_names.append(dept_name)
        except StaleElementReferenceException:
            print("StaleElementReferenceException caught, re-fetching department name.")
            # Re-fetch the select element and the current option
            dept_select_element = Select(WebDriverWait(option.parent, 10).until(
                EC.presence_of_element_located((By.ID, 'SSR_CLSRCH_WRK_ACAD_ORG$2'))
            ))
            # Use the re-fetched option from the same index
            option = dept_select_element.options[i+1]
            dept_name = option.text
            dept_names.append(dept_name)
            print(dept_name)
    
    return dept_names

def select_term(driver, wait, term):
    term_select_element = wait.until(EC.element_to_be_clickable((By.ID, 'CLASS_SRCH_WRK2_STRM$35$')))
    term_select = Select(term_select_element)
    term_select.select_by_visible_text(term)
    print(f"==> {term} selected")

def select_campus(driver, wait, campus):
    location_select_element = wait.until(EC.element_to_be_clickable((By.ID, 'SSR_CLSRCH_WRK_CAMPUS$0')))
    location_select = Select(location_select_element)
    location_select.select_by_visible_text(campus)
    print(f"==> {campus} selected")

def uncheck_open_classes_only(driver, wait):
    checkbox_element = wait.until(EC.element_to_be_clickable((By.ID, 'SSR_CLSRCH_WRK_SSR_OPEN_ONLY$7')))
    ActionChains(driver).move_to_element(checkbox_element).perform()
    try:
        checkbox_element.click()
    except ElementClickInterceptedException:
        print("Failed to uncheck through Selenium. Executing JavaScript")
        driver.execute_script("arguments[0].click();", checkbox_element)
    print("==> Unchecked 'Open Classes Only'")

def click_search_button(driver, wait):
    search_button_element = wait.until(EC.element_to_be_clickable((By.ID, 'CLASS_SRCH_WRK2_SSR_PB_CLASS_SRCH')))
    driver.execute_script("arguments[0].scrollIntoView(true);", search_button_element)
    try:
        search_button_element.click()
        print("==> Search button clicked")
    except ElementClickInterceptedException:
        print("Click intercepted, attempting JavaScript click.")
        driver.execute_script("arguments[0].click();", search_button_element)
        print("==> Search button clicked via JavaScript")

def get_course_attributes(attr_select):
  options = attr_select.options[1:]
  attributes = []
  
  for i, option in enumerate(options):
    try:
      attr_name = option.text
      attributes.append(attr_name)
    except StaleElementReferenceException:
      print("StaleElementReferenceException caught, re-fetching attribute name.")
      attr_select_element = Select(WebDriverWait(option.parent, 10).until(
          EC.presence_of_element_located((By.ID, 'SSR_CLSRCH_WRK_CRSE_ATTR$14'))
      ))
      # Use the re-fetched option from the same index
      option = attr_select_element.options[i+1]
      attr_name = option.text
      attributes.append(attr_name)
      
  return attributes
      
def handle_edge_cases(driver, wait, dept, excess_depts, attribute=None):
    global EXCESS
    global INIT
    try:
        time.sleep(2)
        wait.until(
            lambda d: d.find_elements(By.ID, 'DERIVED_CLSMSG_ERROR_TEXT') or
                      d.find_elements(By.ID, '#ICSave') or
                      d.find_elements(By.ID, 'win0divSSR_CLSRSLT_WRK_GROUPBOX1')
        )
        error_elements = driver.find_elements(By.ID, 'DERIVED_CLSMSG_ERROR_TEXT')
        if error_elements:
            error_text = error_elements[0].text
            if "200" in error_text:
              if INIT:
                excess_depts.append(dept)
                EXCESS = True
                print(f"==> {dept} has over 200 results. Skipping")
              else: 
                print(f"==> {dept} has over 200 results using the {attribute} attribute. Skipping")
            else:
              print(f"==> No results found for department: {dept}")
            return False

        if driver.find_elements(By.ID, '#ICSave'):
            print("===> More than 50 entries warning detected, clicking OK.")
            driver.find_element(By.ID, '#ICSave').click()
            wait.until(EC.staleness_of(driver.find_element(By.ID, '#ICSave')))
        
        print("==> Page loaded.")
        return True
    except TimeoutException:
        print("===> Timed out waiting for page to load or detect messages.")
        return False

def extract_class_data(driver, num_entries):
    class_data = []
    for i in range(num_entries):
        entry = {}
        name_parent = driver.find_element(By.ID, f"win0divSSR_CLSRCH_MTG1${i}")
        entry['class name'] = name_parent.find_element(By.TAG_NAME, "div").text.strip()
        entry['time'] = driver.find_element(By.ID, f'MTG_DAYTIME${i}').text.strip()
        entry['location'] = driver.find_element(By.ID, f'MTG_ROOM${i}').text.strip()
        entry['instructors'] = driver.find_element(By.ID, f'MTG_INSTR${i}').text.strip()
        entry['dates'] = driver.find_element(By.ID, f'MTG_TOPIC${i}').text.strip()
        entry['campus'] = driver.find_element(By.ID, f'DERIVED_CLSRCH_DESCR${i}').text.strip()
        if entry['time'] != 'TBA':
            class_data.append(entry)
    return class_data

def save_class_data(writer, class_data, dept):
    try:
        for entry in class_data:
            writer.writerow(entry)
        print(f"==> All classes in {dept} have been written to CSV")
    except Exception as e:
        print(f"Error writing to file: {e}")
        if input("Exit program? (Y/n)").lower() == "y":
            exit()

def scraper(excess_depts):
  global EXCESS
  global INIT
  global HEADLESS
  HEADLESS = input("Run program headless? (Y/n)\n").lower() == 'y' if HEADLESS == None else HEADLESS
  driver = init_webdriver(HEADLESS)
  wait = WebDriverWait(driver, 20)

  try:
      print("Loading URL...")
      driver.get(URL)
      print("Load complete.")
  
      select_term(driver, wait, FALL_TERM)
      select_campus(driver, wait, CAMPUS_NAME)

      dept_select_element = wait.until(EC.element_to_be_clickable((By.ID, 'SSR_CLSRCH_WRK_ACAD_ORG$2')))
      dept_select = Select(dept_select_element)
      print("Retrieving department names...")
      dept_names = get_department_names(dept_select) if INIT else excess_depts
      print("Departments retrieved:", dept_names)
      write_type = 'w' if INIT else 'a'
      
      with open(CLASS_DATA_FILE, write_type, newline='') as csvfile:
          fieldnames = ['class name', 'time', 'location', 'instructors', 'dates', 'campus']
          writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
          writer.writeheader()

          for index, dept in enumerate(dept_names):
              print(f"\n===> Current department: {dept} | {index+1} out of {len(dept_names)} <=== \n")
              driver.get(URL)
              time.sleep(1)
              dept_select_element = wait.until(EC.element_to_be_clickable((By.ID, 'SSR_CLSRCH_WRK_ACAD_ORG$2')))
              dept_select = Select(dept_select_element)
              dept_select.select_by_visible_text(dept)

              uncheck_open_classes_only(driver, wait)
              select_campus(driver, wait, CAMPUS_NAME)
              
              if EXCESS and not INIT:
                print("Expanding course attributes dropdown...")
                expand_element = wait.until(EC.element_to_be_clickable((By.ID, 'DERIVED_CLSRCH_SSR_EXPAND_COLLAPS$149$$3')))
                expand_element.click()
                print("==> Course attribute dropdown expanded.")
                attribute_select_element = wait.until(EC.element_to_be_clickable((By.ID, 'SSR_CLSRCH_WRK_CRSE_ATTR$14')))
                attribute_select = Select(attribute_select_element)
                attributes = get_course_attributes(attribute_select)
                
                for i, attr in enumerate(attributes):
                  time.sleep(2)
                  attribute_select_element = wait.until(EC.element_to_be_clickable((By.ID, 'SSR_CLSRCH_WRK_CRSE_ATTR$14')))
                  attribute_select = Select(attribute_select_element)
                  print("==> Selecting course attribute")
                  attribute_select.select_by_visible_text(attr)
                  print(f"==> Course attribute selected: {attr} | {i+1} out of {len(attributes)}")
                  click_search_button(driver, wait)
                  
                  if handle_edge_cases(driver, wait, dept, excess_depts, attr):
                    num_sections_text = driver.find_element(By.CLASS_NAME, 'PSGROUPBOXLABEL').text
                    num_entries = int(re.search(r'\d+', num_sections_text).group())
                    print(f"Number of class sections found: {num_entries}")

                    class_data = extract_class_data(driver, num_entries)
                    save_class_data(writer, class_data, dept)
                    print("Clicking modify search to continue through attributes...")
                    mod_search_element = wait.until(EC.element_to_be_clickable((By.ID, 'CLASS_SRCH_WRK2_SSR_PB_MODIFY')))
                    mod_search_element.click()
                    print("==> Modify search clicked")            
              else:
                click_search_button(driver, wait)

                if handle_edge_cases(driver, wait, dept, excess_depts):
                    num_sections_text = driver.find_element(By.CLASS_NAME, 'PSGROUPBOXLABEL').text
                    num_entries = int(re.search(r'\d+', num_sections_text).group())
                    print(f"Number of class sections found: {num_entries}")

                    class_data = extract_class_data(driver, num_entries)
                    save_class_data(writer, class_data, dept)
  finally:
      driver.quit()
      INIT = False

def main():
  excess_depts = []
  scraper(excess_depts)
  if EXCESS and not INIT:
    print("==> Excess departments found.")
    scraper(excess_depts)

if __name__ == "__main__":
    main()