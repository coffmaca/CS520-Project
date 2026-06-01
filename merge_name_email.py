import pandas as pd
import numpy as np
import re


def merge_name_email(corprank_df, degree_df):
    """
    Matches names to Enron email formats and merges the best node.
    """
    # Create copies to avoid mutating original dataframes unexpectedly
    result_df = corprank_df.copy()

    # Ensure standard formatting for the email and degree columns
    degree_df['Node'] = degree_df['Node'].astype(str).str.lower().str.strip()
    degree_df['degree'] = pd.to_numeric(degree_df['degree'], errors='coerce')

    def find_best_email(name):
        if pd.isna(name):
            return np.nan

        # 1. Parse the Name
        name = str(name).lower().strip()

        # Handle "Last, First" vs "First Last" formats
        if ',' in name:
            parts = [p.strip() for p in name.split(',')]
            last = parts[0]
            first = parts[1].split()[0] if parts[1] else ""
        else:
            parts = name.split()
            if len(parts) >= 2:
                first = parts[0]
                last = parts[-1]
            else:
                first = ""
                last = parts[0] if parts else ""

        if not last:
            return np.nan

        # 2. Build Regex Pattern
        # Generate all valid prefixes of the first name (e.g., 'k', 'ke', 'ken', ..., 'kenneth')
        prefixes = [re.escape(first[:i]) for i in range(1, len(first) + 1)] if first else []
        last_esc = re.escape(last)

        # Rule (ii): Only the last name
        regex_parts = [f"^{last_esc}@enron\\.com$"]

        if prefixes:
            # Group all prefixes into an OR statement: (k|ke|ken|kenneth)
            prefix_group = f"({'|'.join(prefixes)})"

            # Rules (i), (iii), (v): prefix.last@enron.com
            regex_parts.append(f"^{prefix_group}\\.{last_esc}@enron\\.com$")

            # Rule (iv): prefix..last@enron.com
            regex_parts.append(f"^{prefix_group}\\.\\.{last_esc}@enron\\.com$")

        full_pattern = "|".join(regex_parts)

        # 3. Filter degree_df using the compiled pattern
        matches = degree_df[degree_df['Node'].str.match(full_pattern, na=False)]

        # 4. Apply match logic and tie-breakers
        if len(matches) == 0:
            return np.nan
        elif len(matches) == 1:
            return matches.iloc[0]['Node']
        else:
            # Multiple matches: sort by 'degree' descending, pick the highest
            best_match = matches.sort_values(by='degree', ascending=False).iloc[0]
            return best_match['Node']

    # Apply the function to create the new column
    result_df['Email'] = result_df['Name'].apply(find_best_email)

    return result_df


if __name__ == "__main__":
    degree_df_path = "data/degree_df.pkl"
    corprank_df_path = "data/CorpRank.csv"

    degree_df = pd.read_pickle(degree_df_path)
    corprank_df = pd.read_csv(corprank_csv_path)

    corprank_df = merge_name_email(corprank_df, degree_df)

    print("")