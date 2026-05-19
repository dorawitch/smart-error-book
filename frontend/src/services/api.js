import axios from "axios";

const apiBase = "http://127.0.0.1:5000";

const http = axios.create({
  baseURL: apiBase,
  timeout: 12000
});

export { apiBase, http };

export async function fetchStats() {
  const { data } = await http.get("/stats");
  return data;
}

export async function fetchList(params = {}) {
  const { data } = await http.get("/list", { params });
  return data;
}

export async function uploadQuestion(formData) {
  const { data } = await http.post("/upload", formData);
  return data;
}

export async function deleteQuestion(id) {
  const { data } = await http.delete(`/delete/${id}`);
  return data;
}

export async function updateQuestion(id, payload) {
  const { data } = await http.put(`/update/${id}`, payload);
  return data;
}

export async function fetchRecommend(id, params = {}) {
  const { data } = await http.get(`/recommend/${id}`, { params });
  return data;
}
