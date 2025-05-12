import { NextResponse } from "next/server"

// This is a mock API endpoint that simulates a FastAPI backend
// In a real application, this would be replaced with actual calls to your FastAPI backend

export async function POST(request: Request) {
  try {
    const body = await request.json()
    const { message, projectDetails, requestType } = body

    // If this is an estimate request with project details
    if (requestType === "estimate" && projectDetails) {
      return handleEstimateRequest(projectDetails)
    }

    // If this is a regular chat message
    return handleChatMessage(message, projectDetails)
  } catch (error) {
    console.error("Error processing request:", error)
    return NextResponse.json({ error: "Failed to process request" }, { status: 500 })
  }
}

// Handle estimate requests
function handleEstimateRequest(projectDetails: any) {
  // Calculate estimate based on project details
  const estimateData = calculateEstimate(projectDetails)

  // Format the cost for display
  const formattedCost = estimateData.costBreakdown.total.toLocaleString()

  // Generate response message
  const response = `Based on your ${projectDetails.projectType} project for a ${
    projectDetails.propertyType
  } in ${projectDetails.city}, ${projectDetails.state} with ${
    projectDetails.squareFootage || "unspecified"
  } square feet, I estimate the cost to be approximately $${formattedCost}.

The breakdown is roughly:
- Labor: $${estimateData.costBreakdown.labor.toLocaleString()}
- Materials: $${estimateData.costBreakdown.materials.toLocaleString()}
- Permits: $${estimateData.costBreakdown.permits.toLocaleString()}
- Other costs: $${estimateData.costBreakdown.other.toLocaleString()}

The project would take approximately ${estimateData.timeline} to complete.

Would you like to see a detailed estimate report with cost breakdown and recommendations? I can generate a downloadable PDF for you.`

  return NextResponse.json({
    response,
    estimateData,
  })
}

// Handle regular chat messages
function handleChatMessage(message: string, projectDetails: any) {
  // If we have project details, we can provide more context-aware responses
  if (projectDetails && Object.keys(projectDetails).length > 0) {
    // This would normally use an LLM to generate a response based on the message and project details
    return NextResponse.json({
      response: `I'm analyzing your ${projectDetails.projectType} project. What specific aspect would you like to know more about?`,
    })
  }

  // Simple rule-based responses for demo purposes
  // In a real app, this would use an LLM like GPT-4o-mini
  if (message.toLowerCase().includes("hello") || message.toLowerCase().includes("hi")) {
    return NextResponse.json({
      response: "Hello! I'm your AI construction estimator. How can I help you today?",
    })
  }

  if (
    message.toLowerCase().includes("cost") ||
    message.toLowerCase().includes("price") ||
    message.toLowerCase().includes("estimate")
  ) {
    return NextResponse.json({
      response:
        "I'd be happy to help with your estimate. To provide an accurate estimate, I'll need some details about your project. Could you please click the 'Project Details' button to fill out the necessary information?",
    })
  }

  if (message.toLowerCase().includes("kitchen")) {
    return NextResponse.json({
      response:
        "Kitchen remodels are one of our specialties! To give you an accurate estimate for your kitchen remodel, I'll need some details about your project. Could you please click the 'Project Details' button to fill out the necessary information?",
    })
  }

  // Default response
  return NextResponse.json({
    response:
      "I'd be happy to help with your estimate. To provide an accurate estimate, I'll need some details about your project. Could you please click the 'Project Details' button to fill out the necessary information?",
  })
}

// Calculate estimate based on project details
function calculateEstimate(details: any) {
  // This is a simplified estimation logic
  // In a real app, this would be a more complex calculation or API call
  let basePrice = 0
  const laborPercentage = 0.45 // 45% of total
  const materialsPercentage = 0.35 // 35% of total
  const permitsPercentage = 0.05 // 5% of total
  const otherPercentage = 0.15 // 15% of total
  let timelineWeeks = "2-3 weeks"
  const confidenceLevel = 85

  // Adjust base price based on project type
  switch (details.projectType) {
    case "Kitchen Remodel":
      basePrice = 40000
      timelineWeeks = "4-6 weeks"
      break
    case "Bathroom Remodel":
      basePrice = 20000
      timelineWeeks = "2-3 weeks"
      break
    case "Basement Remodel":
      basePrice = 30000
      timelineWeeks = "3-5 weeks"
      break
    case "Room Addition":
      basePrice = 50000
      timelineWeeks = "6-8 weeks"
      break
    case "Whole House Renovation":
      basePrice = 150000
      timelineWeeks = "12-16 weeks"
      break
    case "Deck/Patio":
      basePrice = 15000
      timelineWeeks = "1-2 weeks"
      break
    case "Roofing":
      basePrice = 12000
      timelineWeeks = "1 week"
      break
    case "Flooring":
      basePrice = 8000
      timelineWeeks = "1 week"
      break
    case "ADU":
      basePrice = 120000
      timelineWeeks = "12-16 weeks"
      break
    case "Garage Conversion":
      basePrice = 35000
      timelineWeeks = "4-6 weeks"
      break
    default:
      basePrice = 25000
      timelineWeeks = "3-4 weeks"
  }

  // Adjust for property type
  if (details.propertyType === "Condo") {
    basePrice *= 0.9 // 10% less for condos due to smaller spaces
  } else if (details.propertyType === "2-4 Units") {
    basePrice *= 1.2 // 20% more for multi-units due to complexity
  }

  // Adjust for square footage if provided
  if (details.squareFootage) {
    const sqft = Number.parseInt(details.squareFootage)
    if (!isNaN(sqft)) {
      // Adjust price based on square footage
      basePrice = basePrice * (sqft / 250)
    }
  }

  // Calculate breakdown
  const labor = Math.round(basePrice * laborPercentage)
  const materials = Math.round(basePrice * materialsPercentage)
  const permits = Math.round(basePrice * permitsPercentage)
  const other = Math.round(basePrice * otherPercentage)
  const total = labor + materials + permits + other

  return {
    costBreakdown: {
      labor,
      materials,
      permits,
      other,
      total,
    },
    timeline: timelineWeeks,
    confidence: confidenceLevel,
  }
}
