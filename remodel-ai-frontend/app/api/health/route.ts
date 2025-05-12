import { NextResponse } from "next/server"

// This is a mock API health endpoint
export async function GET() {
  // Simulate random API health status for demo purposes
  // In a real app, this would check actual backend health
  const random = Math.random()

  // 80% chance of being up, 10% degraded, 10% down
  if (random < 0.8) {
    return NextResponse.json({ status: "up", message: "API is operational" })
  } else if (random < 0.9) {
    // Simulate a slow response for degraded status
    await new Promise((resolve) => setTimeout(resolve, 1500))
    return NextResponse.json({ status: "degraded", message: "API is experiencing slowdowns" })
  } else {
    // Simulate a server error
    return NextResponse.json({ status: "down", message: "API is currently unavailable" }, { status: 500 })
  }
}
