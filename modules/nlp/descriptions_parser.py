import re
import spacy
import openai
from category_mappings import color_temperatures
import os

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# OpenAI API key 
openai.api_key = os.getenv("OPENAI_API_KEY")

delimiters = [
    "is a",
    "with a",
    "it's a",
    "it is a",
    "it is",
    "it's",
    "it is",
    "it's",
    "it is",
    "it's",
    "is",
    ".",
    "this",
    "its",
]

def parse_description(description):
    """
    Parse color description text
    """

    desc_text = description.lower()
    doc = nlp(description)

    results = {
        "seasonal": [], # snippets discussing seasonal associations
        "cmyk": [], # snippets discussing CMYK values of color
        "rgb": [], # snippets discussing RGB values of color
        "hsl": [], # snippets discussing HSL values of color
        "brightness": [], # snippets discussing brightness of color
        "temperature": [], #snippets discussing temperature of color
        "peopleplacesthings": [], # snippets discussing entities associated with color
        "use_cases": [], # snippets discussing use cases for color
        "emotional": [], # snippets discussing emotional associations
        "finish": [], # snippets discussing finish or texture of color
        "materials": [], # snippets discussing material of color
        "aesthetics": [], # snippets discussing aesthetic style of color
        "historical": [], # snippets discussing historical context of color
        "saturation": [], # snippets discussing saturation of color
        "undertones": [], # snippets discussing undertone of color
        "contrast": [], # snippets discussing contrast of color
        "opacity": [], # snippets discussing opacity of color
    }

    # ---- CMYK EXTRACTION ----
    cmyk_match = re.findall(r'(cyan|magenta|yellow|black)[\s:]+(\d+)', description, re.IGNORECASE)
    if cmyk_match:
        cmyk_values = ', '.join([f"{color} {value}" for color, value in cmyk_match])
        results["cmyk"].append(f"{cmyk_values} (CMYK)")

    # ---- RGB EXTRACTION ----
    rgb_match = re.findall(r'(red|green|blue)[\s:]+(\d+)', description, re.IGNORECASE)
    if rgb_match:
        rgb_values = ', '.join([f"{color} {value}" for color, value in rgb_match])
        results["rgb"].append(f"{rgb_values} (RGB)")

    # ---- HSL EXTRACTION ----
    hsl_match = re.findall(r'(hue|saturation|lightness)[\s:]+(\d+)', description, re.IGNORECASE)
    if hsl_match:
        hsl_values = ', '.join([f"{color} {value}" for color, value in hsl_match])
        results["hsl"].append(f"{hsl_values} (HSL)")

    # ---- BRIGHTNESS EXTRACTION ----
    if "dark" in desc_text:
        results["brightness"].append("dark") 
    elif "light" in desc_text:
        results["brightness"].append("light")

    # ---- TEMPERATURE EXTRACTION ----
    for temp, colors in color_temperatures.items():
        if any(color in desc_text for color in colors):
            results["temperature"].append(f"{temp} color")

    # ---- ENTITY EXTRACTION ----
    # Extract entities from the description
    doc = nlp(description)
    