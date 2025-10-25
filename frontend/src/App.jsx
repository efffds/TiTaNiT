import { BrowserRouter, Routes, Route, Link, Navigate } from "react-router-dom";
import Login from "./pages/Login.jsx";
import Signup from "./pages/Signup.jsx";
import Profile from "./pages/Profile.jsx";

export default function App() {
  return (
    <BrowserRouter>
      <nav className="navbar navbar-dark bg-black sticky-top">
        <div className="container">
          <span className="navbar-brand fw-bold">TiTi</span>
          <div className="d-flex gap-3">
            <Link className="nav-link text-success fw-semibold" to="/login">Войти</Link>
            <Link className="nav-link text-success fw-semibold" to="/signup">Регистрация</Link>
          </div>
        </div>
      </nav>

      <Routes>
        <Route path="/" element={<Navigate to="/signup" replace />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/login" element={<Login />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="*" element={<Navigate to="/signup" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
