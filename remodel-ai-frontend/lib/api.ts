const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
// Helper function to convert camelCase to snake_case
function toSnakeCase(str: string): string {
  return str.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);
}
// Map frontend values to backend enum values
const PROJECT_TYPE_MAP: Record<string, string> = {
  'Kitchen Remodel': 'kitchen_remodel',
  'Bathroom Remodel': 'bathroom_remodel',
  'Room Addition': 'room_addition',
  'Whole House Remodel': 'whole_house_remodel',
  'Accessory Dwelling Unit': 'accessory_dwelling_unit',
  'Landscaping': 'landscaping',
  'Pool Installation': 'pool_installation',
  'Garage Conversion': 'garage_conversion',
  'Roofing': 'roofing',
  'Flooring': 'flooring'
};
const PROPERTY_TYPE_MAP: Record<string, string> = {
  'SFR': 'single_family',
  'Single Family Residence': 'single_family',
  'Condo': 'condo',
  'Townhouse': 'townhouse',
  'Multi Family': 'multi_family'
};
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
// Transform project details to match backend expectations
function transformProjectDetails(details: any): any {
  const transformed = convertKeysToSnakeCase(details);
  // Map project type
  if (transformed.project_type) {
    transformed.project_type = PROJECT_TYPE_MAP[details.projectType] || details.projectType.toLowerCase().replace(/ /g, '_');
  }
  // Map property type
  if (transformed.property_type) {
    transformed.property_type = PROPERTY_TYPE_MAP[details.propertyType] || details.propertyType.toLowerCase().replace(/ /g, '_');
  }
  // Ensure square_footage is a number
  if (transformed.square_footage !== undefined) {
    transformed.square_footage = transformed.square_footage ? parseFloat(transformed.square_footage) : 0;
  }
  return transformed;
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
    // Transform the details to match backend expectations
    const transformedDetails = transformProjectDetails(projectDetails);
    const response = await fetch(`${API_BASE_URL}/api/v1/estimate/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ project_details: transformedDetails }),
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
