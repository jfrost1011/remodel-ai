const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
// Helper function to convert camelCase to snake_case
function toSnakeCase(str: string): string {
  return str.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);
}
// Helper function to convert object keys from camelCase to snake_case
function convertKeysToSnakeCase(obj: any): any {
  if (obj === null || typeof obj !== 'object') return obj;
  if (Array.isArray(obj)) {
    return obj.map(convertKeysToSnakeCase);
  }
  const converted: any = {};
  for (const key in obj) {
    const snakeKey = toSnakeCase(key);
    converted[snakeKey] = convertKeysToSnakeCase(obj[key]);
  }
  return converted;
}
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
    // Convert camelCase to snake_case for the API
    const convertedDetails = convertKeysToSnakeCase(projectDetails);
    const response = await fetch(`${API_BASE_URL}/api/v1/estimate/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ project_details: convertedDetails }),
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
// Export the functions that the app expects
export async function sendChatMessage(
  message: string,
  projectDetails?: any,
  accessToken?: string | null,
): Promise<{
  response: string
  estimateData?: any
  estimateId?: string
}> {
  const result = await api.chat(message);
  return {
    response: result.message,
    estimateData: result.estimate_data,
    estimateId: result.estimate_id
  };
}
export async function getEstimate(
  details: any,
  accessToken?: string | null
): Promise<{
  response: string
  estimateData: any
  estimateId: string
}> {
  const result = await api.createEstimate(details);
  return {
    response: result.message || "Estimate created successfully",
    estimateData: result,
    estimateId: result.estimate_id
  };
}
export async function exportEstimatePDF(estimateId: string): Promise<Blob> {
  const result = await api.exportPDF(estimateId);
  // Fetch the PDF from the URL returned by the API
  const pdfResponse = await fetch(result.file_url);
  if (!pdfResponse.ok) {
    throw new Error('Failed to download PDF');
  }
  return pdfResponse.blob();
}
// Export the api object as default
export default api;
