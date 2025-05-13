// This file contains utility functions for API communication
import { toast } from "@/components/ui/use-toast"
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
export async function sendChatMessage(
  message: string,
  projectDetails?: any,
  accessToken?: string | null,
): Promise<{
  response: string
  estimateData?: {
    costBreakdown: {
      labor: number
      materials: number
      permits: number
      other: number
      total: number
    }
    timeline: string
    confidence: number
  }
}> {
  try {
    const headers: HeadersInit = {
      "Content-Type": "application/json",
    }
    if (accessToken) {
      headers["Authorization"] = `Bearer ${accessToken}`
    }
    const response = await fetch(`${API_BASE_URL}/api/v1/chat`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        content: message,
        role: "user",
      }),
    })
    if (!response.ok) {
      if (response.status === 401 || response.status === 403) {
        toast({
          title: "Authentication Error",
          description: "Please log in to continue.",
          variant: "destructive",
        })
        throw new Error("Authentication error")
      } else if (response.status === 429) {
        toast({
          title: "Rate Limit Exceeded",
          description: "You've made too many requests. Please try again later.",
          variant: "destructive",
        })
        throw new Error("Rate limit exceeded")
      } else {
        toast({
          title: "API Error",
          description: `Error ${response.status}: ${response.statusText}`,
          variant: "destructive",
        })
        throw new Error(`API error: ${response.status}`)
      }
    }
    const data = await response.json()
    return {
      response: data.message,
      estimateData: data.metadata
    }
  } catch (error) {
    console.error("Error sending chat message:", error)
    throw error
  }
}
export async function getEstimate(
  projectDetails: any,
  accessToken?: string | null,
): Promise<{
  response: string
  estimateId: string
  estimateData: {
    costBreakdown: {
      labor: number
      materials: number
      permits: number
      other: number
      total: number
    }
    timeline: string
    confidence: number
  }
}> {
  try {
    const headers: HeadersInit = {
      "Content-Type": "application/json",
    }
    if (accessToken) {
      headers["Authorization"] = `Bearer ${accessToken}`
    }
    // Transform frontend field names to backend format
    const backendDetails = {
      project_type: projectDetails.projectType.toLowerCase().replace(/\s+/g, '_'),
      property_type: projectDetails.propertyType === "SFR" ? "single_family" : 
                    projectDetails.propertyType === "2-4 Units" ? "multi_family" : 
                    projectDetails.propertyType === "Condo" ? "condo" : 
                    projectDetails.propertyType.toLowerCase(),
      city: projectDetails.city,
      state: projectDetails.state,
      square_footage: projectDetails.squareFootage ? parseFloat(projectDetails.squareFootage) : 200,
      additional_details: projectDetails.additionalDetails || ""
    }
    const response = await fetch(`${API_BASE_URL}/api/v1/estimate`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        project_details: backendDetails,
      }),
    })
    if (!response.ok) {
      if (response.status === 401 || response.status === 403) {
        toast({
          title: "Authentication Error",
          description: "Please log in to continue.",
          variant: "destructive",
        })
        throw new Error("Authentication error")
      } else if (response.status === 429) {
        toast({
          title: "Rate Limit Exceeded",
          description: "You've made too many requests. Please try again later.",
          variant: "destructive",
        })
        throw new Error("Rate limit exceeded")
      } else {
        toast({
          title: "API Error",
          description: `Error ${response.status}: ${response.statusText}`,
          variant: "destructive",
        })
        throw new Error(`API error: ${response.status}`)
      }
    }
    const data = await response.json()
    return {
      response: "Estimate generated successfully",
      estimateId: data.estimate_id, // Now returning the estimate_id
      estimateData: {
        costBreakdown: {
          labor: data.cost_breakdown.labor,
          materials: data.cost_breakdown.materials,
          permits: data.cost_breakdown.permits,
          other: data.cost_breakdown.other,
          total: data.cost_breakdown.total
        },
        timeline: `${data.timeline.total_days} days`,
        confidence: data.confidence_score
      }
    }
  } catch (error) {
    console.error("Error getting estimate:", error)
    throw error
  }
}
export async function exportEstimatePDF(
  estimateId: string,
  accessToken?: string | null
): Promise<string> {
  try {
    const headers: HeadersInit = {
      "Content-Type": "application/json",
    }
    if (accessToken) {
      headers["Authorization"] = `Bearer ${accessToken}`
    }
    const response = await fetch(`${API_BASE_URL}/api/v1/export`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        estimate_id: estimateId,
        format: "pdf",
        include_breakdown: true,
        include_similar_projects: true
      }),
    })
    if (!response.ok) {
      throw new Error(`Export error: ${response.status}`)
    }
    const data = await response.json()
    // Download the PDF
    const downloadUrl = `${API_BASE_URL}${data.file_url}`
    const downloadResponse = await fetch(downloadUrl)
    if (!downloadResponse.ok) {
      throw new Error(`Download error: ${downloadResponse.status}`)
    }
    // Create blob and download
    const blob = await downloadResponse.blob()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement("a")
    link.href = url
    link.setAttribute("download", data.download_name)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    return data.download_name
  } catch (error) {
    console.error("Error exporting PDF:", error)
    throw error
  }
}
