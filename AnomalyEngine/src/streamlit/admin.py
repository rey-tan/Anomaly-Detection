import streamlit as st

from src.services.api_client import ApiError, create_user, delete_user, get_all_users, update_user_role


def admin_page():
    st.title("🛠️ Admin")

    if st.session_state.get("role") != "admin":
        st.error("Admin access only.")
        return

    st.subheader("User management")

    try:
        users = get_all_users(st.session_state["auth_token"])
    except ApiError as exc:
        st.error(f"Unable to load users: {exc}")
        return

    for user in users:
        st.write(f"**{user['username']}** — {user['role']}")
        role_options = ["analyst", "admin"]
        if user["role"] not in role_options:
            role_options = [user["role"]] + role_options
        selected_index = role_options.index(user["role"])
        new_role = st.selectbox(
            "New role",
            role_options,
            index=selected_index,
            key=f"role_{user['id']}",
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Update Role", key=f"update_{user['id']}"):
                try:
                    update_user_role(st.session_state["auth_token"], user["id"], new_role)
                    st.success(f"Updated {user['username']} to {new_role}")
                    st.rerun()
                except ApiError as exc:
                    st.error(f"Unable to update role: {exc}")
        with col2:
            if st.button("Delete", key=f"delete_{user['id']}"):
                try:
                    delete_user(st.session_state["auth_token"], user["id"])
                    st.success(f"Deleted {user['username']}")
                    st.rerun()
                except ApiError as exc:
                    st.error(f"Unable to delete user: {exc}")

    st.markdown("---")
    st.subheader("Create new user")
    new_username = st.text_input("New username", key="admin_new_username")
    new_password = st.text_input("New password", type="password", key="admin_new_password")
    new_role = st.selectbox("Role", ["analyst", "admin"], key="admin_new_role")

    if st.button("Create user", key="admin_create_user"):
        if not new_username or not new_password:
            st.error("Username and password are required")
        else:
            try:
                create_user(st.session_state["auth_token"], new_username, new_password, new_role)
                st.success(f"Created user {new_username}")
                st.rerun()
            except ApiError as exc:
                st.error(f"Unable to create user: {exc}")
