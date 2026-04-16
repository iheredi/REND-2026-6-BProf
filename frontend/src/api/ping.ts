import http from "./_http_client";

interface PingResponse {
  msg: string;
}

export const ping = async () => {
  const res = await http.get<PingResponse>("/ping");
  return res;
};
