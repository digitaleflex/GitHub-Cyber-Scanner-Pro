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
}

export type Stats = {
  total_repos: number
  total_stars: number
  languages: number
  lang_distribution: Record<string, number>
  last_scan: string | null
}

export type ApiReposResponse = {
  total: number
  repos: Repo[]
}

export type ApiReportsResponse = {
  reports: string[]
  dashboards: string[]
}

export function useRepos(query?: string) {
  const params = query ? `?q=${encodeURIComponent(query)}` : ''
  return useQuery<ApiReposResponse>({
    queryKey: ['repos', query],
    queryFn: () => fetchJson<ApiReposResponse>(`/repos${params}`),
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
