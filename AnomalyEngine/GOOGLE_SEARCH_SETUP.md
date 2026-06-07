# Google Custom Search Integration

This guide explains how to set up Google Custom Search API for the Anomaly Engine's web search feature.

## Overview

The anomaly explanation system now fetches real web search results to correlate with detected anomalies. This provides factual context (news, events, market updates) that the AI model uses to explain why anomalies occurred.

## Setup Steps

### 1. Create a Google Custom Search Engine

1. Go to [Google Custom Search](https://cse.google.com/)
2. Click **Create** to set up a new search engine
3. Configure search scope:
   - **Sites to search:** Leave blank to search the entire web (or specify Nepal-focused news sites like `kathmandopost.com`, `myrepublica.com`, `nepse.com.np`)
   - **Name:** e.g., "NEPSE Anomaly Search"
4. Click **Create**
5. You'll get a **Search Engine ID** (cx parameter) — save this

### 2. Enable Google Custom Search API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Custom Search API**:
   - Search for "Custom Search API"
   - Click **Enable**
4. Create an API key:
   - Go to **Credentials** → **Create Credentials** → **API Key**
   - Copy the **API Key** — this is your `GOOGLE_SEARCH_API_KEY`

### 3. Set Environment Variables

Add these to your `.env` file or system environment:

```bash
export GOOGLE_SEARCH_API_KEY="your_api_key_here"
export GOOGLE_SEARCH_ENGINE_ID="your_search_engine_id_here"
```

For development, add to your `.env` file in the AnomalyEngine directory:

```
GOOGLE_SEARCH_API_KEY=your_api_key_here
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id_here
```

### 4. Free Tier Limits

- **Free tier:** 100 queries per day
- **Paid tier:** Up to 10,000 queries per day

The anomaly explanation system limits searches to the top 10 anomalies per request, so most typical usage stays within the free tier.

## Usage

When you call `/analyze/explain` endpoint:

1. The backend extracts anomaly rows from the detection result
2. For each anomaly date, it builds search queries:
   - `{Stock} Nepal {Date}` (company-specific)
   - `Nepal protest {Month/Year}` (political events)
   - `Nepal strike {Month/Year}` (labor events)
   - `NEPSE {Stock} {Date}` (market news)
   - `Nepal news {Date}` (general news)
3. Results are fetched from Google Custom Search API
4. Search context is embedded into the AI model prompt
5. The model analyzes the anomalies alongside real news evidence

## Example Output

When search results are found, the prompt includes:

```
## Web Search Results

### 2025-09-18 (API)

**Query:** Nepal protest September 2025
- Gen Z Protest Disrupts Kathmandu: Youth movement against government policies...
- Nepal Youth Strike Impact on Markets: Trading volume declined significantly...

**Query:** NEPSE API September 2025
- API Stock Falls on Market-wide Uncertainty: Broader NEPSE index down 2.3%...
```

The AI then correlates these findings with the technical anomaly (e.g., low volume, price drop).

## Troubleshooting

### No search results found

- Verify API key and Search Engine ID are correct
- Check that API is enabled in Google Cloud Console
- Ensure you haven't exceeded the daily quota (100 free queries)
- Try manually searching at [cse.google.com](https://cse.google.com/) with your search engine

### API Key invalid error

```
Error fetching Google Custom Search results: Invalid API key
```

- Regenerate your API key in Google Cloud Console
- Verify the key is exactly what you pasted into `.env`

### Search Engine ID missing error

- Confirm your Search Engine ID (cx) matches the one from cse.google.com
- Do not include the full URL, just the ID

### Quota exceeded

- Upgrade to the paid plan ($5 USD for 10k extra queries/month)
- Or wait until the next day for the free tier to reset

## Configuration Options

To customize search behavior, modify `src/api/ai_services.py`:

- `build_search_context()`: Adjust search queries or number of results per query
- `fetch_google_custom_search()`: Change `num_results` parameter (max 10 per query)
- System message in `call_github_ai_explanation()` / `call_openai_ai_explanation()`: Adjust AI instructions for interpreting search results

## Disabling Search (Fallback Behavior)

If you don't have a Google API key configured:

1. Search context will be empty
2. The AI model will fall back to technical analysis only
3. No errors will be logged — the system gracefully degrades

To explicitly disable search, comment out the `GOOGLE_SEARCH_API_KEY` environment variable.

## Next Steps

- Test with a sample anomaly explanation request to verify search results are appearing
- Monitor the API quota usage in Google Cloud Console
- Adjust search queries if results are not relevant

## References

- [Google Custom Search API Documentation](https://developers.google.com/custom-search/v1/overview)
- [Google Cloud Console](https://console.cloud.google.com/)
- [Custom Search Engine Management](https://cse.google.com/)
