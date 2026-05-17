import streamlit as st

from src.services.api_client import ApiError, get_user_profile, login


def ensure_session_state():
    state = st.session_state
    if "authenticated" not in state:
        state["authenticated"] = False
    if "auth_token" not in state:
        state["auth_token"] = ""
    if "username" not in state:
        state["username"] = ""
    if "role" not in state:
        state["role"] = "user"
    if "results" not in state:
        state["results"] = None


def show_login_page():
    st.title("Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

        if submit:
            try:
                data = login(username, password)
                st.session_state["authenticated"] = True
                st.session_state["auth_token"] = data["access_token"]
                st.session_state["username"] = username
                profile = get_user_profile(st.session_state["auth_token"])
                st.session_state["role"] = profile.get("role", "user")
                st.success("Login successful")
                st.rerun()
            except ApiError as exc:
                st.error(str(exc))
            except Exception as exc:
                st.error(f"Login failed: {exc}")


def logout():
    st.session_state["authenticated"] = False
    st.session_state["auth_token"] = ""
    st.session_state["username"] = ""
    st.session_state["role"] = "user"
    st.session_state["results"] = None
