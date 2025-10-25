// src/pages/Login.jsx
import { useState, useEffect } from "react";
import { login } from "../api";
import { saveToken, getToken } from "../auth";
import { useNavigate, Link } from "react-router-dom";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);
  const nav = useNavigate();

  // 🔹 Если токен уже есть — сразу в профиль
  useEffect(() => {
    if (getToken()) nav("/profile", { replace: true });
  }, [nav]);

  async function handleLogin(e) {
    e.preventDefault();
    setErr("");
    setLoading(true);

    try {
      const res = await login({ email, password });
      if (res?.access_token) {
        saveToken(res.access_token);
        nav("/profile", { replace: true }); // ✅ редирект в профиль
      } else {
        throw new Error("Неверный ответ от сервера");
      }
    } catch (e) {
      setErr(e.message || "Ошибка входа");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: 400, margin: "80px auto", color: "#fff" }}>
      <h2>Вход</h2>
      {err && <div style={{ color: "crimson", marginBottom: 10 }}>{err}</div>}

      <form onSubmit={handleLogin} style={{ display: "grid", gap: 12 }}>
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <input
          type="password"
          placeholder="Пароль"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <button type="submit" disabled={loading}>
          {loading ? "Входим..." : "Войти"}
        </button>
      </form>

      <div style={{ marginTop: 16 }}>
        Нет аккаунта? <Link to="/signup" style={{ color: "#7dd87d" }}>Регистрация</Link>
      </div>
    </div>
  );
}
