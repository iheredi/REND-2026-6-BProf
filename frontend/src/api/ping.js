import http from "./_http_client";

export const ping = async () => {
  const res = await http.get("/ping");
  return res;
};
