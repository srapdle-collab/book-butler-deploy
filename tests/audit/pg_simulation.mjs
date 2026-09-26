// Disposable PostgreSQL/WASM audit. No network, credentials or production DB.
// node tests/audit/pg_simulation.mjs /tmp/.../node_modules/@electric-sql/pglite/dist/index.js /tmp/.../report.json
import { readFileSync, writeFileSync, mkdtempSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { pathToFileURL } from 'node:url';
import assert from 'node:assert/strict';

const { PGlite } = await import(pathToFileURL(process.argv[2]));
const extract = source => source.match(/POSTGRES_SCHEMA = """([\s\S]*?)"""/)[1].split(';').map(s => s.trim()).filter(Boolean);
const current = extract(readFileSync('lib/schema.py', 'utf8'));
const baseline = extract(execFileSync('git', ['show', '51e5b0c:lib/schema.py'], {encoding:'utf8'}));
writeFileSync(join(dirname(process.argv[3]), 'current-init.sql'), current.join(';\n')+';\n');
writeFileSync(join(dirname(process.argv[3]), 'baseline-init.sql'), baseline.join(';\n')+';\n');
writeFileSync(join(dirname(process.argv[3]), 'additive-delta.sql'), current.filter(s => !baseline.includes(s)).join(';\n')+';\n');
const report = { engine:'PGlite 0.4.6 (PostgreSQL WASM; not Supabase/PgBouncer/psycopg)', cases:[] };
const run = async (db, statements) => { for (const s of statements) await db.exec(s); };
const scalar = async (db, sql) => Object.values((await db.query(sql)).rows[0])[0];
async function snapshot(db) {
  const tables = (await db.query("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename!='reading_chunks' ORDER BY tablename")).rows;
  const result = {};
  for (const {tablename} of tables) {
    const rows = (await db.query(`SELECT row_to_json(t) AS row FROM "${tablename}" t ORDER BY row_to_json(t)::text`)).rows;
    const columns = (await db.query("SELECT column_name,data_type,is_nullable,column_default FROM information_schema.columns WHERE table_schema='public' AND table_name=$1 ORDER BY ordinal_position", [tablename])).rows;
    const constraints = (await db.query("SELECT conname,pg_get_constraintdef(oid) AS definition FROM pg_constraint WHERE conrelid=$1::regclass ORDER BY conname", [tablename])).rows;
    result[tablename] = {count:rows.length,sha256:createHash('sha256').update(JSON.stringify({rows,columns,constraints})).digest('hex')};
  }
  return result;
}
async function seed(db) {
  await db.exec(`
    INSERT INTO books(id,title,author,isbn,current_page,owner_id) SELECT 'b'||i,'TEST 합성 책 '||i,'검증 저자','978'||lpad(i::text,10,'0'),i%100,'audit-owner' FROM generate_series(0,704) i;
    INSERT INTO activities(id,book_id,kind,text,quote,page,date,owner_id,updated_at) SELECT 'a'||i,'b'||(i%705),i%8,E'TEST 원문\n한글 %_'||i,CASE WHEN i%2=0 THEN '합성 인용' END,i%100,1700000000+i,'audit-owner',1700000000000000000+i FROM generate_series(0,5665) i;
    INSERT INTO photo_manifest VALUES('TEST.png','cover','b0','[]');
    INSERT INTO source_book_state VALUES('b0',1,1,'읽는 중','TEST');
    INSERT INTO app_migrations VALUES('TEST-baseline',1700000000);
    INSERT INTO deletion_page_effect VALUES('a0',0,1);
    INSERT INTO reading_sessions VALUES('s','b0',1700000000,1700000010,0,'saved','a0');
    INSERT INTO profiles VALUES('audit-owner','test@example.invalid','TEST',1);
    INSERT INTO reading_groups VALUES('g','TEST','audit-owner',1);
    INSERT INTO group_members VALUES('g','audit-owner','owner',1);
    INSERT INTO group_invites VALUES('t','g','audit-owner',1,NULL,NULL);
    INSERT INTO daily_checkins(id,group_id,user_id,checked_on,is_read,created_at,updated_at) VALUES('c','g','audit-owner','2026-09-26',1,1,1);
    INSERT INTO checkin_reactions VALUES('c','audit-owner','❤️',1);
    INSERT INTO checkin_comments VALUES('comment','c','audit-owner','TEST',1);
  `);
}
let db = new PGlite();
report.version = await scalar(db, 'SELECT version()');
await run(db,current);
assert.equal(await scalar(db,"SELECT count(*)::int FROM information_schema.columns WHERE table_name='reading_chunks' AND table_schema='public'"),22);
assert.equal(await scalar(db,"SELECT count(*)::int FROM pg_indexes WHERE tablename='reading_chunks'"),5);
report.cases.push({name:'empty PostgreSQL',status:'PASS',columns:22,indexes:5,ddl:current.length});
await db.close();

db = new PGlite();
await run(db,baseline);
await seed(db);
const before = await snapshot(db);
for(let i=0;i<4;i++){ await run(db,current); assert.deepEqual(await snapshot(db),before); }
await run(db,baseline);
assert.deepEqual(await snapshot(db),before);
report.cases.push({name:'populated baseline + 4 initializations + old-code schema rollback',status:'PASS',fingerprints:before});
const duplicateSql = readFileSync('lib/reading_chunks.py','utf8').match(/def _duplicate[\s\S]*?query = """([\s\S]*?)"""/)[1];
let parameter = 0;
const pgQuery = duplicateSql.replaceAll('?', () => '$'+(++parameter));
try {
  await db.query(pgQuery,['audit-owner','b0','2026-09-27',null,null,null,null,'hash']);
  report.cases.push({name:'nullable-page duplicate query',status:'PASS'});
} catch(error) {
  report.cases.push({name:'nullable-page duplicate query',status:'REPRODUCED_DEFECT',code:error.code,message:error.message});
}
// Explicit PREPARE types are a diagnostic control, NOT a product change.
await db.exec(`PREPARE typed_duplicate(text,text,text,integer,integer,integer,integer,text) AS ${pgQuery}`);
await db.exec("EXECUTE typed_duplicate('audit-owner','b0','2026-09-27',NULL,NULL,NULL,NULL,'hash')");
report.cases.push({name:'explicitly typed NULL diagnostic control',status:'PASS'});
await db.exec(`INSERT INTO reading_chunks(chunk_id,owner_id,book_id,book_title,source_app,source_ref,read_date,original_text,content_hash,created_at,updated_at)
  VALUES('TEST-chunk','audit-owner','b0','TEST 합성','readdam','TEST-source','2026-09-27','TEST 원문','hash','2026-09-27T00:00:00+09:00','2026-09-27T00:00:00+09:00')`);
await db.exec("UPDATE reading_chunks SET user_note='TEST 수정',tags='[\"한글\"]',minutes=15 WHERE chunk_id='TEST-chunk'");
for (const [label,sql,expected] of [
  ['sourceApp NOT NULL',"UPDATE reading_chunks SET source_app=NULL WHERE chunk_id='TEST-chunk'",'23502'],
  ['sourceApp CHECK',"UPDATE reading_chunks SET source_app='invalid' WHERE chunk_id='TEST-chunk'",'23514'],
  ['book FK',"UPDATE reading_chunks SET book_id='missing' WHERE chunk_id='TEST-chunk'",'23503'],
  ['chunk PK',"INSERT INTO reading_chunks SELECT * FROM reading_chunks WHERE chunk_id='TEST-chunk'",'23505'],
  ['sourceRef UNIQUE',"INSERT INTO reading_chunks(chunk_id,owner_id,book_title,source_app,source_ref,read_date,content_hash,created_at,updated_at) VALUES('different','audit-owner','TEST','readdam','TEST-source','2026-09-27','h','now','now')",'23505'],
]) {
  try { await db.exec(sql); assert.fail('constraint not enforced: '+label); }
  catch(error){ assert.equal(error.code,expected); }
}
await db.exec("UPDATE reading_chunks SET deleted_at='2026-09-27T00:01:00+09:00' WHERE chunk_id='TEST-chunk'");
await run(db,baseline);
assert.equal(await scalar(db,"SELECT count(*)::int FROM reading_chunks WHERE deleted_at IS NOT NULL"),1);
report.cases.push({name:'chunk insert/update/soft-delete + PK/UNIQUE/FK/NOT NULL/CHECK + old-code init',status:'PASS',constraintChecks:5});
await db.exec("UPDATE books SET owner_id=NULL WHERE id='b0'; UPDATE activities SET owner_id=NULL WHERE id='a0';");
await db.exec("UPDATE books SET owner_id='audit-owner' WHERE owner_id IS NULL; UPDATE activities SET owner_id='audit-owner' WHERE owner_id IS NULL;");
assert.deepEqual(await snapshot(db),before);
report.cases.push({name:'legacy owner claim writes NULL-owner book/activity',status:'CONFIRMED_EXISTING_WRITE_PATH',rowsChanged:2});
await db.close();

db = new PGlite();
await run(db,baseline);
await seed(db);
const partialBefore = await snapshot(db);
try {
  for(const statement of current){
    if(statement.includes('idx_reading_chunks_owner')) await db.exec('CREATE INDEX TEST_failure ON reading_chunks(TEST_missing_column)');
    await db.exec(statement);
  }
  assert.fail('failure injection not reached');
} catch(error) {
  assert.equal(error.code,'42703');
}
assert.equal(await scalar(db,"SELECT count(*)::int FROM pg_indexes WHERE tablename='reading_chunks'"),3);
assert.deepEqual(await snapshot(db),partialBefore);
await run(db,current);
assert.equal(await scalar(db,"SELECT count(*)::int FROM pg_indexes WHERE tablename='reading_chunks'"),5);
report.cases.push({name:'autocommit mid-index failure + retry',status:'PASS',partialIndexCount:3,finalIndexCount:5,legacyDataUnchanged:true});
await db.exec('DROP INDEX idx_reading_chunks_owner; CREATE INDEX idx_reading_chunks_owner ON reading_chunks(book_title)');
await run(db,current);
const wrongIndex = await scalar(db,"SELECT indexdef FROM pg_indexes WHERE indexname='idx_reading_chunks_owner'");
assert.match(wrongIndex,/book_title/);
report.cases.push({name:'same-name wrong index',status:'REPRODUCED_DEFECT',definition:wrongIndex});
await db.close();

db = new PGlite();
await run(db,baseline);
await db.exec('CREATE TABLE reading_chunks(chunk_id TEXT PRIMARY KEY)');
try { await run(db,current); assert.fail('expected missing column failure'); }
catch(error){ assert.equal(error.code,'42703'); report.cases.push({name:'partial existing chunk table',status:'EXPECTED_STOP',code:error.code,message:error.message}); }
assert.equal(await scalar(db,"SELECT count(*)::int FROM information_schema.columns WHERE table_name='reading_chunks'"),1);
await db.close();

db = new PGlite();
await run(db,baseline);
await db.exec('BEGIN');
try {
  await run(db,current);
  await db.exec('CREATE INDEX TEST_failure ON reading_chunks(TEST_missing_column)');
} catch(error){ assert.equal(error.code,'42703'); await db.exec('ROLLBACK'); }
assert.equal(await scalar(db,"SELECT to_regclass('public.reading_chunks')"),null);
report.cases.push({name:'explicit transaction rollback control',status:'PASS',chunkTableAbsentAfterRollback:true});
await db.exec('BEGIN READ ONLY');
assert.equal(await scalar(db,'SHOW transaction_read_only'),'on');
await db.query("SELECT * FROM information_schema.columns WHERE table_schema='public' AND table_name IN ('books','activities','reading_chunks')");
try { await db.exec('CREATE TABLE audit_forbidden(id int)'); assert.fail('read-only enforcement missing'); }
catch(error){ assert.equal(error.code,'25006'); await db.exec('ROLLBACK'); }
report.cases.push({name:'metadata-only read-only transaction control',status:'PASS',writesRejected:'25006'});
await db.close();

const persistedPath = mkdtempSync(join(dirname(process.argv[3]), 'pg-restart-'));
db = new PGlite(persistedPath);
await run(db,baseline);
await seed(db);
const restartBefore = await snapshot(db);
await run(db,current);
await db.close();
db = new PGlite(persistedPath);
await run(db,current);
assert.deepEqual(await snapshot(db),restartBefore);
report.cases.push({name:'persistent PostgreSQL WASM DB close/reopen/reinitialize',status:'PASS',path:persistedPath});
await db.close();

writeFileSync(process.argv[3], JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
