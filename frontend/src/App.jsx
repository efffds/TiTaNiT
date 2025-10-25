import { BrowserRouter, Routes, Route, Link, Navigate } from "react-router-dom";
import Login from "./pages/Login.jsx";
import Signup from "./pages/Signup.jsx";
import Profile from "./pages/Profile.jsx";

export default function App() {
  return (
    <BrowserRouter>
      <nav style={styles.nav}>
        <div />
        <div style={{display:"flex", gap:16}}>
          <Link to="/login" style={styles.link}>Войти</Link>
          <Link to="/signup" style={styles.link}>Регистрация</Link>
        </div>
      </nav>

      <Routes>
        <Route path="/" element={<Navigate to="/signup" replace />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/login" element={<Login />} />
        <Route path="/profile" element={<Profile />} /> {/* ← новый маршрут */}
        {/* если кто-то пойдёт на другие маршруты */}
        <Route path="*" element={<Navigate to="/signup" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

const styles = {
  nav: {
    display: "flex",
    justifyContent: "space-between",
    padding: "12px 16px",
    background: "#0b0b0b",
    borderBottom: "1px solid #1e1e1e",
    position: "sticky",
    top: 0,
    zIndex: 10,
  },
  link: {
    color: "#7dd87d",
    textDecoration: "none",
    fontWeight: 600
  }
};
