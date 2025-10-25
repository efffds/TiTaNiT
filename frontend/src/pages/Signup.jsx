import { useState } from "react";
import { signup } from "../api";
import { useNavigate, Link } from "react-router-dom";

export default function Signup() {
  const nav = useNavigate();
  const [step, setStep] = useState(1);

  const [email, setEmail] = useState("");
  const [name, setName]   = useState("");
  const [city, setCity]   = useState("");
  const [age, setAge]     = useState("");
  const [bio, setBio]     = useState("");

  const [password, setPassword]   = useState("");
  const [password2, setPassword2] = useState("");

  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  const goStep2 = (e) => {
    e.preventDefault();
    setErr("");
    if (!email || !name) return setErr("Заполните email и имя");
    setStep(2);
  };

  const doSignup = async (e) => {
    e.preventDefault();
    setErr("");
    if (password.length < 6) return setErr("Пароль должен быть не короче 6 символов");
    if (password !== password2) return setErr("Пароли не совпадают");

    try {
      setLoading(true);
      const res = await signup({ email, password, name, city });
      if (res?.access_token) {
        const { saveToken } = await import("../auth");
        saveToken(res.access_token);
        nav("/profile");
      } else {
        nav("/login");
      }
    } catch (e) {
      setErr(e?.message || "Ошибка регистрации");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container-fluid min-vh-100 d-flex flex-column">
      {/* центральная зона */}
      <div className="container flex-grow-1 d-flex align-items-start align-items-md-center justify-content-center py-4">
        <div className="w-100" style={{ maxWidth: 520 }}>
          {/* логотип */}
          <div className="text-center mb-3">
            <div className="d-inline-flex align-items-center gap-2">
              <span className="text-success fs-4">♥</span>
              <h1 className="m-0 fw-bold" style={{letterSpacing: "1px"}}>TiTi</h1>
              <span className="text-success fs-4">♥</span>
            </div>
            <div className="opacity-75 small mt-n1">for TITANIT</div>
          </div>

          {/* карточка формы */}
          <div className="card shadow-lg p-4">
            <h2 className="fw-bold mb-3">Расскажите о себе</h2>

            {err && (
              <div className="alert alert-danger py-2">{err}</div>
            )}

            {step === 1 ? (
              <form onSubmit={goStep2} className="d-grid gap-3">
                <input
                  className="form-control"
                  placeholder="Электронная почта"
                  type="email"
                  value={email}
                  onChange={(e)=>setEmail(e.target.value)}
                />
                <input
                  className="form-control"
                  placeholder="Имя"
                  value={name}
                  onChange={(e)=>setName(e.target.value)}
                />
                <div className="row g-2">
                  <div className="col-8">
                    <input
                      className="form-control"
                      placeholder="Город"
                      value={city}
                      onChange={(e)=>setCity(e.target.value)}
                    />
                  </div>
                  <div className="col-4">
                    <input
                      className="form-control"
                      placeholder="Возраст"
                      value={age}
                      onChange={(e)=>setAge(e.target.value)}
                    />
                  </div>
                </div>
                <textarea
                  className="form-control"
                  placeholder="О себе"
                  rows={4}
                  value={bio}
                  onChange={(e)=>setBio(e.target.value)}
                />
                <button type="submit" className="btn btn-brand w-100" disabled={loading}>
                    Искать людей
                </button>
                <div className="cta-underline"></div>
              </form>
            ) : (
              <form onSubmit={doSignup} className="d-grid gap-3">
                <input
                  className="form-control"
                  placeholder="Пароль"
                  type="password"
                  value={password}
                  onChange={(e)=>setPassword(e.target.value)}
                />
                <input
                  className="form-control"
                  placeholder="Повторите пароль"
                  type="password"
                  value={password2}
                  onChange={(e)=>setPassword2(e.target.value)}
                />
                <button type="submit" className="btn btn-brand w-100" disabled={loading}>
                  Зарегистрироваться
                </button>
              </form>
            )}

            <hr className="border-secondary my-4" />
            <div className="text-center">
              Уже есть аккаунт?{" "}
              <Link to="/login" className="fw-bold text-success text-decoration-underline">
                Войти
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
