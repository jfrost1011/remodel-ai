﻿import { NextResponse } from "next/server"
export async function POST(request: Request) {
  try {
    const body = await request.json()
    console.log("Chat API received:", body)
    // Get the backend URL from environment variable or default to localhost:8000
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
    
    // Forward the request to the backend API - note the trailing slash
    const response = await fetch(`${backendUrl}/api/v1/chat/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    })
    
    const responseText = await response.text()
    console.log(`Backend response:`, response.status, responseText.substring(0, 200))
    
    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status} - ${responseText}`)
    }
    
    const data = JSON.parse(responseText)
    return NextResponse.json(data)
  } catch (error) {
    console.error("Error processing chat request:", error)
    return NextResponse.json({
      error: "Failed to process request",
      message: error instanceof Error ? error.message : "Unknown error"
    }, { status: 500 })
  }
}

