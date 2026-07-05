import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

const client = axios.create({ baseURL: API_BASE_URL });

// Attach access token to every request if we have one
client.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-refresh on 401 once, then retry the original request
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem("refresh_token");
      if (refreshToken) {
        try {
          const { data } = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, {
            refresh: refreshToken,
          });
          localStorage.setItem("access_token", data.access);
          originalRequest.headers.Authorization = `Bearer ${data.access}`;
          return client(originalRequest);
        } catch {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  signup: (payload) => client.post("/auth/signup/", payload),
  requestOTP: (phone_number, purpose = "signup") =>
    client.post("/auth/otp/request/", { phone_number, purpose }),
  verifyOTP: (phone_number, code, purpose = "signup") =>
    client.post("/auth/otp/verify/", { phone_number, code, purpose }),
  login: (username, password) => client.post("/auth/login/", { username, password }),
  me: () => client.get("/auth/me/"),
  registerFcmToken: (fcm_token) => client.post("/auth/fcm-token/", { fcm_token }),
  uploadIdentityDocument: (formData) =>
    client.post("/auth/identity-documents/", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  myIdentityDocuments: () => client.get("/auth/identity-documents/mine/"),
};

export const hospitalsAPI = {
  list: (params = {}) => client.get("/hospitals/", { params }),
  detail: (id) => client.get(`/hospitals/${id}/`),
  mine: () => client.get("/hospitals/mine/"),

  beds: {
    create: (payload) => client.post("/hospitals/mine/beds/", payload),
    update: (id, payload) => client.patch(`/hospitals/mine/beds/${id}/`, payload),
    delete: (id) => client.delete(`/hospitals/mine/beds/${id}/`),
  },
  doctors: {
    create: (payload) => client.post("/hospitals/mine/doctors/", payload),
    update: (id, payload) => client.patch(`/hospitals/mine/doctors/${id}/`, payload),
    delete: (id) => client.delete(`/hospitals/mine/doctors/${id}/`),
  },
  equipment: {
    create: (payload) => client.post("/hospitals/mine/equipment/", payload),
    update: (id, payload) => client.patch(`/hospitals/mine/equipment/${id}/`, payload),
    delete: (id) => client.delete(`/hospitals/mine/equipment/${id}/`),
  },
};

export const bookingsAPI = {
  create: (payload) => client.post("/bookings/", payload),
  mine: () => client.get("/bookings/mine/"),
  detail: (id) => client.get(`/bookings/${id}/`),
  hospitalList: (status) => client.get("/bookings/hospital/", { params: status ? { status } : {} }),
  transition: (id, status, note = "") => client.patch(`/bookings/${id}/transition/`, { status, note }),
  verifyPayment: (id, payload) => client.post(`/bookings/${id}/verify-payment/`, payload),
};

export const fraudAPI = {
  summary: () => client.get("/admin-panel/summary/"),
  flaggedUsers: () => client.get("/admin-panel/flagged-users/"),
  unflagUser: (id) => client.post(`/admin-panel/flagged-users/${id}/unflag/`),
  suspiciousBookings: () => client.get("/admin-panel/suspicious-bookings/"),
  clearBookingFlag: (id) => client.post(`/admin-panel/suspicious-bookings/${id}/clear/`),
  pendingDocuments: () => client.get("/admin-panel/pending-documents/"),
  reviewDocument: (id, action) => client.post(`/admin-panel/pending-documents/${id}/review/`, { action }),
};

export default client;
