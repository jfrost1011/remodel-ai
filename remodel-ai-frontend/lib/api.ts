/* --------------------------------------------------------------------------
   api.ts  ▸  Front-end API helper with simple response / blob caching
--------------------------------------------------------------------------- */

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/* ==========================================================================
   camelCase → snake_case helpers
============================================================================ */
function toSnakeCase(str: string): string {
  return str.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`);
}

function convertKeysToSnakeCase(obj: any): any {
  if (obj === null || obj === undefined) return obj;

  if (Array.isArray(obj)) return obj.map(convertKeysToSnakeCase);

  if (typeof obj !== "object") return obj;

  const converted: any = {};
  for (const key in obj) {
    const snakeKey = toSnakeCase(key);
    converted[snakeKey] = convertKeysToSnakeCase(obj[key]);
  }
  return converted;
}

/* ==========================================================================
   Value maps  (frontend-label → backend enum)
============================================================================ */
const PROJECT_TYPE_MAP: Record<string, string> = {
  "Kitchen Remodel": "kitchen_remodel",
  "Bathroom Remodel": "bathroom_remodel",
  "Room Addition": "room_addition",
  "Whole House Remodel": "whole_house_remodel",
  "Accessory Dwelling Unit": "accessory_dwelling_unit",
  ADU: "accessory_dwelling_unit",
  Landscaping: "landscaping",
  "Pool Installation": "pool_installation",
  "Garage Conversion": "garage_conversion",
  Roofing: "roofing",
  Flooring: "flooring",
};

const PROPERTY_TYPE_MAP: Record<string, string> = {
  SFR: "single_family",
  "Single Family Residence": "single_family",
  "Single Family": "single_family",
  Condo: "condo",
  Townhouse: "townhouse",
  "Multi Family": "multi_family",
  "Multi-Family": "multi_family",
};

/* Default sq-ft if user leaves it blank */
const DEFAULT_SQUARE_FOOTAGE: Record<string, number> = {
  kitchen_remodel: 150,
  bathroom_remodel: 75,
  room_addition: 300,
  whole_house_remodel: 2000,
  accessory_dwelling_unit: 600,
  landscaping: 500,
  pool_installation: 400,
  garage_conversion: 400,
  roofing: 1800,
  flooring: 1000,
};

/* ==========================================================================
   Tiny 1-hour client-side cache   (FIFO eviction optional)
============================================================================ */
const apiCache: Record<
  string,
  { data?: any; blob?: Blob; timestamp: number }
> = {};
const CACHE_EXPIRY = 60 * 60 * 1000; // 1 h

function getCachedData(key: string) {
  const entry = apiCache[key];
  return entry && Date.now() - entry.timestamp < CACHE_EXPIRY ? entry.data : null;
}

function setCachedData(key: string, data: any) {
  apiCache[key] = { data, timestamp: Date.now() };
}

function getCachedBlob(key: string) {
  const entry = apiCache[key];
  return entry && entry.blob && Date.now() - entry.timestamp < CACHE_EXPIRY
    ? entry.blob
    : null;
}

function setCachedBlob(key: string, blob: Blob) {
  apiCache[key] = { blob, timestamp: Date.now() };
}

/* ==========================================================================
   Request-payload transformer  (UI ➜ backend)
============================================================================ */
function transformProjectDetails(details: any): any {
  const transformed = convertKeysToSnakeCase(details);

  // project_type
  if (details.projectType) {
    transformed.project_type =
      PROJECT_TYPE_MAP[details.projectType] ||
      details.projectType.toLowerCase().replace(/ /g, "_");
  }

  // property_type
  if (details.propertyType) {
    transformed.property_type =
      PROPERTY_TYPE_MAP[details.propertyType] ||
      details.propertyType.toLowerCase().replace(/ /g, "_");
  }

  /* ---------- square_footage ---------- */
  if (transformed.square_footage !== undefined) {
    const sqft = parseFloat(transformed.square_footage) || 0;
    transformed.square_footage =
      sqft > 0
        ? sqft
        : DEFAULT_SQUARE_FOOTAGE[transformed.project_type] || 200;
  } else {
    transformed.square_footage =
      DEFAULT_SQUARE_FOOTAGE[transformed.project_type] || 200;
  }

  // state → uppercase
  if (transformed.state) transformed.state = transformed.state.toUpperCase();

  // prune empty optional fields
  if (!transformed.additional_details) delete transformed.additional_details;
  if (!transformed.address) delete transformed.address;

  return transformed;
}

/* ==========================================================================
   Core API wrapper  (chat • estimate • exportPDF)  with caching
============================================================================ */
const api = {
  /* --------------------------------------------------------------------- */
  async chat(message: string, sessionId?: string) {
    const lower = message.toLowerCase();
    const dynamic =
      lower.includes("cost") ||
      lower.includes("estimate") ||
      lower.includes("price") ||
      lower.includes("timeline");

    const cacheKey = `chat:${sessionId || ""}:${message}`;

    if (!dynamic) {
      const cached = getCachedData(cacheKey);
      if (cached) return cached;
    }

    const resp = await fetch(`/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        content: message,
        role: "user",
        session_id: sessionId,
      }),
    });

    if (!resp.ok) {
      throw new Error(`Chat request failed: ${await resp.text()}`);
    }

    const data = await resp.json();
    if (!dynamic) setCachedData(cacheKey, data);
    return data;
  },

  /* --------------------------------------------------------------------- */
  async createEstimate(projectDetails: any) {
    const transformed = transformProjectDetails(projectDetails);
    console.log("Sending to backend:", transformed);

    const resp = await fetch(`/api/estimate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ project_details: transformed }),
    });

    if (!resp.ok) {
      throw new Error(`Estimate creation failed: ${await resp.text()}`);
    }
    return resp.json();
  },

  /* --------------------------------------------------------------------- */
  async exportPDF(estimateId: string) {
    const cacheKey = `pdf:${estimateId}`;
    const cachedBlob = getCachedBlob(cacheKey);
    if (cachedBlob) return cachedBlob;

    const resp = await fetch(`/api/export`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ estimate_id: estimateId, format: "pdf" }),
    });

    if (!resp.ok) {
      throw new Error(`PDF export failed: ${await resp.text()}`);
    }

    const result = await resp.json();
    let pdfBlob: Blob;

    if (result.file_url) {
      const dl = await fetch(`${API_BASE_URL}${result.file_url}`);
      if (!dl.ok) throw new Error("Failed to download PDF");
      pdfBlob = await dl.blob();
    } else if (result.content) {
      // base64 → blob
      const b64 = (result.content.split(",")[1] || result.content).trim();
      const bin = atob(b64);
      const bytes = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
      pdfBlob = new Blob([bytes], { type: "application/pdf" });
    } else {
      throw new Error("No PDF content received");
    }

    setCachedBlob(cacheKey, pdfBlob);
    return pdfBlob;
  },
};

/* ==========================================================================
   High-level helpers consumed by the React app
============================================================================ */
export async function sendMessage(
  message: string,
  projectDetails?: any,
  accessToken?: string | null,
  sessionId?: string
): Promise<{
  response: string;
  estimateData?: any;
  estimateId?: string;
  sessionId: string;
}> {
  const res = await api.chat(message, sessionId);
  return {
    response: res.message,
    estimateData: res.estimate_data,
    estimateId: res.estimate_id,
    sessionId: res.session_id,
  };
}

export async function getEstimate(
  details: any,
  accessToken?: string | null
): Promise<{
  response: string;
  estimateData: any;
  estimateId: string;
}> {
  const res = await api.createEstimate(details);
  return {
    response: "Estimate created successfully",
    estimateData: {
      costBreakdown: {
        total: res.total_cost,
        labor: res.cost_breakdown?.labor || 0,
        materials: res.cost_breakdown?.materials || 0,
        permits: res.cost_breakdown?.permits || 0,
        other: res.cost_breakdown?.other || 0,
      },
      timeline: `${res.timeline?.total_days || 0} days`,
      confidence: res.confidence_score || 0.85,
    },
    estimateId: res.estimate_id,
  };
}

export async function exportEstimatePDF(estimateId: string): Promise<Blob> {
  return api.exportPDF(estimateId);
}

/* Default export (low-level API) */
export default api;
