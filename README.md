# Chrome History Analyzer

A Python tool to extract and analyze your Chrome browsing history to gain insights about your browsing patterns, sleep habits, work focus, and interests.

## Features

- Extract Chrome browsing history from the local SQLite database
- Analyze browsing patterns by hour and day of week
- Identify top visited domains
- Estimate sleep patterns based on first and last browsing times
- Generate prompts for LLM analysis
- Export data in CSV, JSON, or Markdown formats

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/chrome-history-analyzer.git
cd chrome-history-analyzer

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Basic usage (analyzes last 30 days of history)
python chrome_history_analyzer.py

# Analyze a specific number of days
python chrome_history_analyzer.py --days 7

# Export in different formats
python chrome_history_analyzer.py --output csv
python chrome_history_analyzer.py --output json
python chrome_history_analyzer.py --output markdown
```

## LLM Integration

The tool generates a prompt file (`output/llm_prompt.txt`) that you can use with any LLM (like OpenAI's GPT models) to get AI-powered insights about your browsing habits.

### Example LLM Integration

```python
import openai
import os

# Set your OpenAI API key
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Read the generated prompt
with open('output/llm_prompt.txt', 'r') as f:
    prompt = f.read()

# Send to OpenAI for analysis
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": prompt}]
)

# Print the insights
print(response.choices[0].message.content)
```

## Privacy and Security

This tool processes your browsing history locally on your machine. However, if you use the LLM integration, be aware that:

1. The data sent to external LLM APIs may include domain names and timestamps from your browsing history
2. Consider sanitizing sensitive information before sending to external APIs
3. For complete privacy, consider using a local LLM like Ollama or LM Studio

## File Locations

Chrome history database is typically located at:

- **Windows**: `C:\Users\[username]\AppData\Local\Google\Chrome\User Data\Default\History`
- **macOS**: `/Users/[username]/Library/Application Support/Google/Chrome/Default/History`
- **Linux**: `/home/[username]/.config/google-chrome/Default/History`

## Advanced Usage

### Daily Summaries

You can set up a cron job or scheduled task to run the script daily and generate summaries of your browsing activity:

```bash
# Example cron job (runs daily at 1 AM)
0 1 * * * cd /path/to/chrome-history-analyzer && python chrome_history_analyzer.py --days 1 --output markdown
```

### Custom Analysis

The script is modular and can be extended for custom analysis. See the `analyze_browsing_patterns` function to add your own metrics.

## License

MIT

