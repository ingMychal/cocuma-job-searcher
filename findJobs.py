import subprocess
import os
import glob
from bs4 import BeautifulSoup
import datetime
from keywords import filter_keywords  # Import the filter_keywords list

# Set the working directory to the folder where findJobs.py is located
script_directory = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_directory)

# Run the cocumaScraper.py script
try:
    subprocess.run(["python", "cocumaScraper.py"], check=True)
except subprocess.CalledProcessError:
    print("Error: Failed to run cocumaScraper.py")
    exit(1)

# List all HTML files in the folder with names matching "cocumaScrape_timestamp.html"
html_files = [file for file in glob.glob("cocumaScrape_*.html") if file.startswith("cocumaScrape_")]

# Check if any HTML files were found
if html_files:
    # Find the most recent HTML file based on its timestamp
    try:
        most_recent_file = max(html_files, key=lambda x: os.path.getctime(x))
        print(f"The most recent HTML file is: {most_recent_file}")

        # Read and parse the combined HTML file
        with open(most_recent_file, "r", encoding="utf-8") as html_file:
            combined_html = BeautifulSoup(html_file, 'html.parser')

        # Create a timestamp for the filtered HTML filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

        # Create a new HTML document for the filtered elements
        filtered_html = BeautifulSoup('<html><body></body></html>', 'html.parser')
        body_tag = filtered_html.body

        # Cocuma base URL
        base_url = "https://www.cocuma.cz"

        # Create a dictionary to store elements by their href values
        href_elements = {}

        # Find all elements with class "job-thumbnail" for further processing
        job_thumbnail_elements = combined_html.find_all("a", class_="job-thumbnail")

        # Iterate through the job thumbnail elements
        for job_thumbnail_element in job_thumbnail_elements:
            title_element = job_thumbnail_element.find("p", class_="job-thumbnail-title")
            if title_element:
                title_text = title_element.get_text(strip=True)
                for keyword in filter_keywords:
                    if keyword.lower() in title_text.lower():  # Compare in lowercase
                        # Update the href attribute to use the Cocuma base URL
                        href = job_thumbnail_element.get("href")
                        if href and not href.startswith("http"):
                            job_thumbnail_element["href"] = base_url + href

                        # Add the element to the dictionary based on its href value
                        if href in href_elements:
                            href_elements[href].append(job_thumbnail_element)
                        else:
                            href_elements[href] = [job_thumbnail_element]

                        break  # Stop checking keywords once a match is found

        # Create rectangles around groups of elements with the same href value
        for href, elements in href_elements.items():
            div_tag = filtered_html.new_tag("div", style="border: 1px solid blue;")
            for element in elements:
                div_tag.append(element)

            body_tag.append(div_tag)

        # Save the filtered content to a new HTML file with a timestamp
        filtered_filename = f"filtered_{timestamp}.html"
        with open(filtered_filename, "w", encoding="utf-8") as filtered_file:
            filtered_file.write(filtered_html.prettify())

        print(f"Filtered HTML saved as '{filtered_filename}'")

    except Exception as e:
        print(f"Error: Failed to find and filter the most recent HTML file - {e}")

else:
    print("No HTML files found in the folder.")
