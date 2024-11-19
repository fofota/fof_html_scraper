import requests
from bs4 import BeautifulSoup
import pandas as pd

# Define the range of years to scrape
years = range(2045, 2064)  # Includes 2045 up to 2063

# Function to scrape data for a specific year
def scrape_year(year):
    # URL for the stats and standings page of a specific year
    url_stats = f"https://therzb.com/RZB/leaguehtml/{year}teamstats.html"
    url_standings = f"https://therzb.com/RZB/leaguehtml/{year}standings.html"
    
    # Get stats page content
    response_stats = requests.get(url_stats)
    response_stats.raise_for_status()
    html_content_stats = response_stats.text
    soup_stats = BeautifulSoup(html_content_stats, 'html.parser')
    
    # Get standings page content
    response_standings = requests.get(url_standings)
    response_standings.raise_for_status()
    html_content_standings = response_standings.text
    soup_standings = BeautifulSoup(html_content_standings, 'html.parser')
    
    # Locate tables for stats
    tables_stats = soup_stats.find_all("table", {"bordercolor": "#800000", "width": "95%"})
    table_dict = {
        "Rushing Offense": None,
        "Rushing Defense": None,
        "Passing Offense": None,
        "Passing Defense": None,
        "Misc. Passing Offense": None,
        "Misc. Passing Defense": None,
        "Linemen": None,
        "Opp. Linemen": None,
        "Red Zone Offense": None,
        "Red Zone Defense": None,
        "Miscellaneous": None,
        "Misc. Opponents": None,
        "Kicking": None,
        "Opp. Kicking": None,
        "Returns": None,
        "Scoring/Turnovers": None
    }

    # Find and assign each table to the corresponding key in table_dict
    for table in tables_stats:
        first_cell = table.find("tr").find("th").get_text(strip=True)
        if first_cell in table_dict:
            table_dict[first_cell] = table

    # Check if all required tables are found
    for key, table in table_dict.items():
        if table is None:
            raise ValueError(f"Table '{key}' not found for year {year}.")

    # Helper function to extract headers and data from a table
    def extract_table_data(table):
        headers = [th.get_text(strip=True) for th in table.find_all("tr")[0].find_all("th")]
        data = []
        for row in table.find_all("tr")[1:]:  # Skip header row
            cells = row.find_all("td")
            row_data = [cell.get_text(strip=True) for cell in cells]
            data.append(row_data)
        return headers, data

    # Create DataFrames for each table
    dfs = {}
    for key, table in table_dict.items():
        headers, data = extract_table_data(table)
        df = pd.DataFrame(data, columns=headers)
        # Rename the team column to "Team" for consistent merging
        df.rename(columns={df.columns[0]: "Team"}, inplace=True)
        dfs[key] = df

    # Start merging with the first DataFrame and add each subsequent one
    merged_df = dfs["Rushing Offense"]
    for key in list(table_dict.keys())[1:]:  # Skip the first one, as it's already in merged_df
        suffix = '_vs' if key in [
            "Rushing Defense", "Passing Defense", "Misc. Passing Defense", "Opp. Linemen", 
            "Red Zone Defense", "Misc. Opponents", "Opp. Kicking"
        ] else f'_{key.replace(" ", "").replace(".", "")}'
        merged_df = pd.merge(merged_df, dfs[key], on="Team", suffixes=('', suffix))

    # Scrape the standings table for W, L, T, PF, PA data
    standings_table = soup_standings.find("table", {"bordercolor": "#800000", "width": "80%"})

    # Extract standings data with specific parsing for standings
    def extract_standings_data(table):
        standings_data = []
        for row in table.find_all("tr")[1:]:  # Skip header row
            cells = row.find_all("td")
            if len(cells) == 9:  # Only rows with 9 cells contain team data
                row_data = [cell.get_text(strip=True) for cell in cells]
                standings_data.append(row_data)
        standings_headers = ["Team", "W", "L", "T", "Pct", "PF", "PA", "Conf", "Div"]
        return standings_headers, standings_data

    standings_headers, standings_data = extract_standings_data(standings_table)
    standings_df = pd.DataFrame(standings_data, columns=standings_headers)
    
    # Remove only the final parentheses text, like "(WC)" at the end of team names, if it exists
    standings_df["Team"] = standings_df["Team"].str.replace(r"\s+\([^)]*\)$", "", regex=True).str.strip()
    standings_df = standings_df[["Team", "W", "L", "T", "PF", "PA"]]

    # Convert W, L, T, PF, PA to numeric for calculation
    standings_df[["W", "L", "T", "PF", "PA"]] = standings_df[["W", "L", "T", "PF", "PA"]].apply(pd.to_numeric, errors="coerce")

    # Calculate Wins and Pythagorean Wins
    standings_df["Wins"] = standings_df["W"] + (standings_df["T"] / 2)
    standings_df["pythag_wins"] = ((standings_df["PF"] ** 2.37) / ((standings_df["PF"] ** 2.37) + (standings_df["PA"] ** 2.37)) * 16).round(1)

    # Merge standings data with merged_df
    merged_df = pd.merge(merged_df, standings_df[["Team", "W", "L", "T", "PF", "PA", "Wins", "pythag_wins"]], on="Team", how="left")
    merged_df["Year"] = year  # Add a column for the year

    return merged_df

# Collect all years' data into a single DataFrame
all_years_data = pd.concat([scrape_year(year) for year in years], ignore_index=True)

# Save the final merged DataFrame to a CSV file
all_years_data.to_csv("combined_stats_2045_2063SIMPLE.csv", index=False)
print("Data saved to combined_stats_2045_2063SIMPLE.csv")
