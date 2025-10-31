// src/pages/Profile.jsx
import { useEffect, useRef, useState, useMemo } from "react";
import { me, listPhotos, uploadPhoto, setPrimary, deletePhoto, recs } from "../api";
import { getToken, logout } from "../auth";
import { useNavigate } from "react-router-dom";

// === локальное хранение профиля ===
const LS_PROFILE_KEY = "titanit:profile";
function saveProfileLocal(data) {
  localStorage.setItem(LS_PROFILE_KEY, JSON.stringify(data || {}));
}
function loadProfileLocal() {
  const raw = localStorage.getItem(LS_PROFILE_KEY);
  try {
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

export default function Profile() {
  const token = getToken();
  const nav = useNavigate();
  const fileRef = useRef(null);

  const [user, setUser] = useState(null);
  const [photos, setPhotos] = useState([]); // [{id, photo_path, is_primary?}]
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
  const [recLoading, setRecLoading] = useState(false);
  const [recErr, setRecErr] = useState("");
  const [recItems, setRecItems] = useState([]);

  // дебаунс-сейв формы
  useEffect(() => {
    if (!token) return;
    const t = setTimeout(() => {
      saveProfileLocal(form);
    }, 500);
    return () => clearTimeout(t);
  }, [form, token]);

  useEffect(() => {
    if (!token) {
      nav("/login");
      return;
    }
    (async () => {
      try {
        setErr("");

        // 1) поднимем локальные данные сразу (UX)
        const local = loadProfileLocal();
        if (Object.keys(local).length) {
          setForm((f) => ({ ...f, ...local }));
        }

        // 2) загрузим пользователя с бэка (минимум city)
        const u = await me(token);
        setUser(u);
        if (u?.city) {
          setForm((f) => ({ ...f, city: u.city }));
        }

        // 3) загрузим фото (если доступно)
        try {
          const ph = await listPhotos(token);
          const items = ph.items || ph || [];
          setPhotos(items);
        } catch {
          /* ничего, если эндпоинта нет */
        }
      } catch (e) {
        setErr(e.message || String(e));
      }
    })();
  }, [token, nav]);

  function onPickFile() {
    fileRef.current?.click();
  }

  async function onFileChosen(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      setLoading(true);
      const res = await uploadPhoto(file, token);
      const added = {
        id: res.id,
        photo_path: res.photo_path,
        is_primary: !!res.is_primary,
      };
      setPhotos((p) => {
        const next = [added, ...p];
        // если это первое фото — сделаем его основным и вперед
        if (next.length === 1) {
          return next.map((x, i) => ({ ...x, is_primary: i === 0 }));
        }
        // главное фото — первым
        next.sort((a, b) => (b.is_primary === true) - (a.is_primary === true));
        return next;
      });
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
      try { await setPrimary(id, token); } catch { /* ignore backend absence */ }
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
      try { await deletePhoto(id, token); } catch { /* ignore backend absence */ }
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

  const primaryPhoto = photos.find((p) => p.is_primary);
  const primaryUrl = primaryPhoto?.photo_path ? fullUrl(primaryPhoto.photo_path) : "";

  const canSearch = useMemo(() => {
    const hasPhoto = photos.length > 0;
    const hasInfo = Boolean((form.interests || "").trim() || (form.skills || "").trim() || (form.goals || "").trim());
    return hasPhoto && hasInfo;
  }, [photos, form.interests, form.skills, form.goals]);

  async function doSearch() {
    try {
      setRecErr("");
      setRecLoading(true);
      const resp = await recs(token);
      setRecItems(resp.items || []);
      if (!resp.items || !resp.items.length) {
        setRecErr("По вашим данным пока нет рекомендаций");
      }
    } catch (e) {
      setRecErr(e.message || String(e));
    } finally {
      setRecLoading(false);
    }
  }

  function doLogout() {
    logout();
    nav("/login");
  }

  return (
    <div className="container py-4">
      {/* Верхняя панель */}
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h3 className="text-white m-0">Профиль</h3>
        <button className="btn btn-outline-light" onClick={doLogout}>Выйти</button>
      </div>

      {err && <div className="alert alert-danger">{err}</div>}

      {/* Карточка пользователя */}
      <div className="card bg-dark text-white mb-4">
        <div className="card-body">
          <div className="d-flex align-items-center gap-3">
            <div style={{ width: 72, height: 72, borderRadius: "50%", overflow: "hidden", border: "3px solid #26de50" }}>
              <img
                src={primaryUrl || "https://via.placeholder.com/150?text=No+Photo"}
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

      {/* Фото-сетка + добавление */}
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
                {/* Оверлей кнопок */}
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
          {/* Плитка-заглушка для добавления фоток кликом */}
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

      {/* Поля профиля (локально; бэк — когда появится эндпоинт) */}
      <div className="card bg-dark text-white mb-3">
        <div className="card-body">
          <div className="row g-3">
            <div className="col-md-6">
              <label className="form-label text-white-50">Город</label>
              <input
                className="form-control bg-secondary-subtle text-white border-0"
                value={form.city}
                onChange={(e)=>setForm({...form, city: e.target.value})}
              />
            </div>
            <div className="col-md-6">
              <label className="form-label text-white-50">Возраст</label>
              <input
                className="form-control bg-secondary-subtle text-white border-0"
                value={form.age}
                onChange={(e)=>setForm({...form, age: e.target.value})}
              />
            </div>
            <div className="col-12">
              <label className="form-label text-white-50">О себе</label>
              <textarea
                rows={3}
                className="form-control bg-secondary-subtle text-white border-0"
                value={form.bio}
                onChange={(e)=>setForm({...form, bio: e.target.value})}
              />
            </div>
            <div className="col-md-4">
              <label className="form-label text-white-50">Навыки</label>
              <input
                className="form-control bg-secondary-subtle text-white border-0"
                placeholder="python, sql…"
                value={form.skills}
                onChange={(e)=>setForm({...form, skills: e.target.value})}
              />
            </div>
            <div className="col-md-4">
              <label className="form-label text-white-50">Интересы</label>
              <input
                className="form-control bg-secondary-subtle text-white border-0"
                placeholder="спорт, кино…"
                value={form.interests}
                onChange={(e)=>setForm({...form, interests: e.target.value})}
              />
            </div>
            <div className="col-md-4">
              <label className="form-label text-white-50">Цели</label>
              <input
                className="form-control bg-secondary-subtle text-white border-0"
                placeholder="друзья, проекты…"
                value={form.goals}
                onChange={(e)=>setForm({...form, goals: e.target.value})}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Кнопка поиска и результаты */}
      <div className="card bg-dark text-white mb-5">
        <div className="card-body">
          <div className="d-flex flex-column flex-md-row gap-2 align-items-start align-items-md-center justify-content-between mb-3">
            <div className="text-white-50">Заполните интересы/навыки/цели и добавьте фото, затем нажмите поиск.</div>
            <button className="btn btn-success fw-semibold" disabled={!canSearch || recLoading} onClick={doSearch}>
              {recLoading ? "Ищем…" : "Искать людей"}
            </button>
          </div>
          {recErr && <div className="alert alert-warning py-2">{recErr}</div>}
          {!!recItems.length && (
            <div className="row g-3">
              {recItems.map((it, idx) => (
                <div className="col-12 col-md-6 col-lg-4" key={it.user?.id || idx}>
                  <div className="card bg-black text-white h-100">
                    <div className="card-body d-flex gap-3">
                      <div style={{ width: 64, height: 64, borderRadius: "8px", overflow: "hidden", flex: "0 0 64px", border: "2px solid #26de50" }}>
                        <img src={it.user?.photo_path ? fullUrl(it.user.photo_path) : (primaryUrl || "https://via.placeholder.com/150?text=No+Photo")}
                             alt=""
                             style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                      </div>
                      <div className="flex-grow-1">
                        <div className="d-flex justify-content-between align-items-start">
                          <div>
                            <div className="fw-bold">{it.user?.name || "—"}</div>
                            <div className="text-secondary small">{it.user?.city || "—"}</div>
                          </div>
                          <span className="badge text-bg-success">{Math.round((it.score || 0) * 100)}%</span>
                        </div>
                        {(it.shared_interests?.length || it.shared_skills?.length) ? (
                          <div className="mt-2 d-flex flex-wrap gap-1">
                            {it.shared_interests?.slice(0,3).map((t)=> (
                              <span key={`i-${t}`} className="badge text-bg-secondary">{t}</span>
                            ))}
                            {it.shared_skills?.slice(0,3).map((t)=> (
                              <span key={`s-${t}`} className="badge text-bg-secondary">{t}</span>
                            ))}
                          </div>
                        ) : null}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Нижняя навигация с аватаркой */}
      <nav className="navbar fixed-bottom bg-dark-subtle" style={{borderTop: "1px solid #222"}}>
        <div className="container d-flex justify-content-around">
          <BottomIcon label="Анкеты" active />
          <BottomIcon label="Лайки" />
          <BottomIcon label="Сообщения" />
          <BottomIcon label="Встречи" />
          <BottomIcon label="Профиль" avatarUrl={primaryUrl} />
        </div>
      </nav>
    </div>
  );
}

function BottomIcon({ label, active, avatarUrl }) {
  return (
    <div className="text-center" style={{ color: active ? "#26de50" : "#bbb", fontWeight: 600 }}>
      {avatarUrl ? (
        <img
          src={avatarUrl}
          alt=""
          style={{ width: 22, height: 22, borderRadius: "50%", objectFit: "cover", border: "2px solid #26de50" }}
        />
      ) : (
        <div style={{ fontSize: 18 }}>♥</div>
      )}
      <div style={{ fontSize: 12 }}>{label}</div>
    </div>
  );
}
