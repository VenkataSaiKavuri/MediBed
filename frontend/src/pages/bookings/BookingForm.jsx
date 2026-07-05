import React, { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { bookingsAPI, hospitalsAPI } from "../../api/client";

function loadRazorpayScript() {
  return new Promise((resolve) => {
    if (window.Razorpay) return resolve(true);
    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.onload = () => resolve(true);
    script.onerror = () => resolve(false);
    document.body.appendChild(script);
  });
}

export default function BookingForm() {
  const { hospitalId } = useParams();
  const navigate = useNavigate();

  const [hospital, setHospital] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [payingBooking, setPayingBooking] = useState(null); // holds booking response once created, awaiting payment
  const [error, setError] = useState("");

  const [bedType, setBedType] = useState("");
  const [doctorId, setDoctorId] = useState("");
  const [scheduledTime, setScheduledTime] = useState("");
  const [conditionCategory, setConditionCategory] = useState("");

  useEffect(() => {
    hospitalsAPI
      .detail(hospitalId)
      .then(({ data }) => {
        setHospital(data);
        const firstAvailable = data.bed_inventory.find((b) => b.available_count > 0);
        if (firstAvailable) setBedType(firstAvailable.bed_type);
      })
      .catch(() => setError("Couldn't load hospital details."))
      .finally(() => setLoading(false));
  }, [hospitalId]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const payload = {
        hospital: Number(hospitalId),
        bed_type: bedType,
        condition_category: conditionCategory,
      };
      if (doctorId) payload.doctor = Number(doctorId);
      if (scheduledTime) payload.scheduled_time = new Date(scheduledTime).toISOString();

      const { data } = await bookingsAPI.create(payload);
      if (!data.id) {
        setError("Booking was created but the server response was missing an ID. Check your booking history instead.");
        return;
      }
      setPayingBooking(data); // move to the deposit-payment step instead of navigating away yet
    } catch (err) {
      const errData = err.response?.data;
      const errorText = errData ? Object.values(errData).flat().join(" ") : "Couldn't create booking. Try again.";
      if (errorText.toLowerCase().includes("upload an id document")) {
        navigate("/verify-identity");
        return;
      }
      setError(errorText);
    } finally {
      setSubmitting(false);
    }
  };

  const handleSimulatePayment = async () => {
    setError("");
    setSubmitting(true);
    try {
      await bookingsAPI.verifyPayment(payingBooking.id, {
        razorpay_payment_id: `pay_dev_${Date.now()}`,
        razorpay_signature: "",
      });
      navigate(`/bookings/${payingBooking.id}/confirmation`);
    } catch {
      setError("Simulated payment failed unexpectedly.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleRealPayment = async () => {
    setError("");
    const loaded = await loadRazorpayScript();
    if (!loaded) {
      setError("Couldn't load Razorpay checkout. Check your internet connection.");
      return;
    }
    const options = {
      key: payingBooking.razorpay_key_id,
      amount: Math.round(payingBooking.deposit_amount * 100),
      currency: "INR",
      name: "MedBeds",
      description: `Deposit for ${payingBooking.bed_type} bed booking`,
      order_id: payingBooking.razorpay_order_id,
      handler: async (response) => {
        try {
          await bookingsAPI.verifyPayment(payingBooking.id, {
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_signature: response.razorpay_signature,
          });
          navigate(`/bookings/${payingBooking.id}/confirmation`);
        } catch {
          setError("Payment succeeded but verification failed. Contact support with your payment ID.");
        }
      },
      theme: { color: "#2563eb" },
    };
    const rzp = new window.Razorpay(options);
    rzp.open();
  };

  if (loading) return <p style={{ textAlign: "center", marginTop: 80 }}>Loading...</p>;
  if (!hospital) return <p style={{ textAlign: "center", marginTop: 80, color: "#dc2626" }}>{error}</p>;

  // --- Step 2: booking created, now collect the deposit ---
  if (payingBooking) {
    return (
      <div className="auth-container" style={{ maxWidth: 480, textAlign: "center" }}>
        <div style={{ fontSize: 36, marginBottom: 8 }}>💳</div>
        <h1 style={{ fontSize: 20 }}>Refundable Deposit Required</h1>
        <p className="subtitle">
          A ₹{payingBooking.deposit_amount} refundable hold secures your request and is fully
          refunded if the hospital confirms and you show up, or if it's cancelled/rejected.
          It's only forfeited on a no-show.
        </p>

        {error && <p className="error-text">{error}</p>}

        {payingBooking.is_stub_payment ? (
          <>
            <div style={{ padding: 10, background: "#fef3c7", borderRadius: 8, fontSize: 12, color: "#92400e", marginBottom: 14 }}>
              Dev mode: no real Razorpay keys configured yet. This simulates a successful payment.
            </div>
            <button className="primary-btn" onClick={handleSimulatePayment} disabled={submitting}>
              {submitting ? "Processing..." : `Simulate Payment (₹${payingBooking.deposit_amount})`}
            </button>
          </>
        ) : (
          <button className="primary-btn" onClick={handleRealPayment} disabled={submitting}>
            Pay ₹{payingBooking.deposit_amount} with Razorpay
          </button>
        )}
      </div>
    );
  }

  // --- Step 1: booking details form ---
  const availableBedTypes = hospital.bed_inventory.filter((b) => b.available_count > 0);
  const onDutyDoctors = hospital.doctors.filter((d) => d.is_on_duty);

  return (
    <div className="auth-container" style={{ maxWidth: 480 }}>
      <Link to={`/hospitals/${hospitalId}`} style={{ fontSize: 13, color: "#2563eb", textDecoration: "none" }}>
        ← Back to {hospital.name}
      </Link>

      <h1 style={{ fontSize: 20, marginTop: 12 }}>Book a bed</h1>
      <p className="subtitle">{hospital.name} — {hospital.city}</p>

      {availableBedTypes.length === 0 ? (
        <div style={{ padding: 14, background: "#fef2f2", borderRadius: 8, color: "#b91c1c", fontSize: 14 }}>
          No beds are currently available at this hospital. Try another hospital or check back later.
        </div>
      ) : (
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Bed type</label>
            <select value={bedType} onChange={(e) => setBedType(e.target.value)} required>
              {availableBedTypes.map((b) => (
                <option key={b.id} value={b.bed_type}>
                  {b.bed_type} ({b.available_count} available)
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Preferred doctor (optional)</label>
            <select value={doctorId} onChange={(e) => setDoctorId(e.target.value)}>
              <option value="">No preference</option>
              {onDutyDoctors.map((d) => (
                <option key={d.id} value={d.id}>{d.name} — {d.specialty}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Preferred date/time (optional)</label>
            <input type="datetime-local" value={scheduledTime} onChange={(e) => setScheduledTime(e.target.value)} />
          </div>

          <div className="form-group">
            <label>Reason / condition (optional)</label>
            <input
              placeholder="e.g. post-surgery recovery"
              value={conditionCategory}
              onChange={(e) => setConditionCategory(e.target.value)}
            />
          </div>

          {error && <p className="error-text">{error}</p>}

          <p style={{ fontSize: 12, color: "#999", marginTop: -6, marginBottom: 14 }}>
            A small refundable deposit will be required on the next step to confirm this is a genuine request.
          </p>

          <button className="primary-btn" type="submit" disabled={submitting}>
            {submitting ? "Submitting request..." : "Continue to Deposit"}
          </button>
        </form>
      )}
    </div>
  );
}
