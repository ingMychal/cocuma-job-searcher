import requests
from bs4 import BeautifulSoup
import datetime
import os

# Get the directory where cocumaScraper.py resides
script_directory = os.path.dirname(__file__)

# Generate a timestamp for today's date
today_timestamp = datetime.datetime.now().strftime("%Y%m%d")

# Define the filename with today's timestamp
filename = os.path.join(script_directory, f"cocumaScrape_{today_timestamp}.html")

# List all files in the folder
files_in_folder = os.listdir(script_directory)

# Check if any file in the folder contains today's date in its name
matching_files = [file for file in files_in_folder if today_timestamp in file]

if matching_files:
    print("A file with today's date already exists:")
    for matching_file in matching_files:
        print(matching_file)
    print("Script will not scrape anything.")
else:
    # Define the base URL for the first page
    base_url = "https://www.cocuma.cz/jobs/"
    page_number = 1
    combined_html = ""
    page_count = 0  # Initialize the page count

    while True:
        # Construct the URL based on the page number
        if page_number == 1:
            url = base_url
        else:
            url = f"{base_url}page/{page_number}/"

        # Send a GET request to the URL
        response = requests.get(url)

        # Check if the response is successful (status code 200)
        if response.status_code == 200:
            # Parse the HTML content of the response
            soup = BeautifulSoup(response.content, 'html.parser')

            # Append the entire HTML content of this page to combined_html
            combined_html += soup.prettify()  # Use prettify to preserve formatting

            # Increment the page number and page count for the next iteration
            page_number += 1
            page_count += 1

        else:
            # If the status code is not 200, exit the loop (no more pages)
            break

    # Save the combined HTML content to the file
    with open(filename, "w", encoding="utf-8") as file:
        file.write(combined_html)

    print(f"Scraped {page_count} pages and saved the combined HTML content to {filename}")
