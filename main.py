import warnings
from datetime import date

import pandas as pd
import requests
import streamlit as st

from src.components.visualization import plot_scatter, plot_timeseries, plot_analysis
from src.utils.load import load_config, load_json
from src.utils.paths import CONFIG, ARTIFACTS
from src.utils.timeframes import VALID_TIMEFRAMES

warnings.filterwarnings("ignore")

API_URL = "http://localhost:8000"

app_config = load_config(CONFIG / "config.yaml")

st.set_page_config(layout="wide")

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if "auth_token" not in st.session_state:
    st.session_state["auth_token"] = ""

if "username" not in st.session_state:
    st.session_state["username"] = ""

if "role" not in st.session_state:
    st.session_state["role"] = "user"

if "results" not in st.session_state:
    st.session_state["results"] = None


def login(username: str, password: str):
    try:
        response = requests.post(
            f"{API_URL}/login",
            data={"username": username, "password": password},
            timeout=10,
        )
    except requests.exceptions.RequestException as exc:
        return False, str(exc)

    if response.status_code != 200:
        detail = response.json().get("detail", "Login failed")
        return False, detail

    token = response.json().get("access_token")
    st.session_state["authenticated"] = True
    st.session_state["auth_token"] = token
    st.session_state["username"] = username
    try:
        profile = get_user_profile()
        st.session_state["role"] = profile.get("role", "user")
    except Exception:
        st.session_state["role"] = "user"
    return True, None


def logout():
    st.session_state["authenticated"] = False
    st.session_state["auth_token"] = ""
    st.session_state["username"] = ""
    st.session_state["role"] = "user"
    st.session_state["results"] = None


def get_user_profile():
    headers = {"Authorization": f"Bearer {st.session_state['auth_token']}"}
    response = requests.get(f"{API_URL}/me", headers=headers, timeout=10)
    if response.status_code != 200:
        raise ValueError(response.json().get("detail", response.text))
    return response.json()


def get_notifications():
    headers = {"Authorization": f"Bearer {st.session_state['auth_token']}"}
    response = requests.get(f"{API_URL}/me/notifications", headers=headers, timeout=10)
    if response.status_code != 200:
        raise ValueError(response.json().get("detail", response.text))
    return response.json()


def get_all_users():
    headers = {"Authorization": f"Bearer {st.session_state['auth_token']}"}
    response = requests.get(f"{API_URL}/users", headers=headers, timeout=10)
    if response.status_code != 200:
        raise ValueError(response.json().get("detail", response.text))
    return response.json()


def create_user_via_api(username: str, password: str, role: str = "user"):
    headers = {"Authorization": f"Bearer {st.session_state['auth_token']}"}
    body = {
        "username": username,
        "password": password,
        "role": role,
    }
    response = requests.post(f"{API_URL}/users", json=body, headers=headers, timeout=10)
    if response.status_code != 200:
        raise ValueError(response.json().get("detail", response.text))
    return response.json()


def update_user_role_via_api(user_id: int, new_role: str):
    headers = {"Authorization": f"Bearer {st.session_state['auth_token']}"}
    body = {"role": new_role}
    response = requests.patch(f"{API_URL}/users/{user_id}/role", json=body, headers=headers, timeout=10)
    if response.status_code != 200:
        raise ValueError(response.json().get("detail", response.text))
    return response.json()


def delete_user_via_api(user_id: int):
    headers = {"Authorization": f"Bearer {st.session_state['auth_token']}"}
    response = requests.delete(f"{API_URL}/users/{user_id}", headers=headers, timeout=10)
    if response.status_code != 200:
        raise ValueError(response.json().get("detail", response.text))
    return response.json()


def analyze_via_api(payload: dict):
    headers = {"Authorization": f"Bearer {st.session_state['auth_token']}"}
    response = requests.post(
        f"{API_URL}/analyze",
        json=payload,
        headers=headers,
        timeout=300,
    )
    if response.status_code != 200:
        raise ValueError(response.json().get("detail", response.text))
    return response.json()


def save_cache_via_api(payload: dict, results: dict):
    headers = {"Authorization": f"Bearer {st.session_state['auth_token']}"}
    cache_body = {
        "config": payload,
        "best_params": results.get("best_params", {}),
        "metrics": results.get("metrics", {}),
        "data": results.get("data", []),
    }
    response = requests.post(
        f"{API_URL}/cache",
        json=cache_body,
        headers=headers,
        timeout=300,
    )
    if response.status_code != 200:
        raise ValueError(response.json().get("detail", response.text))
    return response.json()


if not st.session_state["authenticated"]:
    st.title("🔐 Anomaly Engine Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

        if submit:
            success, error = login(username, password)
            if success:
                st.success("Login successful")
                st.rerun()
            else:
                st.error(error)

    st.stop()

st.sidebar.title("⚙️ Controls")
st.sidebar.markdown(f"**Logged in as:** {st.session_state['username']}")
st.sidebar.markdown(f"**Role:** {st.session_state['role']}")
if st.sidebar.button("Logout"):
    logout()
    st.rerun()

stock_options = sorted(load_json(ARTIFACTS / "allowed_symbols.json"))
stock = st.sidebar.selectbox("Symbol", stock_options, index=0)

st.title(f"📊 Anomaly Detection Dashboard - {stock}")

start_date = st.sidebar.date_input(
    "Start Date",
    value=date(2026, 1, 1),
    min_value=date(2023, 1, 1),
    max_value=date.today(),
)

end_date = st.sidebar.date_input(
    "End Date",
    value=date(2026, 1, 30),
    min_value=date(2023, 1, 1),
    max_value=date.today(),
)

timeframe = st.sidebar.selectbox("Timeframe", VALID_TIMEFRAMES, index=1)

mode = st.sidebar.selectbox("Mode", ["Static", "Realtime Simulation"])


if st.sidebar.button("Run Analysis"):
    with st.spinner("Running analysis..."):
        payload = {
            "stock": stock,
            "start_date": str(start_date),
            "end_date": str(end_date),
            "timeframe": timeframe,
            "features": app_config["features"],
            "mode": mode,
        }
        try:
            results = analyze_via_api(payload)
            st.session_state["results"] = results
            try:
                save_cache_via_api(payload, results)
            except Exception as exc:
                st.warning(f"Result stored, but cache save failed: {exc}")
            st.success("Analysis complete! Scroll down to see results.")
        except Exception as exc:
            st.error(f"Analysis failed: {exc}")

try:
    notifications = get_notifications()
except Exception:
    notifications = []

if notifications:
    st.sidebar.markdown("### 🔔 Notifications")
    for note in notifications[:5]:
        status = "✅" if note["is_read"] else "🔔"
        st.sidebar.write(f"{status} **{note['title']}**: {note['message']}")

if st.session_state["role"] == "admin":
    with st.sidebar.expander("Admin Panel", expanded=True):
        st.markdown("#### Manage Users")
        try:
            users = get_all_users()
            for user in users:
                st.write(f"**{user['username']}** ({user['role']})")
                new_role = st.selectbox("New role", ["user", "analyst", "admin"], index=["user", "analyst", "admin"].index(user['role']), key=f"role_{user['id']}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Update Role", key=f"update_{user['id']}"):
                        if new_role != user['role']:
                            try:
                                update_user_role_via_api(user['id'], new_role)
                                st.success(f"Updated {user['username']} to {new_role}")
                                st.rerun()
                            except Exception as exc:
                                st.error(f"Could not update: {exc}")
                with col2:
                    if st.button("Delete", key=f"delete_{user['id']}"):
                        try:
                            delete_user_via_api(user['id'])
                            st.success(f"Deleted {user['username']}")
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Could not delete: {exc}")
        except Exception as exc:
            st.error(f"Could not load users: {exc}")

        st.markdown("---")
        st.markdown("#### Create new user")
        new_username = st.text_input("New username", key="admin_new_username")
        new_password = st.text_input("New password", type="password", key="admin_new_password")
        new_role = st.selectbox("Role", ["user", "analyst", "admin"], key="admin_new_role")
        if st.button("Create user", key="admin_create_user"):
            if not new_username or not new_password:
                st.error("Username and password are required")
            else:
                try:
                    created = create_user_via_api(new_username, new_password, new_role)
                    st.success(f"Created user {created['username']} with role {created['role']}")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not create user: {exc}")

if st.session_state["results"] is None:
    st.warning("Click 'Run Analysis' to generate results")
    st.stop()

results = st.session_state["results"]
df = pd.DataFrame(results["data"])
if "transaction_time" in df.columns:
    df["transaction_time"] = pd.to_datetime(df["transaction_time"])
    df = df.set_index("transaction_time")

st.subheader("📈 Summary")

col1, col2, col3 = st.columns(3)

col1.metric("Total Rows", len(df))
col2.metric("Anomalies", (df["cluster"] == -1).sum())
col3.metric("Anomaly %", f"{(df['cluster'] == -1).mean()*100:.2f}%")

st.subheader("🔍 Anomalies")

st.dataframe(df[df["cluster"] == -1])

st.subheader("📉 Visualization")

fig1 = plot_analysis(stock, df, timeframe)
fig2 = plot_scatter(stock, df, timeframe)
fig3 = plot_timeseries(stock, df, timeframe)

st.plotly_chart(fig1)
st.plotly_chart(fig2)
st.plotly_chart(fig3)


  



# Inspect and optionally save the top-N anomalies from the test period

# TopAnoms = df_test.sort_values(f"anomaly_score_{model}", ascending=False).head(top_n)
# print(str.upper(f"for {model} model"))
# print(f"The anomaly threshold is {threshold}")
# print(f"Top {top_n} most anomalous dates in test set:")
# print(TopAnoms[['close', 'quantity', 'return', f"anomaly_score_{model}", f"anomalous_{model}"]])
# print()



#MAJOR EVENTS
#2025-09-* is the GENZ Revolution

#20**-07-* is the Federal Budget Season

#2026-03-09 NEPSE Hits 6% circuit breaker after R.S.P Win
#The next day 2026-03-10 ppl boooked profits and it fell

#2026-03-29 After formation of new govt Oli and Lekhak were arrested leading to NEPSE falling
#2026-04-05 Jagadamba Group CEO was arrested leading to NEPSE freefall 
#2026-03-22 Official win of R.S.P