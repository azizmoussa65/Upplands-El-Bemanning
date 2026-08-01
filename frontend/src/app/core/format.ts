/** allabolag amounts are expressed "i 1000" (thousands of SEK). */
export function formatSekFromThousands(thousands: number | null | undefined): string {
  if (thousands === null || thousands === undefined || isNaN(thousands)) return '—';
  const sek = thousands * 1000;
  const abs = Math.abs(sek);
  if (abs >= 1_000_000) {
    return `${(sek / 1_000_000).toLocaleString('sv-SE', { maximumFractionDigits: 1 })} M SEK`;
  }
  if (abs >= 1_000) {
    return `${(sek / 1_000).toLocaleString('sv-SE', { maximumFractionDigits: 0 })} tSEK`;
  }
  return `${sek.toLocaleString('sv-SE', { maximumFractionDigits: 0 })} SEK`;
}

export function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined || isNaN(value)) return '—';
  return `${value.toLocaleString('sv-SE', { maximumFractionDigits: 1 })} %`;
}

export function yoyGrowthPercent(latest: number | null | undefined, previous: number | null | undefined): number | null {
  if (latest === null || latest === undefined || !previous) return null;
  return ((latest - previous) / Math.abs(previous)) * 100;
}
