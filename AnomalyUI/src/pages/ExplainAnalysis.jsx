import { explainAnalysis } from "../api";
import { useMemo, useState } from "react";
import React from 'react'
import ReactMarkdown from 'react-markdown'
import {  extractMetricsAndParams } from '../utils/analysisHelpers';



export default function ExplainAnalysis({token,results,selectedAnalysis,flaggedCount}) {
    const [aiExplanation, setAiExplanation] = useState(null);
    const [aiLoading, setAiLoading] = useState(false);
    const [aiError, setAiError] = useState("");

    const aiExplanationMarkdown = useMemo(() => {
        if (!aiExplanation) return "";

        const entries = Array.isArray(aiExplanation.entries) ? aiExplanation.entries : [];
        const isHeuristicFallback =
            entries.length > 0 &&
            typeof aiExplanation.raw_summary === "string" &&
            aiExplanation.raw_summary.trim() === (aiExplanation.summary || "").trim();

        if (isHeuristicFallback) {
            const rowsMarkdown = entries
                .map((entry) => {
                    const rowHeader = `**Row ${entry.row_number}${entry.date ? ` (${entry.date})` : ""}:**`;
                    const bullets = Array.isArray(entry.bullets)
                        ? entry.bullets.map((bullet) => `- ${bullet}`).join("\n")
                        : "";
                    const summaryLine = entry.summary ? `\n_${entry.summary}_` : "";
                    return [rowHeader, bullets, summaryLine].filter(Boolean).join("\n\n");
                })
                .join("\n\n");

            const overall = aiExplanation.summary ? `**Overall summary:**\n${aiExplanation.summary}` : "";
            return [overall, rowsMarkdown].filter(Boolean).join("\n\n");
        }

        return aiExplanation.raw_summary || aiExplanation.summary || "";
    }, [aiExplanation]);
    const anomalyRows = useMemo(
        () =>
            (results?.data || []).filter(
                (item) =>
                    item.dbscan_label === -1 ||
                    item.isolation_forest_label === -1
            ),
        [results]
    );


    const handleExplainWithAI = async () => {
        if (!results?.data?.length) return;
        setAiLoading(true);
        setAiError("");
        try {
            const contextualRows = anomalyRows.map((row) => {
                const index = results.data.findIndex((item) => item.date === row.date);
                const previousRows = index > 0 ? results.data.slice(Math.max(0, index - 3), index) : [];
                const nextRows = index < results.data.length - 1 ? results.data.slice(index + 1, index + 4) : [];
                const windowStart = Math.max(0, index - 20);
                const window = results.data.slice(windowStart, index);
                const averageVolume = window.length
                    ? window.reduce((sum, item) => sum + (item.volume || 0), 0) / window.length
                    : null;

                
                
                return {
                    ...row,
                    previous_close: previousRows.length ? previousRows[previousRows.length - 1].close : null,
                    adjacent_rows: [...previousRows, ...nextRows].map((item) => ({
                        date: item.date,
                        close: item.close,
                        volume: item.volume,
                        change: item.change,
                    })),
                    rolling_mean: row.SMA_20 ?? row.SMA_10 ?? null,
                    rolling_std: row.volatility ?? null,
                    average_volume: averageVolume,
                    detector_flags: [
                        row.cluster === -1 ? "combined" : null,
                        row.dbscan_label === -1 ? "DBSCAN" : null,
                        row.isolation_forest_label === -1 ? "Isolation Forest" : null,
                    ].filter(Boolean),
                    z_score: row.z_score?? null,
                    bb_width: row.bb_width ?? null,
                    RSI: row.RSI ?? null,
                    Upper_BB: row.Upper_BB ?? null,
                    Lower_BB: row.Lower_BB ?? null,
                    isolation_forest_score: row.isolation_forest_score ?? null
                };
            });
            console.log("Contextual rows for AI explanation:", contextualRows);

            const { metrics, bestParams } = extractMetricsAndParams(results);
            const selectedAnalysisParams = extractMetricsAndParams(selectedAnalysis);
            const payload = {
                analysis_id: selectedAnalysis?.analysis_id || null,
                stock: selectedAnalysis?.stock || "",
                mode: selectedAnalysis?.mode || "",
                timeframe: selectedAnalysis?.timeframe || "",
                start_date: selectedAnalysis?.start_date || "",
                end_date: selectedAnalysis?.end_date || "",
                metrics: metrics,
                best_params: bestParams || selectedAnalysisParams.bestParams || {},
                data: contextualRows,
            };
            const explanation = await explainAnalysis(token, payload);
            setAiExplanation(explanation);
        } catch (err) {
            setAiError(err.message || "Failed to generate AI explanation");
        } finally {
            setAiLoading(false);
        }
    };

    return (
        <div className="ai-explanation-section">
            {results ? (
                <div className="results-ai-actions">
                    <button className="primary-button ai-button" type="button" onClick={handleExplainWithAI} disabled={aiLoading || !flaggedCount}>
                        {aiLoading ? 'Analyzing with AI…' : 'Analyze with AI'}
                    </button>
                    <span className="results-ai-note">{flaggedCount ? `${flaggedCount} flagged points available for explanation` : 'No flagged points to explain'}</span>
                </div>
            ) : null}
            {aiError ? <div className="alert-box">{aiError}</div> : null}
            {aiExplanation ? (
                <section className="dashboard-card results-ai-card">
                    <div className="section-heading compact">
                        <div>
                            <p className="eyebrow">AI explanation</p>
                        </div>
                        <div className="results-ai-source">Source: {aiExplanation?.source || 'AI'}</div>
                    </div>
                    <h3>Why these points were flagged</h3>
                    <p>Generated from the latest analyzed result set.</p>
                    <div className="results-ai-markdown">
                        <ReactMarkdown>{aiExplanationMarkdown}</ReactMarkdown>
                    </div>
                </section>
            ) : null}
        </div>
    )
}