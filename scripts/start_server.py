# Given the url of a google doc containing a 3 column table, with 
# a list of unicode characters and their x and y coordinates, write 
# a function that takes a string representing the URL, parse in data 
# in document and print the grid of characters in fixed width font. 
# The characters will create a graphic revealing a hidden message.
# The document specifies:
#  x coordinate (column 1, from 0 to infinity)
#  character (column 2, a unicode character)
#  y coordinate (column 3, from 0 to infinity)
#  Any position not containing a special character should display a space
#  The message is hidden in the horizontal and vertical sequences of characters
#  Print the message in the console

import requests
import re
import pandas as pd
from bs4 import BeautifulSoup

def get_doc_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        return None


def parse_doc_data(data):
    # Parse the HTML data to extract coordinates and characters
    soup = BeautifulSoup(data, 'html.parser')
    coordinates = []
    
    # Find the table - Google Docs typically wraps tables in specific divs
    tables = soup.find_all('table')
    if not tables:
        print("No tables found in document")
        return coordinates
        
    # Look through all tables for our data
    for table in tables:
        rows = table.find_all('tr')
        # Skip the header row
        for row in rows[1:]:
            cells = row.find_all('td')
            if len(cells) == 3:
                try:
                    x = int(cells[0].get_text().strip())
                    char = cells[1].get_text().strip()
                    y = int(cells[2].get_text().strip())
                    coordinates.append((x, y, char))
                except (ValueError, IndexError):
                    continue
    
    return coordinates

def print_grid(coordinates):
    if not coordinates:
        print("No data to display")
        return
        
    # Find grid dimensions
    max_x = max(coord[0] for coord in coordinates) + 1
    max_y = max(coord[1] for coord in coordinates) + 1
    
    # Create empty grid
    grid = [[' ' for _ in range(max_x)] for _ in range(max_y)]
    
    # Place characters in grid
    for x, y, char in coordinates:
        grid[y][x] = char
    
    # Print grid in reverse order (bottom to top)
    for row in reversed(grid):
        print(''.join(row))


if __name__ == "__main__":
    url = "https://docs.google.com/document/d/e/2PACX-1vQGUck9HIFCyezsrBSnmENk5ieJuYwpt7YHYEzeNJkIb9OSDdx-ov2nRNReKQyey-cwJOoEKUhLmN9z/pub"
    data = get_doc_data(url)
    print("Got response:", bool(data))
    if data:
        print("Length of response:", len(data))
        soup = BeautifulSoup(data, 'html.parser')
        rows = soup.find_all('tr', class_='c1')
        print("Found rows:", len(rows))
    parsed_data = parse_doc_data(data)
    print("Parsed coordinates:", parsed_data)
    print("\nGrid output:")
    print_grid(parsed_data)
