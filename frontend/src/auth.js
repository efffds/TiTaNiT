// src/auth.js

// Сохранить токен
export function saveToken(token) {
  localStorage.setItem("token", token);
}

// Получить токен
export function getToken() {
  return localStorage.getItem("token");
}

// Удалить токен (логаут)
export function logout() {
  localStorage.removeItem("token");
}
