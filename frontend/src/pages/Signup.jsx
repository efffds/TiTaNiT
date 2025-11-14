import { useState } from "react";
import { signup } from "../api";
import { useNavigate, Link } from "react-router-dom";
import Logo from "../components/Logo";
import Card from "../components/Card";
import Input from "../components/Input";
import Btn from "../components/Btn";

export default function Signup() {
  const nav = useNavigate();
  const [step, setStep] = useState(1);
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [city, setCity] = useState("");
  const [age, setAge] = useState("");
  const [bio, setBio] = useState("");
  const [password, setPassword] = useState("");
  const [password2, setPassword2] = useState("");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  const goStep2 = (e) => {
    e.preventDefault();
    if (!email || !name) return setErr("Заполните email и имя");
    setErr("");
    setStep(2);
  };

  const doSignup = async (e) => {
    e.preventDefault();
    if (password.length < 6) return setErr("Пароль минимум 6 символов");
    if (password !== password2) return setErr("Пароли не совпадают");
    setLoading(true);
    try {
      const res = await signup({ email, password, name, city, age, bio });
      if (res?.access_token) {
        const { saveToken } = await import("../auth");
        saveToken(res.access_token);
        nav("/profile");
      } else nav("/login");
    } catch (e) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="d-flex justify-content-center align-items-center min-vh-100">
      <Card className="col-12 col-sm-9 col-md-6">
        <Logo />
        <h2 className="section-title text-center">Регистрация</h2>

        {err && <div className="alert alert-danger">{err}</div>}

        {step === 1 ? (
          <form onSubmit={goStep2}>
            <Input
              type="email"
              placeholder="Э‑почта"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <Input
              placeholder="Имя"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
            <div className="row g-2">
              <div className="col-8">
                <Input
                  placeholder="Город"
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                />
              </div>
              <div className="col-4">
                <Input
                  placeholder="Возраст"
                  type="number"
                  min="0"
                  value={age}
                  onChange={(e) => setAge(e.target.value)}
                />
              </div>
            </div>
            <div className="mb-3">
              <textarea
                className="custom-input w-100"
                placeholder="О себе"
                rows={4}
                value={bio}
                onChange={(e) => setBio(e.target.value)}
              />
            </div>
            <Btn>Продолжить →</Btn>
          </form>
        ) : (
          <form onSubmit={doSignup}>
            <Input
              type="password"
              placeholder="Пароль"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <Input
              type="password"
              placeholder="Повторите пароль"
              value={password2}
              onChange={(e) => setPassword2(e.target.value)}
              required
            />
            <Btn disabled={loading}>
              {loading ? "Регистрация…" : "Зарегистрироваться"}
            </Btn>
          </form>
        )}

        <div className="mt-3 text-center">
          Уже есть аккаунт?{" "}
          <Link to="/login" className="text-success">
            Войти
          </Link>
        </div>
      </Card>
    </div>
  );
}
