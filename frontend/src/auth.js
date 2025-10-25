export const getToken = () => localStorage.getItem("token") || "";
export const setToken = (t) => t && localStorage.setItem("token", t);
export const clearToken = () => localStorage.removeItem("token");
