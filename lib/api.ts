const BASE = process.env.NEXT_PUBLIC_API_BASE_URL || ''

async function req<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`)
  return res.json()
}

export const api = {
  // Health
  health: () => req<{ status: string; db: string }>('/health/db'),

  // Websites
  listWebsites: () => req<any[]>('/api/websites'),
  createWebsite: (data: any) => req('/api/websites', { method: 'POST', body: JSON.stringify(data) }),

  // Accounts
  listManagers: () => req<any[]>('/api/accounts/managers'),
  listAdsAccounts: () => req<any[]>('/api/accounts/ads'),
  listBindings: () => req<any[]>('/api/accounts/bindings'),
  createBinding: (data: any) => req('/api/accounts/bindings', { method: 'POST', body: JSON.stringify(data) }),
  toggleAutopilot: (id: string, enabled: boolean) =>
    req(`/api/accounts/bindings/${id}/autopilot?enabled=${enabled}`, { method: 'PATCH' }),

  // Jobs
  listPlans: (websiteId: string) => req<any[]>(`/api/jobs/plans/${websiteId}`),
  listActions: (websiteId: string, status?: string) =>
    req<any[]>(`/api/jobs/actions/${websiteId}${status ? `?status=${status}` : ''}`),
  listMutateLogs: (websiteId: string) => req<any[]>(`/api/jobs/logs/${websiteId}`),
  triggerOptimize: (websiteId: string) => req(`/api/jobs/optimize/${websiteId}`, { method: 'POST' }),
  triggerExecute: (websiteId: string) => req(`/api/jobs/execute/${websiteId}`, { method: 'POST' }),
}
