import { useState } from "react";
import { signup } from "../api";
import { setToken } from "../auth";
import { useNavigate } from "react-router-dom";

export default function Signup() {
  const [email, setEmail] = useState("test2@example.com");
  const [password, setPassword] = useState("Password123!");
  const [name, setName] = useState("Nadezhda");
  const [city, setCity] = useState("Amsterdam");
  const [err, setErr] = useState("");
  const nav = useNavigate();

  const submit = async (e) => {
    e.preventDefault();
    setErr("");
    try {
      const { access_token } = await signup({ email, password, name, city });
      setToken(access_token);
      nav("/home");
    } catch (e) { setErr(String(e.message || e)); }
  };

  return (
    <form onSubmit={submit} style={{display:"grid", gap:8}}>
      <h2>Sign up</h2>
      <input placeholder="email" value={email} onChange={e=>setEmail(e.target.value)} />
      <input type="password" placeholder="password" value={password} onChange={e=>setPassword(e.target.value)} />
      <input placeholder="name" value={name} onChange={e=>setName(e.target.value)} />
      <input placeholder="city" value={city} onChange={e=>setCity(e.target.value)} />
      <button type="submit">Create account</button>
      {err && <div style={{color:"crimson"}}>{err}</div>}
    </form>
  );
}
