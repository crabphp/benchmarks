// Explicit checks equivalent to the PHP HTTP-library adapters (Next.js ships no validator).
// The reviver keeps the JSON source text so 36.0 is rejected as a non-integer, as in PHP.
const EMAIL = /^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$/;

export function validate(body) {
  let data;
  try {
    data = JSON.parse(body, (key, value, context) =>
      typeof value === 'number' && !/^-?\d+$/.test(context?.source ?? '') ? { float: value } : value);
  } catch {
    return null;
  }
  if (data === null || typeof data !== 'object') return null;
  const { name, email, age } = data;
  const length = typeof name === 'string' ? [...name].length : 0;
  if (length < 1 || length > 100) return null;
  if (typeof email !== 'string' || !EMAIL.test(email)) return null;
  if (!Number.isSafeInteger(age) || age < 18 || age > 120) return null;
  return { name, email, age };
}
