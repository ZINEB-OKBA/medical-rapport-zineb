// src/services/api.js
const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(method, path, body = null) {
  const opts = {
    method,
    headers: { "Content-Type": "application/json" },
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(`${BASE_URL}${path}`, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Erreur serveur");
  }
  return res.json();
}

export const api = {
  startSession: () => request("POST", "/sessions/start"),
  startConsultation: (thread_id, patient_info) =>
    request("POST", "/consultation/start", { thread_id, patient_info }),
  resumeConsultation: (thread_id, response, response_type, question_index) =>
    request("POST", "/consultation/resume", {
      thread_id, response, response_type, question_index,
    }),
  getState: (thread_id) => request("GET", `/consultation/${thread_id}`),
  getReport: (thread_id) => request("GET", `/consultation/${thread_id}/report`),
};
