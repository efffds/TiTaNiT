import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getToken } from "../auth";
import { openChat, getUserById, listMessages, sendMessage } from "../api";

export default function Chat() {
  const nav = useNavigate();
  const { partnerId } = useParams();
  const token = getToken();
  const [conversationId, setConversationId] = useState(null);
  const [partner, setPartner] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [err, setErr] = useState("");
  const pollRef = useRef(null);

  useEffect(() => {
    if (!token) { nav("/login"); return; }
    const pid = Number(partnerId);
    if (!pid) { setErr("Invalid partner id"); return; }
    (async () => {
      try {
        setErr("");
        const { conversation_id } = await openChat(token, pid);
        setConversationId(conversation_id);
        try { const u = await getUserById(token, pid); setPartner(u); } catch {}
      } catch (e) { setErr(String(e.message || e)); }
    })();
  }, [token, partnerId]);

  useEffect(() => {
    if (!conversationId) return;
    const load = async () => {
      try { const ms = await listMessages(token, conversationId); setMessages(ms); }
      catch (e) { /* ignore */ }
    };
    load();
    pollRef.current = setInterval(load, 2000);
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [conversationId]);

  const onSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || !conversationId) return;
    try {
      await sendMessage(token, conversationId, input.trim());
      setInput("");
      const ms = await listMessages(token, conversationId);
      setMessages(ms);
    } catch (e) { setErr(String(e.message || e)); }
  };

  if (!token) return null;

  return (
    <div style={{display:"grid", gap:12}}>
      <h2>Chat {partner ? `with ${partner.name}` : `with #${partnerId}`}</h2>
      {err && <div style={{color:"crimson"}}>{err}</div>}
      <div style={{border:"1px solid #ccc", padding:12, borderRadius:8, height:360, overflowY:"auto"}}>
        {messages.map((m) => (
          <div key={m.id} style={{marginBottom:8}}>
            <div style={{fontSize:12, color:"#666"}}>from {m.sender_id}</div>
            <div>{m.body}</div>
          </div>
        ))}
        {!messages.length && <div>No messages yet</div>}
      </div>
      <form onSubmit={onSend} style={{display:"flex", gap:8}}>
        <input value={input} onChange={e=>setInput(e.target.value)} placeholder="Type a message" style={{flex:1}} />
        <button type="submit" disabled={!input.trim()}>Send</button>
      </form>
    </div>
  );
}
