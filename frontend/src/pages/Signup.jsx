// src/pages/Signup.jsx
import { useState, useEffect } from "react";
import { signup } from "../api";
import { useNavigate, Link } from "react-router-dom";
import { saveToken, getToken } from "../auth";

export default function Signup() {
  const nav = useNavigate();

  // если уже залогинен — сразу в профиль
  useEffect(() => {
    if (getToken()) nav("/profile", { replace: true });
  }, [nav]);

  // шаги
  const [step, setStep] = useState(1);

  // поля шага 1
  const [email, setEmail] = useState("");
  const [name, setName]   = useState("");
  const [city, setCity]   = useState("");
  const [age, setAge]     = useState("");
  const [bio, setBio]     = useState("");

  // поля шага 2
  const [password, setPassword]   = useState("");
  const [password2, setPassword2] = useState("");

  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  function validateStep1() {
    if (!email || !name) return "Заполните email и имя";
    const emailOk = /\S+@\S+\.\S+/.test(email);
    if (!emailOk) return "Неверный формат email";
    if (age && !/^\d+$/.test(age)) return "Возраст должен быть числом";
    return "";
  }

  function validateStep2() {
    if (password.length < 6) return "Пароль должен быть не короче 6 символов";
    if (password.length > 72) return "Пароль слишком длинный (макс. 72 символа)";
    if (password !== password2) return "Пароли не совпадают";
    return "";
  }

  const goStep2 = (e) => {
    e.preventDefault();
    setErr("");
    const v = validateStep1();
    if (v) return setErr(v);
    setStep(2);
  };

  const doSignup = async (e) => {
    e.preventDefault();
    setErr("");
    const v = validateStep2();
    if (v) return setErr(v);

    try {
      setLoading(true);

      // Бэк сейчас принимает: email, password, name, city
      const res = await signup({
        email: email.trim(),
        password,
        name: name.trim(),
        city: city.trim(),
        // age, bio — пока не шлём, если бэк их не принимает
      });

      // если бэк вернул токен — сохраняем, ведём в профиль
      if (res?.access_token) {
        saveToken(res.access_token);
        nav("/profile", { replace: true });
      } else {
        // если токена нет (например, бэк решил по-другому) — ведём на логин
        nav("/login", { replace: true });
      }
    } catch (e) {
      // показать понятное сообщение (пытаемся достать detail)
      const msg =
        (e?.response?.data && (e.response.data.detail || e.response.data.message)) ||
        e?.message ||
        "Ошибка регистрации";
      setErr(String(msg));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.page}>
      <div style={styles.logoBlock}>
        <div style={styles.logoRow}>
          <span style={styles.heart}>♥</span>
          <h1 style={styles.logoText}>TiTi</h1>
          <span style={styles.heart}>♥</span>
        </div>
        <div style={styles.logoSub}>for TITANIT</div>
      </div>

      <h2 style={styles.title}>Расскажите о себе</h2>

      {err && <div style={styles.err}>{err}</div>}

      {step === 1 ? (
        <form onSubmit={goStep2} style={styles.form}>
          <input
            placeholder="Электронная почта"
            type="email"
            value={email}
            onChange={(e)=>setEmail(e.target.value)}
            style={styles.input}
            required
          />
          <input
            placeholder="Имя"
            value={name}
            onChange={(e)=>setName(e.target.value)}
            style={styles.input}
            required
          />
          <input
            placeholder="Город"
            value={city}
            onChange={(e)=>setCity(e.target.value)}
            style={styles.input}
          />
          <input
            placeholder="Возраст"
            value={age}
            onChange={(e)=>setAge(e.target.value)}
            style={styles.input}
            inputMode="numeric"
          />
          <textarea
            placeholder="О себе"
            value={bio}
            onChange={(e)=>setBio(e.target.value)}
            rows={4}
            style={{...styles.input, resize:"vertical"}}
          />
          <button type="submit" style={styles.cta} disabled={loading}>
            Далее
          </button>
          <div style={styles.underline}/>
        </form>
      ) : (
        <form onSubmit={doSignup} style={styles.form}>
          <input
            placeholder="Пароль"
            type="password"
            value={password}
            onChange={(e)=>setPassword(e.target.value)}
            style={styles.input}
            required
          />
          <input
            placeholder="Повторите пароль"
            type="password"
            value={password2}
            onChange={(e)=>setPassword2(e.target.value)}
            style={styles.input}
            required
          />
          <button type="submit" style={styles.cta} disabled={loading}>
            {loading ? "Создаём..." : "Зарегистрироваться"}
          </button>
          <div style={styles.underline}/>
        </form>
      )}

      <div style={styles.bottomNote}>
        Уже есть аккаунт?{" "}
        <Link to="/login" style={styles.loginLink}>Войти</Link>
      </div>
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
    padding: "24px 16px",
    fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, sans-serif",
  },
  logoBlock: { marginTop: 24, marginBottom: 24, textAlign: "center" },
  logoRow: { display: "flex", alignItems: "center", gap: 12 },
  heart: { color: "#26de50", fontSize: 28, lineHeight: 1 },
  logoText: { margin: 0, fontWeight: 800, letterSpacing: 1, fontSize: 36 },
  logoSub: { opacity: 0.7, fontSize: 12, marginTop: -6 },
  title: { fontSize: 28, margin: "8px 0 20px 0", fontWeight: 800 },
  form: { width: "100%", maxWidth: 420, display: "grid", gap: 14 },
  input: {
    width: "100%",
    background: "#1d1d1d",
    border: "1px solid #2b2b2b",
    borderRadius: 16,
    color: "#eaeaea",
    padding: "14px 16px",
    fontSize: 16,
    outline: "none",
  },
  cta: {
    width: "100%",
    padding: "14px 16px",
    fontWeight: 800,
    fontSize: 20,
    borderRadius: 14,
    background: "#0f0f0f",
    color: "#fff",
    border: "2px solid #26de50",
    cursor: "pointer",
  },
  underline: {
    width: "100%",
    maxWidth: 420,
    height: 6,
    background: "linear-gradient(90deg, #26de50 0%, #26de50 100%)",
    borderRadius: 8,
    marginTop: 8,
  },
  bottomNote: { marginTop: 28, opacity: 0.9 },
  loginLink: {
    color: "#26de50",
    fontWeight: 800,
    textDecoration: "underline",
    textUnderlineOffset: 3,
  },
  err: {
    background: "#3a0f0f",
    border: "1px solid #5a1a1a",
    color: "#ffb3b3",
    padding: "10px 12px",
    borderRadius: 10,
    marginBottom: 12,
    maxWidth: 420,
  },
};
