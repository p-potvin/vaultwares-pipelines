// Simple API client for workflow backend (TypeScript)
const API_BASE = import.meta.env.VITE_API_URL || ''

export interface Workflow {
  id: string;
  name: string;
  category: string;
  // Add more fields as needed
}

export interface CreateWorkflowParams {
  name: string;
  category: string;
}

export async function fetchWorkflows(): Promise<Workflow[]> {
  const res = await fetch(`${API_BASE}/api/workflows`);
  if (!res.ok) throw new Error('Failed to fetch workflows');
  return res.json();
}

export async function createWorkflow(params: CreateWorkflowParams): Promise<Workflow> {
  const res = await fetch(`${API_BASE}/api/workflows`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  });
  if (!res.ok) throw new Error('Failed to create workflow');
  return res.json();
}
// Add more API methods as needed (update, delete, etc.)