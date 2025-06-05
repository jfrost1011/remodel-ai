import { NextRequest, NextResponse } from "next/server"

const API_BASE_URL = process.env.BACKEND_URL || "http://localhost:8000"

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    const response = await fetch(`${API_BASE_URL}/api/analyze-image`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error("Image analysis error:", error)
    return NextResponse.json(
      { error: "Failed to analyze image" },
      { status: 500 }
    )
  }
} 