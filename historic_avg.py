import os
import pandas as pd
import matplotlib.pyplot as plt

# Path to the input CSV files
input_file = 'filtered_stats_2045_2063.csv'
smoothed_avg_file = 'smoothed_avg.csv'
# Note - this file smoothed_avg.csv is a file that has been created manually in excel based on raw_avg.csv which is created by the code below
# this smoothing is needed to that all functions go one way i.e. increase or decrease with wins...not go up and down
# this is needed to then be able to simply alot observed statistics against wins on a one-way ratchet

# Path to save the output CSV file
output_file = 'filtered_reordered_stats.csv'

# List of columns to retain and their desired order
columns_to_keep = [
    'team', 'year', 'pythag_wins', 'wins', 'yds_per_game', 
    'ydsvs_per_game', 'Pen_per_snap', 'Fum_per_snap', 'Rate', 'ypt', 
    'Int_per_Att', 'SPct', 'ypc', 'KRB_per_Rply', 'Rate_vs', 'PDPct', 
    'Intvs_per_Att', 'ypt_vs', 'SPct_vs', 'KRBvs_per_Rply', 'ypc_vs', 
    'PR_avg', 'KR_avg', 'Net_punt_vs', 'OppPR_avg', 'OppKR_avg', 
    'Net_punt', 'Punt_for'
]

# Rounding rules for each column
rounding_rules = {
    'pythag_wins': 1,
    'wins': 0,
    'yds_per_game': 1,
    'ydsvs_per_game': 1,
    'Pen_per_snap': 1,
    'Fum_per_snap': 3,
    'Rate': 1,
    'ypt': 2,
    'Int_per_Att': 2,
    'SPct': 2,
    'ypc': 2,
    'KRB_per_Rply': 1,
    'Rate_vs': 1,
    'PDPct': 1,
    'Intvs_per_Att': 2,
    'ypt_vs': 2,
    'SPct_vs': 2,
    'KRBvs_per_Rply': 1,
    'ypc_vs': 2,
    'PR_avg': 1,
    'KR_avg': 1,
    'Net_punt_vs': 1,
    'OppPR_avg': 1,
    'OppKR_avg': 1,
    'Net_punt': 1,
    'Punt_for': 1
}

# Load the CSV file
df = pd.read_csv(input_file)
smoothed_avg_df = pd.read_csv(smoothed_avg_file)

# Remove rows where the 'team' column or any other relevant column has the value 'League'
df_filtered = df[~df['team'].str.contains('League', na=False)]

# Keep only the specified columns and reorder them
df_final = df_filtered[columns_to_keep]

# Apply rounding rules
for column, decimals in rounding_rules.items():
    if column in df_final.columns:
        df_final[column] = df_final[column].round(decimals)

# Save the cleaned, reordered, and rounded dataframe to a new CSV file
df_final.to_csv(output_file, index=False)

print(f"Filtered, reordered, and rounded data has been saved to {output_file}")

# Filter data to include only whole-number values of 'wins'
df_whole_wins = df_final[df_final['wins'] == df_final['wins'].astype(int)]

# Calculate averages for each variable from 'pythag_wins' onwards, grouped by 'wins'
columns_to_average = df_whole_wins.columns[2:]  # Columns from 'pythag_wins' onwards
averages_by_wins = df_whole_wins.groupby('wins')[columns_to_average].mean()

# Apply rounding rules to the averages
for column, decimals in rounding_rules.items():
    if column in averages_by_wins.columns:
        averages_by_wins[column] = averages_by_wins[column].round(decimals)

# Save the averages to a new CSV file
averages_output_file = 'raw_avg.csv'
averages_by_wins.to_csv(averages_output_file)

print(f"Averages grouped by wins (with rounding) have been saved to {averages_output_file}")

# Generate line graphs for each variable from 'yds_per_game' onwards
variables_to_plot = [
    'yds_per_game', 'ydsvs_per_game', 'Pen_per_snap', 'Fum_per_snap', 'Rate', 
    'ypt', 'Int_per_Att', 'SPct', 'ypc', 'KRB_per_Rply', 'Rate_vs', 'PDPct', 
    'Intvs_per_Att', 'ypt_vs', 'SPct_vs', 'KRBvs_per_Rply', 'ypc_vs', 
    'PR_avg', 'KR_avg', 'Net_punt_vs', 'OppPR_avg', 'OppKR_avg', 
    'Net_punt', 'Punt_for'
]

for variable in variables_to_plot:
    plt.figure()
    
    # Plot the line graph for the average values grouped by wins
    plt.plot(averages_by_wins.index, averages_by_wins[variable], marker='o', label=f"Avg {variable}")
    
    # Add the smoothed average line for the same variable
    if variable in smoothed_avg_df.columns:
        plt.plot(smoothed_avg_df['wins'], smoothed_avg_df[variable], marker='x', linestyle='--', label=f"Smoothed {variable}")
    
    plt.title(f"Line Graph of {variable} vs Wins")
    plt.xlabel("Wins")
    plt.ylabel(variable)
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join("graphs", f"{variable}_vs_wins.png"))  # Save to existing graphs folder
    plt.close()

print("Line graphs for each variable have been saved as PNG files.")
