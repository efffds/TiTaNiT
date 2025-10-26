import { useEffect, useRef, useState } from "react";
import { me, listPhotos, uploadPhoto, setPrimary, deletePhoto, getProfile, saveProfile } from "../api";
import { getToken, logout } from "../auth";
import { useNavigate, Link, useLocation } from "react-router-dom";

const LS_KEY = "titi_profile_draft";

export default function Profile() {
  const token = getToken();
  const nav = useNavigate();
  const loc = useLocation();
  const fileRef = useRef(null);

  const [user, setUser] = useState(null);
  const [photos, setPhotos] = useState([]);
  const [form, setForm] = useState({
    city: "",
    age: "",
    bio: "",
    skills: "",
    interests: "",
    goals: "",
  });
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);
  const saveTimer = useRef(null);

  // загрузка пользователя, фоток и профиля/черновика
  useEffect(() => {
    if (!token) { nav("/login"); return; }

    (async () => {
      try {
        setErr("");
        const u = await me(token);
        setUser(u);

        // 1) подтянуть профиль с бэка (если есть)
        try {
          const p = await getProfile(token);
          if (p && typeof p === "object") {
            setForm((f) => ({ ...f, ...p }));
            // обновим черновик локально
            localStorage.setItem(LS_KEY, JSON.stringify({ ...form, ...p }));
          }
        } catch {
          // 2) если бэка нет — взять из локального черновика
          const raw = localStorage.getItem(LS_KEY);
          if (raw) {
            try { setForm(JSON.parse(raw)); } catch {}
          } else if (u?.city) {
            setForm((f) => ({ ...f, city: u.city }));
          }
        }

        // фото (если эндпоинт есть)
        try {
          const ph = await listPhotos(token);
          const items = ph.items || ph || [];
          setPhotos(items);
        } catch {}
      } catch (e) {
        setErr(e.message || String(e));
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  // локальное и серверное автосохранение с debounce
  useEffect(() => {
    // сохраняем в localStorage мгновенно
    localStorage.setItem(LS_KEY, JSON.stringify(form));

    // и пытаемся отправить на бэк через 800мс (если он есть)
    clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(async () => {
      try { await saveProfile(form, token); } catch {}
    }, 800);

    return () => clearTimeout(saveTimer.current);
  }, [form, token]);

  function onPickFile() { fileRef.current?.click(); }

  async function onFileChosen(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      setLoading(true);
      const res = await uploadPhoto(file, token);
      const added = { id: res.id, photo_path: res.photo_path, is_primary: false };
      setPhotos((p) => [added, ...p]);
    } catch (e) {
      setErr(e.message || "Не удалось загрузить фото");
    } finally {
      setLoading(false);
      e.target.value = "";
    }
  }

  async function makePrimary(id) {
    try {
      setLoading(true);
      try { await setPrimary(id, token); } catch {}
      setPhotos((arr) => {
        const withFlag = arr.map((p) => ({ ...p, is_primary: p.id === id }));
        withFlag.sort((a, b) => (b.is_primary === true) - (a.is_primary === true));
        return withFlag;
      });
    } catch (e) {
      setErr(e.message || "Не удалось установить основное фото");
    } finally {
      setLoading(false);
    }
  }

  async function removePhoto(id) {
    if (!confirm("Удалить фото?")) return;
    try {
      setLoading(true);
      try { await deletePhoto(id, token); } catch {}
      setPhotos((p) => p.filter((x) => x.id !== id));
    } catch (e) {
      setErr(e.message || "Не удалось удалить фото");
    } finally {
      setLoading(false);
    }
  }

  function fullUrl(path) {
    if (!path) return "";
    return path.startsWith("http")
      ? path
      : `${import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"}/${path.replace(/^\/+/, "")}`;
  }

  function doLogout() { logout(); nav("/login"); }

  return (
    <div className="container py-4">
      {/* top bar */}
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h3 className="text-white m-0">Профиль</h3>
        <button className="btn btn-outline-light" onClick={doLogout}>Выйти</button>
      </div>

      {err && <div className="alert alert-danger">{err}</div>}

      {/* карточка шапки */}
      <div className="card bg-dark text-white mb-4">
        <div className="card-body">
          <div className="d-flex align-items-center gap-3">
            <div style={{ width: 72, height: 72, borderRadius: "50%", overflow: "hidden", border: "3px solid #26de50" }}>
              <img
                src={
                  photos.find(p => p.is_primary)?.photo_path
                    ? fullUrl(photos.find(p => p.is_primary).photo_path)
                    : "https://via.placeholder.com/150?text=No+Photo"
                }
                alt=""
                style={{ width: "100%", height: "100%", objectFit: "cover" }}
              />
            </div>
            <div>
              <div className="fw-bold fs-5">{user?.name || "—"}</div>
              <div className="text-secondary">{form.city || "—"}</div>
            </div>
          </div>
        </div>
      </div>

      {/* фото-сетка */}
      <div className="mb-4">
        <div className="d-flex align-items-center justify-content-between mb-2">
          <div className="text-white fw-semibold">Фотографии</div>
          <button className="btn btn-success" onClick={onPickFile} disabled={loading}>
            + Добавить фото
          </button>
          <input ref={fileRef} type="file" accept="image/*" className="d-none" onChange={onFileChosen} />
        </div>

        <div className="row g-3">
          {photos.map((p) => (
            <div key={p.id} className="col-6 col-md-4 col-lg-3">
              <div className="position-relative">
                <img
                  src={fullUrl(p.photo_path)}
                  alt=""
                  className="img-fluid rounded"
                  style={{ aspectRatio: "1 / 1", objectFit: "cover", width: "100%" }}
                />
                <div className="position-absolute top-0 end-0 p-2 d-flex gap-2">
                  <button
                    title="Сделать основным"
                    className={`btn btn-sm ${p.is_primary ? "btn-success" : "btn-outline-success"}`}
                    onClick={() => makePrimary(p.id)}
                  >
                    ★
                  </button>
                  <button
                    title="Удалить"
                    className="btn btn-sm btn-outline-danger"
                    onClick={() => removePhoto(p.id)}
                  >
                    ✕
                  </button>
                </div>
              </div>
            </div>
          ))}
          <div className="col-6 col-md-4 col-lg-3">
            <div
              className="d-flex align-items-center justify-content-center border rounded text-success"
              style={{ aspectRatio: "1 / 1", cursor: "pointer", background: "#151515" }}
              onClick={onPickFile}
            >
              <span className="fs-3">+</span>
            </div>
          </div>
        </div>
      </div>

      {/* анкетные поля */}
      <div className="card bg-dark text-white mb-5">
        <div className="card-body">
          <div className="row g-3">
            <div className="col-md-6">
              <label className="form-label text-white">Город</label>
              <input className="form-control bg-secondary-subtle text-white border-0"
                     value={form.city}
                     onChange={(e)=>setForm({...form, city: e.target.value})}/>
            </div>
            <div className="col-md-6">
              <label className="form-label text-white">Возраст</label>
              <input className="form-control bg-secondary-subtle text-white border-0"
                     value={form.age}
                     onChange={(e)=>setForm({...form, age: e.target.value})}/>
            </div>
            <div className="col-12">
              <label className="form-label text-white">О себе</label>
              <textarea rows={3}
                        className="form-control bg-secondary-subtle text-white border-0"
                        value={form.bio}
                        onChange={(e)=>setForm({...form, bio: e.target.value})}/>
            </div>
            <div className="col-md-4">
              <label className="form-label text-white">Навыки</label>
              <input className="form-control bg-secondary-subtle text-white border-0"
                     value={form.skills}
                     onChange={(e)=>setForm({...form, skills: e.target.value})}/>
            </div>
            <div className="col-md-4">
              <label className="form-label text-white">Интересы</label>
              <input className="form-control bg-secondary-subtle text-white border-0"
                     value={form.interests}
                     onChange={(e)=>setForm({...form, interests: e.target.value})}/>
            </div>
            <div className="col-md-4">
              <label className="form-label text-white">Цели</label>
              <input className="form-control bg-secondary-subtle text-white border-0"
                     value={form.goals}
                     onChange={(e)=>setForm({...form, goals: e.target.value})}/>
            </div>
          </div>
        </div>
      </div>

      {/* нижняя навигация с иконкой профиля */}
      <nav className="navbar fixed-bottom bg-dark-subtle" style={{borderTop: "1px solid #222"}}>
        <div className="container d-flex justify-content-around">
          <NavBtn to="/cards" label="Анкеты" active={loc.pathname === "/cards"} icon="📋" />
          <NavBtn to="/likes" label="Лайки" active={loc.pathname === "/likes"} icon="❤️" />
          <NavBtn to="/messages" label="Сообщения" active={loc.pathname === "/messages"} icon="💬" />
          <NavBtn to="/meetings" label="Встречи" active={loc.pathname === "/meetings"} icon="📅" />
          <NavBtn to="/profile" label="Профиль" active={loc.pathname === "/profile"} icon="👤" />
        </div>
      </nav>
    </div>
  );
}

function NavBtn({ to, label, active, icon }) {
  return (
    <Link to={to} className="text-decoration-none text-center">
      <div style={{ color: active ? "#26de50" : "#bbb", fontWeight: 700 }}>
        <div style={{ fontSize: 18, lineHeight: 1 }}>{icon}</div>
        <div style={{ fontSize: 12 }}>{label}</div>
      </div>
    </Link>
  );
}
