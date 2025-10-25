import { useState } from "react";
import { login } from "../api";
import { setToken } from "../auth";
import { useNavigate } from "react-router-dom";

export default function Login() {
  const [email, setEmail] = useState("test1@example.com");
  const [password, setPassword] = useState("Password123!");
  const [err, setErr] = useState("");
  const nav = useNavigate();

  const submit = async (e) => {
    e.preventDefault();
    setErr("");
    try {
      const { access_token } = await login({ email, password });
      setToken(access_token);
      nav("/home");
    } catch (e) { setErr(String(e.message || e)); }
  };

  return (
    <form onSubmit={submit} style={{display:"grid", gap:8}}>
      <h2>Login</h2>
      <input placeholder="email" value={email} onChange={e=>setEmail(e.target.value)} />
      <input type="password" placeholder="password" value={password} onChange={e=>setPassword(e.target.value)} />
      <button type="submit">Log in</button>
      {err && <div style={{color:"crimson"}}>{err}</div>}
    </form>
  );
}
