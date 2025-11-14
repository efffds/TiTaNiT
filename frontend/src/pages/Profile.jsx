import { useEffect, useRef, useState, useMemo } from "react";
import {
  me,
  listPhotos,
  uploadPhoto,
  setPrimary,
  deletePhoto,
  recs,
} from "../api";
import { getToken, logout } from "../auth";
import { useNavigate } from "react-router-dom";

import Logo from "../components/Logo";
import Card from "../components/Card";
import Input from "../components/Input";
import Btn from "../components/Btn";

/* ---------- local storage для профиля (fallback) ---------- */
const LS_PROFILE_KEY = "titanit:profile";
function saveProfileLocal(data) {
  localStorage.setItem(LS_PROFILE_KEY, JSON.stringify(data || {}));
}
function loadProfileLocal() {
  const raw = localStorage.getItem(LS_PROFILE_KEY);
  try { return raw ? JSON.parse(raw) : {}; }
  catch { return {}; }
}

/* -------------------- UI -------------------- */
export default function Profile() {
  const token = getToken();
  const nav = useNavigate();
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
  const [recLoading, setRecLoading] = useState(false);
  const [recErr, setRecErr] = useState("");
  const [recItems, setRecItems] = useState([]);

  /* ---------- автосохраняем в localStorage ---------- */
  useEffect(() => {
    if (!token) return;
    const t = setTimeout(() => saveProfileLocal(form), 500);
    return () => clearTimeout(t);
  }, [form, token]);

  /* ---------- получаем данные о пользователе и фото ---------- */
  useEffect(() => {
    if (!token) {
      nav("/login");
      return;
    }
    (async () => {
      try {
        setErr("");

        // 1️⃣ локальное кэшированное состояние
        const local = loadProfileLocal();
        if (Object.keys(local).length) setForm((f) => ({ ...f, ...local }));

        // 2️⃣ данные из бек‑энда
        const u = await me(token);
        setUser(u);
        if (u?.city) setForm((f) => ({ ...f, city: u.city }));

        // 3️⃣ фото
        try {
          const ph = await listPhotos(token);
          setPhotos(ph?.items || []);
        } catch {
          /* если эндпоинт не найден — просто оставляем пустой массив */
        }
      } catch (e) {
        setErr(e.message);
      }
    })();
  }, [token, nav]);

  /* ---------- загрузка фото ---------- */
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
      setPhotos((prev) => {
        const next = [added, ...prev];
        next.sort((a, b) => (b.is_primary === true) - (a.is_primary === true));
        return next;
      });
    } catch (e) {
      setErr(e.message);
    } finally {
      setLoading(false);
      e.target.value = "";
    }
  }

  /* ---------- установить основное фото ---------- */
  async function makePrimary(id) {
    try {
      setLoading(true);
      try { await setPrimary(id, token); } catch {}
      setPhotos((arr) => {
        const upd = arr.map((p) => ({ ...p, is_primary: p.id === id }));
        upd.sort((a, b) => (b.is_primary === true) - (a.is_primary === true));
        return upd;
      });
    } catch (e) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  }

  /* ---------- удалить фото ---------- */
  async function removePhoto(id) {
    if (!window.confirm("Удалить фото?")) return;
    try {
      setLoading(true);
      try { await deletePhoto(id, token); } catch {}
      setPhotos((p) => p.filter((x) => x.id !== id));
    } catch (e) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  }

  /* ---------- Формирование URL‑ов фотографий ---------- */
  function fullUrl(path) {
    if (!path) return "";
    return path.startsWith("http")
      ? path
      : `${import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"}/${path.replace(/^\/+/, "")}`;
  }
  const primary = photos.find((p) => p.is_primary);
  const primaryUrl = primary?.photo_path ? fullUrl(primary.photo_path) : "";

  /* ---------- Доступность кнопки “Искать” ---------- */
  const canSearch = useMemo(() => {
    const hasPhoto = photos.length > 0;
    const hasInfo =
      !!form.interests?.trim() ||
      !!form.skills?.trim() ||
      !!form.goals?.trim();
    return hasPhoto && hasInfo;
  }, [photos, form.interests, form.skills, form.goals]);

  /* ---------- Запрос рекомендаций ---------- */
  async function doSearch() {
    try {
      setRecErr("");
      setRecLoading(true);
      const resp = await recs(token);
      setRecItems(resp?.items || []);
      if (!resp?.items?.length) setRecErr("По вашим данным пока нет рекомендаций");
    } catch (e) {
      setRecErr(e.message);
    } finally {
      setRecLoading(false);
    }
  }

  function doLogout() {
    logout();
    nav("/login");
  }

  /* ---------- UI ---------- */
  return (
    <div className="container py-4">
      {/* Шапка */}
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h3 className="text-white m-0">Профиль</h3>
        <button className="btn btn-outline-light" onClick={doLogout}>
          Выйти
        </button>
      </div>

      {err && <div className="alert alert-danger">{err}</div>}

      {/* Карточка пользователя */}
      <Card>
        <div className="d-flex align-items-center gap-3">
          <div
            style={{
              width: 80,
              height: 80,
              borderRadius: "50%",
              overflow: "hidden",
              border: "3px solid var(--color-primary)",
            }}
          >
            <img
              src={
                primaryUrl ||
                "https://via.placeholder.com/150?text=No+Photo"
              }
              alt=""
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
          </div>
          <div>
            <div className="fw-bold fs-5">{user?.name || "—"}</div>
            <div className="text-muted">{form.city || "—"}</div>
          </div>
        </div>
      </Card>

      {/* Фотогалерея */}
      <Card title="Фотографии">
        <div className="d-flex align-items-center justify-content-between mb-2">
          <Btn onClick={onPickFile} disabled={loading}>
            + Добавить фото
          </Btn>
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            className="d-none"
            onChange={onFileChosen}
          />
        </div>

        <div className="row g-3">
          {photos.map((p) => (
            <div key={p.id} className="col-6 col-sm-4 col-md-3">
              <div className="position-relative">
                <img
                  src={fullUrl(p.photo_path)}
                  alt=""
                  className="img-fluid rounded"
                  style={{
                    aspectRatio: "1 / 1",
                    objectFit: "cover",
                    width: "100%",
                  }}
                />
                <div className="position-absolute top-0 end-0 p-2 d-flex gap-2">
                  <button
                    className={`btn btn-sm ${p.is_primary ? "btn-success" : "btn-outline-success"}`}
                    title="Сделать основным"
                    onClick={() => makePrimary(p.id)}
                  >
                    ★
                  </button>
                  <button
                    className="btn btn-sm btn-outline-danger"
                    title="Удалить"
                    onClick={() => removePhoto(p.id)}
                  >
                    ✕
                  </button>
                </div>
              </div>
            </div>
          ))}

          {/* Плитка‑заглушка «+» */}
          <div className="col-6 col-sm-4 col-md-3">
            <div
              className="d-flex align-items-center justify-content-center border rounded"
              style={{
                aspectRatio: "1 / 1",
                cursor: "pointer",
                background: "#151515",
              }}
              onClick={onPickFile}
            >
              <span className="fs-3 text-success">+</span>
            </div>
          </div>
        </div>
      </Card>

      {/* Форма профиля */}
      <Card title="Мой профиль">
        <div className="row g-3">
          <div className="col-md-6">
            <Input
              label="Город"
              value={form.city}
              onChange={(e) => setForm({ ...form, city: e.target.value })}
            />
          </div>
          <div className="col-md-6">
            <Input
              label="Возраст"
              type="number"
              min="0"
              value={form.age}
              onChange={(e) => setForm({ ...form, age: e.target.value })}
            />
          </div>
          <div className="col-12">
            <label className="form-label text-muted">О себе</label>
            <textarea
              rows={3}
              className="custom-input w-100"
              value={form.bio}
              onChange={(e) => setForm({ ...form, bio: e.target.value })}
            />
          </div>
          <div className="col-md-4">
            <Input
              label="Навыки"
              placeholder="python, sql…"
              value={form.skills}
              onChange={(e) => setForm({ ...form, skills: e.target.value })}
            />
          </div>
          <div className="col-md-4">
            <Input
              label="Интересы"
              placeholder="спорт, кино…"
              value={form.interests}
              onChange={(e) => setForm({ ...form, interests: e.target.value })}
            />
          </div>
          <div className="col-md-4">
            <Input
              label="Цели"
              placeholder="друзья, проекты…"
              value={form.goals}
              onChange={(e) => setForm({ ...form, goals: e.target.value })}
            />
          </div>
        </div>
      </Card>

      {/* Поиск рекомендаций */}
      <Card title="Поиск людей">
        <div className="d-flex flex-column flex-md-row align-items-start align-items-md-center justify-content-between mb-3">
          <div className="text-muted">
            Заполните интересы/навыки/цели и добавьте фото, затем нажмите поиск.
          </div>
          <Btn
            disabled={!canSearch || recLoading}
            onClick={doSearch}
            className="mt-2 mt-md-0"
          >
            {recLoading ? "Ищем…" : "Искать людей"}
          </Btn>
        </div>

        {recErr && <div className="alert alert-warning">{recErr}</div>}

        {recItems.length > 0 && (
          <div className="row g-3">
            {recItems.map((it, idx) => (
              <div key={it.user?.id || idx} className="col-12 col-md-6 col-lg-4">
                <Card>
                  <div className="d-flex gap-3 align-items-start">
                    <div
                      style={{
                        width: 64,
                        height: 64,
                        borderRadius: "8px",
                        overflow: "hidden",
                        border: "2px solid var(--color-primary)",
                      }}
                    >
                      <img
                        src={
                          it.user?.photo_path
                            ? fullUrl(it.user.photo_path)
                            : primaryUrl || "https://via.placeholder.com/150?text=No+Photo"
                        }
                        alt=""
                        style={{ width: "100%", height: "100%", objectFit: "cover" }}
                      />
                    </div>
                    <div className="flex-grow-1">
                      <div className="d-flex justify-content-between align-items-start">
                        <div>
                          <div className="fw-bold">{it.user?.name || "—"}</div>
                          <div className="text-muted small">{it.user?.city || "—"}</div>
                        </div>
                        <span className="badge bg-success">
                          {Math.round((it.score || 0) * 100)}%
                        </span>
                      </div>
                      {(it.shared_interests?.length || it.shared_skills?.length) && (
                        <div className="mt-2 d-flex flex-wrap gap-1">
                          {it.shared_interests?.slice(0, 3).map((t) => (
                            <span key={t} className="badge bg-secondary">
                              {t}
                            </span>
                          ))}
                          {it.shared_skills?.slice(0, 3).map((t) => (
                            <span key={t} className="badge bg-secondary">
                              {t}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </Card>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Нижняя навигация – теперь тоже в едином стиле */}
      <nav className="navbar fixed-bottom bottom-nav">
        <div className="container d-flex">
          <div className="nav-item active">Анкеты</div>
          <div className="nav-item">Лайки</div>
          <div className="nav-item">Сообщения</div>
          <div className="nav-item">Встречи</div>
          <div className="nav-item">
            {primaryUrl ? (
              <img
                src={primaryUrl}
                alt=""
                style={{
                  width: 22,
                  height: 22,
                  borderRadius: "50%",
                  border: "2px solid var(--color-primary)",
                }}
              />
            ) : (
              <span>♥</span>
            )}
          </div>
        </div>
      </nav>
    </div>
  );
}
