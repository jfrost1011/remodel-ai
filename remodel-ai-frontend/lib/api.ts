export async function getEstimate(
  details: any,
  accessToken?: string | null
): Promise<{
  response: string
  estimateData: any
  estimateId: string
}> {
  const result = await api.createEstimate(details);
  
  // The backend returns the full estimate response
  // We need to format it for the frontend
  return {
    response: "Estimate created successfully",
    estimateData: {
      costBreakdown: {
        total: result.total_cost,
        labor: result.cost_breakdown?.labor || 0,
        materials: result.cost_breakdown?.materials || 0,
        permits: result.cost_breakdown?.permits || 0,
        other: result.cost_breakdown?.other || 0
      },
      timeline: `${result.timeline?.total_days || 0} days`,
      confidence: result.confidence_score || 0.85
    },
    estimateId: result.estimate_id
  };
}