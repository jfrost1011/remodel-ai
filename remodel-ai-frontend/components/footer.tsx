"use client"

import { useState, useEffect } from "react"
import { CheckCircle, XCircle, AlertCircle, Wifi, WifiOff } from "lucide-react"
import { cn } from "@/lib/utils"
import { useApiStatus } from "@/hooks/use-api-status"

export function Footer() {
  const { status, lastChecked, checkApi } = useApiStatus()
  const [online, setOnline] = useState(true)

  // Monitor internet connection
  useEffect(() => {
    const handleOnline = () => setOnline(true)
    const handleOffline = () => setOnline(false)

    window.addEventListener("online", handleOnline)
    window.addEventListener("offline", handleOffline)

    return () => {
      window.removeEventListener("online", handleOnline)
      window.removeEventListener("offline", handleOffline)
    }
  }, [])

  // Format last checked time
  const formatLastChecked = () => {
    if (!lastChecked) return "Never"

    const now = new Date()
    const diff = now.getTime() - lastChecked.getTime()

    // If less than a minute ago
    if (diff < 60000) {
      return "Just now"
    }

    // If less than an hour ago
    if (diff < 3600000) {
      const minutes = Math.floor(diff / 60000)
      return `${minutes} minute${minutes !== 1 ? "s" : ""} ago`
    }

    // Otherwise show time
    return lastChecked.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
  }

  return (
    <footer className="border-t py-2 px-4 text-xs text-muted-foreground">
      <div className="container mx-auto flex flex-col sm:flex-row justify-between items-center gap-2">
        <div>© {new Date().getFullYear()} RemodelAI Estimator. All rights reserved.</div>

        <div className="flex items-center gap-4">
          {/* Internet connection status */}
          <div className="flex items-center gap-1">
            {online ? <Wifi className="h-3 w-3 text-green-500" /> : <WifiOff className="h-3 w-3 text-red-500" />}
            <span>{online ? "Online" : "Offline"}</span>
          </div>

          {/* API status indicator */}
          <div className="flex items-center gap-1">
            <button
              onClick={checkApi}
              className="flex items-center gap-1 hover:underline"
              aria-label="Check API status"
            >
              {status === "up" && <CheckCircle className="h-3 w-3 text-green-500" />}
              {status === "down" && <XCircle className="h-3 w-3 text-red-500" />}
              {status === "degraded" && <AlertCircle className="h-3 w-3 text-yellow-500" />}
              {status === "unknown" && <AlertCircle className="h-3 w-3 text-gray-500" />}

              <span
                className={cn(
                  status === "up" && "text-green-600",
                  status === "down" && "text-red-600",
                  status === "degraded" && "text-yellow-600",
                  status === "unknown" && "text-gray-600",
                )}
              >
                API:{" "}
                {status === "up"
                  ? "Operational"
                  : status === "down"
                    ? "Offline"
                    : status === "degraded"
                      ? "Degraded"
                      : "Unknown"}
              </span>
            </button>
            <span className="text-gray-400 ml-1">(Checked: {formatLastChecked()})</span>
          </div>
        </div>
      </div>
    </footer>
  )
}
