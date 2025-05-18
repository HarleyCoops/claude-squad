#!/usr/bin/env python3
"""
Daily Summary Generator for Chrome History Analyzer

This script generates a daily summary of Chrome browsing activity and optionally
sends it to an LLM for analysis.

Usage:
    python daily_summary.py [--days DAYS] [--analyze]

Options:
    --days DAYS     Number of days to look back (default: 1)
    --analyze       Send the summary to an LLM for analysis
"""

import argparse
import datetime
import os
import pandas as pd
from pathlib import Path
import subprocess
import json

def generate_daily_summary(days=1, analyze=False):
    """
    Generate a daily summary of Chrome browsing activity.
    
    Args:
        days: Number of days to look back
        analyze: Whether to send the summary to an LLM for analysis
    """
    # Run the chrome_history_analyzer.py script
    cmd = ["python", "chrome_history_analyzer.py", "--days", str(days), "--output", "markdown"]
    subprocess.run(cmd, check=True)
    
    # Check if the output file exists
    output_file = Path("output/chrome_history_report.md")
    if not output_file.exists():
        print(f"Output file not found: {output_file}")
        return
    
    # Read the markdown report
    with open(output_file, "r") as f:
        report = f.read()
    
    # Create a dated copy of the report
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    dated_output_file = Path(f"output/daily/{today}_chrome_history.md")
    dated_output_file.parent.mkdir(exist_ok=True, parents=True)
    
    with open(dated_output_file, "w") as f:
        f.write(report)
    
    print(f"Daily summary saved to {dated_output_file}")
    
    # Optionally send to LLM for analysis
    if analyze:
        # Run the llm_integration.py script
        cmd = ["python", "llm_integration.py"]
        subprocess.run(cmd, check=True)
        
        # Check if the insights file exists
        insights_file = Path("output/llm_insights.md")
        if insights_file.exists():
            # Create a dated copy of the insights
            dated_insights_file = Path(f"output/daily/{today}_insights.md")
            
            with open(insights_file, "r") as f_in:
                insights = f_in.read()
            
            with open(dated_insights_file, "w") as f_out:
                f_out.write(insights)
            
            print(f"Daily insights saved to {dated_insights_file}")

def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description='Generate daily summary of Chrome browsing activity')
    parser.add_argument('--days', type=int, default=1, help='Number of days to look back')
    parser.add_argument('--analyze', action='store_true', help='Send the summary to an LLM for analysis')
    
    args = parser.parse_args()
    
    generate_daily_summary(days=args.days, analyze=args.analyze)

if __name__ == "__main__":
    main()

