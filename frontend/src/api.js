const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function asJson(res) {
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}: ${await res.text()}`);
  return res.json();
}

export async function signup({ email, password, name, city }) {
  return asJson(await fetch(`${API_URL}/auth/signup`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, name, city })
  }));
}

export async function login({ email, password }) {
  return asJson(await fetch(`${API_URL}/auth/login`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  }));
}

export async function me(token) {
  return asJson(await fetch(`${API_URL}/users/me`, {
    headers: { Authorization: `Bearer ${token}` }
  }));
}

export async function recs(token) {
  return asJson(await fetch(`${API_URL}/recommendations`, {
    headers: { Authorization: `Bearer ${token}` }
  }));
}
