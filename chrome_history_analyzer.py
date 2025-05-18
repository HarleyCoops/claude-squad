#!/usr/bin/env python3
"""
Chrome History Analyzer

This script extracts browsing history from Google Chrome and analyzes it to provide
insights about browsing patterns, sleep habits, work focus, and interests.

Usage:
    python chrome_history_analyzer.py [--days DAYS] [--output OUTPUT]

Options:
    --days DAYS     Number of days of history to analyze (default: 30)
    --output OUTPUT Output format: 'csv', 'json', or 'markdown' (default: 'csv')
"""

import sqlite3
import pandas as pd
import datetime
import os
import argparse
import json
from pathlib import Path
from urllib.parse import urlparse
import platform
import shutil
import sys

def get_chrome_history_path():
    """Get the path to Chrome's History database based on the operating system."""
    home = Path.home()
    
    if platform.system() == "Windows":
        return home / "AppData/Local/Google/Chrome/User Data/Default/History"
    elif platform.system() == "Darwin":  # macOS
        return home / "Library/Application Support/Google/Chrome/Default/History"
    elif platform.system() == "Linux":
        return home / ".config/google-chrome/Default/History"
    else:
        raise OSError(f"Unsupported operating system: {platform.system()}")

def extract_chrome_history(days=30):
    """
    Extract Chrome browsing history for the specified number of days.
    
    Args:
        days: Number of days of history to extract
        
    Returns:
        DataFrame containing the browsing history
    """
    # Get the path to Chrome's History database
    history_db = get_chrome_history_path()
    
    if not history_db.exists():
        print(f"Chrome history database not found at {history_db}")
        print("Please check if Chrome is installed or if the path is correct.")
        sys.exit(1)
    
    # Create a temporary copy of the database (Chrome locks the original)
    temp_copy = Path.home() / "history_temp.db"
    
    try:
        # Copy the database
        shutil.copy2(history_db, temp_copy)
        
        # Connect to the database
        conn = sqlite3.connect(temp_copy)
        
        # Calculate the cutoff date
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
        cutoff_timestamp = int((cutoff_date - datetime.datetime(1970, 1, 1)).total_seconds() * 1000000) + 11644473600000000
        
        # Query the visits with timestamps and URLs
        query = """
        SELECT 
            datetime(visits.visit_time/1000000-11644473600, 'unixepoch', 'localtime') as visit_time,
            urls.url, 
            urls.title,
            visits.visit_duration/1000000 as duration_seconds
        FROM 
            visits JOIN urls ON visits.url = urls.id
        WHERE 
            visits.visit_time > ?
        ORDER BY 
            visits.visit_time DESC
        """
        
        df = pd.read_sql_query(query, conn, params=(cutoff_timestamp,))
        conn.close()
        
        # Convert visit_time to datetime
        df['visit_time'] = pd.to_datetime(df['visit_time'])
        
        # Add additional columns for analysis
        df['hour'] = df['visit_time'].dt.hour
        df['date'] = df['visit_time'].dt.date
        df['day_of_week'] = df['visit_time'].dt.day_name()
        df['domain'] = df['url'].apply(lambda x: urlparse(x).netloc)
        
        return df
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        # Clean up the temporary file
        if temp_copy.exists():
            os.remove(temp_copy)

def analyze_browsing_patterns(df):
    """
    Analyze browsing patterns from the history data.
    
    Args:
        df: DataFrame containing browsing history
        
    Returns:
        Dictionary containing analysis results
    """
    # Activity by hour
    hourly_activity = df.groupby('hour').size().reset_index(name='count')
    
    # Activity by day of week
    daily_activity = df.groupby('day_of_week').size().reset_index(name='count')
    
    # Top domains
    domain_counts = df.groupby('domain').size().reset_index(name='count').sort_values('count', descending=True)
    
    # First and last browsing times per day
    daily_first_last = df.groupby('date').agg(
        first_browse=('visit_time', 'min'),
        last_browse=('visit_time', 'max')
    ).reset_index()
    
    # Add first and last hour
    daily_first_last['first_hour'] = daily_first_last['first_browse'].dt.hour
    daily_first_last['last_hour'] = daily_first_last['last_browse'].dt.hour
    
    # Calculate average first and last browsing hours
    avg_first_hour = daily_first_last['first_hour'].mean()
    avg_last_hour = daily_first_last['last_hour'].mean()
    
    return {
        'hourly_activity': hourly_activity.to_dict('records'),
        'daily_activity': daily_activity.to_dict('records'),
        'top_domains': domain_counts.head(20).to_dict('records'),
        'avg_first_hour': avg_first_hour,
        'avg_last_hour': avg_last_hour
    }

def generate_llm_prompt(analysis_results, df):
    """
    Generate a prompt for an LLM to analyze the browsing data.
    
    Args:
        analysis_results: Dictionary containing analysis results
        df: DataFrame containing browsing history
        
    Returns:
        String containing the prompt
    """
    hourly_activity = pd.DataFrame(analysis_results['hourly_activity'])
    top_domains = pd.DataFrame(analysis_results['top_domains'])
    
    prompt = f"""
    Analyze this Chrome browsing history data:
    
    1. Hourly activity pattern:
    {hourly_activity.to_string()}
    
    2. Top domains visited:
    {top_domains.to_string()}
    
    3. Average first browsing hour: {analysis_results['avg_first_hour']:.2f}
    4. Average last browsing hour: {analysis_results['avg_last_hour']:.2f}
    
    5. Sample of recent URLs and titles:
    {df[['visit_time', 'title', 'url']].head(10).to_string()}
    
    Based on this data, please provide insights about:
    1. Sleep patterns (when the person likely wakes up and goes to sleep)
    2. Work focus and productivity patterns
    3. Main interests based on content
    4. Recommendations for better time management
    """
    
    return prompt

def save_output(df, analysis_results, output_format='csv', output_prefix='chrome_history'):
    """
    Save the results to files in the specified format.
    
    Args:
        df: DataFrame containing browsing history
        analysis_results: Dictionary containing analysis results
        output_format: Format to save the output ('csv', 'json', or 'markdown')
        output_prefix: Prefix for the output files
    """
    # Create output directory if it doesn't exist
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    
    # Save raw data
    if output_format == 'csv':
        df.to_csv(output_dir / f"{output_prefix}_raw.csv", index=False)
        
        # Save analysis results
        hourly_activity = pd.DataFrame(analysis_results['hourly_activity'])
        hourly_activity.to_csv(output_dir / f"{output_prefix}_hourly.csv", index=False)
        
        top_domains = pd.DataFrame(analysis_results['top_domains'])
        top_domains.to_csv(output_dir / f"{output_prefix}_domains.csv", index=False)
        
    elif output_format == 'json':
        df.to_json(output_dir / f"{output_prefix}_raw.json", orient='records')
        
        # Save analysis results
        with open(output_dir / f"{output_prefix}_analysis.json", 'w') as f:
            json.dump(analysis_results, f, indent=2, default=str)
            
    elif output_format == 'markdown':
        # Create a markdown report
        markdown = f"# Chrome Browsing History Analysis\n\n"
        markdown += f"Analysis date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Hourly activity
        markdown += "## Activity by Hour\n\n"
        hourly_activity = pd.DataFrame(analysis_results['hourly_activity'])
        for _, row in hourly_activity.iterrows():
            markdown += f"- {row['hour']}:00 - {row['count']} visits\n"
        
        # Top domains
        markdown += "\n## Top Domains\n\n"
        top_domains = pd.DataFrame(analysis_results['top_domains'])
        for _, row in top_domains.head(10).iterrows():
            markdown += f"- {row['domain']}: {row['count']} visits\n"
        
        # Sleep patterns
        markdown += f"\n## Estimated Sleep Patterns\n\n"
        markdown += f"- Average first browsing hour: {analysis_results['avg_first_hour']:.2f}\n"
        markdown += f"- Average last browsing hour: {analysis_results['avg_last_hour']:.2f}\n"
        
        # Sample of recent URLs
        markdown += "\n## Recent Browsing Activity\n\n"
        for _, row in df.head(10).iterrows():
            date_str = row['visit_time'].strftime('%Y-%m-%d %H:%M:%S')
            markdown += f"- {date_str}: [{row['title']}]({row['url']})\n"
        
        # Save the markdown file
        with open(output_dir / f"{output_prefix}_report.md", 'w') as f:
            f.write(markdown)
    
    print(f"Output saved to {output_dir} directory")

def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description='Analyze Chrome browsing history')
    parser.add_argument('--days', type=int, default=30, help='Number of days of history to analyze')
    parser.add_argument('--output', type=str, default='csv', choices=['csv', 'json', 'markdown'], 
                        help='Output format: csv, json, or markdown')
    
    args = parser.parse_args()
    
    print(f"Extracting Chrome history for the past {args.days} days...")
    df = extract_chrome_history(days=args.days)
    
    print(f"Analyzing {len(df)} browsing history entries...")
    analysis_results = analyze_browsing_patterns(df)
    
    print("Generating LLM prompt...")
    prompt = generate_llm_prompt(analysis_results, df)
    
    # Save the prompt for later use with an LLM
    with open('output/llm_prompt.txt', 'w') as f:
        f.write(prompt)
    
    print(f"Saving results in {args.output} format...")
    save_output(df, analysis_results, output_format=args.output)
    
    print("Analysis complete!")
    print("To get AI insights, use the generated prompt in output/llm_prompt.txt with your preferred LLM.")

if __name__ == "__main__":
    main()

