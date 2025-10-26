// src/api.js
const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

// ===== Local fallback storage for profile =====
const LS_PROFILE_KEY = "titanit:profile";

function saveProfileLocal(data) {
  localStorage.setItem(LS_PROFILE_KEY, JSON.stringify(data || {}));
  return { ...data, _local: true };
}

function loadProfileLocal() {
  const raw = localStorage.getItem(LS_PROFILE_KEY);
  try { return raw ? { ...JSON.parse(raw), _local: true } : { _local: true }; }
  catch { return { _local: true }; }
}

function authHeaders(token) {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function handle(res) {
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}: ${text || "Request failed"}`);
  }
  const ct = res.headers.get("content-type") || "";
  return ct.includes("application/json") ? res.json() : {};
}

// ===== auth =====
export async function signup(payload) {
  const res = await fetch(`${API}/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handle(res);
}

export async function login(payload) {
  const res = await fetch(`${API}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handle(res);
}

export async function me(token) {
  const res = await fetch(`${API}/users/me`, {
    headers: { ...authHeaders(token) },
  });
  return handle(res);
}

// ===== photos (мягкий фолбэк на пустой список/OK) =====
export async function listPhotos(token) {
  try {
    const res = await fetch(`${API}/profile/photos`, {
      headers: { ...authHeaders(token) },
    });
    if (!res.ok) {
      if (res.status === 404 || res.status === 405) return { items: [] };
      const text = await res.text().catch(() => "");
      throw new Error(`${res.status} ${res.statusText}: ${text || "Request failed"}`);
    }
    return res.json();
  } catch {
    return { items: [] };
  }
}

export async function uploadPhoto(file, token) {
  const fd = new FormData();
  fd.append("file", file);
  try {
    const res = await fetch(`${API}/profile/photos`, {
      method: "POST",
      headers: { ...authHeaders(token) },
      body: fd,
    });
    if (!res.ok) {
      if (res.status === 404 || res.status === 405) return { ok: true }; // просто игнорируем
      const text = await res.text().catch(() => "");
      throw new Error(`${res.status} ${res.statusText}: ${text || "Request failed"}`);
    }
    return res.json().catch(() => ({}));
  } catch {
    return { ok: true };
  }
}

export async function setPrimary(photoId, token) {
  try {
    const res = await fetch(`${API}/profile/photos/${photoId}/set_primary`, {
      method: "PUT",
      headers: { ...authHeaders(token) },
    });
    if (!res.ok && !(res.status === 404 || res.status === 405)) {
      const text = await res.text().catch(() => "");
      throw new Error(`${res.status} ${res.statusText}: ${text || "Request failed"}`);
    }
    return { ok: true };
  } catch {
    return { ok: true };
  }
}

export async function deletePhoto(photoId, token) {
  try {
    const res = await fetch(`${API}/profile/photos/${photoId}`, {
      method: "DELETE",
      headers: { ...authHeaders(token) },
    });
    if (!res.ok && !(res.status === 404 || res.status === 405)) {
      const text = await res.text().catch(() => "");
      throw new Error(`${res.status} ${res.statusText}: ${text || "Request failed"}`);
    }
    return { ok: true };
  } catch {
    return { ok: true };
  }
}

// ===== profile (синхронизируется с localStorage, если сервера нет) =====
export async function getProfile(token) {
  try {
    const res = await fetch(`${API}/profile`, {
      headers: { "Accept": "application/json", ...authHeaders(token) },
    });
    if (!res.ok) {
      if ([404, 405, 500].includes(res.status)) return loadProfileLocal();
      const text = await res.text().catch(() => "");
      throw new Error(`${res.status} ${res.statusText}: ${text || "Request failed"}`);
    }
    const data = await res.json().catch(() => ({}));
    saveProfileLocal(data);
    return data;
  } catch {
    return loadProfileLocal();
  }
}

export async function saveProfile(data, token) {
  try {
    const res = await fetch(`${API}/profile`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", ...authHeaders(token) },
      body: JSON.stringify(data || {}),
    });
    if (!res.ok) {
      if ([404, 405, 500].includes(res.status)) return saveProfileLocal(data);
      const text = await res.text().catch(() => "");
      throw new Error(`${res.status} ${res.statusText}: ${text || "Request failed"}`);
    }
    const saved = await res.json().catch(() => (data || {}));
    saveProfileLocal(saved);
    return saved;
  } catch {
    return saveProfileLocal(data);
  }
}
