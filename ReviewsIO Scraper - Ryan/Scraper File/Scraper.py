import time
import undetected_chromedriver as uc
import json
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from xextract import String
import sys

# Take url and no_of_days from command line with url (ask for url if not provided)
if len(sys.argv) < 2:
    print("Usage: python myscript.py <url> <no_of_days>")
    quit()
else:
    # Access and print the command-line arguments
    script_name = sys.argv[0]
    try:
        url = str(sys.argv[1]).split("?")[0]
    except:
        url = str(sys.argv[1])

    no_of_days = int(sys.argv[2])

    print("Script name:", script_name)
    print("Arguments:", url, no_of_days)


def get_text_data(xpath_selector):
    try:
        return String(xpath=xpath_selector).parse_html(html_data_page)[0]
    except:
        return ""


def convert_date(date_x: str):
    split_number = int(date_x.lower().split('posted ')[-1].split(' ')[0])
    if "month" in date_x:
        date_x = datetime.now() - timedelta(days=30 * split_number)
    elif "week" in date_x:
        date_x = datetime.now() - timedelta(days=7 * split_number)
    elif "day" in date_x:
        date_x = datetime.now() - timedelta(days=split_number)
    elif "hour" in date_x:
        date_x = datetime.now() - timedelta(hours=split_number)
    elif "minute" in date_x:
        date_x = datetime.now() - timedelta(minutes=split_number)
    elif "second" in date_x:
        date_x = datetime.now() - timedelta(seconds=split_number)
    elif "year" in date_x:
        date_x = datetime.now() - timedelta(days=365 * split_number)
    else:
        date_x = datetime.now()

    return date_x.strftime("%m/%d/%Y")


def days_until_date(input_date):
    date_format = "%m/%d/%Y"

    try:
        input_datetime = datetime.strptime(input_date, date_format)

        current_datetime = datetime.now()

        time_difference = current_datetime - input_datetime

        days_difference = time_difference.days

        return int(days_difference)
    except ValueError:
        return "Invalid date format"


# Set up the Chrome WebDriver
uc_options = uc.ChromeOptions()
uc_options.headless = False
driver = uc.Chrome(options=uc_options)
driver.maximize_window()
cloudflare_url = "https://www.reviews.io/company-reviews/store/www.super.com/Na?xhr"

# Open a new tab with the specified URL
driver.execute_script(
    f"window.open('{cloudflare_url}', '_blank');")

time.sleep(4)
driver.execute_script(
    f"window.open('{cloudflare_url}', '_blank');")
time.sleep(16)

# Switch to the first tab
driver.switch_to.window(driver.window_handles[0])
time.sleep(5)
driver.get(url + "?xhr")

data = []
pages_scraped = 0
keep_running = True

while True:
    try:
        page_source = str(driver.find_element(By.XPATH, "//pre").text)
        # json conversion
        html_data_page = json.loads(page_source)['reviews']
        pagination_html_page = json.loads(page_source)['pagination']
    except:
        page_source = str(driver.page_source)
        html_data_page = page_source
        pagination_html_page = page_source

    # data extraction
    total_reviews = String(xpath='//div[@class="Review "]').parse_html(html_data_page)
    for review_index in range(len(total_reviews)):
        review_xpath = f'(//div[@class="Review "])[{review_index + 1}]'

        author_name = get_text_data(f'{review_xpath}//a[@class="Review__author"]')
        review_description = get_text_data(f"{review_xpath}//span[contains(@class,'Review__body')]")
        source_url = "https://www.reviews.io" + \
                     String(xpath=f'{review_xpath}//a[@class="Review__author"]', attr='href').parse_html(
                         html_data_page)[0]
        review_id = str(source_url).split('/')[-1]

        review_rating = len(
            String(xpath=f'{review_xpath}//i[@class="stars__icon ricon-percentage-star--100 stars__icon--100"]')
            .parse_html(html_data_page))

        if review_rating == 0:
            review_rating = 1

        review_date = str(get_text_data(f'{review_xpath}//div[@class="Review__dateSource"]')).strip()
        review_date = convert_date(review_date)
        days_since_review = days_until_date(review_date)


        data.append({
            "user": author_name,
            "stars": review_rating,
            "date": review_date,
            "source_url": source_url,
            "id": review_id,
            "details": review_description
        })

        print(days_since_review, days_since_review <= no_of_days)

        if no_of_days < days_since_review:
            keep_running = False
            break



    if not keep_running:
        break

    try:
        next_url = String(xpath="//ul[@class='pagination']//li[last()]/a[text()='»']", attr='href') \
                       .parse_html(pagination_html_page)[0] + "?xhr"
        driver.get(next_url)
    except:
        break

    pages_scraped += 1
    print(f"Pages Scraped: {pages_scraped}")

# save data into json file
# current date - trustpilot_scraper_110823_curve.com.json
current_datetime = datetime.now().strftime("%d%m%y")
file_name = f"reviewsio_scraper_{current_datetime}.json"
with open(file_name, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4)

driver.quit()

print(f"Scraping Complete, Scraped {pages_scraped} pages")
