"use client"

import type React from "react"

import { useState } from "react"
import { X, DollarSign } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Sheet, SheetContent } from "@/components/ui/sheet"

// First, update the ProjectDetails interface to include propertyType
interface ProjectDetails {
  projectType: string
  propertyType: string // Add this line
  address?: string
  city: string
  state: string
  squareFootage?: string
  additionalDetails?: string
}

interface ProjectDetailsFormProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (data: ProjectDetails) => void
  initialValues: ProjectDetails
}

const PROJECT_TYPES = [
  "Kitchen Remodel",
  "Bathroom Remodel",
  "Basement Remodel",
  "Room Addition",
  "Whole House Renovation",
  "Deck/Patio",
  "Roofing",
  "Flooring",
  "ADU",
  "Garage Conversion",
  "Other",
]

const US_STATES = [
  "AL",
  "AK",
  "AZ",
  "AR",
  "CA",
  "CO",
  "CT",
  "DE",
  "FL",
  "GA",
  "HI",
  "ID",
  "IL",
  "IN",
  "IA",
  "KS",
  "KY",
  "LA",
  "ME",
  "MD",
  "MA",
  "MI",
  "MN",
  "MS",
  "MO",
  "MT",
  "NE",
  "NV",
  "NH",
  "NJ",
  "NM",
  "NY",
  "NC",
  "ND",
  "OH",
  "OK",
  "OR",
  "PA",
  "RI",
  "SC",
  "SD",
  "TN",
  "TX",
  "UT",
  "VT",
  "VA",
  "WA",
  "WV",
  "WI",
  "WY",
]

// Add a constant for property type options after the US_STATES constant
const PROPERTY_TYPES = ["SFR", "2-4 Units", "Condo"]

// Add this function after the PROJECT_TYPES and US_STATES constants
const normalizeCity = (city: string): string => {
  return city.trim().toLowerCase().replace(/\s+/g, " ")
}

export function ProjectDetailsForm({ isOpen, onClose, onSubmit, initialValues }: ProjectDetailsFormProps) {
  const [formData, setFormData] = useState<ProjectDetails>(initialValues)
  const [errors, setErrors] = useState<Record<string, string>>({})

  const handleChange = (field: keyof ProjectDetails, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }))

    // Clear error when field is updated
    if (errors[field]) {
      setErrors((prev) => {
        const newErrors = { ...prev }
        delete newErrors[field]
        return newErrors
      })
    }
  }

  // In the validateForm function, add validation for propertyType
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!formData.projectType) {
      newErrors.projectType = "Project type is required"
    }

    if (!formData.propertyType) {
      newErrors.propertyType = "Property type is required"
    }

    if (!formData.city) {
      newErrors.city = "City is required"
    }

    if (!formData.state) {
      newErrors.state = "State is required"
    }

    // Check if California is selected but city is not San Diego or Los Angeles
    if (formData.state === "CA" && formData.city) {
      const normalizedCity = normalizeCity(formData.city)
      if (normalizedCity !== "san diego" && normalizedCity !== "los angeles") {
        newErrors.city = "We are not servicing that area yet but we will soon be expanding"
      }
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (validateForm()) {
      onSubmit(formData)
    }
  }

  return (
    <Sheet open={isOpen} onOpenChange={onClose}>
      <SheetContent className="sm:max-w-md md:max-w-lg overflow-y-auto">
        <div className="flex flex-col h-full">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">Project Details</h2>
            <p className="text-sm text-muted-foreground">Provide information about your remodeling project</p>
            <Button variant="ghost" size="icon" onClick={onClose} className="absolute right-4 top-4">
              <X className="h-4 w-4" />
              <span className="sr-only">Close</span>
            </Button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6 flex-1">
            {/* Add the Property Type dropdown in the form, after the Project Type dropdown */}
            <div className="space-y-2">
              <Label htmlFor="projectType" className="flex items-center gap-1">
                Project Type <span className="text-red-500">*</span>
              </Label>
              <Select value={formData.projectType} onValueChange={(value) => handleChange("projectType", value)}>
                <SelectTrigger id="projectType" className={errors.projectType ? "border-red-500" : ""}>
                  <SelectValue placeholder="Select project type" />
                </SelectTrigger>
                <SelectContent>
                  {PROJECT_TYPES.map((type) => (
                    <SelectItem key={type} value={type}>
                      {type}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.projectType && <p className="text-sm text-red-500">{errors.projectType}</p>}
            </div>

            <div className="space-y-2">
              <Label htmlFor="propertyType" className="flex items-center gap-1">
                Property Type <span className="text-red-500">*</span>
              </Label>
              <Select value={formData.propertyType} onValueChange={(value) => handleChange("propertyType", value)}>
                <SelectTrigger id="propertyType" className={errors.propertyType ? "border-red-500" : ""}>
                  <SelectValue placeholder="Select property type" />
                </SelectTrigger>
                <SelectContent>
                  {PROPERTY_TYPES.map((type) => (
                    <SelectItem key={type} value={type}>
                      {type}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.propertyType && <p className="text-sm text-red-500">{errors.propertyType}</p>}
            </div>

            <div className="space-y-2">
              <Label htmlFor="address">Address (Optional)</Label>
              <Input
                id="address"
                value={formData.address}
                onChange={(e) => handleChange("address", e.target.value)}
                placeholder="123 Main St"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="city" className="flex items-center gap-1">
                  City <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="city"
                  value={formData.city}
                  onChange={(e) => handleChange("city", e.target.value)}
                  placeholder="City"
                  className={errors.city ? "border-red-500" : ""}
                />
                {errors.city && <p className="text-sm text-red-500">{errors.city}</p>}
                {formData.state === "CA" && (
                  <p className="text-xs text-muted-foreground mt-1">
                    Note: Currently only servicing San Diego and Los Angeles in California
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="state" className="flex items-center gap-1">
                  State <span className="text-red-500">*</span>
                </Label>
                <Select value={formData.state} onValueChange={(value) => handleChange("state", value)}>
                  <SelectTrigger id="state" className={errors.state ? "border-red-500" : ""}>
                    <SelectValue placeholder="State" />
                  </SelectTrigger>
                  <SelectContent>
                    {US_STATES.map((state) => (
                      <SelectItem key={state} value={state}>
                        {state}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.state && <p className="text-sm text-red-500">{errors.state}</p>}
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="squareFootage">Square Footage (Optional)</Label>
              <Input
                id="squareFootage"
                type="number"
                value={formData.squareFootage}
                onChange={(e) => handleChange("squareFootage", e.target.value)}
                placeholder="e.g., 500"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="additionalDetails">Additional Details (Optional)</Label>
              <Textarea
                id="additionalDetails"
                value={formData.additionalDetails}
                onChange={(e) => handleChange("additionalDetails", e.target.value)}
                placeholder="Describe any specific requirements or features..."
                rows={4}
              />
            </div>

            <Button type="submit" className="w-full" style={{ backgroundColor: "#10B981" }}>
              <DollarSign className="h-4 w-4 mr-2" />
              Get Estimate
            </Button>
          </form>
        </div>
      </SheetContent>
    </Sheet>
  )
}
