import http from "./_http_client";

const TOKEN_KEY = "token";
const USER_KEY = "user";
const ROLE_KEY = "role";

export const saveAuth = (data) => {
  localStorage.setItem(TOKEN_KEY, data.access_token);
  localStorage.setItem(USER_KEY, data.user);
  localStorage.setItem(ROLE_KEY, data.role);
};

export const getToken = () => localStorage.getItem(TOKEN_KEY);

export const logout = () => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem(ROLE_KEY);
};

export const login = async (email, password) => {
  return await http.post("/login", {
    email,
    password,
  });
};

export const me = () => {
  return http.get("/me");
};
