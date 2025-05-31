// components/chat-interface.tsx
"use client"

import type React from "react"
import { useState, useRef, useEffect } from "react"
import { Send, Ruler, FileText, Mic, MicOff, Camera } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"
import { LoadingIndicator } from "@/components/loading-indicator"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  image?: string // Add image support
}

interface ChatInterfaceProps {
  messages: Message[]
  isLoading: boolean
  onSendMessage: (message: string, image?: string) => void
  onProjectDetailsClick: () => void
  onViewEstimateReport: () => void
  showEstimateButton: boolean
}

// Voice recognition hook
function useVoiceRecognition() {
  const [isListening, setIsListening] = useState(false)
  const [transcript, setTranscript] = useState("")
  const recognitionRef = useRef<any>(null)

  useEffect(() => {
    if (typeof window !== 'undefined' && 'webkitSpeechRecognition' in window) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition
      recognitionRef.current = new SpeechRecognition()
      recognitionRef.current.continuous = false
      recognitionRef.current.interimResults = true
      recognitionRef.current.lang = 'en-US'

      recognitionRef.current.onresult = (event: any) => {
        const current = event.resultIndex
        const transcript = event.results[current][0].transcript
        setTranscript(transcript)
      }

      recognitionRef.current.onerror = () => {
        setIsListening(false)
      }

      recognitionRef.current.onend = () => {
        setIsListening(false)
      }
    }
  }, [])

  const startListening = () => {
    if (recognitionRef.current && !isListening) {
      recognitionRef.current.start()
      setIsListening(true)
      setTranscript("")
    }
  }

  const stopListening = () => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop()
      setIsListening(false)
    }
  }

  return {
    isListening,
    transcript,
    startListening,
    stopListening,
    isSupported: !!recognitionRef.current
  }
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
  const [showImageUpload, setShowImageUpload] = useState(false)
  const [uploadedImage, setUploadedImage] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  const {
    isListening,
    transcript,
    startListening,
    stopListening,
    isSupported: isVoiceSupported
  } = useVoiceRecognition()

  // Update input when voice transcript changes
  useEffect(() => {
    if (transcript) {
      setInput(transcript)
    }
  }, [transcript])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if ((input.trim() || uploadedImage) && !isSending) {
      setIsSending(true)
      try {
        await onSendMessage(input || "Uploaded an image for analysis", uploadedImage || undefined)
        setInput("")
        setUploadedImage(null)
        setShowImageUpload(false)
      } finally {
        setIsSending(false)
      }
    }
  }

  const handleVoiceClick = () => {
    if (isListening) {
      stopListening()
    } else {
      startListening()
    }
  }

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onloadend = () => {
        setUploadedImage(reader.result as string)
        setShowImageUpload(false)
      }
      reader.readAsDataURL(file)
    }
  }

  // Check for triggers to show image upload
  useEffect(() => {
    const lastMessage = messages[messages.length - 1]
    if (lastMessage?.role === 'assistant' && 
        (lastMessage.content.toLowerCase().includes('upload') || 
         lastMessage.content.toLowerCase().includes('photo'))) {
      setShowImageUpload(true)
    }
  }, [messages])

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  return (
    <div className="flex-1 flex flex-col min-h-[500px] h-[70vh] sm:h-[500px] md:h-[calc(100vh-10rem)] border rounded-lg overflow-hidden bg-white">
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
              {message.image && (
                <img 
                  src={message.image} 
                  alt="Uploaded" 
                  className="max-w-full h-auto rounded mb-2"
                  style={{ maxHeight: '200px' }}
                />
              )}
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

        {showImageUpload && (
          <div className="flex justify-center my-4">
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
              <Camera className="mx-auto h-12 w-12 text-gray-400 mb-2" />
              <p className="text-sm text-gray-600 mb-2">Upload a photo of your space</p>
              <Button
                onClick={() => fileInputRef.current?.click()}
                variant="outline"
                size="sm"
              >
                Choose Photo
              </Button>
              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                accept="image/*"
                onChange={handleImageUpload}
              />
            </div>
          </div>
        )}

        {uploadedImage && (
          <div className="flex justify-center my-4">
            <div className="relative">
              <img 
                src={uploadedImage} 
                alt="To be uploaded" 
                className="max-w-full h-auto rounded"
                style={{ maxHeight: '200px' }}
              />
              <Button
                onClick={() => setUploadedImage(null)}
                variant="destructive"
                size="sm"
                className="absolute top-2 right-2"
              >
                Remove
              </Button>
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
            placeholder={isListening ? "Listening..." : "Type or speak your message..."}
            className="flex-1"
            disabled={isLoading || isSending}
          />
          
          {/* Voice Input Button */}
          {isVoiceSupported && (
            <Button
              type="button"
              size="icon"
              variant={isListening ? "destructive" : "outline"}
              onClick={handleVoiceClick}
              disabled={isLoading || isSending}
            >
              {isListening ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
            </Button>
          )}

          {/* Camera Button */}
          <Button
            type="button"
            size="icon"
            variant="outline"
            onClick={() => fileInputRef.current?.click()}
            disabled={isLoading || isSending}
          >
            <Camera className="h-4 w-4" />
          </Button>
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            accept="image/*"
            onChange={handleImageUpload}
          />

          <Button
            type="submit"
            size="icon"
            style={{ backgroundColor: "#10B981" }}
            disabled={isLoading || isSending || (!input.trim() && !uploadedImage)}
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