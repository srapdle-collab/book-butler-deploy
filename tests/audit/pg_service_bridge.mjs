// Test-only stdin bridge to in-memory PostgreSQL/WASM; no TCP or credentials.
import { createInterface } from 'node:readline';
import { readFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
const { PGlite } = await import(pathToFileURL(process.argv[2]));
const db = new PGlite();
const schema = readFileSync('lib/schema.py', 'utf8').match(/POSTGRES_SCHEMA = """([\s\S]*?)"""/)[1];
await db.exec(schema);
console.log(JSON.stringify({ready: true}));
for await (const line of createInterface({input: process.stdin})) {
  try {
    const {sql, params} = JSON.parse(line);
    let parameter = 0;
    const result = await db.query(sql.replaceAll('%s', () => '$' + (++parameter)), params);
    console.log(JSON.stringify({rows: result.rows, rowcount: result.affectedRows ?? result.rows.length}));
  } catch (error) {
    console.log(JSON.stringify({error: error.message, code: error.code}));
  }
}
await db.close();
