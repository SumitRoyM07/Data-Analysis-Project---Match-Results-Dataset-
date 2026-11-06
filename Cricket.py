import pandas as pd

# Load the data
df = pd.read_csv("Batting new.csv")

def title(t):
    print("\n" + "=" * len(t) + f"\n{t}\n" + "=" * len(t))

title("Q1: Who are the top 10 batsmen based on their total runs scored across all matches?")
# Group by player and sum their runs across all matches
top_batsmen = (
    df.groupby('Player')['Runs']
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
)

top_batsmen.columns = ['Player', 'Total Runs']
print(top_batsmen.to_string(index=False))


title("Q2: Which 10 players have the highest strike rate among players who have faced at least 50 balls?")
# Aggregate total runs and balls per player
grp = df.groupby('Player').agg(
    Total_Runs=('Runs', 'sum'),
    Total_Balls=('Balls', 'sum')
).reset_index()

# Filter to players who faced at least 50 balls
grp = grp[grp['Total_Balls'] >= 50]

# Compute overall strike rate
grp['Strike Rate'] = (grp['Total_Runs'] / grp['Total_Balls'] * 100).round(2)

top10_sr = grp.sort_values('Strike Rate', ascending=False).head(10)
print(top10_sr.to_string(index=False))

title("Q3: Which player has scored the most fours and which player has scored the most sixes?")
# Sum boundaries per player
grp = df.groupby('Player').agg(
    Total_4s=('4s', 'sum'),
    Total_6s=('6s', 'sum')
).reset_index()

most_fours = grp.sort_values('Total_4s', ascending=False).head(1)
most_sixes = grp.sort_values('Total_6s', ascending=False).head(1)

print("Most fours:")
print(most_fours.to_string(index=False))
print("\nMost sixes:")
print(most_sixes.to_string(index=False))


title("Q4: Which team has won the highest number of matches, and how many matches did they win?")
# The CSV has one row per player per innings, so multiple rows share the
# same match. To count matches (not player-innings), dedupe on the columns
# that identify a unique match result: Date, Team, Vs, Win
matches = df[['Date', 'Team', 'Vs', 'Win']].drop_duplicates()

# Keep only the winning side's record for each match
wins = matches[matches['Win'] == 1]

# Count wins per team, sorted descending
win_counts = wins.groupby('Team').size().sort_values(ascending=False)

print(win_counts)

# Team with the most wins
top_team = win_counts.idxmax()
top_wins = win_counts.max()
print(f"\n{top_team} has won the most matches, with {top_wins} wins.")

title("Q5: For each match, who was the highest run scorer? Can you display the player name, team, opponent, match date, and runs scored?")
# Each match appears from both teams' perspectives (Team vs Vs, and Vs vs Team
# on the same date), so build a match identifier from Date + the unordered
# pair of the two teams involved.
df['MatchID'] = df.apply(
    lambda r: (r['Date'], frozenset([r['Team'], r['Vs']])), axis=1
)

# For each match, find the row with the highest Runs
top_scorer_idx = df.groupby('MatchID')['Runs'].idxmax()
top_scorers = df.loc[top_scorer_idx, ['Date', 'Player', 'Team', 'Vs', 'Runs']]

# Rename 'Vs' to 'Opponent' for clarity, and sort by date
top_scorers = top_scorers.rename(columns={'Vs': 'Opponent'})
top_scorers = top_scorers.sort_values('Date').reset_index(drop=True)

print(top_scorers.to_string(index=False))

# Q6: Do teams perform better while chasing or while batting first? Compare their average runs and overall performance in both situations.
# Aggregate to team-innings level: sum runs/balls for each team in each match,
# keeping the Chase flag (0 = batting first, 1 = chasing) and Win flag
team_innings = df.groupby(['Date', 'Team', 'Vs', 'Chase', 'Win']).agg(
    Team_Runs=('Runs', 'sum'),
    Team_Balls=('Balls', 'sum')
).reset_index()

# Compare performance: average runs scored and win rate, by Chase vs Bat-first
summary = team_innings.groupby('Chase').agg(
    Avg_Runs=('Team_Runs', 'mean'),
    Win_Rate=('Win', 'mean'),
    Innings_Count=('Win', 'count')
).reset_index()

summary['Chase'] = summary['Chase'].map({0: 'Batting First', 1: 'Chasing'})
summary['Win_Rate'] = (summary['Win_Rate'] * 100).round(1)
summary['Avg_Runs'] = summary['Avg_Runs'].round(1)

print(summary.to_string(index=False))

title("Q7: Who are the top 10 bowlers based on total wickets taken, and what are their average economy rates?")
def get_bowler(dismissal):
    """
    Extract the bowler credited with the wicket from the Dismissal text.
    Formats seen in this data:
      'b Bowler'            -> bowled
      'c Fielder b Bowler'  -> caught, bowler credited
      'lbw b Bowler'        -> leg before wicket, bowler credited
      'st Keeper b Bowler'  -> stumped, bowler credited
      'run out (...)'       -> NOT a bowler's wicket
      'not out'             -> no dismissal
    """
    if pd.isna(dismissal):
        return None
    d = dismissal.strip()
    if d == 'not out' or d.startswith('run out'):
        return None
    if d.startswith('b '):          # plain "bowled"
        return d[2:].strip()
    if ' b ' in d:                  # catches, lbw, stumpings all end " b <bowler>"
        return d.split(' b ')[-1].strip()
    return None

df['Bowler'] = df['Dismissal'].apply(get_bowler)

# Top 10 bowlers by wickets taken
top_bowlers = df['Bowler'].value_counts().head(10).reset_index()
top_bowlers.columns = ['Bowler', 'Wickets']

print(top_bowlers.to_string(index=False))

title("Q8: Which players have scored the most runs through boundaries (fours and sixes), and how does their strike rate compare with other players?")
# Aggregate stats per player across all their innings
player_stats = df.groupby('Player').agg(
    Total_Runs=('Runs', 'sum'),
    Total_Balls=('Balls', 'sum'),
    Fours=('4s', 'sum'),
    Sixes=('6s', 'sum'),
    Innings=('Runs', 'count')
).reset_index()

# Runs scored specifically via boundaries (4s worth 4, 6s worth 6)
player_stats['Boundary_Runs'] = player_stats['Fours'] * 4 + player_stats['Sixes'] * 6
player_stats['Boundary_Pct'] = (player_stats['Boundary_Runs'] / player_stats['Total_Runs'] * 100).round(1)

# True strike rate = total runs / total balls faced * 100 (more accurate than averaging per-innings SR)
player_stats['Strike_Rate'] = (player_stats['Total_Runs'] / player_stats['Total_Balls'] * 100).round(2)

# Top 10 players by boundary runs
top10 = player_stats.sort_values('Boundary_Runs', ascending=False).head(10)
print(top10[['Player', 'Total_Runs', 'Boundary_Runs', 'Boundary_Pct', 'Strike_Rate', 'Innings']].to_string(index=False))

# Compare their strike rate with the rest of the field
overall_avg_sr = player_stats['Strike_Rate'].mean()
top10_avg_sr = top10['Strike_Rate'].mean()
print(f"\nAverage strike rate — Top 10 boundary scorers: {top10_avg_sr:.2f}")
print(f"Average strike rate — All players:             {overall_avg_sr:.2f}")

title("Q9: Can you create a Player Performance Score using runs, strike rate, fours, sixes, and balls faced, and use it to rank the top 20 batsmen?")
# Aggregate stats per player across all their innings
player_stats = df.groupby('Player').agg(
    Total_Runs=('Runs', 'sum'),
    Total_Balls=('Balls', 'sum'),
    Fours=('4s', 'sum'),
    Sixes=('6s', 'sum'),
    Innings=('Runs', 'count')
).reset_index()

# True strike rate: total runs / total balls faced * 100
player_stats['Strike_Rate'] = (player_stats['Total_Runs'] / player_stats['Total_Balls'] * 100).round(2)

# Filter out players with very few innings so small samples don't distort the score
player_stats = player_stats[player_stats['Innings'] >= 3].copy()

# Min-max normalize each metric to a 0-100 scale so they're comparable
def normalize(series):
    return (series - series.min()) / (series.max() - series.min()) * 100

player_stats['N_Runs']   = normalize(player_stats['Total_Runs'])
player_stats['N_SR']     = normalize(player_stats['Strike_Rate'])
player_stats['N_Fours']  = normalize(player_stats['Fours'])
player_stats['N_Sixes']  = normalize(player_stats['Sixes'])
player_stats['N_Balls']  = normalize(player_stats['Total_Balls'])  # rewards sustained contribution

# Weighted composite score — weights reflect relative importance of each skill
weights = {
    'N_Runs':  0.35,   # volume of runs matters most
    'N_SR':    0.30,   # scoring speed is nearly as important
    'N_Fours': 0.10,
    'N_Sixes': 0.15,   # sixes weighted a bit higher than fours (harder to hit)
    'N_Balls': 0.10,   # rewards players who contribute over more deliveries
}

player_stats['Performance_Score'] = sum(
    player_stats[col] * w for col, w in weights.items()
).round(2)

top20 = player_stats.sort_values('Performance_Score', ascending=False).head(20)

print(top20[['Player', 'Total_Runs', 'Strike_Rate', 'Fours', 'Sixes', 'Total_Balls', 'Performance_Score']].to_string(index=False))

title("Q10: Can you combine the batting and bowling data to identify the top 10 all-round performers? Create your own Match Impact Score using runs, wickets, strike rate, economy rate, boundaries, and match result?")

# ============================================================
# STEP 1 — Batting stats per player
# ============================================================
bat = df.groupby('Player').agg(
    Total_Runs=('Runs', 'sum'),
    Total_Balls=('Balls', 'sum'),
    Fours=('4s', 'sum'),
    Sixes=('6s', 'sum'),
    Innings=('Runs', 'count'),
    Matches_Won=('Win', 'sum')
).reset_index()

bat['Strike_Rate'] = (bat['Total_Runs'] / bat['Total_Balls'] * 100).round(2)
bat['Win_Rate'] = (bat['Matches_Won'] / bat['Innings']).round(3)
bat['Boundary_Runs'] = bat['Fours'] * 4 + bat['Sixes'] * 6

# ============================================================
# STEP 2 — Wickets per bowler, inferred from the Dismissal text
# NOTE: this dataset has no overs/runs-conceded data, so a real
# economy rate cannot be computed. We can only recover *wickets*
# because the Dismissal string names the bowler who took them.
# ============================================================
def get_bowler(dismissal):
    if pd.isna(dismissal):
        return None
    d = dismissal.strip()
    if d == 'not out' or d.startswith('run out'):
        return None            # no bowler credited
    if d.startswith('b '):     # bowled
        return d[2:].strip()
    if ' b ' in d:              # caught / lbw / stumped -> "... b Bowler"
        return d.split(' b ')[-1].strip()
    return None

df['Bowler'] = df['Dismissal'].apply(get_bowler)
bowl = df['Bowler'].value_counts().reset_index()
bowl.columns = ['Player', 'Wickets']

# ============================================================
# STEP 3 — Combine batting + bowling into one all-rounder table
# ============================================================
allround = pd.merge(bat, bowl, on='Player', how='outer')
allround[['Total_Runs','Total_Balls','Fours','Sixes','Innings','Matches_Won',
          'Strike_Rate','Win_Rate','Boundary_Runs','Wickets']] = \
    allround[['Total_Runs','Total_Balls','Fours','Sixes','Innings','Matches_Won',
              'Strike_Rate','Win_Rate','Boundary_Runs','Wickets']].fillna(0)

# Keep players with a reasonable sample (avoid one-off outliers dominating)
allround = allround[(allround['Innings'] >= 2) | (allround['Wickets'] >= 2)].copy()

# ============================================================
# STEP 4 — Normalize each ingredient to 0–100 and build the score
# ============================================================
def normalize(s):
    rng = s.max() - s.min()
    return (s - s.min()) / rng * 100 if rng > 0 else s * 0

allround['N_Runs']     = normalize(allround['Total_Runs'])
allround['N_SR']       = normalize(allround['Strike_Rate'])
allround['N_Boundary']  = normalize(allround['Boundary_Runs'])
allround['N_Wickets']  = normalize(allround['Wickets'])
allround['N_WinRate']  = normalize(allround['Win_Rate'])
# Placeholder — set to 0 because economy rate isn't computable from this file.
# If you later provide a bowling dataset with Overs & Runs_Conceded, compute:
#   Economy = Runs_Conceded / Overs
#   N_Economy = normalize(-Economy)   # lower economy = better, so invert
allround['N_Economy'] = 0

weights = {
    'N_Runs':    0.25,
    'N_SR':      0.20,
    'N_Boundary': 0.10,
    'N_Wickets': 0.25,
    'N_Economy': 0.10,   # currently contributes 0 — see note above
    'N_WinRate': 0.10,
}

allround['Match_Impact_Score'] = sum(allround[c] * w for c, w in weights.items()).round(2)

top10 = allround.sort_values('Match_Impact_Score', ascending=False).head(10)
print(top10[['Player','Total_Runs','Strike_Rate','Boundary_Runs','Wickets','Win_Rate','Match_Impact_Score']].to_string(index=False))