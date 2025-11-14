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

export async function me(token) {
  const res = await fetch(`${API}/users/me`, {
    headers: { ...authHeaders(token) },
  });
  return handle(res);
}
export async function login(payload) {
  const res = await fetch(`${API}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  
  if (!res.ok) {
    let errorMessage = "Неверный email или пароль";
    
    try {
      const errorData = await res.json();
      
      if (res.status === 422) {
        // Обработка ошибок валидации (например, невалидный email)
        errorMessage = "Пожалуйста, введите корректный email адрес";
      } else if (res.status === 401) {
        errorMessage = "Неверный email или пароль";
      } else if (errorData.detail) {
        // Если detail - массив (как в случае 422), берем первое сообщение
        if (Array.isArray(errorData.detail) && errorData.detail.length > 0) {
          const firstError = errorData.detail[0];
          if (firstError.msg && firstError.loc && firstError.loc.includes("email")) {
            errorMessage = "Пожалуйста, введите корректный email адрес";
          } else {
            errorMessage = firstError.msg || "Ошибка в данных";
          }
        } else {
          errorMessage = errorData.detail;
        }
      }
    } catch {
      errorMessage = `Ошибка ${res.status}`;
    }
    
    throw new Error(errorMessage);
  }
  
  return await res.json();
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
      if (res.status === 404 || res.status === 405) return { ok: true };
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

// ===== swipe / matches =====
export async function swipe(token, targetUserId, action) {
  const res = await fetch(`${API}/swipe/`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(token) },
    body: JSON.stringify({ target_user_id: targetUserId, action }),
  });
  return handle(res);
}

export async function matches(token) {
  const res = await fetch(`${API}/swipe/matches`, { headers: { ...authHeaders(token) } });
  return handle(res);
}

// ===== users =====
export async function getUserById(token, userId) {
  const res = await fetch(`${API}/users/${userId}`, { headers: { ...authHeaders(token) } });
  return handle(res);
}

// ===== chat =====
export async function listConversations(token) {
  const res = await fetch(`${API}/chat/conversations`, { headers: { ...authHeaders(token) } });
  return handle(res);
}

export async function openChat(token, targetUserId) {
  const res = await fetch(`${API}/chat/open`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(token) },
    body: JSON.stringify({ target_user_id: targetUserId }),
  });
  return handle(res);
}

export async function listMessages(token, conversationId) {
  const res = await fetch(`${API}/chat/${conversationId}/messages`, { headers: { ...authHeaders(token) } });
  return handle(res);
}

export async function sendMessage(token, conversationId, body) {
  const res = await fetch(`${API}/chat/${conversationId}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(token) },
    body: JSON.stringify({ body }),
  });
  return handle(res);
}

// ===== recommendations =====
export async function recs(token, { interests, skills, goals } = {}) {
  try {
    const q = new URLSearchParams();
    if (interests) q.set("interests", String(interests));
    if (skills) q.set("skills", String(skills));
    if (goals) q.set("goals", String(goals));
    const url = `${API}/recommendations/${q.toString() ? `?${q.toString()}` : ""}`;
    const res = await fetch(url, { headers: { ...authHeaders(token) } });
    if (!res.ok) {
      if ([404,405,500].includes(res.status)) return { items: [] };
      const text = await res.text().catch(() => "");
      throw new Error(`${res.status} ${res.statusText}: ${text || "Request failed"}`);
    }
    return res.json();
  } catch {
    return { items: [] };
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
