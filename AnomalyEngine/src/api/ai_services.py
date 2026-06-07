import json
import os
import re
from typing import Any, Dict, List
from datetime import datetime, timedelta

from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
import requests
from openai import OpenAI, api_key

from . import schemas
from tavily import TavilyClient






def _extract_anomaly_rows(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract rows marked as anomalies from the analysis data."""
    rows: List[Dict[str, Any]] = []
    for index, row in enumerate(data, start=1):
        cluster = row.get("cluster")
        is_anomaly = row.get("anomaly") is True or cluster == -1 or row.get("cluster_dbscan") == -1 or row.get("cluster_isolation_forest") == -1
        if not is_anomaly:
            continue
        rows.append({
            "index": index,
            "date": row.get("date") or row.get("transaction_time"),
            "close": row.get("close") or row.get("price") or row.get("adj_close"),
            "volume": row.get("volume"),
            "z_score": row.get("Anomaly_Z_Score") or row.get("z_score") or row.get("Z_Score"),
            "cluster": cluster,
            "dbscan": row.get("Anomaly_DBSCAN") or row.get("cluster_dbscan"),
            "isolation_forest": row.get("Anomaly_Isolation_Forest") or row.get("cluster_isolation_forest"),
        })
    return rows


def tavily_search(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
    """Fetch search results from Tavily API."""
    api_key = os.getenv("TAVILY_API_KEY", "").strip()
    if not api_key:
        print("Warning: Tavily API key not configured. Skipping search.")
        return []
    
    try:
        tavily_client = TavilyClient(api_key=api_key)
        response = tavily_client.search(
            query=query,
            max_results=min(num_results, 10),  # Tavily supports up to 10 results per query
            include_answer=False,  # We only want search results, not QA answers
        )
        
        results = []
        if response.get("results"):
            for item in response["results"][:num_results]:
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("url", ""),
                    "snippet": item.get("content", ""),
                })
        return results
    except Exception as e:
        print(f"Error fetching Tavily Search results: {e}")
        return []




def build_search_context(stock: str, anomaly_rows: List[Dict[str, Any]]) -> str:
    """
    Build search context from anomaly rows by fetching news for each date using Tavily API.
    Returns formatted markdown text with search results.
    """
    search_context_parts = ["## Search Context\n"]
    
    for row in anomaly_rows[:5]:  # limit to first 5 anomalies to reduce token usage
        date_str = row.get("date", "")
        if not date_str:
            continue
        
        try:
            # Parse date for context window
            anomaly_date = datetime.strptime(str(date_str), "%Y-%m-%d")
            
            # Build minimal search queries (reduced from 5 to 2 most important)
            queries = [
                f"{stock} Nepal {date_str}",
                f"Nepal protest {anomaly_date.strftime('%B %Y')}",
            ]
            
            section_found = False
            for query in queries:
                results = tavily_search(query, num_results=1)  # reduced from 3 to 1 result per query
                if results:
                    if not section_found:
                        search_context_parts.append(f"\n### {date_str} ({stock})")
                        section_found = True
                    
                    # Minimal formatting: just the result, no query header
                    for result in results:
                        search_context_parts.append(f"- {result['title']}: {result['snippet'][:100]}... ([link]({result['link']}))")  # reduced from 200 to 100 chars
            
            if not section_found:
                search_context_parts.append(f"\n### {date_str} ({stock})")
                search_context_parts.append("No news found.")
        
        except Exception as e:
            print(f"Error processing anomaly date {date_str}: {e}")
            continue
    
    return "\n".join(search_context_parts) if len(search_context_parts) > 1 else ""


def build_ai_prompt(payload: schemas.AnomalyExplanationRequest, search_context: str = "") -> str:
    """Build a detailed prompt for AI model to explain anomalies."""
    anomaly_rows = payload.data or []
    compact_rows = anomaly_rows

    row_summaries = []
    for index, row in enumerate(compact_rows, start=1):
        flags = []
        if row.get("cluster") == -1:
            flags.append("combined")
        if row.get("dbscan") == -1:
            flags.append("DBSCAN")
        if row.get("isolation_forest") == -1:
            flags.append("Isolation Forest")
        if row.get("anomaly") is True:
            flags.append("anomaly")

        z_score = row.get("z_score") if row.get("z_score") is not None else row.get("Anomaly_Z_Score")
        z_score_text = f"{float(z_score):.2f}" if isinstance(z_score, (int, float)) else str(z_score)

        detail_parts = [
            f"date={row.get('date')}",
            f"close={row.get('close')}",
        ]
        if row.get("previous_close") is not None:
            detail_parts.append(f"previous_close={row.get('previous_close')}")
        if row.get("rolling_mean") is not None:
            detail_parts.append(f"rolling_mean={row.get('rolling_mean')}")
        if row.get("rolling_std") is not None:
            detail_parts.append(f"rolling_std={row.get('rolling_std')}")
        if row.get("average_volume") is not None:
            detail_parts.append(f"average_volume={row.get('average_volume')}")
        if row.get("volume") is not None:
            detail_parts.append(f"volume={row.get('volume')}")
        if row.get("change") is not None:
            detail_parts.append(f"change={row.get('change')}")
        if z_score is not None:
            detail_parts.append(f"z_score={z_score_text}")
        if row.get("bb_width") is not None:
            detail_parts.append(f"bb_width={row.get('bb_width')}")

        if row.get("adjacent_rows"):
            adjacent = []
            for adj in row.get("adjacent_rows", [])[:6]:
                adjacent_close = adj.get("close")
                adjacent_volume = adj.get("volume")
                adjacent_date = adj.get("date")
                adjacent_change = adj.get("change")
                adjacent.append(
                    f"[{adjacent_date}: close={adjacent_close}, volume={adjacent_volume}, change={adjacent_change}]"
                )
            detail_parts.append(f"adjacent_rows={'; '.join(adjacent)}")

        if row.get("detector_flags"):
            detail_parts.append(f"detector_flags={', '.join(row.get('detector_flags'))}")
        elif flags:
            detail_parts.append(f"flagged_by={', '.join(flags)}")

        row_summaries.append(f"  Row {index}: " + ", ".join(detail_parts))

    params_lines = []
    if payload.best_params:
        for method, params in (payload.best_params or {}).items():
            if isinstance(params, dict):
                params_lines.append(f"- {method}:")
                for key, value in params.items():
                    params_lines.append(f"  - {key} = {value}")
            else:
                params_lines.append(f"- {method} = {params}")
    if not params_lines:
        params_lines.append("- No tuning parameters provided.")

    summary = {
        "stock": payload.stock,
        "mode": payload.mode,
        "timeframe": payload.timeframe,
        "window": {"start_date": payload.start_date, "end_date": payload.end_date},
        "metrics": payload.metrics or {},
        "best_params": payload.best_params or {},
        "total_anomaly_rows": len(anomaly_rows),
    }

    return (
        "You are an equity market analyst specializing in NEPSE (Nepal Stock Exchange) stocks. "
        "The rows below have already been flagged as anomalies by the detection system. \n\n"
        f"Focus on the ticker '{payload.stock}' and the date range {payload.start_date} to {payload.end_date}.\n\n"
        "Explain anomalies using these event categories:\n"
        "1. FINANCIAL EVENTS: Earnings reports, dividend announcements, earnings guidance changes, "
        "regulatory approvals/rejections, licensing changes, policy changes affecting the sector, mergers/acquisitions, "
        "capital raises, write-downs, or accounting restatements.\n"
        "2. REAL-WORLD EVENTS: Political developments, labor strikes/protests, natural disasters (earthquakes, floods), "
        "infrastructure changes, supply chain disruptions, or major accidents affecting operations.\n"
        "3. MARKET EVENTS: Sector-wide news, competitor announcements affecting market dynamics, "
        "macroeconomic policy changes (interest rates, currency movements), or market sentiment shifts.\n"
        "4. COMPANY-SPECIFIC NEWS: Executive appointments/departures, major contracts/deals, new products/services, "
        "management commentary, or analyst reports.\n"
        f"\n## Web Search Results\n{search_context if search_context.strip() else 'No search results available. Proceed with technical analysis.'}\n\n"
        "Based on the search results above, correlate any found news/events with the anomalies below. If search results are empty for a date, explicitly state that and focus on technical indicators.\n\n"
        "Explain why each point is unusual using the provided feature values, detector labels, and any external context you find. "
        "Mention relative price movement, volume behavior, z-score severity, and whether multiple detectors agree. "
        "Do not invent facts—only report news you actually find. If no relevant news is found, explicitly state that and focus on technical indicators. "
        "Return only markdown. Use bold headings like **Row 1:**, bullet lists for each anomaly (including any news correlation), and finish with a bold **Overall Summary:** section. Do not wrap the response in code fences.\n\n"
        f"Analysis context:\n{json.dumps(summary, ensure_ascii=False, indent=2, default=str)}\n\n"
        "Detection parameters:\n"
        f"{chr(10).join(params_lines)}\n\n"
        "Flagged anomaly rows with context:\n"
        f"{chr(10).join(row_summaries)}"
    )


def extract_overall_summary(summary: str) -> str:
    """Extract the overall summary section from AI markdown response."""
    overall_match = re.search(r"\*\*(?:Overall\s+)?Summary:\*\*\s*(.*)", summary, re.S)
    if overall_match:
        overall_text = overall_match.group(1).strip()
        overall_text = re.split(r"^-{3,}$", overall_text, maxsplit=1, flags=re.MULTILINE)[0].strip()
        return overall_text
    return re.split(r"^-{3,}$", summary, maxsplit=1, flags=re.MULTILINE)[0].strip()


def parse_ai_explanation_entries(summary: str) -> List[Dict[str, Any]]:
    """Parse AI explanation markdown into structured entry objects."""
    if not summary:
        return []

    row_pattern = re.compile(r"^\*\*Row\s+(\d+)(?:\s*\(([^)]+)\))?:\s*\*\*", re.MULTILINE)
    matches = list(row_pattern.finditer(summary))
    if not matches:
        return []

    entries: List[Dict[str, Any]] = []
    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(summary)
        block = summary[start:end].strip()

        # Remove any section after the row bullets that belongs to the global summary
        block = re.split(r"\*\*Overall Summary:\*\*", block, maxsplit=1)[0].strip()
        block = re.split(r"\*\*Summary:\*\*", block, maxsplit=1)[0].strip()
        block = re.split(r"^-{3,}$", block, maxsplit=1, flags=re.MULTILINE)[0].strip()

        bullets = []
        row_summary = ""
        for line in block.splitlines():
            normalized = line.strip()
            if normalized.startswith("-") or normalized.startswith("*"):
                text = re.sub(r"^[-*]\s*", "", normalized)
                if text and text != "--":
                    bullets.append(text)
            elif normalized and not row_summary:
                # If there's a paragraph after bullets, treat it as the row summary.
                row_summary = normalized

        entries.append({
            "row_number": int(match.group(1)),
            "date": match.group(2).strip() if match.group(2) else None,
            "bullets": bullets,
            "summary": row_summary,
        })

    return entries


def call_github_ai_explanation(token:str,payload: schemas.AnomalyExplanationRequest) -> Dict[str, Any]:
    """Call GitHub Models endpoint for AI explanation."""
    endpoint = os.getenv("MODEL_ENDPOINT")
    model = os.getenv("MODEL_NAME", "openai/gpt-4.1")

    print(f"Using GitHub model endpoint {endpoint} with model {model} for anomaly explanation")

    # Fetch search context from Google Custom Search
    anomaly_rows = _extract_anomaly_rows(payload.data or [])
    search_context = build_search_context(payload.stock, anomaly_rows)
    print(f"Fetched search context for {len(anomaly_rows)} anomalies")
    print(search_context)
    prompt = build_ai_prompt(payload, search_context=search_context)

    try:
        client = ChatCompletionsClient(endpoint=endpoint, credential=AzureKeyCredential(token))
        response = client.complete(
            model=model,
            messages=[
                SystemMessage(
                    "You are a NEPSE (Nepal Stock Exchange) financial analyst. "
                    "Analyze the provided anomalies and web search results to identify correlations. "
                    "Use the search context to validate or explain the detected anomalies. "
                    "Focus on: (1) Financial events: earnings, dividends, regulatory changes, sector policy; "
                    "(2) Real-world events: political developments, strikes, protests, natural disasters, supply chain disruptions; "
                    "(3) Market events: sector news, competitor moves, macroeconomic changes; "
                    "(4) Company news: executive changes, major contracts, product launches. "
                    "Search 2 weeks before to 2 weeks after each anomaly date. Correlate findings with technical anomalies. "
                    "Report only what you find—do not speculate or invent facts."
                ),
                UserMessage(prompt),
            ],
            temperature=0.2, #for more strict, factual and less creative responses
        )
        summary = str(response.choices[0].message.content).strip()
    except Exception as e:
        print("Error calling GitHub model endpoint, falling back to heuristic explanation", e)
        return heuristic_anomaly_explanation(payload)

    if not summary:
        return heuristic_anomaly_explanation(payload)

    entries = parse_ai_explanation_entries(summary)
    overall = extract_overall_summary(summary)

    return {
        "raw_summary": summary,
        "summary": overall,
        "highlights": [],
        "entries": entries,
        "anomaly_count": len(_extract_anomaly_rows(payload.data)),
        "source": model,
    }


def call_openai_ai_explanation(token:str,payload: schemas.AnomalyExplanationRequest) -> Dict[str, Any]:
    """Call OpenAI API for AI explanation (fallback)."""
   
    model = os.getenv("MODEL_NAME", "openai/gpt-4.1")
    endpoint = os.getenv("MODEL_ENDPOINT")

    print(f"Using OpenAI model {model} for anomaly explanation")

    # Fetch search context from Google Custom Search
    anomaly_rows = _extract_anomaly_rows(payload.data or [])
    search_context = build_search_context(payload.stock, anomaly_rows)
    print(f"Fetched search context for {len(anomaly_rows)} anomalies")

    prompt = build_ai_prompt(payload, search_context=search_context)

    try:
        client = OpenAI(
            base_url=endpoint,
            api_key=token,
        )
        response = client.chat.completions.create(
            messages = [
                {
                    "role":"system",
                    "content":"You are a NEPSE (Nepal Stock Exchange) financial analyst. "
                    "Analyze the provided anomalies and web search results to identify correlations. "
                    "Use the search context to validate or explain the detected anomalies. "
                    "Focus on: (1) Financial events: earnings, dividends, regulatory changes, sector policy; "
                    "(2) Real-world events: political developments, strikes, protests, natural disasters, supply chain disruptions; "
                    "(3) Market events: sector news, competitor moves, macroeconomic changes; "
                    "(4) Company news: executive changes, major contracts, product launches. "
                    "Report only what you find in the search results—do not speculate or invent facts."
                },
                {
                    "role":"user",
                    "content":prompt
                }
            ],
            temperature=0.2,

        )
        response = requests.post(
            endpoint,
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "You explain anomaly detection results in concise analyst-friendly language."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
                "top_p": 1,
                "model":model
            },
        )
        response.raise_for_status()
        data = response.json()
        summary = data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print("Error calling OpenAI API, falling back to heuristic explanation", e)
        return heuristic_anomaly_explanation(payload)

    if not summary:
        return heuristic_anomaly_explanation(payload)

    entries = parse_ai_explanation_entries(summary)
    overall = extract_overall_summary(summary)

    return {
        "raw_summary": summary,
        "summary": overall,
        "highlights": [],
        "entries": entries,
        "anomaly_count": len(_extract_anomaly_rows(payload.data)),
        "source": model,
    }


def heuristic_anomaly_explanation(payload: schemas.AnomalyExplanationRequest) -> Dict[str, Any]:
    """Generate heuristic explanation with structured table format."""
    anomaly_rows = _extract_anomaly_rows(payload.data)
    
    if not anomaly_rows:
        return {
            "raw_summary": "No rows in the result set were marked as anomalies, so there is nothing to explain.",
            "summary": "No rows in the result set were marked as anomalies, so there is nothing to explain.",
            "highlights": ["The current run did not produce anomaly flags."],
            "entries": [],
            "anomaly_count": 0,
            "source": "heuristic",
        }

    # Build structured entries from anomaly rows
    entries: List[Dict[str, Any]] = []
    highlights = []
    
    for row in anomaly_rows:
        z_score = row.get("z_score")
        z_score_val = float(z_score) if z_score is not None and str(z_score).replace(".", "", 1).replace("-", "", 1).isdigit() else None
        
        close = row.get("close")
        rolling_mean = row.get("rolling_mean")
        bb_width = row.get("bb_width")
        rsi = row.get("RSI")
        volume = row.get("volume")
        average_volume = row.get("average_volume")
        
        # Determine detector agreement
        detectors = []
        if row.get("dbscan") == -1:
            detectors.append("DBSCAN")
        if row.get("isolation_forest") == -1:
            detectors.append("Isolation Forest")
        
        detector_summary = " + ".join(detectors) if len(detectors) > 1 else (detectors[0] if detectors else "Unknown")
        
        # Build explanation bullets with RSI and BB width context
        bullets = []
        
        if close is not None:
            bullets.append(f"Close: {close}")
        
        if volume is not None:
            bullets.append(f"Volume: {volume:,}")
        
        # Price anomaly: Z-score deviation from mean
        if z_score_val is not None:
            direction = "above" if z_score_val > 0 else "below"
            bullets.append(f"Price is {abs(z_score_val):.2f}σ {direction} mean")
        
        # Volatility anomaly: BB width interpretation
        if bb_width is not None and isinstance(bb_width, (int, float)):
            if bb_width > 0.15:
                bullets.append(f"BB width {bb_width:.3f} indicates elevated volatility spike")
            elif bb_width < 0.02:
                bullets.append(f"BB width {bb_width:.3f} shows extremely compressed bands")
            else:
                bullets.append(f"BB width {bb_width:.3f} indicates notable volatility change")
        
        # Volume anomaly context
        if average_volume is not None and volume is not None and isinstance(volume, (int, float)) and isinstance(average_volume, (int, float)) and average_volume > 0:
            volume_ratio = volume / average_volume
            if volume_ratio > 2.5:
                bullets.append(f"Volume {volume_ratio:.1f}× average signals strong trading activity")
            elif volume_ratio < 0.3:
                bullets.append(f"Volume {volume_ratio:.1f}× average signals weak trading")
        
        # RSI-based momentum context
        if rsi is not None and isinstance(rsi, (int, float)):
            if rsi > 70:
                bullets.append(f"RSI {rsi:.0f} indicates overbought conditions")
            elif rsi < 30:
                bullets.append(f"RSI {rsi:.0f} indicates oversold conditions")
        
        if len(detectors) > 1:
            bullets.append(f"Strong signal: {' + '.join(detectors)} agreement")
        elif detectors:
            bullets.append(f"Flagged by {detectors[0]}")
        
        if not bullets:
            bullets.append("This row was flagged by the anomaly detection system.")
        
        entry = {
            "row_number": row.get("index", 0),
            "date": row.get("date", ""),
            "bullets": bullets,
            "summary": f"Anomaly detected with {len(detectors)} detector(s) confirming.",
        }
        entries.append(entry)
        
        # (no highlights produced here, UI builds highlights from entries)
    
    # Generate overall summary
    summary = (
        f"Detected {len(anomaly_rows)} anomalous rows. Price anomalies shown via z-score deviation. "
        f"Volatility changes via Bollinger Band width. RSI indicates momentum extremes. "
        f"Volume spikes show trading strength."
    )
    
    return {
        "summary": summary,
        "entries": entries,
        "anomaly_count": len(anomaly_rows),
        "source": "heuristic",
    }


def call_ai_explanation(payload: schemas.AnomalyExplanationRequest) -> Dict[str, Any]:

    github_token = os.getenv("TOKEN", "").strip()
    
    if github_token:
        return call_github_ai_explanation(github_token,payload)
    
    openai_key = os.getenv("TOKEN", "").strip()
    if openai_key:
        return call_openai_ai_explanation(openai_key,payload)
    
    # Fallback to heuristic
    return heuristic_anomaly_explanation(payload)
