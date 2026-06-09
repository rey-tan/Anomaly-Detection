import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
from sqlalchemy.orm import Session
from tavily import TavilyClient

from src.api import crud, models, schemas
from src.utils.io import write_explanation_artifact


class ExplanationEngine:
    def __init__(self, request: schemas.AnomalyExplanationRequest):
        self.request = request

    def explain(self) -> Dict[str, Any]:
        
        github_token = os.getenv("TOKEN", "").strip()
        # if github_token:
          
        #     return self._call_github_ai_explanation(github_token, self.request)
        return self._heuristic_anomaly_explanation(self.request)

    def _call_github_ai_explanation(
        self,
        token: str,
        payload: schemas.AnomalyExplanationRequest,
    ) -> Dict[str, Any]:
        endpoint = os.getenv("MODEL_ENDPOINT")
        model = os.getenv("MODEL_NAME", "openai/gpt-4.1")

        anomaly_rows = self._extract_anomaly_rows(payload.data or [])
        search_context = self._build_search_context(payload.stock, anomaly_rows)
        prompt = self._build_ai_prompt(payload, search_context=search_context)

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
                temperature=0.2,
            )
            summary = str(response.choices[0].message.content).strip()
        except Exception as e:
            print("Error calling AI model endpoint, falling back to heuristic explanation", e)
            return self._heuristic_anomaly_explanation(payload)

        if not summary:
            return self._heuristic_anomaly_explanation(payload)

        entries = self._parse_ai_explanation_entries(summary)
        overall = self._extract_overall_summary(summary)

        return {
            "raw_summary": summary,
            "summary": overall,
            "entries": entries,
            "anomaly_count": len(self._extract_anomaly_rows(payload.data)),
            "source": model,
        }

    def _heuristic_anomaly_explanation(self, payload: schemas.AnomalyExplanationRequest) -> Dict[str, Any]:
        anomaly_rows = self._extract_anomaly_rows(payload.data)
        if not anomaly_rows:
            return {
                "raw_summary": "No rows in the result set were marked as anomalies, so there is nothing to explain.",
                "summary": "No rows in the result set were marked as anomalies, so there is nothing to explain.",
                "entries": [],
                "anomaly_count": 0,
                "source": "heuristic",
            }

        entries: List[Dict[str, Any]] = []
        for row in anomaly_rows:
            z_score = row.get("z_score")
            z_score_val = (
                float(z_score)
                if z_score is not None
                and str(z_score).replace(".", "", 1).replace("-", "", 1).isdigit()
                else None
            )

            close = row.get("close")
            bb_width = row.get("bb_width")
            rsi = row.get("RSI")
            volume = row.get("volume")
            average_volume = row.get("average_volume")

            detectors = []
            if row.get("dbscan") == -1:
                detectors.append("DBSCAN")
            if row.get("isolation_forest") == -1:
                detectors.append("Isolation Forest")

            bullets: List[str] = []
            if close is not None:
                bullets.append(f"Close: {close}")
            if volume is not None:
                bullets.append(f"Volume: {volume:,}")
            if z_score_val is not None:
                direction = "above" if z_score_val > 0 else "below"
                bullets.append(f"Price is {abs(z_score_val):.2f}σ {direction} mean")

            if bb_width is not None and isinstance(bb_width, (int, float)):
                if bb_width > 0.15:
                    bullets.append(f"BB width {bb_width:.3f} indicates elevated volatility spike")
                elif bb_width < 0.02:
                    bullets.append(f"BB width {bb_width:.3f} shows extremely compressed bands")
                else:
                    bullets.append(f"BB width {bb_width:.3f} indicates notable volatility change")

            if average_volume is not None and volume is not None and isinstance(volume, (int, float)) and isinstance(average_volume, (int, float)) and average_volume > 0:
                volume_ratio = volume / average_volume
                if volume_ratio > 2.5:
                    bullets.append(f"Volume {volume_ratio:.1f}× average signals strong trading activity")
                elif volume_ratio < 0.3:
                    bullets.append(f"Volume {volume_ratio:.1f}× average signals weak trading")

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

        summary = (
            f"Detected {len(anomaly_rows)} anomalous rows. Price anomalies shown via z-score deviation. "
            f"Volatility changes via Bollinger Band width. RSI indicates momentum extremes. "
            f"Volume spikes show trading strength."
        )

        return {
            "raw_summary": summary,
            "summary": summary,
            "entries": entries,
            "anomaly_count": len(anomaly_rows),
            "source": "heuristic",
        }

    def _extract_anomaly_rows(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for index, row in enumerate(data or [], start=1):
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

    def _tavily_search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        api_key = os.getenv("TAVILY_API_KEY", "").strip()
        if not api_key:
            print("Warning: Tavily API key not configured. Skipping search.")
            return []

        try:
            tavily_client = TavilyClient(api_key=api_key)
            response = tavily_client.search(query=query, max_results=min(num_results, 10), include_answer=False)
            results = []
            for item in response.get("results", [])[:num_results]:
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("url", ""),
                    "snippet": item.get("content", ""),
                })
            return results
        except Exception as e:
            print(f"Error fetching Tavily Search results: {e}")
            return []

    def _build_search_context(self, stock: str, anomaly_rows: List[Dict[str, Any]]) -> str:
        search_context_parts = ["## Search Context\n"]
        for row in anomaly_rows[:5]:
            date_str = row.get("date", "")
            if not date_str:
                continue
            try:
                anomaly_date = datetime.strptime(str(date_str), "%Y-%m-%d")
                queries = [
                    f"{stock} Nepal {date_str}",
                    f"Nepal protest {anomaly_date.strftime('%B %Y')}",
                ]
                section_found = False
                for query in queries:
                    results = self._tavily_search(query, num_results=1)
                    if results:
                        if not section_found:
                            search_context_parts.append(f"\n### {date_str} ({stock})")
                            section_found = True
                        for result in results:
                            search_context_parts.append(f"- {result['title']}: {result['snippet'][:100]}... ([link]({result['link']}))")
                if not section_found:
                    search_context_parts.append(f"\n### {date_str} ({stock})")
                    search_context_parts.append("No news found.")
            except Exception as e:
                print(f"Error processing anomaly date {date_str}: {e}")
                continue
        return "\n".join(search_context_parts) if len(search_context_parts) > 1 else ""

    def _build_ai_prompt(self, payload: schemas.AnomalyExplanationRequest, search_context: str = "") -> str:
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
                    adjacent.append(
                        f"[{adj.get('date')}: close={adj.get('close')}, volume={adj.get('volume')}, change={adj.get('change')}]"
                    )
                detail_parts.append(f"adjacent_rows={'; '.join(adjacent)}")

            if row.get("detector_flags"):
                detail_parts.append(f"detector_flags={', '.join(row.get('detector_flags'))}")
            elif flags:
                detail_parts.append(f"flagged_by={', '.join(flags)}")

            row_summaries.append(f"  Row {index}: " + ", ".join(detail_parts))

        params_lines: List[str] = []
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

        summary_data = {
            "stock": payload.stock,
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
            f"Analysis context:\n{json.dumps(summary_data, ensure_ascii=False, indent=2, default=str)}\n\n"
            "Detection parameters:\n"
            f"{chr(10).join(params_lines)}\n\n"
            "Flagged anomaly rows with context:\n"
            f"{chr(10).join(row_summaries)}"
        )

    def _extract_overall_summary(self, summary: str) -> str:
        overall_match = re.search(r"\*\*(?:Overall\s+)?Summary:\*\*\s*(.*)", summary, re.S)
        if overall_match:
            overall_text = overall_match.group(1).strip()
            overall_text = re.split(r"^-{3,}$", overall_text, maxsplit=1, flags=re.MULTILINE)[0].strip()
            return overall_text
        return re.split(r"^-{3,}$", summary, maxsplit=1, flags=re.MULTILINE)[0].strip()

    def _parse_ai_explanation_entries(self, summary: str) -> List[Dict[str, Any]]:
        if not summary:
            return []

        row_pattern = re.compile(r"^\*\*Row\s+(\d+)(?:\s*\([^)]+\))?:\s*\*\*", re.MULTILINE)
        matches = list(row_pattern.finditer(summary))
        if not matches:
            return []

        entries: List[Dict[str, Any]] = []
        for idx, match in enumerate(matches):
            start = match.end()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(summary)
            block = summary[start:end].strip()
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
                    row_summary = normalized

            entries.append({
                "row_number": int(match.group(1)),
                "date": None,
                "bullets": bullets,
                "summary": row_summary,
            })

        return entries

   
