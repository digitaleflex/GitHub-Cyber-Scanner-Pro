const KEY = 'hashcode.profile_id'

export function getProfileId(): string {
  if (typeof localStorage === 'undefined') return '1'
  return localStorage.getItem(KEY) || '1'
}

export function setProfileId(id: string | number): void {
  if (typeof localStorage === 'undefined') return
  localStorage.setItem(KEY, String(id))
}
