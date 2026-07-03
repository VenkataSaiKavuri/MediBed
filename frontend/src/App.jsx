import React from "react";
import { Navigate, Route, BrowserRouter as Router, Routes } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
import { AuthProvider } from "./context/AuthContext.jsx";
import Login from "./pages/Login.jsx";
import Signup from "./pages/Signup.jsx";
import VerifyOtp from "./pages/VerifyOtp.jsx";
import HospitalDetail from "./pages/HospitalDetail.jsx";
import HospitalAdminDashboard from "./pages/dashboard/HospitalAdminDashboard.jsx";
import PatientDashboard from "./pages/dashboard/PatientDashboard.jsx";

export default function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/verify-otp" element={<VerifyOtp />} />

          <Route
            path="/dashboard/patient"
            element={
              <ProtectedRoute allowedRoles={["patient"]}>
                <PatientDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/hospitals/:id"
            element={
              <ProtectedRoute allowedRoles={["patient"]}>
                <HospitalDetail />
              </ProtectedRoute>
            }
          />

          <Route
            path="/dashboard/hospital-admin"
            element={
              <ProtectedRoute allowedRoles={["hospital_admin"]}>
                <HospitalAdminDashboard />
              </ProtectedRoute>
            }
          />
          {/* /dashboard/platform-admin comes when we build the fraud dashboard, Day 19 */}
        </Routes>
      </Router>
    </AuthProvider>
  );
}
