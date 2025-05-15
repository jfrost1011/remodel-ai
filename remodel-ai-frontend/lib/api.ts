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
  'ADU': 'accessory_dwelling_unit',
  'Landscaping': 'landscaping',
  'Pool Installation': 'pool_installation',
  'Garage Conversion': 'garage_conversion',
  'Roofing': 'roofing',
  'Flooring': 'flooring'
};

// Default square footage based on project type
const DEFAULT_SQUARE_FOOTAGE: Record<string, number> = {
  'kitchen_remodel': 150,
  'bathroom_remodel': 75,
  'room_addition': 300,
  'whole_house_remodel': 2000,
  'accessory_dwelling_unit': 600,
  'landscaping': 500,
  'pool_installation': 400,
  'garage_conversion': 400,
  'roofing': 1800,
  'flooring': 1000
};

const PROPERTY_TYPE_MAP: Record<string, string> = {
  'SFR': 'single_family',
  'Single Family Residence': 'single_family',
  'Single Family': 'single_family',
  'Condo': 'condo',
  'Townhouse': 'townhouse',
  'Multi Family': 'multi_family',
  'Multi-Family': 'multi_family'
};

// Helper function to convert object keys from camelCase to snake_case
function convertKeysToSnakeCase(obj: any): any {
  if (obj === null || obj === undefined) {
    return obj;
  }
  
  if (Array.isArray(obj)) {
    return obj.map(convertKeysToSnakeCase);
  }
  
  if (typeof obj !== 'object') {
    return obj;
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
  
  // Map project type - use the original value from the form, not the snake_case version
  if (details.projectType) {
    transformed.project_type = PROJECT_TYPE_MAP[details.projectType] || details.projectType.toLowerCase().replace(/ /g, '_');
  }
  
  // Map property type - use the original value from the form
  if (details.propertyType) {
    transformed.property_type = PROPERTY_TYPE_MAP[details.propertyType] || details.propertyType.toLowerCase().replace(/ /g, '_');
  }
  
  // Ensure square_footage is a valid number with smart defaults
  if (transformed.square_footage !== undefined) {
    const squareFootage = parseFloat(transformed.square_footage) || 0;
    if (squareFootage <= 0) {
      // Use project-specific default
      transformed.square_footage = DEFAULT_SQUARE_FOOTAGE[transformed.project_type] || 200;
    } else {
      transformed.square_footage = squareFootage;
    }
  } else {
    // If no square footage provided, use default based on project type
    transformed.square_footage = DEFAULT_SQUARE_FOOTAGE[transformed.project_type] || 200;
  }
  
  // Ensure state is uppercase
  if (transformed.state) {
    transformed.state = transformed.state.toUpperCase();
  }
  
  // Remove empty optional fields
  if (!transformed.additional_details) {
    delete transformed.additional_details;
  }
  
  if (!transformed.address) {
    delete transformed.address;
  }
  
  return transformed;
}

// The main API object
const api = {
  async chat(message: string, sessionId?: string) {
    const response = await fetch(`/api/chat`, {
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
    console.log('Sending to backend:', transformedDetails); // Debug log
    
    const response = await fetch(`/api/estimate`, {
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
    const response = await fetch(`/api/export`, {
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

    const result = await response.json();
    
    // Check if we have a URL or base64 data
    if (result.file_url) {
      // Download from URL
      const downloadResponse = await fetch(`${API_BASE_URL}${result.file_url}`);
      if (!downloadResponse.ok) {
        throw new Error('Failed to download PDF');
      }
      return downloadResponse.blob();
    } else if (result.content) {
      // Convert base64 to blob
      const base64Data = result.content.split(',')[1] || result.content;
      const binaryData = atob(base64Data);
      const bytes = new Uint8Array(binaryData.length);
      for (let i = 0; i < binaryData.length; i++) {
        bytes[i] = binaryData.charCodeAt(i);
      }
      return new Blob([bytes], { type: 'application/pdf' });
    } else {
      throw new Error('No PDF content received');
    }
  }
};

// High-level API functions for the frontend
export async function sendMessage(
  message: string,
  projectDetails?: any,
  accessToken?: string | null,
  sessionId?: string
): Promise<{
  response: string
  estimateData?: any
  estimateId?: string
  sessionId: string
}> {
  const result = await api.chat(message, sessionId);
  
  return {
    response: result.message,
    estimateData: result.estimate_data,
    estimateId: result.estimate_id,
    sessionId: result.session_id
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
  
  // The backend returns the full estimate response
  // We need to format it for the frontend
  return {
    response: "Estimate created successfully",
    estimateData: {
      costBreakdown: {
        total: result.total_cost,
        labor: result.cost_breakdown?.labor || 0,
        materials: result.cost_breakdown?.materials || 0,
        permits: result.cost_breakdown?.permits || 0,
        other: result.cost_breakdown?.other || 0
      },
      timeline: `${result.timeline?.total_days || 0} days`,
      confidence: result.confidence_score || 0.85
    },
    estimateId: result.estimate_id
  };
}

export async function exportEstimatePDF(estimateId: string): Promise<Blob> {
  // Just call the api.exportPDF method which already returns a blob
  return api.exportPDF(estimateId);
}

// Export the api object as default
export default api;