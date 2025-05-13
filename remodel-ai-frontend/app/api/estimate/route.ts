import { NextResponse } from "next/server"
export async function POST(request: Request) {
  try {
    const body = await request.json()
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
    const response = await fetch(`${backendUrl}/api/v1/estimate/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    })
    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`)
    }
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error("Error processing estimate request:", error)
    return NextResponse.json({ 
      error: "Failed to process request",
      message: error instanceof Error ? error.message : "Unknown error"
    }, { status: 500 })
  }
}
