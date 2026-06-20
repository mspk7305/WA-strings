import os
import re
import pandas as pd

# Regular expression to extract player, level, time (HH:MM), and kills
# Matches: "PlayerName leveled to X in HH:MM after Y kills"
log_pattern = re.compile(
    r":\s+(?P<player>[\w\-]+)\s+leveled\s+to\s+(?P<level>\d+)\s+in\s+(?P<time>\d{2}:\d{2})\s+after\s+(?P<kills>\d+)\s+kills"
)


def time_to_minutes(time_str):
    """Converts HH:MM string to total minutes (float)"""
    try:
        hours, minutes = map(int, time_str.split(":"))
        return float(hours * 60 + minutes)
    except:
        return None


parsed_data = []

# Loop from level 2 through 60 to target specific files
for lvl in range(2, 61):
    filename = f"level{lvl}.log"

    if not os.path.exists(filename):
        continue

    with open(filename, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            match = log_pattern.search(line)
            if match:
                # Double-check that the log entry level matches the file level
                log_level = int(match.group("level"))
                if log_level != lvl:
                    continue

                minutes = time_to_minutes(match.group("time"))
                kills = int(match.group("kills"))

                parsed_data.append(
                    {
                        "Level": log_level,
                        "Player": match.group("player"),
                        "Minutes": minutes,
                        "Kills": kills,
                    }
                )

# Load into a Pandas DataFrame
df = pd.DataFrame(parsed_data)

# Dictionary to hold our cleaned, level-by-level summary rows
summary_rows = []

# Process each level individually to filter outliers and aggregate
for lvl in sorted(df["Level"].unique()):
    df_lvl = df[df["Level"] == lvl].copy()

    if df_lvl.empty:
        continue

    # --- Outlier Filtering (Normalize to within 10% of the Median) ---
    # We use Median as the baseline so true outliers don't skew the target center.
    median_time = df_lvl["Minutes"].median()
    median_kills = df_lvl["Kills"].median()

    # Define strict 10% boundaries
    time_lower, time_upper = median_time * 0.90, median_time * 1.10
    kills_lower, kills_upper = median_kills * 0.90, median_kills * 1.10

    # Filter rows that fall within BOTH the time and kills 10% thresholds
    df_clean = df_lvl[
        (df_lvl["Minutes"] >= time_lower)
        & (df_lvl["Minutes"] <= time_upper)
        & (df_lvl["Kills"] >= kills_lower)
        & (df_lvl["Kills"] <= kills_upper)
    ]

    # If the 10% constraint is too aggressive and wipes out all data, fallback to original
    if df_clean.empty:
        df_clean = df_lvl

    # --- Aggregation ---
    unique_players = df_clean["Player"].nunique()
    avg_minutes = df_clean["Minutes"].mean()
    avg_kills = df_clean["Kills"].mean()

    # Convert average minutes back to a readable HH:MM string format
    avg_hours_int = int(avg_minutes // 60)
    avg_mins_int = int(avg_minutes % 60)
    avg_time_str = f"{avg_hours_int:02d}:{avg_mins_int:02d}"

    summary_rows.append(
        {
            "Level": lvl,
            "Number of Player Names": unique_players,
            "Average Time to Reach Level (HH:MM)": avg_time_str,
            "Average Kills to Reach Level": round(avg_kills, 1),
        }
    )

# Create final summary DataFrame and export to Excel
summary_df = pd.DataFrame(summary_rows)
output_file = "wow_level_analysis.xlsx"
summary_df.to_excel(output_file, index=False)

print(f"Analysis complete! Data saved to {output_file}")
