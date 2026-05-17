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

export async function fetchProfile(token) {
  const response = await fetch(`${BASE_URL}/me`, {
    headers: buildHeaders(token),
  });
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

export async function saveCache(token, config, results) {
  const body = {
    config,
    best_params: results.best_params || {},
    metrics: results.metrics || {},
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
