import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

base_url = "https://www.color-meanings.com"

# pages
color_groups = [
    "red",
    "orange",
    "yellow",
    "green",
    "blue",
    "purple",
    "pink",
    "brown",
    "gray",
    "white",
    "black",
]
shades_urls = [base_url + f"/shades-of-{color_group}-color-names-html-hex-rgb-codes/" for color_group in color_groups]
master_data = [] # list to store data

# send GET request to URL
headers = {'User-Agent': 'Mozilla/5.0 (compatible; MyScraper/1.0)'}

for color_group, url in zip(color_groups, shades_urls):
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to retrieve data for {color_group}: {response.status_code}")
        continue
    html_content = response.text
    soup = BeautifulSoup(html_content, 'html.parser')

    # find elements with shade information
    shade_elements = soup.find_all('p', class_='has-white-color has-text-color has-background')
    print(f"Found {len(shade_elements)} shade elements for {color_group}")
    more_shade_elements = soup.find_all('p', class_='has-black-color has-text-color has-background')
    print(f"Found {len(more_shade_elements)} more shade elements for {color_group}")

    for shade in shade_elements:
        shade_text = shade.get_text(separator="\n").split("\n") # split lines
        shade_text = [line.strip() for line in shade_text if line.strip()]
        shade_text = shade.get_text(separator="\n").split("\n")
        shade_text = [line.replace("\xa0", " ").strip() for line in shade_text if line.strip()]
        color_data = {
            "name": shade_text[0],
            "hex": shade_text[1].replace("Hex ", "").strip(),
            "rgb": tuple(map(int, shade_text[2].split("RGB ")[1].split(", "))),
            "cmyk": tuple(map(int, shade_text[3].split("CMYK ")[1].split(", "))),
        }
        description = shade.find_previous('p').get_text(separator="\n").split("\n")
        description = [line.strip() for line in description if line.strip()]
        color_data["description"] = description
        master_data.append(color_data)
    
    for shade in more_shade_elements:
        shade_text = shade.get_text(separator="\n").split("\n")
        shade_text = [line.replace("\xa0", " ").strip() for line in shade_text if line.strip()]
        color_data = {
            "name": shade_text[0],
            "hex": shade_text[1].replace("Hex ", "").strip(),
            "rgb": tuple(map(int, shade_text[2].split("RGB ")[1].split(", "))),
            "cmyk": tuple(map(int, shade_text[3].split("CMYK ")[1].split(", "))),
        }
        if (color_data["name"] == "Desire"):
            print(shade)
        description = shade.find_previous('p').get_text(separator="\n").split("\n")
        description = [line.strip() for line in description if line.strip()]
        color_data["description"] = description
        master_data.append(color_data)
    print(f"Processed {color_group}")
    time.sleep(2)

# create dataframe
df = pd.DataFrame(master_data)

# save to csv
df.to_csv('color_shades.csv', index=False)