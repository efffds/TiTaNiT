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

export async function swipe(token, targetUserId, action /* 'like' | 'dislike' */) {
  return asJson(await fetch(`${API_URL}/swipe/`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ target_user_id: targetUserId, action })
  }));
}

// --- Likes & matches ---
export async function matches(token) {
  return asJson(await fetch(`${API_URL}/swipe/matches`, {
    headers: { Authorization: `Bearer ${token}` }
  }));
}

// --- Users ---
export async function getUserById(token, userId) {
  return asJson(await fetch(`${API_URL}/users/${userId}`, {
    headers: { Authorization: `Bearer ${token}` }
  }));
}

// --- Chat ---
export async function listConversations(token) {
  return asJson(await fetch(`${API_URL}/chat/conversations`, {
    headers: { Authorization: `Bearer ${token}` }
  }));
}

export async function openChat(token, targetUserId) {
  return asJson(await fetch(`${API_URL}/chat/open`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ target_user_id: targetUserId })
  }));
}

export async function listMessages(token, conversationId) {
  return asJson(await fetch(`${API_URL}/chat/${conversationId}/messages`, {
    headers: { Authorization: `Bearer ${token}` }
  }));
}

export async function sendMessage(token, conversationId, body) {
  return asJson(await fetch(`${API_URL}/chat/${conversationId}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ body })
  }));
}
