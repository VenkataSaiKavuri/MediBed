import React, { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { authAPI } from "../api/client";

export default function VerifyOtp() {
  const location = useLocation();
  const navigate = useNavigate();
  const phoneFromSignup = location.state?.phone_number || "";

  const [phoneNumber, setPhoneNumber] = useState(phoneFromSignup);
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);

  const handleVerify = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);
    try {
      const { data } = await authAPI.verifyOTP(phoneNumber, code, "signup");
      setSuccess(data.message);
      setTimeout(() => navigate("/login"), 1200);
    } catch (err) {
      setError(err.response?.data?.message || "Verification failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setError("");
    setSuccess("");
    setResending(true);
    try {
      await authAPI.requestOTP(phoneNumber, "signup");
      setSuccess("New OTP sent.");
    } catch {
      setError("Couldn't resend OTP. Try again shortly.");
    } finally {
      setResending(false);
    }
  };

  return (
    <div className="auth-container">
      <h1>Verify your phone</h1>
      <p className="subtitle">Enter the 6-digit code we sent to your phone.</p>

      <form onSubmit={handleVerify}>
        <div className="form-group">
          <label>Phone number</label>
          <input value={phoneNumber} onChange={(e) => setPhoneNumber(e.target.value)} required />
        </div>
        <div className="form-group">
          <label>OTP code</label>
          <input
            value={code}
            onChange={(e) => setCode(e.target.value)}
            maxLength={6}
            placeholder="123456"
            required
          />
        </div>

        {error && <p className="error-text">{error}</p>}
        {success && <p className="success-text">{success}</p>}

        <button className="primary-btn" type="submit" disabled={loading}>
          {loading ? "Verifying..." : "Verify"}
        </button>
      </form>

      <p className="switch-link">
        Didn't get a code?{" "}
        <a href="#" onClick={handleResend} style={{ pointerEvents: resending ? "none" : "auto" }}>
          {resending ? "Sending..." : "Resend OTP"}
        </a>
      </p>
    </div>
  );
}
