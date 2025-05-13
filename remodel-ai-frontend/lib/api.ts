const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
export const api = {
  baseURL: API_BASE_URL,
  async chat(message: string, sessionId?: string) {
    const response = await fetch(`${API_BASE_URL}/api/v1/chat/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        content: message,
        role: 'user',
        session_id: sessionId
      }),
    });
    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Chat request failed: ${error}`);
    }
    return response.json();
  },
  async createEstimate(projectDetails: any) {
    const response = await fetch(`${API_BASE_URL}/api/v1/estimate/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ project_details: projectDetails }),
    });
    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Estimate creation failed: ${error}`);
    }
    return response.json();
  },
  async exportPDF(estimateId: string) {
    const response = await fetch(`${API_BASE_URL}/api/v1/export/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        estimate_id: estimateId,
        format: 'pdf'
      }),
    });
    if (!response.ok) {
      const error = await response.text();
      throw new Error(`PDF export failed: ${error}`);
    }
    return response.json();
  },
};
