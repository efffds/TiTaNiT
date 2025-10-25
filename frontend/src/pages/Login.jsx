import { useState } from "react";
import { login } from "../api";
import { saveToken } from "../auth";
import { useNavigate } from "react-router-dom";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const nav = useNavigate();

  async function handleLogin(e) {
    e.preventDefault();
    setErr("");

    try {
      const res = await login({ email, password });
      if (res?.access_token) {
        saveToken(res.access_token);
        nav("/profile");
      } else {
        throw new Error("Неверный ответ от сервера");
      }
    } catch (e) {
      setErr(e.message || "Ошибка входа");
    }
  }

  return (
    <div style={{ maxWidth: 400, margin: "80px auto", color: "#fff" }}>
      <h2>Вход</h2>
      {err && <div style={{ color: "crimson" }}>{err}</div>}
      <form onSubmit={handleLogin} style={{ display: "grid", gap: 12 }}>
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <input
          type="password"
          placeholder="Пароль"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <button type="submit">Войти</button>
      </form>
    </div>
  );
}

