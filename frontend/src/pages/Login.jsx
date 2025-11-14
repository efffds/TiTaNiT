import { useState, useEffect } from "react";
import { login } from "../api";
import { saveToken, getToken } from "../auth";
import { useNavigate, Link } from "react-router-dom";
import Logo from "../components/Logo";
import Card from "../components/Card";
import Input from "../components/Input";
import Btn from "../components/Btn";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);
  const nav = useNavigate();

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
        nav("/profile", { replace: true });
      } else {
        throw new Error("Неверный email или пароль");
      }
    } catch (e) {
      // Показываем общее сообщение об ошибке
      setErr("Неверный email или пароль");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="d-flex justify-content-center align-items-center min-vh-100">
      <Card className="col-12 col-sm-8 col-md-5">
        <Logo />
        <h2 className="section-title text-center">Вход</h2>

        {err && <div className="alert alert-danger">{err}</div>}

        <form onSubmit={handleLogin}>
          <Input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <Input
            type="password"
            placeholder="Пароль"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <Btn disabled={loading}>
            {loading ? "Входим…" : "Войти"}
          </Btn>
        </form>

        <div className="mt-3 text-center">
          Нет аккаунта?{" "}
          <Link to="/signup" className="text-success">
            Регистрация
          </Link>
        </div>
      </Card>
    </div>
  );
}
