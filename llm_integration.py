#!/usr/bin/env python3
"""
LLM Integration for Chrome History Analyzer

This script takes the output from chrome_history_analyzer.py and sends it to an LLM
for analysis and insights.

Usage:
    python llm_integration.py [--provider PROVIDER] [--prompt_file PROMPT_FILE]

Options:
    --provider PROVIDER     LLM provider: 'openai', 'anthropic', or 'local' (default: 'openai')
    --prompt_file PROMPT_FILE  Path to the prompt file (default: 'output/llm_prompt.txt')
"""

import argparse
import os
import json
from pathlib import Path

def analyze_with_openai(prompt):
    """
    Analyze the browsing data using OpenAI's API.
    
    Args:
        prompt: String containing the prompt for the LLM
        
    Returns:
        String containing the LLM's response
    """
    try:
        import openai
    except ImportError:
        print("OpenAI package not installed. Install it with: pip install openai")
        return None
    
    # Check for API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("OpenAI API key not found. Set it as an environment variable: OPENAI_API_KEY")
        return None
    
    openai.api_key = api_key
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return None

def analyze_with_anthropic(prompt):
    """
    Analyze the browsing data using Anthropic's API.
    
    Args:
        prompt: String containing the prompt for the LLM
        
    Returns:
        String containing the LLM's response
    """
    try:
        import anthropic
    except ImportError:
        print("Anthropic package not installed. Install it with: pip install anthropic")
        return None
    
    # Check for API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Anthropic API key not found. Set it as an environment variable: ANTHROPIC_API_KEY")
        return None
    
    client = anthropic.Anthropic(api_key=api_key)
    
    try:
        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=2000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text
    except Exception as e:
        print(f"Error calling Anthropic API: {e}")
        return None

def analyze_with_local_llm(prompt):
    """
    Analyze the browsing data using a local LLM (via Ollama).
    
    Args:
        prompt: String containing the prompt for the LLM
        
    Returns:
        String containing the LLM's response
    """
    try:
        import requests
    except ImportError:
        print("Requests package not installed. Install it with: pip install requests")
        return None
    
    # Assuming Ollama is running locally on the default port
    ollama_url = "http://localhost:11434/api/generate"
    
    try:
        response = requests.post(
            ollama_url,
            json={
                "model": "llama3",  # or any other model you have in Ollama
                "prompt": prompt,
                "stream": False
            }
        )
        
        if response.status_code == 200:
            return response.json().get("response", "No response from local LLM")
        else:
            print(f"Error from Ollama API: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error calling local LLM: {e}")
        print("Make sure Ollama is running. Install from: https://ollama.ai/")
        return None

def save_insights(insights, output_file='output/llm_insights.md'):
    """
    Save the LLM insights to a file.
    
    Args:
        insights: String containing the LLM's insights
        output_file: Path to save the insights
    """
    # Create output directory if it doesn't exist
    output_dir = Path(output_file).parent
    output_dir.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        f.write("# Chrome History Analysis Insights\n\n")
        f.write(insights)
    
    print(f"Insights saved to {output_file}")

def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description='Analyze Chrome history with an LLM')
    parser.add_argument('--provider', type=str, default='openai', 
                        choices=['openai', 'anthropic', 'local'],
                        help='LLM provider: openai, anthropic, or local')
    parser.add_argument('--prompt_file', type=str, default='output/llm_prompt.txt',
                        help='Path to the prompt file')
    
    args = parser.parse_args()
    
    # Check if prompt file exists
    if not os.path.exists(args.prompt_file):
        print(f"Prompt file not found: {args.prompt_file}")
        print("Run chrome_history_analyzer.py first to generate the prompt file.")
        return
    
    # Read the prompt
    with open(args.prompt_file, 'r') as f:
        prompt = f.read()
    
    print(f"Analyzing browsing history with {args.provider}...")
    
    # Call the appropriate LLM provider
    if args.provider == 'openai':
        insights = analyze_with_openai(prompt)
    elif args.provider == 'anthropic':
        insights = analyze_with_anthropic(prompt)
    elif args.provider == 'local':
        insights = analyze_with_local_llm(prompt)
    
    if insights:
        print("\n=== LLM Insights ===\n")
        print(insights)
        
        # Save insights to file
        save_insights(insights)
    else:
        print("Failed to get insights from LLM.")

if __name__ == "__main__":
    main()

