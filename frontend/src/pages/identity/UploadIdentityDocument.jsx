import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { authAPI } from "../../api/client";

export default function UploadIdentityDocument() {
  const navigate = useNavigate();
  const [documentType, setDocumentType] = useState("aadhaar");
  const [nameOnDocument, setNameOnDocument] = useState("");
  const [file, setFile] = useState(null);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (!file) {
      setError("Please select a file to upload.");
      return;
    }
    setSubmitting(true);
    try {
      const formData = new FormData();
      formData.append("document_type", documentType);
      formData.append("name_on_document", nameOnDocument);
      formData.append("encrypted_file", file);
      await authAPI.uploadIdentityDocument(formData);
      navigate(-1); // back to wherever they were trying to book from
    } catch (err) {
      const data = err.response?.data;
      setError(data ? Object.values(data).flat().join(" ") : "Upload failed. Try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-container">
      <h1>Verify your identity</h1>
      <p className="subtitle">
        A one-time step to help prevent fraudulent bookings. Your document is encrypted and only
        visible to you and platform administrators reviewing flagged cases.
      </p>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Document type</label>
          <select value={documentType} onChange={(e) => setDocumentType(e.target.value)}>
            <option value="aadhaar">Aadhaar Card</option>
            <option value="passport">Passport</option>
          </select>
        </div>

        <div className="form-group">
          <label>Full name exactly as it appears on the document</label>
          <input value={nameOnDocument} onChange={(e) => setNameOnDocument(e.target.value)} required />
        </div>

        <div className="form-group">
          <label>Upload document (image or PDF)</label>
          <input
            type="file"
            accept="image/*,application/pdf"
            onChange={(e) => setFile(e.target.files[0])}
            required
          />
        </div>

        {error && <p className="error-text">{error}</p>}

        <button className="primary-btn" type="submit" disabled={submitting}>
          {submitting ? "Uploading..." : "Upload & Continue"}
        </button>
      </form>
    </div>
  );
}
