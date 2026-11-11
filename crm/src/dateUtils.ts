/** Format a local calendar date for an HTML date input without UTC shifting. */
export function localDateInputValue(date: Date = new Date()): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/** Add calendar days in the browser's local timezone, independent of DST length. */
export function addLocalCalendarDays(date: Date, days: number): string {
  const result = new Date(date.getFullYear(), date.getMonth(), date.getDate(), 12);
  result.setDate(result.getDate() + days);
  return localDateInputValue(result);
}

/** Add days to an ISO calendar date without interpreting it in the browser timezone. */
export function addCalendarDaysToIsoDate(value: string, days: number): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!match || !Number.isInteger(days)) throw new RangeError('Expected an ISO date and an integer day offset.');
  const date = new Date(Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3])));
  if (date.toISOString().slice(0, 10) !== value) throw new RangeError('Invalid ISO calendar date.');
  date.setUTCDate(date.getUTCDate() + days);
  return date.toISOString().slice(0, 10);
}
