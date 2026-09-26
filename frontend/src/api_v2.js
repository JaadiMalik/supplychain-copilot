const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";


async function parseResponse(response) {
  if (!response.ok) {
    let message = `Request failed: ${response.status}`;
    try {
      const body = await response.json();
      message = body.detail || body.message || message;
    } catch {
      // Keep generic message.
    }
    throw new Error(message);
  }
  return response.json();
}


export async function resolveV2Context(question) {
  const response = await fetch(`${API_BASE_URL}/v2/context/resolve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  return parseResponse(response);
}


export async function askV2Copilot(question) {
  const response = await fetch(`${API_BASE_URL}/v2/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  return parseResponse(response);
}


export async function getV2History(limit = 20) {
  const response = await fetch(`${API_BASE_URL}/v2/history?limit=${limit}`);
  return parseResponse(response);
}


export function reportUrl(analysisId, format) {
  return `${API_BASE_URL}/v2/reports/${encodeURIComponent(analysisId)}/${format}`;
}
