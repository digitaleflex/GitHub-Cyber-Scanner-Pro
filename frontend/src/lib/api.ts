import { useQuery } from '@tanstack/react-query'

const API_BASE = '/api'

export async function fetchJson<T>(url: string): Promise<T> {
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
  total_cves: number
  pending_keywords: number
  new_repos_24h: number
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

export type SearchResultType = 'repo' | 'cve' | 'book' | 'keyword'

export type SearchResult = {
  name: string
  desc: string | null
  result_type: SearchResultType
  stars?: number
  lang?: string
  url?: string
  security_verdict?: string
  vitality_score?: number
  severity?: string
  cvss_score?: number
  published?: string
  source_name?: string
  category?: string
  score?: number
  status?: string
  repo_name?: string
}

export type SearchFacets = {
  types: Record<SearchResultType, number>
  languages: { lang: string | null; count: number }[]
  severities: Record<string, number>
  categories: { category: string | null; count: number }[]
}

export type SearchResponse = {
  query: string
  total: number
  page: number
  per_page: number
  pages: number
  results: SearchResult[]
  facets: SearchFacets
}

export type SearchParams = {
  q: string
  page?: number
  per_page?: number
  types?: SearchResultType[]
  language?: string
  severity?: string
  security_verdict?: string
  category?: string
  sort?: 'relevance' | 'stars' | 'updated' | 'cvss' | 'published'
}

export function useSearch(params: SearchParams) {
  const { q } = params
  return useQuery<SearchResponse>({
    queryKey: ['search', params],
    queryFn: () => {
      const sp = new URLSearchParams({ q, page: String(params.page ?? 1), per_page: String(params.per_page ?? 20) })
      if (params.types?.length) sp.set('types', params.types.join(','))
      if (params.language) sp.set('language', params.language)
      if (params.severity) sp.set('severity', params.severity)
      if (params.security_verdict) sp.set('security_verdict', params.security_verdict)
      if (params.category) sp.set('category', params.category)
      if (params.sort && params.sort !== 'relevance') sp.set('sort', params.sort)
      return fetchJson<SearchResponse>(`/search?${sp.toString()}`)
    },
    enabled: q.length >= 2,
    staleTime: 15_000,
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

export type CveEntry = {
  cve_id: string
  description: string
  published: string | null
  last_modified: string | null
  severity: string
  cvss_score: number | null
  weaknesses: string[]
}

export type ApiCvesResponse = {
  total: number
  page: number
  per_page: number
  pages: number
  cves: CveEntry[]
}

export type Keyword = {
  term: string
  category_guess: string | null
  score: number
  sources: number
  source_samples: string | null
  status: string
  discovered_at: string | null
  reviewed_at: string | null
}

export function useKeywords(status: string = 'pending', limit: number = 200) {
  return useQuery<{ keywords: Keyword[] }>({
    queryKey: ['keywords', status],
    queryFn: () => fetchJson<{ keywords: Keyword[] }>(`/keywords?status=${status}&limit=${limit}`),
    staleTime: 15_000,
  })
}

export async function approveKeyword(term: string, category?: string): Promise<{ success: boolean }> {
  const params = category ? `?category=${encodeURIComponent(category)}` : ''
  const res = await fetch(`${API_BASE}/keywords/${encodeURIComponent(term)}/approve${params}`, { method: 'POST' })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export async function rejectKeyword(term: string): Promise<{ success: boolean }> {
  const res = await fetch(`${API_BASE}/keywords/${encodeURIComponent(term)}/reject`, { method: 'POST' })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export async function enrichKeywords(): Promise<{ message: string }> {
  const res = await fetch(`${API_BASE}/enrich-keywords`, { method: 'POST' })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export async function enrichOntology(): Promise<{ message: string }> {
  const res = await fetch(`${API_BASE}/enrich-ontology`, { method: 'POST' })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export function useCves(q?: string, severity?: string, page: number = 1) {
  const params = new URLSearchParams()
  if (q) params.set('q', q)
  if (severity) params.set('severity', severity)
  params.set('page', String(page))
  params.set('per_page', '20')
  return useQuery<ApiCvesResponse>({
    queryKey: ['cves', q ?? '', severity ?? '', page],
    queryFn: () => fetchJson<ApiCvesResponse>(`/cves?${params}`),
    staleTime: 30_000,
    retry: 1,
  })
}


