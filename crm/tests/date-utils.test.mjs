import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';

const source = await readFile(new URL('../src/dateUtils.ts', import.meta.url), 'utf8');
const compiled = ts.transpileModule(source, {
  compilerOptions: { target: ts.ScriptTarget.ES2020, module: ts.ModuleKind.ESNext },
}).outputText;
const dateUtils = await import(`data:text/javascript;base64,${Buffer.from(compiled).toString('base64')}`);

test('follow-up days remain local calendar days late at night in Cancun', () => {
  process.env.TZ = 'America/Cancun';
  const lateEvening = new Date('2026-11-11T04:30:00.000Z'); // Nov 10, 23:30 in Cancun.

  assert.equal(dateUtils.localDateInputValue(lateEvening), '2026-11-10');
  assert.equal(dateUtils.addLocalCalendarDays(lateEvening, 3), '2026-11-13');
});

test('follow-up days keep the selected calendar date across DST changes', () => {
  process.env.TZ = 'America/New_York';
  const beforeDst = new Date('2026-03-08T05:30:00.000Z'); // Mar 8, 00:30 before the spring transition.

  assert.equal(dateUtils.localDateInputValue(beforeDst), '2026-03-08');
  assert.equal(dateUtils.addLocalCalendarDays(beforeDst, 3), '2026-03-11');
});
