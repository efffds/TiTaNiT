import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getToken } from "../auth";
import { matches, getUserById, listConversations, openChat } from "../api";

export default function Chats() {
  const nav = useNavigate();
  const token = getToken();
  const [items, setItems] = useState([]); // {partnerId, name}
  const [err, setErr] = useState("");

  useEffect(() => {
    if (!token) { nav("/login"); return; }
    (async () => {
      try {
        setErr("");
        const ms = await matches(token); // { user_ids: number[] }
        const ids = ms.user_ids || [];
        const enriched = await Promise.all(ids.map(async (id) => {
          try { const u = await getUserById(token, id); return { partnerId: id, name: u.name || `User ${id}` }; }
          catch { return { partnerId: id, name: `User ${id}` }; }
        }));
        setItems(enriched);
      } catch (e) { setErr(String(e.message || e)); }
    })();
  }, [token]);

  const goChat = async (partnerId) => {
    try { await openChat(token, partnerId); nav(`/chat/${partnerId}`); }
    catch (e) { setErr(String(e.message || e)); }
  };

  if (!token) return null;

  return (
    <div style={{display:"grid", gap:12}}>
      <h2>Chats (matches)</h2>
      {err && <div style={{color:"crimson"}}>{err}</div>}
      <ul style={{display:"grid", gap:8, listStyle:"none", padding:0}}>
        {items.map(({ partnerId, name }) => (
          <li key={partnerId} style={{display:"flex", gap:8, alignItems:"center"}}>
            <span>{name}</span>
            <button onClick={()=>goChat(partnerId)}>Open chat</button>
          </li>
        ))}
      </ul>
      {!items.length && <div>No matches yet</div>}
    </div>
  );
}
