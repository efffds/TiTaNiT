import { Link, Outlet, useNavigate } from "react-router-dom";
import { getToken, clearToken } from "./auth";

export default function App() {
  const nav = useNavigate();
  const token = getToken();
  return (
    <div style={{maxWidth: 760, margin: "32px auto", fontFamily: "system-ui, sans-serif"}}>
      <header style={{display:"flex", justifyContent:"space-between", marginBottom:16}}>
        <nav style={{display:"flex", gap:12}}>
          <Link to="/home">Home</Link>
          <Link to="/login">Login</Link>
          <Link to="/signup">Signup</Link>
        </nav>
        {token ? <button onClick={()=>{clearToken(); nav("/login");}}>Logout</button> : null}
      </header>
      <Outlet />
    </div>
  );
}