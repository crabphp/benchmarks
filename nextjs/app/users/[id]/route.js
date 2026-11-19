import { pool } from '../../../lib/db.js';

export const dynamic = 'force-dynamic';

export async function GET(request, { params }) {
  const { id } = await params;
  if (!/^\d+$/.test(id)) return Response.json({ error: 'Not found' }, { status: 404 });
  const [rows] = await pool().execute('SELECT id, name, email, age FROM users WHERE id = ?', [Number(id)]);
  const row = rows[0];
  if (!row) return Response.json({ error: 'Not found' }, { status: 404 });
  return Response.json({ id: Number(row.id), name: row.name, email: row.email, age: Number(row.age) });
}
