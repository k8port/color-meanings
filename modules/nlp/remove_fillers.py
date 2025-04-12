import re
import pandas as pd

# Load your CSV file
csv_path = '/Users/dk8furia/gh-projects/color-meanings/data/descriptions.csv'
df = pd.read_csv(csv_path);

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
    "\."
]

# Sort by length desceding order (longer delimiters first)
delimiters = sorted(delimiters, key=lambda x: len(x), reverse=True)

# build regex to match any of the delimiters
pattern = '|'.join(delimiters)
print("regex pattern: ", pattern)


def split_description(description, color):
    print("\nOriginal description: ", description)
    # split desc on pattern
    snippets = re.split(pattern, description, flags=re.IGNORECASE)  
    print("\nSnippets: ", snippets)

    processed = [
        re.sub(r'\b' + re.escape(color) + r'\b', '', snippet, flags=re.IGNORECASE)
        for snippet in snippets
    ]
    print("After removing color name: ", processed)    

    # remove empty strings
    final_snippets = [snippet for snippet in processed if snippet]
    print("Final snippets: ", final_snippets)
    return final_snippets

df['snippet'] = df.apply(lambda row: split_description(row['description'], row['']), axis=1)
print("\nDataFrame with snippets:")
print(df[['color', 'snippet']])
df.to_csv('colors_snippets.csv', index=False)

print("Descriptions split")
