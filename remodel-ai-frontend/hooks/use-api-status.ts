"use client"

import { useState, useEffect, useCallback } from "react"

type ApiStatus = "up" | "down" | "degraded" | "unknown"

export function useApiStatus() {
  const [status, setStatus] = useState<ApiStatus>("unknown")
  const [lastChecked, setLastChecked] = useState<Date | null>(null)
  const [isChecking, setIsChecking] = useState(false)

  const checkApi = useCallback(async () => {
    if (isChecking) return

    setIsChecking(true)

    try {
      // Check API health endpoint
      const startTime = Date.now()
      const response = await fetch("/api/health", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
        cache: "no-store",
      })

      const endTime = Date.now()
      const responseTime = endTime - startTime

      if (!response.ok) {
        setStatus("down")
      } else {
        // If response time is slow, mark as degraded
        if (responseTime > 1000) {
          setStatus("degraded")
        } else {
          setStatus("up")
        }
      }
    } catch (error) {
      console.error("Error checking API status:", error)
      setStatus("down")
    } finally {
      setLastChecked(new Date())
      setIsChecking(false)
    }
  }, [isChecking])

  // Check API status on mount and every 5 minutes
  useEffect(() => {
    checkApi()

    const interval = setInterval(
      () => {
        checkApi()
      },
      5 * 60 * 1000,
    ) // 5 minutes

    return () => clearInterval(interval)
  }, [checkApi])

  return {
    status,
    lastChecked,
    checkApi,
    isChecking,
  }
}
