"use client"

import { useState, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import api from '@/lib/api'
import { Download, FileText, ChevronDown, X, RefreshCw } from "lucide-react"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"

interface CostBreakdown {
  labor: number
  materials: number
  permits: number
  other: number
  total: number
}

// Update the projectDetails interface to include propertyType
interface EstimateReportProps {
  estimateId: string | null
  projectDetails: {
    projectType: string
    propertyType: string // Add this line
    city: string
    state: string
    squareFootage?: string
  }
  costBreakdown: CostBreakdown
  timeline: string
  confidence: number
  onClose: () => void
  onNewEstimate: () => void
}

export function EstimateReport({
  projectDetails,
  costBreakdown,
  timeline,
  confidence,
  onClose,
  onNewEstimate,
  estimateId,}: EstimateReportProps) {
  const [isPdfLoading, setIsPdfLoading] = useState(false)
  const reportRef = useRef<HTMLDivElement>(null)

  const handleDownloadPdf = async () => {
    if (!estimateId) {
      console.error("No estimate ID available")
      return
    }
    
    setIsPdfLoading(true)
    try {
      const blob = await api.exportPDF(estimateId)
      
      // Create a download link
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `estimate_${estimateId}.pdf`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error("Error downloading PDF:", error)
    } finally {
      setIsPdfLoading(false)
    }
  }

  const squareFootage = projectDetails.squareFootage || "N/A"
  const costPerSqFt = projectDetails.squareFootage
    ? `$${Math.round(costBreakdown.total / Number.parseInt(projectDetails.squareFootage))}/sq ft`
    : "N/A"

  return (
    <div ref={reportRef} className="bg-white rounded-lg border shadow-lg p-6 max-w-4xl mx-auto my-6 relative">
      {/* Close button */}
      <Button variant="ghost" size="icon" onClick={onClose} className="absolute right-2 top-2">
        <X className="h-4 w-4" />
        <span className="sr-only">Close</span>
      </Button>

      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <FileText className="h-6 w-6 text-emerald-500" />
          <h2 className="text-2xl font-bold">Renovation Cost Estimator</h2>
        </div>
        <div className="flex gap-2">
          <Button onClick={onNewEstimate} variant="outline" className="flex items-center gap-2">
            <RefreshCw className="h-4 w-4" />
            New Estimate
          </Button>
          <Button onClick={handleDownloadPdf} disabled={isPdfLoading} style={{ backgroundColor: "#10B981" }}>
            <Download className="h-4 w-4 mr-2" />
            {isPdfLoading ? "Generating PDF..." : "Download PDF"}
          </Button>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6 mb-8">
        <div>
          <h3 className="text-lg font-semibold mb-4">Project Details</h3>
          {/* Add propertyType to the Project Details section in the report */}
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Project Type:</span>
              <span className="font-medium">{projectDetails.projectType}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Property Type:</span>
              <span className="font-medium">{projectDetails.propertyType}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Location:</span>
              <span className="font-medium">
                {projectDetails.city}, {projectDetails.state}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Square Footage:</span>
              <span className="font-medium">{squareFootage}</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <Card>
            <CardHeader className="p-3">
              <CardTitle className="text-sm text-muted-foreground">Estimated Cost</CardTitle>
            </CardHeader>
            <CardContent className="p-3 pt-0">
              <div className="text-2xl font-bold">${costBreakdown.total.toLocaleString()}</div>
              <p className="text-xs text-muted-foreground">{costPerSqFt}</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="p-3">
              <CardTitle className="text-sm text-muted-foreground">Timeline</CardTitle>
            </CardHeader>
            <CardContent className="p-3 pt-0">
              <div className="text-2xl font-bold">{timeline}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="p-3">
              <CardTitle className="text-sm text-muted-foreground">Confidence</CardTitle>
            </CardHeader>
            <CardContent className="p-3 pt-0">
              <div className="text-2xl font-bold">{confidence}%</div>
            </CardContent>
          </Card>
        </div>
      </div>

      <h3 className="text-xl font-semibold mb-4">Cost Breakdown</h3>
      <div className="mb-8">
        <div className="mb-2 flex justify-between">
          <span>Estimated Total:</span>
          <span className="font-bold">${costBreakdown.total.toLocaleString()}</span>
        </div>

        {/* Cost breakdown bars */}
        <div className="space-y-3">
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span>Labor</span>
              <span>${costBreakdown.labor.toLocaleString()}</span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-4">
              <div
                className="bg-blue-500 h-4 rounded-full"
                style={{ width: `${(costBreakdown.labor / costBreakdown.total) * 100}%` }}
              ></div>
            </div>
          </div>

          <div>
            <div className="flex justify-between text-sm mb-1">
              <span>Materials</span>
              <span>${costBreakdown.materials.toLocaleString()}</span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-4">
              <div
                className="bg-orange-400 h-4 rounded-full"
                style={{ width: `${(costBreakdown.materials / costBreakdown.total) * 100}%` }}
              ></div>
            </div>
          </div>

          <div>
            <div className="flex justify-between text-sm mb-1">
              <span>Permits</span>
              <span>${costBreakdown.permits.toLocaleString()}</span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-4">
              <div
                className="bg-green-500 h-4 rounded-full"
                style={{ width: `${(costBreakdown.permits / costBreakdown.total) * 100}%` }}
              ></div>
            </div>
          </div>

          <div>
            <div className="flex justify-between text-sm mb-1">
              <span>Other</span>
              <span>${costBreakdown.other.toLocaleString()}</span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-4">
              <div
                className="bg-red-500 h-4 rounded-full"
                style={{ width: `${(costBreakdown.other / costBreakdown.total) * 100}%` }}
              ></div>
            </div>
          </div>
        </div>
      </div>

      <Collapsible className="mb-6">
        <div className="flex items-center justify-between">
          <h3 className="text-xl font-semibold">Recommended Services</h3>
          <CollapsibleTrigger asChild>
            <Button variant="ghost" size="sm" className="w-9 p-0">
              <ChevronDown className="h-4 w-4" />
              <span className="sr-only">Toggle services</span>
            </Button>
          </CollapsibleTrigger>
        </div>

        <CollapsibleContent className="mt-2">
          <h4 className="font-medium mb-2">Recommended Services for {projectDetails.projectType}</h4>
          <ul className="list-disc pl-5 space-y-1 text-sm">
            {projectDetails.projectType.includes("Kitchen") && (
              <>
                <li>Kitchen Design Services: Professional layout and design optimization ($500-$2,000)</li>
                <li>Appliance Package Delivery: Coordinated appliance selection for cohesive look</li>
                <li>Custom Cabinetry Consultations: Maximize storage and functionality</li>
                <li>Lighting Design: Task and ambient lighting plan for improved functionality</li>
                <li>Plumbing Upgrades: Consider water filtration systems and efficient fixtures</li>
              </>
            )}
            {projectDetails.projectType.includes("Bathroom") && (
              <>
                <li>Bathroom Design Services: Professional layout optimization ($400-$1,500)</li>
                <li>Fixture Selection: Coordinated fixtures for a cohesive aesthetic</li>
                <li>Waterproofing Consultation: Ensure proper moisture barriers and ventilation</li>
                <li>Lighting Design: Task and ambient lighting plan for improved functionality</li>
                <li>Storage Solutions: Maximize space efficiency in your bathroom</li>
              </>
            )}
            {projectDetails.projectType.includes("ADU") && (
              <>
                <li>ADU Design Services: Professional space planning ($1,000-$3,000)</li>
                <li>Permit Expediting: Navigate complex ADU regulations</li>
                <li>Utility Connection Planning: Ensure proper electrical, plumbing, and HVAC</li>
                <li>Space-Saving Solutions: Maximize functionality in compact spaces</li>
                <li>Sound Insulation Consultation: Create privacy between living spaces</li>
              </>
            )}
            {projectDetails.projectType.includes("Garage") && (
              <>
                <li>Conversion Design Services: Transform your garage effectively ($800-$2,500)</li>
                <li>Insulation Consultation: Ensure comfort in converted space</li>
                <li>Electrical System Upgrades: Plan for new living space requirements</li>
                <li>Flooring Solutions: Convert concrete floors to comfortable living surfaces</li>
                <li>Window and Door Installation: Add natural light and proper access</li>
              </>
            )}
          </ul>

          <h4 className="font-medium mt-4 mb-2">General Services for All Projects</h4>
          <ul className="list-disc pl-5 space-y-1 text-sm">
            <li>3D Rendering: Visualize your project before construction begins</li>
            <li>Project Management: Professional oversight to keep your project on track</li>
            <li>Permit Expediting: Navigate local building codes and requirements</li>
            <li>Financing Options: Explore renovation loans with competitive rates</li>
            <li>Post-Construction Cleaning: Professional detailed cleaning once work is complete</li>
          </ul>
        </CollapsibleContent>
      </Collapsible>

      <Collapsible className="mb-6">
        <div className="flex items-center justify-between">
          <h3 className="text-xl font-semibold">Next Steps</h3>
          <CollapsibleTrigger asChild>
            <Button variant="ghost" size="sm" className="w-9 p-0">
              <ChevronDown className="h-4 w-4" />
              <span className="sr-only">Toggle next steps</span>
            </Button>
          </CollapsibleTrigger>
        </div>

        <CollapsibleContent className="mt-2">
          <p className="text-sm mb-3">Now that you have your estimate, you can:</p>
          <ol className="list-decimal pl-5 space-y-1 text-sm">
            <li>Contact contractors for quotes</li>
            <li>Plan your renovation timeline</li>
            <li>Create a budget based on this estimate</li>
            <li>Download a detailed report to share</li>
          </ol>
        </CollapsibleContent>
      </Collapsible>

      <div className="text-xs text-center text-muted-foreground mt-8">
        This estimate is based on average costs for similar projects in your area. Actual costs may vary based on
        specific materials, contractor availability, and project complexity.
      </div>
    </div>
  )
}
