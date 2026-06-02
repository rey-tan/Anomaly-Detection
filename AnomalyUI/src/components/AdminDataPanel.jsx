import { useEffect, useState } from "react";
import { downloadAdminFile, fetchAdminPreview, fetchAdminSymbols, runAdminScrape } from "../api";


export default function AdminDataPanel({ token }) {
    const [adminSymbols, setAdminSymbols] = useState([]);
    const [adminState, setAdminState] = useState({
        loadingList: false,
        loadingPreview: false,
        openPreview: null,
        previewData: null,
    });
    const [scrapeState, setScrapeState] = useState({
        loading: false,
        error: "",
        successMessage: "",
        result: null,
    });
    const [symbolQuery, setSymbolQuery] = useState("");
    const [scrapePayload, setScrapePayload] = useState({ source: "sharesansar", start_date: "", end_date: "", output_format: "csv" });

    const fmtDate = (raw) => {
        if (!raw) return "";
        const d = new Date(raw);
        if (Number.isNaN(d.getTime())) return "";
        const yyyy = d.getFullYear();
        const mm = String(d.getMonth() + 1).padStart(2, "0");
        const dd = String(d.getDate()).padStart(2, "0");
        return `${yyyy}-${mm}-${dd}`;
    };
    const addDays = (date, days) => {
        const d = new Date(date);
        d.setDate(d.getDate() + days);
        return d;
    };

    const todayDate = fmtDate(new Date());
    const minDate = adminSymbols ? fmtDate(addDays(adminSymbols[0]?.last_date, 1)) : "";
    const maxDate = todayDate;

    const loadAdminSymbols = async () => {
        if (!token) return;
        setAdminState((prev) => ({ ...prev, loadingList: true }));
        setScrapeState((prev) => ({ ...prev, error: "" }));
        try {
            const payload = await fetchAdminSymbols(token);
            setAdminSymbols(Array.isArray(payload) ? payload : []);
        } catch (err) {
            setScrapeState((prev) => ({ ...prev, error: err.message || "Failed to load admin data" }));
        } finally {
            setAdminState((prev) => ({ ...prev, loadingList: false }));
        }
    };

    const loadPreview = async (symbol) => {
        if (!token || !symbol) return;
        setAdminState((prev) => ({ ...prev, loadingPreview: true }));
        setScrapeState((prev) => ({ ...prev, error: "" }));
        try {
            const payload = await fetchAdminPreview(token, symbol, 10);
            setAdminState((prev) => ({ ...prev, previewData: payload, openPreview: symbol }));
        } catch (err) {
            setScrapeState((prev) => ({ ...prev, error: err.message || "Failed to load preview data" }));
        } finally {
            setAdminState((prev) => ({ ...prev, loadingPreview: false }));
        }
    };

    useEffect(() => {
        if (!token) return;
        loadAdminSymbols();
    }, [token]);

    useEffect(() => {
        if (adminState.previewData) {
            const s = fmtDate(addDays(adminState.previewData.last_date, 1)) || "";
            const e = todayDate;
            setScrapePayload((p) => ({
                ...p,
                start_date: p.start_date || s,
                end_date: p.end_date || e,
            }));
        }
    }, [adminState.previewData, todayDate]);

    const handleRunScrape = async (event) => {
        event.preventDefault();
        setScrapeState((prev) => ({ ...prev, error: "", successMessage: "", result: null }));
        if (!scrapePayload.source) {
            setScrapeState((prev) => ({ ...prev, error: "Select a scrape source before running." }));
            return;
        }
        setScrapeState((prev) => ({ ...prev, loading: true }));
        try {
            const payload = { ...scrapePayload };
            const resp = await runAdminScrape(token, payload);
            setScrapeState({ loading: false, error: "", successMessage: "Scrape completed successfully.", result: resp });
            await loadAdminSymbols();
        } catch (err) {
            setScrapeState((prev) => ({ ...prev, loading: false, error: err.message || "Scrape failed" }));
        } finally {
            setAdminState((prev) => ({ ...prev, loadingPreview: false }));
        }
    };

    return (
    <>
        <div className="page-panel">
            <div className="page-intro">
                <p className="eyebrow">Data Management</p>
                <h2>Dataset inventory and scraping</h2>
                <p>Browse available market files, preview a selected symbol, and trigger admin scrapes from a dedicated page.</p>
            </div>
            <div className="admin-panel">
                <div className="admin-panel-head">
                    <h3>Dataset inventory</h3>
                    <div className="admin-count">{adminState.loadingList ? "…" : `${adminSymbols.length} symbols`}</div>
                </div>
                <div style={{ display: "grid", gap: 12 }}>
                    <div style={{ display: "flex", gap: 8 }}>
                        <input
                            placeholder="Symbol"
                            id="admin-symbol-input"
                            value={symbolQuery}
                            onChange={(e) => setSymbolQuery(e.target.value)}
                            className="admin-input"
                        />
                        <button className="primary-button" onClick={() => loadAdminSymbols()} type="button" style={{ width: "190px", flexShrink: 0 }}>
                            Refresh inventory
                        </button>
                    </div>

                    <div className="admin-list">
                        {adminState.loadingList ? <div>Loading data…</div> : null}
                        {adminSymbols.length ? (
                            (() => {
                                const query = (symbolQuery || "").toLowerCase().trim();
                                const filtered = query
                                    ? adminSymbols.filter((name) => name.toLowerCase().includes(query))
                                    : adminSymbols;

                                if (!filtered.length) {
                                    return <div className="admin-user-card">No datasets match "{symbolQuery}"</div>;
                                }
                                
                                return filtered.map((item,index) => (
                                    <div key={index} className="admin-user-card">
                                        <div className="data-content">
                                            <div style={{ display: "flex", flexDirection: "column" }}>
                                                <div style={{ fontWeight: 700 }}>{item.name}</div>
                                                <div style={{ color: "rgb(148, 163, 184)", fontSize: "12px", marginTop: "6px" }}>
                                                    {item.first_date} → {item.last_date}
                                                </div>
                                            </div>
                                            <div style={{ display: "flex", gap: 8 }}>
                                                <button
                                                    className="text-button"
                                                    onClick={async () => {
                                                        await loadPreview(item.name);
                                                    }}
                                                    type="button"
                                                    disabled={adminState.loadingPreview}
                                                >
                                                    Preview
                                                </button>
                                                <button
                                                    className="text-button"
                                                    onClick={async () => {
                                                        try {
                                                            await downloadAdminFile(token, `${item.name}.csv`);
                                                        } catch (err) {
                                                            setScrapeState((prev) => ({ ...prev, error: err.message || "Download failed" }));
                                                        }
                                                    }}
                                                    type="button"
                                                >
                                                    Download
                                                </button>
                                            </div>
                                        </div>
                                        {adminState.openPreview === name && adminState.previewData ? (
                                            <div style={{ marginTop: 10, width: "100%" }}>
                                                <div className="dashboard-card">
                                                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                                                        <strong>Preview: {adminState.previewData.name}</strong>
                                                        <div style={{ color: "#94a3b8" }}>
                                                            {adminState.previewData.rows} rows · last updated {adminState.previewData.last_date || adminState.previewData.modified_at}
                                                        </div>
                                                    </div>
                                                    <div style={{ maxHeight: 260, overflow: "auto", marginTop: 8 }}>
                                                        <pre style={{ whiteSpace: "pre-wrap" }}>{JSON.stringify(adminState.previewData.preview, null, 2)}</pre>
                                                    </div>
                                                </div>
                                            </div>
                                        ) : null}
                                    </div>
                                ));
                            })()
                        ) : (
                            <div className="admin-user-card">No datasets found</div>
                        )}
                    </div>
                    {adminState.loadingPreview ? <div style={{ color: "#94a3b8" }}>Loading preview…</div> : null}
                </div>
            </div>
        </div>
        <div className="page-panel" style={{ height: "max-content" }}>
            <div className="admin-panel">
                <div className="admin-panel-head">
                    <div>
                        <h3>Dataset scraping</h3>
                    </div>
                    <div className="admin-count">{adminState.loadingList ? "…" : `${adminSymbols.length} symbols`}</div>
                </div>
                <form className="admin-form" onSubmit={handleRunScrape}>
                    <div className="admin-form-grid">
                        <select className="admin-select" value={scrapePayload.source} onChange={(e) => setScrapePayload((p) => ({ ...p, source: e.target.value }))} disabled={scrapeState.loading}>
                            <option value="sharesansar">sharesansar</option>
                        </select>
                        <input type="date" className="admin-input" value={scrapePayload.start_date} min={minDate} max={maxDate} onChange={(e) => setScrapePayload((p) => ({ ...p, start_date: e.target.value }))} disabled={scrapeState.loading} />
                        <input type="date" className="admin-input" value={scrapePayload.end_date} min={minDate} max={maxDate} onChange={(e) => setScrapePayload((p) => ({ ...p, end_date: e.target.value }))} disabled={scrapeState.loading} />
                        <select className="admin-select" value={scrapePayload.output_format} onChange={(e) => setScrapePayload((p) => ({ ...p, output_format: e.target.value }))} disabled={scrapeState.loading}>
                            <option value="csv">csv</option>
                            <option value="json">json</option>
                            <option value="excel">excel</option>
                            <option value="both">both</option>
                        </select>
                    </div>
                    {(minDate || maxDate) ? <div style={{ color: "#94a3b8", fontSize: 12, marginTop: 6 }}>{`Available range: ${minDate || "—"} → ${maxDate || "—"}`}</div> : null}
                    <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                        <button className="primary-button admin-submit" type="submit" disabled={scrapeState.loading}>
                            {scrapeState.loading ? "Scraping..." : "Run scrape"}
                        </button>
                    </div>
                    {scrapeState.error ? <div className="form-error admin-error">{scrapeState.error}</div> : null}
                    {scrapeState.successMessage ? <div className="success-message">{scrapeState.successMessage}</div> : null}

                </form>
            </div>
        </div>
    </>
    );
}