# Import necessary packages for web scraping and logging
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import random
import time
import getpass

# Configure logging settings
logging.basicConfig(filename="scraping.log", level=logging.INFO)

TARGET_JOBTITLE = input("Enter the job title you are looking for: \n")
TARGET_JOBLEVEL = int(input("Enter Experience level: (1.Internship 2.Entry level 3.Associate 4.Mid-Senior level 5.Director 6.Executive)\n").strip())
TARGET_POSTDATE = input("Enter Date posted: (1.Any Time 2.Past Month 3.Past Week 4.Past 24 hours)\n").strip()
TARGET_JOBTYPE = input("Enter Job type: (1.Full-time 2.Part-time 3.Contract 4.Temporary 5.Volunteer 6.Internship 7.Other) \n").strip()

# Ask user for LinkedIn credentials
username = input("Enter your LinkedIn email: ")
password = getpass.getpass("Enter your LinkedIn password: ")  # Hidden input

# Mappings for date posted
date_posted = {
    '1': '',        # Any time
    '2': 'r2592000',  # Past month (30 days)
    '3': 'r604800',   # Past week (7 days)
    '4': 'r86400'     # Past 24 hours
}
job_type = {
    '1': 'F',   
    '2': 'P',  
    '3': 'C',   
    '4': 'T',
    '5': 'V',
    '6': 'I',
    '7': 'O'
}

base_url = 'https://www.linkedin.com/jobs/search/'
search_url = f"{base_url}?keywords={TARGET_JOBTITLE}"
if TARGET_JOBLEVEL:
    search_url += f"&f_E={TARGET_JOBLEVEL}"
if TARGET_POSTDATE:
    search_url += f"&f_TPR={date_posted[TARGET_POSTDATE]}"
if TARGET_JOBTYPE:
    search_url += f"&f_JT={job_type[TARGET_JOBTYPE]}"


def scrape_linkedin_jobs():

    # Log a message indicating that we're starting a LinkedIn job search
    logging.info(f'Starting LinkedIn job scrape for "{TARGET_JOBTITLE}" ...')

    # Sets the pages to scrape if not provided
    pages = 10

    # Specify the path to your WebDriver executable
    service = Service(executable_path='chromedriver-mac-arm64/chromedriver')

    # Initialize Chrome WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument("start-maximized")  # Start maximized
    driver = webdriver.Chrome(service=service, options=options)

    # Step 1: Open LinkedIn Login Page
    driver.get("https://www.linkedin.com/login")
    time.sleep(2)  # Wait for the page to load

    # Step 2: Locate the username and password fields, then enter credentials
    driver.find_element(By.ID, "username").send_keys(username)
    driver.find_element(By.ID, "password").send_keys(password)

    # Step 3: Submit the login form
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    time.sleep(5)  # Wait for login to complete

    # Step 4: Verify login success
    if "feed" in driver.current_url:  
        print("Login successful!")
    else:
        print("Login failed. Check your credentials.")
        driver.quit()
        exit()

    # Navigate to the LinkedIn job search page with the given job title and location
    driver.get(search_url)

    # # Scroll through the first 50 pages of search results on LinkedIn
    # for i in range(pages):

    #     # Log the current page number
    #     logging.info(f"Scrolling to bottom of page {i+1}...")

    #     # Scroll to the bottom of the page using JavaScript
    #     driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    #     try:
    #         # Wait for the "Show more" button to be present on the page
    #         element = WebDriverWait(driver, 5).until(
    #             EC.presence_of_element_located(
    #                 (By.XPATH, "/html/body/div[1]/div/main/section[2]/button")
    #             )
    #         )
    #         # Click on the "Show more" button
    #         element.click()

    #     # Handle any exception that may occur when locating or clicking on the button
    #     except Exception:
    #         # Log a message indicating that the button was not found and we're retrying
    #         logging.info("Show more button not found, retrying...")

    #     # Wait for a random amount of time before scrolling to the next page
    #     time.sleep(random.choice(list(range(3, 7))))

    # Scrape the job postings
    jobs = []
    soup = BeautifulSoup(driver.page_source, "html.parser")
    job_listings = soup.find_all(
        "div",
        class_="base-card relative w-full hover:no-underline focus:no-underline base-card--link base-search-card base-search-card--link job-search-card",
    )
    
    try:
        for job in job_listings:
            # Extract job details

            # job title
            job_title = job.find("h3", class_="base-search-card__title").text.strip()
            # job company
            job_company = job.find(
                "h4", class_="base-search-card__subtitle"
            ).text.strip()
            # job location
            job_location = job.find(
                "span", class_="job-search-card__location"
            ).text.strip()
            # job link
            apply_link = job.find("a", class_="base-card__full-link")["href"]

            # Navigate to the job posting page and scrape the description
            driver.get(apply_link)

            # Sleeping randomly
            time.sleep(random.choice(list(range(5, 11))))

            # Use try-except block to handle exceptions when retrieving job description
            try:
                # Create a BeautifulSoup object from the webpage source
                description_soup = BeautifulSoup(driver.page_source, "html.parser")

                # Find the job description element and extract its text
                job_description = description_soup.find(
                    "div", class_="description__text description__text--rich"
                ).text.strip()

            # Handle the AttributeError exception that may occur if the element is not found
            except AttributeError:
                # Assign None to the job_description variable to indicate that no description was found
                job_description = None

                # Write a warning message to the log file
                logging.warning(
                    "AttributeError occurred while retrieving job description."
                )

            # Add job details to the jobs list
            jobs.append(
                {
                    "title": job_title,
                    "company": job_company,
                    "location": job_location,
                    "link": apply_link,
                    "description": job_description,
                }
            )
            # Logging scrapped job with company and location information
            logging.info(f'Scraped "{job_title}" at {job_company} in {job_location}...')

    # Catching any exception that occurs in the scrapping process
    except Exception as e:
        # Log an error message with the exception details
        logging.error(f"An error occurred while scraping jobs: {str(e)}")

        # Return the jobs list that has been collected so far
        # This ensures that even if the scraping process is interrupted due to an error, we still have some data
        return jobs

    # Close the Selenium web driver
    driver.quit()

    # Return the jobs list
    return jobs

def save_job_data(data: dict) -> None:
    """
    Save job data to a CSV file.

    Args:
        data: A dictionary containing job data.

    Returns:
        None
    """

    # Create a pandas DataFrame from the job data dictionary
    df = pd.DataFrame(data)

    # Save the DataFrame to a CSV file without including the index column
    df.to_csv("jobs.csv", index=False)

    # Log a message indicating how many jobs were successfully scraped and saved to the CSV file
    logging.info(f"Successfully scraped {len(data)} jobs and saved to jobs.csv")


data = scrape_linkedin_jobs()
save_job_data(data)