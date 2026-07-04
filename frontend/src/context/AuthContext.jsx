import React, { createContext, useContext, useEffect, useState } from "react";
import client, { authAPI } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchMe = async () => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setLoading(false);
      return;
    }
    try {
      const { data } = await client.get("/auth/me/");
      setUser(data);
      registerDeviceToken();
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const registerDeviceToken = () => {
    // STUB: real Firebase Cloud Messaging setup (requesting browser notification
    // permission + getToken() from the Firebase SDK) is a production-only step, since it
    // requires a real Firebase project. For local development we register a fake but
    // stable per-browser token so the whole pipeline (register -> store -> send push on
    // status change) can be exercised end-to-end. Swap this for real firebase.messaging()
    // logic before production.
    let fakeToken = localStorage.getItem("dev_fcm_token");
    if (!fakeToken) {
      fakeToken = "dev-" + Math.random().toString(36).slice(2);
      localStorage.setItem("dev_fcm_token", fakeToken);
    }
    authAPI.registerFcmToken(fakeToken).catch(() => {});
  };

  useEffect(() => {
    fetchMe();
  }, []);

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setUser(null);
    window.location.href = "/login";
  };

  return (
    <AuthContext.Provider value={{ user, loading, logout, refetch: fetchMe }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
