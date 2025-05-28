import pandas as pd
import re
from rapidfuzz import process, fuzz

# Load your main songs CSV (must have 'name' and 'artist' columns)
songs_df = pd.read_csv("song_list.csv")

# Read the descriptions file lines
with open("song_descriptions.txt", "r", encoding="utf-8") as f:
    lines = [line.strip() for line in f if line.strip()]

# Parse descriptions into a dict keyed by "song - artist"
desc_dict = {}
i = 0
while i < len(lines) - 1:
    header_line = lines[i]
    description = lines[i + 1]

    # Regex to extract number, song name, artist(s)
    # Format assumed: "1. Maand – Bayaan, Hasan Raheem, Rovalio"
    match = re.match(r'^\d+\.\s*(.*?)\s*–\s*(.*)$', header_line)
    if match:
        song_name = match.group(1).strip()
        artists = match.group(2).strip()

        key = f"{song_name.lower()} - {artists.lower()}"
        if key not in desc_dict:  # ignore duplicates
            desc_dict[key] = description

    i += 2

# Function to create key for main song row for matching
def make_key(row):
    return f"{row['name'].lower()} - {row['artist'].lower()}"

# Build list of description keys for fuzzy matching
desc_keys = list(desc_dict.keys())

# Function to find best description match given song and artist key
def find_best_description(key):
    match = process.extractOne(key, desc_keys, scorer=fuzz.token_sort_ratio)
    if match and match[1] >= 80:  # 80% threshold can be tuned
        return desc_dict[match[0]]
    return None

# Create a key column in songs_df for matching
songs_df['match_key'] = songs_df.apply(make_key, axis=1)

# Apply matching to get descriptions
songs_df['description'] = songs_df['match_key'].apply(find_best_description)

# Drop helper column
songs_df.drop(columns=['match_key'], inplace=True)

# Save result
songs_df.to_csv("songs_with_descriptions.csv", index=False)
print("Matching done! Saved as songs_with_descriptions.csv")
