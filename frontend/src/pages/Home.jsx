import { useEffect, useState } from "react";
import { me, recs } from "../api";
import { getToken } from "../auth";
import { useNavigate } from "react-router-dom";

export default function Home() {
  const [user, setUser] = useState(null);
  const [items, setItems] = useState([]);
  const [err, setErr] = useState("");
  const nav = useNavigate();
  const token = getToken();

  useEffect(() => {
    if (!token) { nav("/login"); return; }
    (async () => {
      try {
        setErr("");
        const u = await me(token);
        setUser(u);
        const r = await recs(token);
        setItems(r.items || []);
      } catch (e) { setErr(String(e.message || e)); }
    })();
  }, [token]);

  if (!token) return null;

  return (
    <div style={{display:"grid", gap:12}}>
      <h2>Home</h2>
      {err && <div style={{color:"crimson"}}>{err}</div>}
      <div>
        <h3>Me</h3>
        <pre style={{background:"#f5f5f5", padding:12}}>{user ? JSON.stringify(user, null, 2) : "..."}</pre>
      </div>
      <div>
        <h3>Recommendations</h3>
        <ul>
          {items.map(({ user, score }) => (
            <li key={user.id}><strong>{user.name}</strong> — {user.email} — score: {score}</li>
          ))}
        </ul>
        {!items.length && <div>no items yet</div>}
      </div>
    </div>
  );
}
