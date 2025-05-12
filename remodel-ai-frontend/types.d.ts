type Message = {
  id: string
  role: "user" | "assistant"
  content: string
}

type ProjectDetails = {
  projectType: string
  propertyType: string // Add this line
  address: string
  city: string
  state: string
  squareFootage: string
  additionalDetails: string
}
