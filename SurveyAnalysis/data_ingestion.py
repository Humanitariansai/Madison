"""
Data Ingestion Module
This module handles reading and processing survey data from CSV files.

Author: Nidhi
Date: 2025
"""

import pandas as pd


def load_survey(filename):
    """
    Load survey data from a CSV file.
    
    Parameters:
    -----------
    filename : str
        Path to the CSV file (e.g., 'data/raw/survey.csv')
    
    Returns:
    --------
    pandas.DataFrame
        DataFrame containing the survey data
    
    Example:
    --------
    >>> data = load_survey('data/raw/customer_survey.csv')
    >>> print(data.head())
    """
    
    try:
        # Read the CSV file
        data = pd.read_csv(filename)
        
        print(f"✅ Successfully loaded survey data from: {filename}")
        print(f"📊 Number of responses: {len(data)}")
        print(f"📋 Number of questions: {len(data.columns)}")
        
        return data
        
    except FileNotFoundError:
        print(f"❌ Error: File '{filename}' not found!")
        print("Please check the file path and try again.")
        return None
        
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return None


# Test the function when this file is run directly
if __name__ == "__main__":
    print("=" * 50)
    print("DATA INGESTION MODULE - TEST")
    print("=" * 50)
    print("\nThis module is ready to load survey data!")
    print("Use: data = load_survey('path/to/file.csv')")