/** UTC-safe date formatting helpers (backend stores UTC; render in UTC). */

export function formatUtcDate(iso: string | null | undefined): string {
  if (!iso) return '';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  return d.toLocaleDateString(undefined, { timeZone: 'UTC' });
}

export function formatUtcDateTime(iso: string | null | undefined): string {
  if (!iso) return '';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  return d.toLocaleString(undefined, { timeZone: 'UTC' });
}
