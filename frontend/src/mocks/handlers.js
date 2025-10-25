import { http, HttpResponse } from "msw";

// простая БД в памяти
const users = [];
let currentId = 1;

function makeToken(id) {
  return btoa(`user:${id}:${Date.now()}`);
}

export const handlers = [
  // POST /auth/signup
  http.post(`${import.meta.env.VITE_API_URL}/auth/signup`, async ({ request }) => {
    const body = await request.json();
    const { email, password, name, city } = body || {};
    if (!email || !password || !name) {
      return HttpResponse.json({ detail: "email, password, name are required" }, { status: 422 });
    }
    if (users.find(u => u.email === email)) {
      return HttpResponse.json({ detail: "Email already registered" }, { status: 400 });
    }
    const user = { id: currentId++, email, name, city: city || null };
    users.push({ ...user, password }); // храним пароль в mock для логина
    return HttpResponse.json({ access_token: makeToken(user.id), token_type: "bearer" }, { status: 200 });
  }),

  // POST /auth/login
  http.post(`${import.meta.env.VITE_API_URL}/auth/login`, async ({ request }) => {
    const { email, password } = await request.json();
    const found = users.find(u => u.email === email && u.password === password);
    if (!found) {
      return HttpResponse.json({ detail: "Invalid credentials" }, { status: 401 });
    }
    return HttpResponse.json({ access_token: makeToken(found.id), token_type: "bearer" });
  }),

  // GET /users/me
  http.get(`${import.meta.env.VITE_API_URL}/users/me`, ({ request }) => {
    const auth = request.headers.get("authorization") || "";
    if (!auth.startsWith("Bearer ")) {
      return HttpResponse.json({ detail: "Not authenticated" }, { status: 401 });
    }
    // В реале токен надо валидировать. В моках вернем последнего юзера.
    const last = users.at(-1);
    if (!last) return HttpResponse.json({ detail: "No user" }, { status: 401 });
    const { password, ...safe } = last;
    return HttpResponse.json(safe);
  }),

  // GET /recommendations
  http.get(`${import.meta.env.VITE_API_URL}/recommendations`, () => {
    const items = users
      .slice(0, 5)
      .map(u => ({
        user: { id: u.id, name: u.name, email: u.email, city: u.city },
        score: Number((Math.random() * 0.5 + 0.5).toFixed(2)),
      }));
    return HttpResponse.json({ items });
  }),

  // GET /health
  http.get(`${import.meta.env.VITE_API_URL}/health`, () => {
    return HttpResponse.json({ status: "ok (mock)" });
  }),
];
