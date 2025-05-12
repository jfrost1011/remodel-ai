"use client"

import { AlertCircle, RefreshCw } from "lucide-react"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"

interface ApiErrorProps {
  title?: string
  message: string
  onRetry?: () => void
}

export function ApiError({ title = "Error", message, onRetry }: ApiErrorProps) {
  return (
    <Alert variant="destructive" className="my-4">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>{title}</AlertTitle>
      <AlertDescription className="flex flex-col gap-2">
        <p>{message}</p>
        {onRetry && (
          <Button variant="outline" size="sm" onClick={onRetry} className="self-start mt-2 flex items-center gap-2">
            <RefreshCw className="h-3 w-3" />
            Try Again
          </Button>
        )}
      </AlertDescription>
    </Alert>
  )
}
