import { useQuery } from '@tanstack/react-query'

const API_BASE = '/api'

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`)
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`)
  return res.json()
}

export type Repo = {
  name: string
  desc: string
  stars: number
  lang: string | null
  url: string
  created: string
  updated: string
  size_kb: number
  security_verdict: string | null
}

export type Stats = {
  total_repos: number
  total_stars: number
  languages: number
  lang_distribution: Record<string, number>
  last_scan: string | null
  status: string
  security_critique: number
  security_suspect: number
  security_unscanned: number
}

export type ApiReposResponse = {
  total: number
  page: number
  per_page: number
  pages: number
  repos: Repo[]
}

export type ApiReportsResponse = {
  reports: string[]
  dashboards: string[]
}

export function useRepos(query?: string, page: number = 1) {
  const params = new URLSearchParams()
  if (query) params.set('q', query)
  params.set('page', String(page))
  params.set('per_page', '20')
  return useQuery<ApiReposResponse>({
    queryKey: ['repos', query, page],
    queryFn: () => fetchJson<ApiReposResponse>(`/repos?${params}`),
    staleTime: 30_000,
  })
}

export function useStats() {
  return useQuery<Stats>({
    queryKey: ['stats'],
    queryFn: () => fetchJson<Stats>('/stats'),
    staleTime: 30_000,
  })
}

export function useReports() {
  return useQuery<ApiReportsResponse>({
    queryKey: ['reports'],
    queryFn: () => fetchJson<ApiReportsResponse>('/reports'),
    staleTime: 60_000,
  })
}

export async function startScan(): Promise<{ message: string }> {
  const res = await fetch(`${API_BASE}/scan`, { method: 'POST' })
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`)
  return res.json()
}

export function useScanStatus() {
  return useQuery<Stats>({
    queryKey: ['stats'],
    queryFn: () => fetchJson<Stats>('/stats'),
    refetchInterval: (query) =>
      query.state.data?.status?.includes('en cours') ? 3000 : false,
  })
}
