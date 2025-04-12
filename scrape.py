import requests
from bs4 import BeautifulSoup
import pandas as pd

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
    "black",
    "white",
]
shades_urls = [base_url + "/shades-of-{color_group}-color-names-html-hex-rgb-codes/" for color_group in color_groups]
master_data = [] # list to store data

# send GET request to URL
headers = {'User-Agent': 'Mozilla/5.0 (compatible; MyScraper/1.0)'}
for color_group in color_groups:
    response = requests.get(shades_urls[color_group], headers=headers)
    html_content = response.text
    soup = BeautifulSoup(html_content, 'html.parser')

    # find elements with shade information
    shade_elements = soup.find_all('p', class_='has-white-color has-text-color has-background')
    for shade in shade_elements:
        shade_text = shade.get_text(separator="\n").split("\n") # split lines
        color_data = {
            "name": shade_text[0],
            "hex": shade_text[1],
            "rgb": tuple(map(int, shade_text[2].split("RGB ")[1].split(", "))),
            "cmyk": tuple(map(int, shade_text[3].split("CMYK ")[1].split(", "))),
        }
        master_data.append(color_data)

# create dataframe
df = pd.DataFrame(master_data)

# save to csv
df.to_csv('color_shades.csv', index=False)

