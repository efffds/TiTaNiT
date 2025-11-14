// src/components/Card.jsx
export default function Card({ title, children, className = '' }) {
  return (
    <div className={`app-card ${className}`}>
      {title && <h3 className="section-title">{title}</h3>}
      {children}
    </div>
  );
}
