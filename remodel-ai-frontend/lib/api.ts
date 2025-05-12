// This file contains utility functions for API communication

import { toast } from "@/components/ui/use-toast"

/**
 * Send a message to the chat API
 * @param message The user's message
 * @param projectDetails Optional project details to include with the message
 * @param accessToken Optional access token for authentication
 * @returns The AI response
 */
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

    // Add authorization header if access token is provided
    if (accessToken) {
      headers["Authorization"] = `Bearer ${accessToken}`
    }

    const response = await fetch("/api/chat", {
      method: "POST",
      headers,
      body: JSON.stringify({
        message,
        projectDetails,
      }),
    })

    if (!response.ok) {
      // Handle different error status codes
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

    return await response.json()
  } catch (error) {
    console.error("Error sending chat message:", error)
    throw error
  }
}

/**
 * Send project details to get an estimate
 * @param projectDetails The project details
 * @param accessToken Optional access token for authentication
 * @returns The estimate data
 */
export async function getEstimate(
  projectDetails: any,
  accessToken?: string | null,
): Promise<{
  response: string
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

    // Add authorization header if access token is provided
    if (accessToken) {
      headers["Authorization"] = `Bearer ${accessToken}`
    }

    const response = await fetch("/api/chat", {
      method: "POST",
      headers,
      body: JSON.stringify({
        message: "Generate estimate",
        projectDetails,
        requestType: "estimate",
      }),
    })

    if (!response.ok) {
      // Handle different error status codes
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

    return await response.json()
  } catch (error) {
    console.error("Error getting estimate:", error)
    throw error
  }
}
