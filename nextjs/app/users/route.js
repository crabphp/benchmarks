import { validate } from '../../lib/validate.js';

export const dynamic = 'force-dynamic';

export async function POST(request) {
  const data = validate(await request.text());
  return data === null
    ? Response.json({ error: 'Invalid input' }, { status: 422 })
    : Response.json(data, { status: 201 });
}
