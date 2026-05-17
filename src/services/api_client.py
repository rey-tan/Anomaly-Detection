import requests

API_URL = "http://localhost:8000"


class ApiError(Exception):
    pass


def _get_headers(token: str):
    return {"Authorization": f"Bearer {token}"}


def login(username: str, password: str):
    response = requests.post(
        f"{API_URL}/login",
        data={"username": username, "password": password},
        timeout=10,
    )
    if response.status_code != 200:
        raise ApiError(response.json().get("detail", response.text))
    return response.json()


def get_user_profile(token: str):
    response = requests.get(f"{API_URL}/me", headers=_get_headers(token), timeout=10)
    if response.status_code != 200:
        raise ApiError(response.json().get("detail", response.text))
    return response.json()


def get_notifications(token: str):
    response = requests.get(f"{API_URL}/me/notifications", headers=_get_headers(token), timeout=10)
    if response.status_code != 200:
        raise ApiError(response.json().get("detail", response.text))
    return response.json()


def get_all_users(token: str):
    response = requests.get(f"{API_URL}/users", headers=_get_headers(token), timeout=10)
    if response.status_code != 200:
        raise ApiError(response.json().get("detail", response.text))
    return response.json()


def create_user(token: str, username: str, password: str, role: str = "user"):
    body = {"username": username, "password": password, "role": role}
    response = requests.post(f"{API_URL}/users", json=body, headers=_get_headers(token), timeout=10)
    if response.status_code != 200:
        raise ApiError(response.json().get("detail", response.text))
    return response.json()


def update_user_role(token: str, user_id: int, role: str):
    response = requests.patch(
        f"{API_URL}/users/{user_id}/role",
        json={"role": role},
        headers=_get_headers(token),
        timeout=10,
    )
    if response.status_code != 200:
        raise ApiError(response.json().get("detail", response.text))
    return response.json()


def delete_user(token: str, user_id: int):
    response = requests.delete(f"{API_URL}/users/{user_id}", headers=_get_headers(token), timeout=10)
    if response.status_code != 200:
        raise ApiError(response.json().get("detail", response.text))
    return response.json()


def analyze(token: str, payload: dict):
    response = requests.post(
        f"{API_URL}/analyze",
        json=payload,
        headers=_get_headers(token),
        timeout=300,
    )
    if response.status_code != 200:
        raise ApiError(response.json().get("detail", response.text))
    return response.json()


def save_cache(token: str, payload: dict, results: dict):
    body = {
        "config": payload,
        "best_params": results.get("best_params", {}),
        "metrics": results.get("metrics", {}),
        "data": results.get("data", []),
    }
    response = requests.post(f"{API_URL}/cache", json=body, headers=_get_headers(token), timeout=300)
    if response.status_code != 200:
        raise ApiError(response.json().get("detail", response.text))
    return response.json()
