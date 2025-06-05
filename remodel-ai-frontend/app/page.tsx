"use client"

import { useState } from "react"
import { Navbar } from "@/components/navbar"
import { ChatInterface } from "@/components/chat-interface"
import { ProjectDetailsForm } from "@/components/project-details-form"
import { AboutModal } from "@/components/about-modal"
import { EstimateReport } from "@/components/estimate-report"
import { sendMessage, getEstimate, analyzeImage } from "@/lib/api"
import { Footer } from "@/components/footer"
import { ApiError } from "@/components/api-error"
import { useAuth } from "@/components/auth-provider"

// Define the Message type
interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  imageUrl?: string
}

// Define the ProjectDetails type
export interface ProjectDetails {
  projectType: string
  propertyType: string
  address?: string
  city: string
  state: string
  squareFootage?: string
  additionalDetails?: string
}

// Define the CostBreakdown type
interface CostBreakdown {
  total: number
  labor: number
  materials: number
  permits: number
  other: number
}

export default function Home() {
  const { getAccessToken, isAuthenticated } = useAuth()
  const [isProjectDetailsOpen, setIsProjectDetailsOpen] = useState(false)
  const [isAboutOpen, setIsAboutOpen] = useState(false)
  const [showEstimateReport, setShowEstimateReport] = useState(false)
  const [sessionId, setSessionId] = useState<string | undefined>(undefined)
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content:
        "Hello! I'm your AI construction estimator. I can help you get an estimate for your remodeling project. Would you like to provide details about your project now?",
    },
  ])
  const [projectDetails, setProjectDetails] = useState<ProjectDetails>({
    projectType: "",
    propertyType: "",
    address: "",
    city: "",
    state: "",
    squareFootage: "",
    additionalDetails: "",
  })
  const [costBreakdown, setCostBreakdown] = useState<CostBreakdown>({
    total: 0,
    labor: 0,
    materials: 0,
    permits: 0,
    other: 0,
  })
  const [timeline, setTimeline] = useState("")
  const [confidence, setConfidence] = useState(0)
  const [estimateId, setEstimateId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [apiError, setApiError] = useState<string | null>(null)

  // Function to reset the state for a new estimate
  const handleNewEstimate = () => {
    setShowEstimateReport(false)
    setSessionId(undefined)
    setCostBreakdown({
      total: 0,
      labor: 0,
      materials: 0,
      permits: 0,
      other: 0,
    })
    setProjectDetails({
      projectType: "",
      propertyType: "",
      address: "",
      city: "",
      state: "",
      squareFootage: "",
      additionalDetails: "",
    })
    setMessages([
      {
        id: Date.now().toString(),
        role: "assistant",
        content:
          "Hello! I'm your AI construction estimator. I can help you get an estimate for your remodeling project. Would you like to provide details about your project now?",
      },
    ])
    setApiError(null)
  }

  const handleSendMessage = async (message: string, imageData?: { url: string; base64: string }) => {
    if (!message.trim() && !imageData) return
    
    console.log('handleSendMessage called with:', { 
      hasMessage: !!message, 
      hasImage: !!imageData,
      messagePreview: message?.substring(0, 50) 
    });
    
    // Add user message to chat (with image if provided)
    const newUserMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: message || "Uploaded an image for analysis",
      imageUrl: imageData?.url, // Add image URL to message if present
    }
    setMessages((prev) => [...prev, newUserMessage])
    setIsLoading(true)
    setApiError(null)
    
    try {
      // Get access token if authenticated
      const accessToken = isAuthenticated ? await getAccessToken() : null
      
      let response: string
      let estimateData: any
      let currentSessionId: string | undefined = sessionId // Use existing sessionId
      
      // Check if we have an image to analyze
      if (imageData) {
        console.log('Processing image upload...');
        console.log('Current sessionId before image analysis:', currentSessionId);
        
        // First, analyze the image - FIXED: Pass currentSessionId
        const imageAnalysis = await analyzeImage(imageData.base64, currentSessionId)
        console.log('Image analysis received:', imageAnalysis);
        
        // Use the session ID from image analysis if we don't have one
        const imageSessionId = imageAnalysis.sessionId;
        if (!currentSessionId && imageSessionId) {
          currentSessionId = imageSessionId;
          setSessionId(currentSessionId); // Update state immediately
          console.log('Updated currentSessionId to:', currentSessionId);
        }
        
        // FIXED: Create a more contextual message
        // Count images based on what WE'VE uploaded in this session
        const imageCount = messages.filter(m => 
          m.role === 'user' && 
          m.imageUrl
        ).length;
        
        console.log('Frontend image count:', {
          messagesLength: messages.length,
          imageCount: imageCount,
          userMessages: messages.filter(m => m.role === 'user').map(m => m.content)
        });
        const messageToSend = `Here's ${imageCount > 0 ? 'another image' : 'an image'} for you to look at.`;
        console.log('Message to send:', messageToSend);
        
        // Send the message with the full image analysis
        const result = await sendMessage(
          messageToSend,
          (costBreakdown?.total ?? 0) > 0 ? projectDetails : undefined,
          accessToken,
          currentSessionId,
          imageAnalysis.analysis,  // Send the full analysis
          undefined,
          imageData.base64
        )
        
        response = result.response
        estimateData = result.estimateData
        
        // Update session ID if returned
        if (result.sessionId && !sessionId) {
          setSessionId(result.sessionId)
        }
      } else {
        // Regular text message without image
        console.log('Processing text message...');
        const result = await sendMessage(
          message,
          (costBreakdown?.total ?? 0) > 0 ? projectDetails : undefined,
          accessToken,
          currentSessionId
        )
        
        response = result.response
        estimateData = result.estimateData
        
        // Update session ID if returned
        if (result.sessionId && !sessionId) {
          setSessionId(result.sessionId)
        }
      }
      
      console.log('AI response received:', response?.substring(0, 100));
      
      // Add AI response to chat
      const newAiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response,
      }
      setMessages((prev) => [...prev, newAiMessage])
      
      // If the API returned estimate data, update the state
      if (estimateData) {
        setCostBreakdown(estimateData.costBreakdown)
        setEstimateId(estimateData?.estimateId || `temp-${Date.now()}`)
        setTimeline(estimateData.timeline)
        setConfidence(estimateData.confidence)
      }
    } catch (error) {
      // Set API error state with more specific error message
      const errorMessage = error instanceof Error ? error.message : "Failed to get response from the server";
      setApiError(errorMessage)
      console.error("Error sending message:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleProjectDetailsSubmit = async (details: ProjectDetails) => {
    setProjectDetails(details)
    setIsProjectDetailsOpen(false)
    setIsLoading(true)
    setApiError(null)

    try {
      // Get access token if authenticated
      const accessToken = isAuthenticated ? await getAccessToken() : null

      // Get estimate from API
      const { response, estimateData } = await getEstimate(details, accessToken)

      // Update state with estimate data
      setCostBreakdown(estimateData.costBreakdown)
      setEstimateId(estimateData?.estimateId || `temp-${Date.now()}`)
      setTimeline(estimateData.timeline)
      setConfidence(estimateData.confidence)

      // Add AI response to chat
      const estimateMessage: Message = {
        id: Date.now().toString(),
        role: "assistant",
        content: response,
      }

      setMessages((prev) => [...prev, estimateMessage])
    } catch (error) {
      // Set API error state with more specific error message
      const errorMessage = error instanceof Error ? error.message : "Failed to get estimate from the server";
      setApiError(errorMessage)
      console.error("Error getting estimate:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleViewEstimateReport = () => {
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: "Yes, I'd like to see the detailed estimate report.",
    }

    // Add AI response
    const aiResponse: Message = {
      id: (Date.now() + 1).toString(),
      role: "assistant",
      content:
        "Great! I've generated a detailed estimate report for you below. You can view the cost breakdown, timeline, and recommendations. You can also download it as a PDF to save or share.",
    }

    setMessages((prev) => [...prev, userMessage, aiResponse])
    setShowEstimateReport(true)
  }

  const handleCloseEstimateReport = () => {
    setShowEstimateReport(false)
  }

  const handleRetry = () => {
    setApiError(null)
    // If we have project details, retry getting an estimate
    if (projectDetails.projectType && projectDetails.city && projectDetails.state) {
      handleProjectDetailsSubmit(projectDetails)
    }
  }

  return (
    <div className="flex flex-col min-h-screen">
      <Navbar onAboutClick={() => setIsAboutOpen(true)} onNewEstimate={handleNewEstimate} />

      <main className="flex-1 container mx-auto p-4 flex flex-col gap-4">
        <div className="flex flex-col md:flex-row gap-4">
          <ChatInterface
            messages={messages}
            isLoading={isLoading}
            onSendMessage={handleSendMessage}
            onProjectDetailsClick={() => setIsProjectDetailsOpen(true)}
            onViewEstimateReport={handleViewEstimateReport}
            showEstimateButton={(costBreakdown?.total ?? 0) > 0 && !showEstimateReport}
          />
        </div>

        {/* Display API error if there is one */}
        {apiError && <ApiError title="API Communication Error" message={apiError} onRetry={handleRetry} />}

        {showEstimateReport && (
          <EstimateReport
            projectDetails={projectDetails}
            costBreakdown={costBreakdown}
            timeline={timeline}
            estimateId={estimateId}
            confidence={confidence}
            onClose={handleCloseEstimateReport}
            onNewEstimate={handleNewEstimate}
          />
        )}

        {isProjectDetailsOpen && (
          <ProjectDetailsForm
            isOpen={isProjectDetailsOpen}
            onClose={() => setIsProjectDetailsOpen(false)}
            onSubmit={handleProjectDetailsSubmit}
            initialValues={projectDetails}
          />
        )}
      </main>

      <Footer />
      <AboutModal isOpen={isAboutOpen} onClose={() => setIsAboutOpen(false)} />
    </div>
  )
}
