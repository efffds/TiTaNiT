// src/components/Btn.jsx
export default function Btn({ children, ...rest }) {
  return (
    <button className="btn-primary-eco" {...rest}>
      {children}
    </button>
  );
}
