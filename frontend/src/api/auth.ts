import http from "./_http_client";
import type { AxiosResponse } from "axios";

// API response típusa loginnál
interface LoginResponse {
  access_token: string;
  user: string; 
  role: string;
}

// User adat típusa / me() hívásnál
interface MeResponse {
  id: string;
  email: string;
  name?: string;
}

const TOKEN_KEY = "token";
const USER_KEY = "user";
const ROLE_KEY = "role";

export const saveAuth = (data: LoginResponse) => {
  localStorage.setItem(TOKEN_KEY, data.access_token);
  localStorage.setItem(USER_KEY, data.user);
  localStorage.setItem(ROLE_KEY, data.role);
};

export const getToken = (): string|null => localStorage.getItem(TOKEN_KEY);

export const logout = ():void => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem(ROLE_KEY);
};

export const login = async (email:string, password:string): Promise<AxiosResponse<LoginResponse>> => {
  return await http.post("/login", {
    email,
    password,
  });
};

export const me = (): Promise<AxiosResponse<MeResponse>> => {
  return http.get<MeResponse>("/me");
};
