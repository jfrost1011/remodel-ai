"use client"

import { X, Ruler } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent } from "@/components/ui/sheet"

interface AboutModalProps {
  isOpen: boolean
  onClose: () => void
}

export function AboutModal({ isOpen, onClose }: AboutModalProps) {
  return (
    <Sheet open={isOpen} onOpenChange={onClose}>
      <SheetContent className="sm:max-w-md overflow-y-auto">
        <div className="flex flex-col h-full">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold">About RemodelAI</h2>
            <Button variant="ghost" size="icon" onClick={onClose} className="absolute right-4 top-4">
              <X className="h-4 w-4" />
              <span className="sr-only">Close</span>
            </Button>
          </div>

          <div className="space-y-4">
            <p>RemodelAI provides AI-powered construction cost estimates for residential remodeling projects.</p>

            <h3 className="text-lg font-medium mt-4">How It Works</h3>
            <ul className="space-y-2 list-disc pl-5">
              <li>Enter your project details including location, type, and size</li>
              <li>Our AI analyzes thousands of similar projects in your area</li>
              <li>Get accurate cost estimates based on current material and labor costs</li>
              <li>Ask follow-up questions to refine your estimate or explore options</li>
            </ul>

            <h3 className="text-lg font-medium mt-4">Our Technology</h3>
            <p>
              RemodelAI combines machine learning with a comprehensive database of construction costs. Our system is
              trained on real-world project data and continuously updated with the latest pricing information from
              suppliers and contractors across the country.
            </p>

            <Button onClick={onClose} className="w-full mt-6" style={{ backgroundColor: "#10B981" }}>
              <Ruler className="h-4 w-4 mr-2" />
              Start New Estimate
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  )
}
