const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function buildHeaders(token) {
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function unwrapResponse(response) {
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || payload.message || response.statusText || "An error occurred");
  }
  return payload;
}

export async function login(username, password) {
  const form = new URLSearchParams();
  form.append("username", username);
  form.append("password", password);

  const response = await fetch(`${BASE_URL}/login`, {
    method: "POST",
    body: form,
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });

  return unwrapResponse(response);
}

export async function register(username, email, password) {
  return registerRequest(username, email, password);
}

export async function registerRequest(username, email, password) {
  const response = await fetch(`${BASE_URL}/register/request`, {
    method: "POST",
    headers: buildHeaders(),
    body: JSON.stringify({ username, email, password, role: "analyst" }),
  });
  return unwrapResponse(response);
}

export async function verifyOTP(email, otp_code) {
  const response = await fetch(`${BASE_URL}/register/verify`, {
    method: "POST",
    headers: buildHeaders(),
    body: JSON.stringify({ email, otp_code }),
  });
  return unwrapResponse(response);
}

export async function fetchProfile(token) {
  const response = await fetch(`${BASE_URL}/me`, {
    headers: buildHeaders(token),
  });
  return unwrapResponse(response);
}

export async function fetchSymbols() {
  const response = await fetch(`${BASE_URL}/symbols`);
  return unwrapResponse(response);
}

export async function analyze(token, payload) {
  const response = await fetch(`${BASE_URL}/analyze`, {
    method: "POST",
    headers: buildHeaders(token),
    body: JSON.stringify(payload),
  });
  return unwrapResponse(response);
}

export async function explainAnalysis(token, payload) {
  const response = await fetch(`${BASE_URL}/analyze/explain`, {
    method: "POST",
    headers: buildHeaders(token),
    body: JSON.stringify(payload),
  });
  return unwrapResponse(response);
}

export async function saveCache(token, config, results) {
  // Convert new response format (with models) to old format for cache storage
  let best_params = {};
  let metrics = {};
  
  if (results.models) {
    // New format: extract metrics and params from models
    Object.entries(results.models).forEach(([modelName, modelResult]) => {
      if (modelResult.metrics) metrics[modelName] = modelResult.metrics;
      if (modelResult.params) {
        // Map zscore back to z_score for consistency
        const paramKey = modelName === 'zscore' ? 'z_score' : modelName;
        best_params[paramKey] = modelResult.params;
      }
    });
  } else {
    // Old format: use directly
    best_params = results.best_params || {};
    metrics = results.metrics || {};
  }
  
  const body = {
    config,
    best_params,
    metrics,
    data: results.data || [],
  };
  const response = await fetch(`${BASE_URL}/cache`, {
    method: "POST",
    headers: buildHeaders(token),
    body: JSON.stringify(body),
  });
  return unwrapResponse(response);
}

export async function getUsers(token) {
  const response = await fetch(`${BASE_URL}/users`, {
    headers: buildHeaders(token),
  });
  return unwrapResponse(response);
}

export async function createUser(token, username, password, role = "analyst") {
  const response = await fetch(`${BASE_URL}/users`, {
    method: "POST",
    headers: buildHeaders(token),
    body: JSON.stringify({ username, password, role }),
  });
  return unwrapResponse(response);
}

export async function updateUserRole(token, userId, role) {
  const response = await fetch(`${BASE_URL}/users/${userId}/role`, {
    method: "PATCH",
    headers: buildHeaders(token),
    body: JSON.stringify({ role }),
  });
  return unwrapResponse(response);
}

export async function deleteUser(token, userId) {
  const response = await fetch(`${BASE_URL}/users/${userId}`, {
    method: "DELETE",
    headers: buildHeaders(token),
  });
  return unwrapResponse(response);
}

export async function fetchAnalyses(token) {
  const response = await fetch(`${BASE_URL}/me/analyses`, {
    headers: buildHeaders(token),
  });
  return unwrapResponse(response);
}

export async function fetchAdminSymbols(token) {
  const response = await fetch(`${BASE_URL}/admin/data/symbols`, {
    headers: buildHeaders(token),
  });
  return unwrapResponse(response);
}

export async function fetchAdminPreview(token, symbol, preview_limit = 10) {
  const response = await fetch(`${BASE_URL}/admin/data/preview/${encodeURIComponent(symbol)}?preview_limit=${encodeURIComponent(preview_limit)}`, {
    headers: buildHeaders(token),
  });
  return unwrapResponse(response);
}

export async function runAdminScrape(token, payload) {
  const response = await fetch(`${BASE_URL}/admin/scrape`, {
    method: "POST",
    headers: buildHeaders(token),
    body: JSON.stringify(payload),
  });
  return unwrapResponse(response);
}

export async function downloadAdminFile(token, filename) {
  const response = await fetch(`${BASE_URL}/admin/data/file/${encodeURIComponent(filename)}`, {
    headers: buildHeaders(token),
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || response.statusText || "Failed to download file");
  }
  const blob = await response.blob();
  // trigger download
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
  return { success: true };
}

export async function fetchAnalysisData(token, analysisId) {
  const response = await fetch(`${BASE_URL}/me/analyses/${analysisId}/data`, {
    headers: buildHeaders(token),
  });
  if (!response.ok) {
    throw new Error(response.statusText || "Failed to fetch analysis data");
  }
  return response.json();
}

export async function toggleFavorite(token, analysisId, favorite) {
  const response = await fetch(`${BASE_URL}/me/analyses/${analysisId}/favorite`, {
    method: "POST",
    headers: buildHeaders(token),
    body: JSON.stringify({ favorite }),
  });
  return unwrapResponse(response);
}

export async function fetchNotifications(token, unreadOnly = false) {
  const url = new URL(`${BASE_URL}/me/notifications`);
  if (unreadOnly) url.searchParams.append("unread_only", "1");
  const response = await fetch(url.toString(), { headers: buildHeaders(token) });
  return unwrapResponse(response);
}

export async function markNotificationRead(token, notificationId) {
  const response = await fetch(`${BASE_URL}/me/notifications/${notificationId}/read`, {
    method: "POST",
    headers: buildHeaders(token),
  });
  return unwrapResponse(response);
}

export async function fetchUserActivity(token, userId, opts = {}) {
  const url = new URL(`${BASE_URL}/users/${userId}/activity`);
  if (opts.q) url.searchParams.append("q", opts.q);
  if (opts.start) url.searchParams.append("start", opts.start);
  if (opts.end) url.searchParams.append("end", opts.end);
  if (opts.page) url.searchParams.append("page", String(opts.page));
  if (opts.page_size) url.searchParams.append("page_size", String(opts.page_size));

  const response = await fetch(url.toString(), {
    headers: buildHeaders(token),
  });
  return unwrapResponse(response);
}

export async function fetchActivity(token, opts = {}) {
  const url = new URL(`${BASE_URL}/activity`);
  if (opts.q) url.searchParams.append("q", opts.q);
  if (opts.start) url.searchParams.append("start", opts.start);
  if (opts.end) url.searchParams.append("end", opts.end);
  if (opts.page) url.searchParams.append("page", String(opts.page));
  if (opts.page_size) url.searchParams.append("page_size", String(opts.page_size));

  const response = await fetch(url.toString(), { headers: buildHeaders(token) });
  return unwrapResponse(response);
}
