import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { authAPI } from "../api/client";

export default function Signup() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    username: "",
    email: "",
    phone_number: "",
    password: "",
    first_name: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await authAPI.signup(form);
      // Signup automatically triggers an OTP send server-side — go straight to verification
      navigate("/verify-otp", { state: { phone_number: form.phone_number } });
    } catch (err) {
      const data = err.response?.data;
      setError(data ? Object.values(data).flat().join(" ") : "Signup failed. Try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <h1>Create your account</h1>
      <p className="subtitle">Book hospital beds fast — verified and fraud-checked.</p>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Full name</label>
          <input name="first_name" value={form.first_name} onChange={handleChange} required />
        </div>
        <div className="form-group">
          <label>Username</label>
          <input name="username" value={form.username} onChange={handleChange} required />
        </div>
        <div className="form-group">
          <label>Email</label>
          <input type="email" name="email" value={form.email} onChange={handleChange} required />
        </div>
        <div className="form-group">
          <label>Phone number</label>
          <input
            name="phone_number"
            placeholder="+91XXXXXXXXXX"
            value={form.phone_number}
            onChange={handleChange}
            required
          />
        </div>
        <div className="form-group">
          <label>Password</label>
          <input
            type="password"
            name="password"
            value={form.password}
            onChange={handleChange}
            minLength={8}
            required
          />
        </div>

        {error && <p className="error-text">{error}</p>}

        <button className="primary-btn" type="submit" disabled={loading}>
          {loading ? "Creating account..." : "Sign up"}
        </button>
      </form>

      <p className="switch-link">
        Already have an account? <Link to="/login">Log in</Link>
      </p>
    </div>
  );
}
