// src/components/Input.jsx
export default function Input({ label, ...rest }) {
  return (
    <div className="mb-3">
      {label && <label className="form-label text-muted">{label}</label>}
      <input className="custom-input w-100" {...rest} />
    </div>
  );
}
