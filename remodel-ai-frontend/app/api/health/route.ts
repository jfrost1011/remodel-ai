import { NextResponse } from "next/server"
export async function GET() {
  try {
    // Get the backend URL from environment variable or default to localhost:8000
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
    // Call the actual backend health endpoint
    const response = await fetch(`${backendUrl}/api/v1/health`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    })
    if (!response.ok) {
      return NextResponse.json({ status: "down", message: "Backend is not responding" }, { status: 500 })
    }
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error("Error checking backend health:", error)
    return NextResponse.json({ status: "down", message: "Backend is currently unavailable" }, { status: 500 })
  }
}
