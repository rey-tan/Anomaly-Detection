import { useEffect, useState } from "react";
import { getUsers, createUser, updateUserRole, deleteUser } from "../api";
import AdminActivityPanel from "./AdminActivityPanel";

export default function UsersPanel({ token, currentUser, onOpenActivity }) {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [newUser, setNewUser] = useState({ username: "", password: "", role: "analyst" });
  const [error, setError] = useState("");
  const [selectedUserId, setSelectedUserId] = useState(null);

  useEffect(() => {
    if (!token) return;
    let active = true;

    const loadUsers = async () => {
      setLoading(true);
      setError("");
      try {
        const data = await getUsers(token);
        if (active) {
          setUsers(data || []);
        }
      } catch (err) {
        if (active) {
          setError(err.message || "Failed to load users");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    loadUsers();

    return () => {
      active = false;
    };
  }, [token]);

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
    <div className="admin-panel">
      

      <div className="admin-panel-head" style={{ marginTop: 8 }}>
        <div>
          <p className="eyebrow">Users</p>
          <h3>User management</h3>
        </div>
        <div className="admin-count">{loading ? "…" : `${users.length} users`}</div>
      </div>

      {error ? <div className="form-error admin-error">{error}</div> : null}


      <div className="admin-list">
        {users.map((u) => (
          <div key={u.id} className={u.role === "admin" || u.id === currentUser?.id ? "admin-user-card protected" : "admin-user-card"}>
            <div className="admin-user-copy">
              <div className="admin-user-name">{u.username}</div>
              <div className="admin-user-role">{u.role}</div>
            </div>
              <div className="admin-user-actions">
              <select
                value={u.role}
                onChange={(e) => handleRoleChange(u.id, e.target.value)}
                className="admin-select"
                disabled={u.role === "admin" || u.id === currentUser?.id}
              >
                <option value="analyst">analyst</option>
                <option value="admin">admin</option>
              </select>
              <button className="text-button" onClick={() => { if (onOpenActivity) { onOpenActivity(u.id); } else { setSelectedUserId(u.id); } }} type="button">Activity</button>
              {u.role === "admin" || u.id === currentUser?.id ? null : (
                <button className="text-button danger" onClick={() => handleDelete(u.id)} type="button">
                  Delete
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {selectedUserId ? (
        <AdminActivityPanel token={token} userId={selectedUserId} onClose={() => setSelectedUserId(null)} />
      ) : null}

      <form onSubmit={handleCreate} className="admin-form">
        <div className="admin-form-grid">
          <input className="admin-input" placeholder="username" value={newUser.username} onChange={(e) => setNewUser((p) => ({ ...p, username: e.target.value }))} required />
          <input className="admin-input" placeholder="password" type="password" value={newUser.password} onChange={(e) => setNewUser((p) => ({ ...p, password: e.target.value }))} required />
          <select className="admin-select" value={newUser.role} onChange={(e) => setNewUser((p) => ({ ...p, role: e.target.value }))}>
            <option value="analyst">analyst</option>
            <option value="admin">admin</option>
          </select>
        </div>
        <button className="primary-button admin-submit" type="submit">Create user</button>
      </form>
    </div>
  );
}
