import requests
from bs4 import BeautifulSoup
import pandas as pd

# Function to determine the most recent year
def get_most_recent_year():
    url_index = "https://therzb.com/RZB/leaguehtml/index.html"
    response = requests.get(url_index)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    # Locate the year from the standings section
    recent_year = max(int(link.text.strip()) for link in soup.find_all("a") if link.text.strip().isdigit())
    return recent_year

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
        df.rename(columns={df.columns[0]: "Team"}, inplace=True)  # Standardize team column name
        dfs[key] = df

    # Start merging with the first DataFrame and add each subsequent one
    merged_df = dfs["Rushing Offense"]
    for key in list(table_dict.keys())[1:]:
        suffix = '_vs' if key in [
            "Rushing Defense", "Passing Defense", "Misc. Passing Defense", "Opp. Linemen", 
            "Red Zone Defense", "Misc. Opponents", "Opp. Kicking"
        ] else f'_{key.replace(" ", "").replace(".", "")}'
        merged_df = pd.merge(merged_df, dfs[key], on="Team", suffixes=('', suffix))

    # Scrape the standings table for W, L, T, PF, PA data
    standings_table = soup_standings.find("table", {"bordercolor": "#800000", "width": "80%"})

    # Extract standings data
    def extract_standings_data(table):
        standings_data = []
        for row in table.find_all("tr")[1:]:
            cells = row.find_all("td")
            if len(cells) == 9:
                row_data = [cell.get_text(strip=True) for cell in cells]
                standings_data.append(row_data)
        standings_headers = ["Team", "W", "L", "T", "Pct", "PF", "PA", "Conf", "Div"]
        return standings_headers, standings_data

    standings_headers, standings_data = extract_standings_data(standings_table)
    standings_df = pd.DataFrame(standings_data, columns=standings_headers)
    standings_df["Team"] = standings_df["Team"].str.replace(r"\s+\([^)]*\)$", "", regex=True).str.strip()
    standings_df = standings_df[["Team", "W", "L", "T", "PF", "PA"]]
    standings_df[["W", "L", "T", "PF", "PA"]] = standings_df[["W", "L", "T", "PF", "PA"]].apply(pd.to_numeric, errors="coerce")
    standings_df["Wins"] = standings_df["W"] + (standings_df["T"] / 2)
    standings_df["pythag_wins"] = ((standings_df["PF"] ** 2.37) / ((standings_df["PF"] ** 2.37) + (standings_df["PA"] ** 2.37)) * 16).round(1)

    # Merge standings data with merged_df
    merged_df = pd.merge(merged_df, standings_df[["Team", "W", "L", "T", "PF", "PA", "Wins", "pythag_wins"]], on="Team", how="left")
    merged_df["Year"] = year  # Add a column for the year

    # Add a prefix number to all column names in ascending order
    merged_df.columns = [f"{i+1}{col}" for i, col in enumerate(merged_df.columns)]

    return merged_df

# Main script
most_recent_year = get_most_recent_year()
print(f"Most recent year identified: {most_recent_year}")

# Scrape data for the most recent year only
data = scrape_year(most_recent_year)

# Columns to keep and their new names
columns_to_keep = {
    "1Team": "team",
    "3Yards": "run_yds",
    "4Avg": "ypc",
    "14Yards_vs": "run_yds_vs",
    "15Avg_vs": "ypc_vs",
    "24Att": "Att",
    "27Yards_PassingOffense": "pass_yds",
    "29Yds/A": "ypt",
    "31Rate": "Rate",
    "32PPly": "Pply",
    "39Yards_vs": "pass_yds_vs",
    "41Yds/A_vs": "ypt_vs",
    "43Rate_vs": "Rate_vs",
    "46OpPDPct_vs": "PDPct",
    "72KRB": "KRB",
    "75RPly": "Rply",
    "80SPct": "SPct",
    "84KRB_vs": "KRB_vs",
    "87RPly_vs": "Rply_vs",
    "92SPct_vs": "SPct_vs",
    "131Pnlty": "Pnlty",
    "154Avg_Kicking": "Punt_for",
    "156Avg_Kicking": "Net_punt",
    "167Avg_vs": "Net_punt_vs",
    "169Avg_Returns": "PR_avg",
    "171Avg_Returns": "KR_avg",
    "173Avg_Returns": "OppPR_avg",
    "175Avg_Returns": "OppKR_avg",
    "178Yds/G": "yds_per_game",
    "179OpYds/G": "ydsvs_per_game",
    "180Fum": "Fum",
    "181Int": "Int",
    "187W": "W",
    "188L": "L",
    "189T": "T",
    "190PF": "PF",
    "191PA": "PA",
    "192Wins": "wins",
    "193pythag_wins": "pythag_wins",
    "194Year": "year"
}

# Filter and rename columns
filtered_data = data[list(columns_to_keep.keys())]
filtered_data = filtered_data.rename(columns=columns_to_keep)

# Convert all columns except "team" to numeric
filtered_data.iloc[:, 1:] = filtered_data.iloc[:, 1:].apply(pd.to_numeric, errors="coerce")

# Calculate Int_per_Att and other useful rate stats
filtered_data["Int_per_Att"] = filtered_data["Int"] / filtered_data["Att"]
filtered_data["Fum_per_snap"] = filtered_data["Fum"] / (filtered_data["Pply"] + filtered_data["Rply"])
filtered_data["KRB_per_Rply"] = filtered_data["KRB"] / filtered_data["Rply"]
filtered_data["KRBvs_per_Rply"] = filtered_data["KRB_vs"] / filtered_data["Rply_vs"]
filtered_data["Pen_per_snap"] = filtered_data["Pnlty"] / (filtered_data["Pply"] + filtered_data["Rply"])
filtered_data["Ydsgain_per_game"] = filtered_data["yds_per_game"] - filtered_data["ydsvs_per_game"]

# Print column headings, each on a new line
print("Column Headings:")
for column in filtered_data.columns:
    print(column)

# Save the filtered DataFrame to a new CSV file
filtered_data.to_csv(f"filtered_stats_latest.csv", index=False)
print(f"Filtered data saved to filtered_stats_latest.csv")
