import { useState } from "react";
import { saveCache } from "../api";

export default function SaveCacheButton({ token, config, results, onSaved }) {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  const handleSave = async () => {
    setMessage("");
    setBusy(true);
    try {
      const resp = await saveCache(token, config, results);
      setMessage("Saved to cache");
      if (onSaved) onSaved(resp);
    } catch (err) {
      setMessage(err.message || "Save failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={{ marginTop: 12 }}>
      <button className="primary-button" onClick={handleSave} disabled={busy}>
        {busy ? "Saving…" : "Save results to cache"}
      </button>
      {message ? <div className="form-error" style={{ marginTop: 12 }}>{message}</div> : null}
    </div>
  );
}
