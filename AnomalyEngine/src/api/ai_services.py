import json
import os
import re
from typing import Any, Dict, List

from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
import requests
from openai import OpenAI, api_key

from . import schemas


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


def build_ai_prompt(payload: schemas.AnomalyExplanationRequest) -> str:
    """Build a detailed prompt for AI model to explain anomalies."""
    anomaly_rows = payload.data or []
    compact_rows = anomaly_rows[:15]

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
        "You are an equity market analyst explaining anomaly detection results to an analyst user. "
        "The rows below have already been flagged as anomalies by the detection system. "
        "Explain why each point is unusual using the provided feature values and detector labels. "
        "Mention relative price movement, volume behavior, z-score severity, and whether multiple detectors agree. "
        "Do not invent facts or claim causal certainty. Use 3-6 short bullet points, then one concise summary paragraph.\n\n"
        f"Analysis context:\n{json.dumps(summary, ensure_ascii=False, indent=2, default=str)}\n\n"
        "Detection parameters:\n"
        f"{chr(10).join(params_lines)}\n\n"
        "Flagged anomaly rows with context:\n"
        f"{chr(10).join(row_summaries)}"
    )


def extract_overall_summary(summary: str) -> str:
    """Extract the overall summary section from AI markdown response."""
    overall_match = re.search(r"\*\*Overall Summary:\*\*\s*(.*)", summary, re.S)
    return overall_match.group(1).strip() if overall_match else summary.strip()


def parse_ai_explanation_entries(summary: str) -> List[Dict[str, Any]]:
    """Parse AI explanation markdown into structured entry objects."""
    if not summary:
        return []

    row_pattern = re.compile(r"^\*\*Row\s+(\d+):\s*([^*]+)\*\*", re.MULTILINE)
    matches = list(row_pattern.finditer(summary))
    if not matches:
        return []

    entries: List[Dict[str, Any]] = []
    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(summary)
        block = summary[start:end].strip()
        block = re.split(r"\*\*Overall Summary:\*\*", block, maxsplit=1)[0].strip()

        parts = re.split(r"\*\*Summary:\*\*", block, maxsplit=1)
        bullets_text = parts[0].strip()
        row_summary = parts[1].strip() if len(parts) > 1 else ""

        bullets = []
        for line in bullets_text.splitlines():
            normalized = line.strip()
            if normalized.startswith("-") or normalized.startswith("*"):
                bullets.append(re.sub(r"^[-*]\s*", "", normalized))

        entries.append({
            "row_number": int(match.group(1)),
            "date": match.group(2).strip(),
            "bullets": bullets,
            "summary": row_summary,
        })

    return entries


def extract_meaningful_highlights(entries: List[Dict[str, Any]]) -> List[str]:
    """Extract meaningful highlights from all entries, not just duplicates."""
    if not entries:
        return []
    
    highlights = set()
    
    # Extract key patterns from all entries
    for entry in entries:
        for bullet in entry.get("bullets", []):
            # Extract high-level patterns
            if "z-score" in bullet.lower() or "σ" in bullet:
                highlights.add(bullet[:100] + "..." if len(bullet) > 100 else bullet)
            elif "volume" in bullet.lower() and ("spike" in bullet.lower() or "high" in bullet.lower() or "low" in bullet.lower()):
                highlights.add(bullet[:100] + "..." if len(bullet) > 100 else bullet)
            elif "detector" in bullet.lower() and ("all" in bullet.lower() or "flagged" in bullet.lower()):
                highlights.add(bullet[:100] + "..." if len(bullet) > 100 else bullet)
    
    # If no patterns found, take first bullet from first few entries
    if not highlights:
        for entry in entries[:3]:
            if entry.get("bullets"):
                highlights.add(entry["bullets"][0])
    
    return sorted(list(highlights))[:5]


def call_github_ai_explanation(token:str,payload: schemas.AnomalyExplanationRequest) -> Dict[str, Any]:
    """Call GitHub Models endpoint for AI explanation."""
    github_token = os.getenv("GITHUB_TOKEN", "").strip()
    endpoint = os.getenv("GITHUB_MODEL_ENDPOINT")
    model = os.getenv("GITHUB_MODEL_NAME", "openai/gpt-4.1")

    print(f"Using GitHub model endpoint {endpoint} with model {model} for anomaly explanation")

    prompt = build_ai_prompt(payload)

    try:
        client = ChatCompletionsClient(endpoint=endpoint, credential=AzureKeyCredential(github_token))
        response = client.complete(
            model=model,
            messages=[
                SystemMessage("You explain anomaly detection results in concise analyst-friendly language."),
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

    prompt = build_ai_prompt(payload)

    try:
        client = OpenAI(
            base_url=endpoint,
            api_key=token,
        )
        response = client.chat.completions.create(
            messages = [
                {
                    "role":"system",
                    "content":"You explain anomaly detection results in concise analyst-friendly language."
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

    # github_token = os.getenv("TOKEN", "").strip()
    
    # if github_token:
    #     return call_github_ai_explanation(github_token)
    
    # openai_key = os.getenv("TOKEN", "").strip()
    # if openai_key:
    #     return call_openai_ai_explanation(openai_key,payload)
    
    # Fallback to heuristic
    return heuristic_anomaly_explanation(payload)
