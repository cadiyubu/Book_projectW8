# Shared helper functions for Week 9 — Book Recommendation System
# Populate as scraping / cleaning / modeling logic stabilizes across notebooks.
# Keep pure functions here; notebooks import from this module, not the reverse.


import io
import requests
import pandas as pd
import numpy as np
import yaml


# =============================================================================
# 1. DATA LOADING / SAVING
# =============================================================================

def read_file(yaml_path, inp_data_section, file_name):
    """Load a CSV whose path is stored in a YAML config.
    Returns a DataFrame, or None on a handled error.

    sep=None + engine='python' lets pandas sniff the delimiter, which also
    absorbs Windows CRLF/BOM exports without choking.
    """
    # Read the YAML config
    try:
        with open(yaml_path, "r") as file:
            cfg = yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Config file not found: {yaml_path}")
        return None
    except yaml.YAMLError as e:
        print(f"Could not parse YAML: {e}")
        return None

    # Look up the CSV path inside the config
    try:
        csv_path = cfg[inp_data_section][file_name]
    except KeyError as e:
        print(f"Missing key in config: {e}")
        return None

    # Load the CSV
    return pd.read_csv(csv_path, sep=None, engine="python")


def out_csv(df, yaml_path, output_section_yaml, file_name):
    """Write a DataFrame to the CSV path stored under
    cfg[output_section_yaml][file_name] in the YAML config.

    KNOWN ISSUE (flagged, not fixed without sign-off): the bare `except:`
    below catches *every* exception and mislabels it as "file not found".
    A YAML parse error or a missing config key would print the wrong message.
    Left as-is to avoid a silent behaviour change.
    """
    try:
        with open(yaml_path, "r") as file:
            cfg = yaml.safe_load(file)
    except:
        print("Yaml configuration file not found!")
        return None

    df.to_csv(cfg[output_section_yaml][file_name], index=False)
    print(f"File saved to: {cfg[output_section_yaml][file_name]}")

    # -- EDA helpers ----------------------------------------------------------------

def summarise_dataframe(df):
    """Print shape, dtypes, null counts, and basic stats."""
    print(f"Shape: {df.shape}")
    print("\n--- Null counts ---")
    print(df.isnull().sum()[df.isnull().sum() > 0])
    print("\n--- Dtypes ---")
    print(df.dtypes)
