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
  vitality_score: number | null
  synopsis: string | null
  semantic_category: string | null
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
  avg_vitality: number
  top_vitality: number
  low_vitality: number
  dead_vitality: number
}

export type ApiReposResponse = {
  total: number
  page: number
  per_page: number
  pages: number
  repos: Repo[]
}

export type Book = {
  id: number
  title: string
  url: string
  category: string
  type_ressource: string
  repo_name: string
  repo_url: string
  is_dead: number
  last_checked: string | null
}

export type ApiReportsResponse = {
  reports: string[]
  dashboards: string[]
}

export function useRepos(query?: string, page: number = 1, sortBy: string = 'stars', vitalityMin: number = 0, securityVerdict?: string | null) {
  const params = new URLSearchParams()
  if (query) params.set('q', query)
  params.set('page', String(page))
  params.set('per_page', '20')
  params.set('sort_by', sortBy)
  if (vitalityMin > 0) params.set('vitality_min', String(vitalityMin))
  if (securityVerdict) params.set('security_verdict', securityVerdict)
  return useQuery<ApiReposResponse>({
    queryKey: ['repos', query, page, sortBy, vitalityMin, securityVerdict],
    queryFn: () => fetchJson<ApiReposResponse>(`/repos?${params}`),
    staleTime: 30_000,
  })
}

export function useBooks(query?: string) {
  const params = query ? `?q=${encodeURIComponent(query)}` : ''
  return useQuery<Book[]>({
    queryKey: ['books', query ?? ''],
    queryFn: () => fetchJson<Book[]>(`/books${params}`),
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

export type NewsHealth = {
  collector: 'miniflux' | 'builtin'
  feeds_total: number
  feeds_usable: number
  feeds_dead: string[]
  feeds_blocked_antibot: string[]
  miniflux?: { enabled: boolean; reachable?: boolean; feeds?: number; error?: string }
}

export function useNewsHealth() {
  return useQuery<NewsHealth>({
    queryKey: ['news-health'],
    queryFn: () => fetchJson<NewsHealth>('/news/health'),
    staleTime: 60_000,
    retry: 1,
  })
}

export type NewsCountry = { country: string; count: number }

export function useNewsCountries() {
  return useQuery<NewsCountry[]>({
    queryKey: ['news-countries'],
    queryFn: () => fetchJson<NewsCountry[]>('/news/countries'),
    staleTime: 120_000,
    retry: 1,
  })
}

export type IncidentNewsItem = {
  id: number
  title: string
  link: string
  summary?: string
  source_name?: string
  country?: string
  published?: string
  category?: string
}

export type Incident = {
  incident_id: number
  title: string
  cves: string[]
  products: string[]
  domains: string[]
  hashes: string[]
  ips: string[]
  attack_details: { technique: string; name: string; tactic: string }[]
  sources: string[]
  countries: string[]
  num_sources: number
  severity_score: number
  news: IncidentNewsItem[]
  primary_link: string
}

export function useNewsIncidents(limit = 50, country?: string) {
  const params = new URLSearchParams()
  params.set('limit', String(limit))
  if (country) params.set('country', country)
  return useQuery<{ incidents: Incident[] }>({
    queryKey: ['news-incidents', limit, country ?? 'all'],
    queryFn: () => fetchJson<{ incidents: Incident[] }>(`/news/incidents?${params.toString()}`),
    staleTime: 60_000,
    retry: 1,
  })
}
