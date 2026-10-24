/** Indian money format: crores as "₹1.50 crore", smaller amounts with lakh grouping ("₹1,07,000"). */
export function formatInr(n: number, lang: 'en' | 'hi' = 'en'): string {
  if (n >= 1e7) return `₹${(n / 1e7).toFixed(2)} ${lang === 'hi' ? 'करोड़' : 'crore'}`
  return `₹${Math.round(n).toLocaleString('en-IN')}`
}
