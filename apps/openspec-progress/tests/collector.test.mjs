import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, readFileSync, realpathSync, rmSync } from 'node:fs';
import { createRequire } from 'node:module';
import os from 'node:os';
import path from 'node:path';
import { after, test } from 'node:test';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const { collect } = require('../src/collector.cjs');
const cwd = realpathSync(mkdtempSync(path.join(os.tmpdir(), 'openspec-collector-')));
const otherRoot = realpathSync(mkdtempSync(path.join(os.tmpdir(), 'openspec-other-root-')));
after(() => { rmSync(cwd, { recursive: true, force: true }); rmSync(otherRoot, { recursive: true, force: true }); });
const change = 'example-change';
const sourcePath = path.join(cwd, 'openspec', 'changes', change, 'tasks.md');

function list() {
  return { root: { path: cwd, source: 'nearest' }, changes: [{ name: change, completedTasks: 1,
    totalTasks: 2, lastModified: '2026-10-03T00:00:00.000Z', status: 'in-progress' }] };
}

function status() {
  return { root: { path: cwd }, changeName: change, schemaName: 'spec-driven', isPlanningComplete: true,
    artifacts: [{ id: 'proposal', status: 'done', outputPath: 'proposal.md', requires: [] },
      { id: 'tasks', status: 'done', outputPath: 'tasks.md', requires: ['proposal'] }] };
}

function apply() {
  return { root: { path: cwd }, changeName: change, schemaName: 'spec-driven', taskTrackingConfigured: true,
    state: 'ready', instruction: 'Implement the remaining task.', progress: { total: 2, complete: 1, remaining: 1 },
    tasks: [{ id: '1', description: 'Build the UI', done: true, sourcePath, line: 3 },
      { id: '2', description: 'Verify the UI', done: false, sourcePath, line: 4 }] };
}

function cli(responses) {
  const calls = [];
  const run = async (file, args, options) => {
    calls.push({ file, args, options });
    const response = responses.shift();
    if (response instanceof Error) throw response;
    assert.notEqual(response, undefined, 'Unexpected extra CLI invocation');
    return { stdout: typeof response === 'string' ? response : JSON.stringify(response), stderr: '' };
  };
  return { run, calls };
}

test('overview invokes only the local read-only list command and preserves validated counts', async () => {
  const fake = cli([list()]);
  const result = await collect({ action: 'overview' }, { run: fake.run, cwd });
  assert.equal(result.kind, 'overview');
  assert.equal(result.version, 1);
  assert.equal(result.workspace, cwd);
  assert.deepEqual(result.changes, list().changes);
  assert.ok(Number.isFinite(Date.parse(result.generatedAt)));
  assert.equal(fake.calls.length, 1);
  const call = fake.calls[0];
  assert.equal(call.file, 'npx');
  assert.deepEqual(call.args, ['--no-install', 'openspec', 'list', '--json']);
  assert.equal(call.options.shell, false);
  assert.equal(call.options.cwd, cwd);
  assert.equal(call.options.timeout, 12_000);
  assert.equal(call.options.maxBuffer, 512 * 1024);
  assert.equal(call.options.env.OPENSPEC_TELEMETRY, '0');
  assert.equal(call.options.env.PATH, process.env.PATH);
});

test('detail uses exact status/apply command vectors and preserves task evidence', async () => {
  const fake = cli([status(), apply()]);
  const result = await collect({ action: 'change', change }, { run: fake.run, cwd });
  assert.equal(result.kind, 'change');
  assert.equal(result.name, change);
  assert.equal(result.planningComplete, true);
  assert.deepEqual(result.artifacts, status().artifacts);
  assert.deepEqual(result.progress, apply().progress);
  assert.deepEqual(result.tasks, apply().tasks);
  assert.equal(result.applyState, 'ready');
  assert.deepEqual(fake.calls.map(call => call.args), [
    ['--no-install', 'openspec', 'status', '--change', change, '--json'],
    ['--no-install', 'openspec', 'instructions', 'apply', '--change', change, '--json'],
  ]);
});

test('blocked planning has unknown task progress, not an invented zero-percent result', async () => {
  const planning = status();
  planning.isPlanningComplete = false;
  planning.artifacts[1].status = 'blocked';
  const instructions = apply();
  Object.assign(instructions, { state: 'blocked', instruction: 'Missing tasks artifact.',
    progress: { total: 0, complete: 0, remaining: 0 }, tasks: [] });
  const fake = cli([planning, instructions]);
  const result = await collect({ action: 'change', change }, { run: fake.run, cwd });
  assert.equal(result.kind, 'change');
  assert.equal(result.planningComplete, false);
  assert.equal(result.applyState, 'blocked');
  assert.equal(result.progress, null);
  assert.deepEqual(result.tasks, []);
  assert.equal(result.instruction, 'Missing tasks artifact.');
});

test('apply command failure preserves planning artifacts with a safe task error', async () => {
  const failure = new Error('Internal details with a secret token');
  const fake = cli([status(), failure]);
  const result = await collect({ action: 'change', change }, { run: fake.run, cwd });
  assert.equal(result.kind, 'change');
  assert.deepEqual(result.artifacts, status().artifacts);
  assert.equal(result.progress, null);
  assert.deepEqual(result.tasks, []);
  assert.equal(result.applyState, 'unavailable');
  assert.match(result.taskError, /command failed/);
  assert.doesNotMatch(JSON.stringify(result), /secret token/);
});

test('schemas without task tracking do not report measurable task completion', async () => {
  const instructions = apply();
  Object.assign(instructions, { taskTrackingConfigured: false, tasks: [], progress: { total: 0, complete: 0, remaining: 0 } });
  const fake = cli([status(), instructions]);
  const result = await collect({ action: 'change', change }, { run: fake.run, cwd });
  assert.equal(result.progress, null);
  assert.equal(result.applyState, 'ready');
});

test('unreadable tracking evidence never reports a completion percentage', async () => {
  const instructions = apply();
  instructions.unavailableTrackingFiles = [{ path: sourcePath, reason: 'Unreadable' }];
  const fake = cli([status(), instructions]);
  const result = await collect({ action: 'change', change }, { run: fake.run, cwd });
  assert.equal(result.progress, null);
  assert.equal(result.tasks.length, 2);
  assert.match(result.taskError, /not verified/);
});

test('unknown actions, extra keys, long names and traversal cannot invoke the CLI', async () => {
  const bad = [null, [], {}, { action: 'archive', change }, { action: 'overview', change },
    { action: 'overview', cwd: '/another' }, { action: 'change', change: '../escape' },
    { action: 'change', change: '--help' }, { action: 'change', change: 'a'.repeat(101) }];
  const fake = cli([]);
  for (const input of bad) {
    const result = await collect(input, { run: fake.run, cwd });
    assert.equal(result.kind, 'error');
  }
  assert.equal(fake.calls.length, 0);
});

test('overview rejects ancestor or different project roots', async () => {
  for (const root of [path.dirname(cwd), otherRoot]) {
    const value = list();
    value.root.path = root;
    const fake = cli([value]);
    const result = await collect({ action: 'overview' }, { run: fake.run, cwd });
    assert.equal(result.kind, 'error');
    assert.match(result.message, /different project root/);
  }
});

test('missing root and malformed JSON produce structured errors', async () => {
  for (const value of ['not JSON', { changes: [] }]) {
    const fake = cli([value]);
    const result = await collect({ action: 'overview' }, { run: fake.run, cwd });
    assert.equal(result.version, 1);
    assert.equal(result.kind, 'error');
    assert.equal(typeof result.message, 'string');
  }
});

test('duplicate changes and inconsistent task counts or status are rejected', async () => {
  const fixtures = [];
  let value = list(); value.changes.push({ ...value.changes[0] }); fixtures.push(value);
  value = list(); value.changes[0].completedTasks = 3; fixtures.push(value);
  value = list(); value.changes[0].totalTasks = -1; fixtures.push(value);
  value = list(); value.changes[0].status = 'complete'; fixtures.push(value);
  for (const fixture of fixtures) {
    const fake = cli([fixture]);
    assert.equal((await collect({ action: 'overview' }, { run: fake.run, cwd })).kind, 'error');
  }
});

test('invalid artifact paths fail the detail rather than exposing another directory', async () => {
  for (const outputPath of ['../outside.md', '/absolute.md', 'specs/../../outside.md']) {
    const planning = status();
    planning.artifacts[0].outputPath = outputPath;
    const fake = cli([planning]);
    const result = await collect({ action: 'change', change }, { run: fake.run, cwd });
    assert.equal(result.kind, 'error');
    assert.equal(fake.calls.length, 1);
  }
});

test('invalid task paths, counts and duplicate IDs preserve planning but reject task data', async () => {
  const fixtures = [];
  let value = apply(); value.tasks[0].sourcePath = path.join(cwd, 'secret.md'); fixtures.push(value);
  value = apply(); value.tasks[0].sourcePath = path.join(cwd, 'openspec/changes/other/tasks.md'); fixtures.push(value);
  value = apply(); value.progress.remaining = 9; fixtures.push(value);
  value = apply(); value.tasks[1].id = '1'; fixtures.push(value);
  value = apply(); value.tasks[1].done = true; fixtures.push(value);
  for (const fixture of fixtures) {
    const fake = cli([status(), fixture]);
    const result = await collect({ action: 'change', change }, { run: fake.run, cwd });
    assert.equal(result.kind, 'change');
    assert.equal(result.progress, null);
    assert.deepEqual(result.tasks, []);
    assert.equal(typeof result.taskError, 'string');
  }
});

test('apply root mismatch does not contaminate valid planning evidence', async () => {
  const instructions = apply();
  instructions.root.path = otherRoot;
  const fake = cli([status(), instructions]);
  const result = await collect({ action: 'change', change }, { run: fake.run, cwd });
  assert.equal(result.kind, 'change');
  assert.equal(result.progress, null);
  assert.match(result.taskError, /different project root/);
});

test('oversized CLI and final dashboard output return errors rather than truncating JSON', async () => {
  let fake = cli([' '.repeat(512 * 1024 + 1)]);
  let result = await collect({ action: 'overview' }, { run: fake.run, cwd });
  assert.equal(result.kind, 'error');
  assert.match(result.message, /size limit/);
  const instructions = apply();
  instructions.tasks[0].description = 'x'.repeat(70_000);
  instructions.tasks[1].description = 'y'.repeat(70_000);
  fake = cli([status(), instructions]);
  result = await collect({ action: 'change', change }, { run: fake.run, cwd });
  assert.equal(result.kind, 'error');
  assert.match(result.message, /128 KiB/);
  assert.ok(Buffer.byteLength(JSON.stringify(result)) < 1024);
});

test('CLI timeout messages are bounded and never expose subprocess stderr', async () => {
  const error = new Error('sensitive stderr'); error.killed = true;
  const fake = cli([error]);
  const result = await collect({ action: 'overview' }, { run: fake.run, cwd });
  assert.equal(result.kind, 'error');
  assert.match(result.message, /timed out/);
  assert.doesNotMatch(JSON.stringify(result), /sensitive/);
});

test('node -e entrypoint emits structured JSON and exit 1 for invalid input', () => {
  const filename = fileURLToPath(new URL('../src/collector.cjs', import.meta.url));
  const source = readFileSync(filename, 'utf8');
  for (const encoded of ['not-base64!', Buffer.from(JSON.stringify({ action: 'archive' })).toString('base64')]) {
    try {
      execFileSync(process.execPath, ['-e', source, encoded], { cwd, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
      assert.fail('Invalid input unexpectedly succeeded');
    } catch (error) {
      assert.equal(error.status, 1);
      const result = JSON.parse(error.stdout);
      assert.equal(result.kind, 'error');
      assert.equal(result.version, 1);
      assert.equal(error.stderr, '');
    }
  }
});
