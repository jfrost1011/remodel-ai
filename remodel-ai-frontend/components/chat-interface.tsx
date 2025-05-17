"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Send, Ruler, FileText } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"
import { LoadingIndicator } from "@/components/loading-indicator"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
}

interface ChatInterfaceProps {
  messages: Message[]
  isLoading: boolean
  onSendMessage: (message: string) => void
  onProjectDetailsClick: () => void
  onViewEstimateReport: () => void
  showEstimateButton: boolean
}

export function ChatInterface({
  messages,
  isLoading,
  onSendMessage,
  onProjectDetailsClick,
  onViewEstimateReport,
  showEstimateButton,
}: ChatInterfaceProps) {
  const [input, setInput] = useState("")
  const [isSending, setIsSending] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim() && !isSending) {
      setIsSending(true)
      try {
        await onSendMessage(input)
        setInput("")
      } finally {
        setIsSending(false)
      }
    }
  }

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  return (
    <div
      className="flex-1 flex flex-col min-h-[500px] h-[70vh] sm:h-[500px] md:h-[calc(100vh-10rem)] border rounded-lg overflow-hidden bg-white"
    >
      <div className="p-4 border-b">
        <h1 className="text-2xl font-bold">Construction Estimator</h1>
        <p className="text-muted-foreground">
          Get AI-powered estimates for your remodeling project
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={cn(
              "flex",
              message.role === "user" ? "justify-end" : "justify-start"
            )}
          >
            <div
              className={cn(
                "max-w-[80%] rounded-lg p-3",
                message.role === "user"
                  ? "bg-emerald-500 text-white"
                  : "bg-gray-100 text-gray-800"
              )}
            >
              {message.content.split("\n").map((line, i) => (
                <p key={i} className={i > 0 ? "mt-2" : ""}>
                  {line}
                </p>
              ))}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="max-w-[80%] rounded-lg p-3 bg-gray-100">
              <div className="flex space-x-2">
                <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" />
                <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce [animation-delay:0.2s]" />
                <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce [animation-delay:0.4s]" />
              </div>
            </div>
          </div>
        )}

        {showEstimateButton && (
          <div className="flex justify-center my-4">
            <Button
              onClick={onViewEstimateReport}
              style={{ backgroundColor: "#10B981" }}
              className="flex items-center gap-2"
            >
              <FileText className="h-4 w-4" />
              View Detailed Estimate Report
            </Button>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 border-t">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            className="flex-1"
            disabled={isLoading || isSending}
          />
          <Button
            type="submit"
            size="icon"
            style={{ backgroundColor: "#10B981" }}
            disabled={isLoading || isSending || !input.trim()}
          >
            {isSending ? (
              <LoadingIndicator size="sm" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={onProjectDetailsClick}
            className="flex items-center gap-2 whitespace-nowrap"
            disabled={isLoading || isSending}
          >
            <Ruler className="h-4 w-4" />
            <span className="hidden sm:inline">Project Details</span>
          </Button>
        </form>
      </div>
    </div>
  )
}
