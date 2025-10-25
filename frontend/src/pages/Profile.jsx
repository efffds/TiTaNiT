import { useEffect, useState } from "react";
import { getToken, logout } from "../auth";
import { me } from "../api";
import { useNavigate } from "react-router-dom";

export default function Profile() {
  const [user, setUser] = useState(null);
  const [err, setErr] = useState("");
  const nav = useNavigate();
  const token = getToken();

  useEffect(() => {
    if (!token) return nav("/login");
    (async () => {
      try {
        const u = await me(token);
        setUser(u);
      } catch (e) {
        setErr(e?.message || "Ошибка загрузки профиля");
      }
    })();
  }, [token]);

  if (!token) return null;

  return (
    <div style={styles.page}>
      <h2 style={styles.title}>Ваш профиль</h2>
      {err && <div style={styles.err}>{err}</div>}

      {user ? (
        <pre style={styles.card}>{JSON.stringify(user, null, 2)}</pre>
      ) : (
        <div style={styles.loading}>Загрузка...</div>
      )}

      <button onClick={() => { logout(); nav("/login"); }} style={styles.btn}>
        Выйти
      </button>
    </div>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    background: "#0a0a0a",
    color: "#fff",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    padding: "32px 16px",
  },
  title: { fontSize: 28, fontWeight: 800, marginBottom: 20 },
  card: {
    background: "#1b1b1b",
    color: "#eaeaea",
    borderRadius: 12,
    padding: 16,
    maxWidth: 400,
    width: "100%",
    marginBottom: 20,
  },
  loading: { opacity: 0.6, marginBottom: 20 },
  btn: {
    background: "#26de50",
    border: "none",
    color: "#000",
    fontWeight: 700,
    padding: "10px 24px",
    borderRadius: 10,
    cursor: "pointer",
  },
  err: {
    color: "#ff8a8a",
    background: "#3a0f0f",
    borderRadius: 8,
    padding: "10px 16px",
    marginBottom: 16,
  },
};
