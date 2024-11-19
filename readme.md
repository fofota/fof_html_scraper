This scraper reads the html files for the RZB league and

- takes the seasons after the 'tzach patch' (2045 onwards; currently 2045 to 2063) and scrapes the team statistics and record for each team for each regular season

- processes that file into an easier-to-use table

- calculates averages by number of wins, i.e. for a given metric what the mean average of that metric was for all teams with a 7-win record

Based on the raw averages calculated like this a 'smoothed average' has been created for each metric which is a one-way function i.e. always upward or always downward as wins vary, for each metric