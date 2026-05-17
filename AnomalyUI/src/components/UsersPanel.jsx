import { useEffect, useState } from "react";
import { getUsers, createUser, updateUserRole, deleteUser } from "../api";

export default function UsersPanel({ token }) {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [newUser, setNewUser] = useState({ username: "", password: "", role: "analyst" });
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await getUsers(token);
      setUsers(data || []);
    } catch (err) {
      setError(err.message || "Failed to load users");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!token) return;
    load();
  }, [token]);

  const handleCreate = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await createUser(token, newUser.username, newUser.password, newUser.role);
      setNewUser({ username: "", password: "", role: "analyst" });
      await load();
    } catch (err) {
      setError(err.message || "Create failed");
    }
  };

  const handleRoleChange = async (userId, role) => {
    setError("");
    try {
      await updateUserRole(token, userId, role);
      await load();
    } catch (err) {
      setError(err.message || "Update failed");
    }
  };

  const handleDelete = async (userId) => {
    if (!confirm("Delete this user?")) return;
    setError("");
    try {
      await deleteUser(token, userId);
      await load();
    } catch (err) {
      setError(err.message || "Delete failed");
    }
  };

  return (
    <div className="panel-card" style={{ padding: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h3 style={{ margin: 0 }}>Users</h3>
        <div style={{ color: "#94a3b8" }}>{loading ? "Loading…" : `${users.length} users`}</div>
      </div>

      {error ? <div className="form-error" style={{ marginTop: 12 }}>{error}</div> : null}

      <div style={{ marginTop: 12, display: "grid", gap: 8 }}>
        {users.map((u) => (
          <div key={u.id} style={{ display: "flex", gap: 8, alignItems: "center", justifyContent: "space-between", padding: 10, borderRadius: 12, background: "rgba(15,23,42,0.6)" }}>
            <div>
              <div style={{ fontWeight: 700 }}>{u.username}</div>
              <div style={{ color: "#94a3b8", fontSize: 12 }}>{u.role}</div>
            </div>
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <select value={u.role} onChange={(e) => handleRoleChange(u.id, e.target.value)} style={{ padding: 8, borderRadius: 10 }}>
                <option value="analyst">analyst</option>
                <option value="admin">admin</option>
              </select>
              <button className="text-button" onClick={() => handleDelete(u.id)} style={{ color: "#fb7185" }}>Delete</button>
            </div>
          </div>
        ))}
      </div>

      <form onSubmit={handleCreate} style={{ marginTop: 16, display: "grid", gap: 8 }}>
        <input placeholder="username" value={newUser.username} onChange={(e) => setNewUser((p) => ({ ...p, username: e.target.value }))} required />
        <input placeholder="password" type="password" value={newUser.password} onChange={(e) => setNewUser((p) => ({ ...p, password: e.target.value }))} required />
        <select value={newUser.role} onChange={(e) => setNewUser((p) => ({ ...p, role: e.target.value }))}>
          <option value="analyst">analyst</option>
          <option value="admin">admin</option>
        </select>
        <button className="primary-button" type="submit">Create user</button>
      </form>
    </div>
  );
}
