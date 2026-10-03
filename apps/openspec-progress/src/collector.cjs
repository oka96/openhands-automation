'use strict';

// Read-only collector embedded in the App and executed by the local Agent Server.
const { execFile } = require('node:child_process');
const { realpathSync } = require('node:fs');
const path = require('node:path');
const { promisify } = require('node:util');

const MAX_OUTPUT = 128 * 1024;
const MAX_CLI_OUTPUT = 512 * 1024;
const SLUG = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const execute = promisify(execFile);

class CollectorError extends Error {}

function requireValue(condition, message) {
  if (!condition) throw new CollectorError(message);
}

function object(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function text(value, limit = 2000) {
  return typeof value === 'string' && value.length > 0 && value.length <= limit && !value.includes('\0');
}

function slug(value) {
  return text(value, 100) && SLUG.test(value);
}

function count(value) {
  return Number.isSafeInteger(value) && value >= 0;
}

function unique(values, message) {
  requireValue(new Set(values).size === values.length, message);
}

function validateInput(input) {
  requireValue(object(input), 'Input must be an object.');
  requireValue(Object.keys(input).every(key => ['action', 'change'].includes(key)), 'Unsupported input field.');
  requireValue(input.action === 'overview' || input.action === 'change', 'Unsupported action.');
  if (input.action === 'overview') {
    requireValue(!Object.hasOwn(input, 'change'), 'Overview does not accept a change name.');
  } else {
    requireValue(slug(input.change), 'Change must be a kebab-case name of at most 100 characters.');
  }
  return input;
}

function verifyRoot(value, workspace) {
  requireValue(object(value) && object(value.root) && typeof value.root.path === 'string', 'OpenSpec did not report its project root.');
  let root;
  try { root = realpathSync(value.root.path); } catch { throw new CollectorError('OpenSpec reported an unavailable project root.'); }
  requireValue(root === workspace && path.resolve(value.root.path) === workspace,
    'OpenSpec resolved a different project root; select the exact local project directory.');
}

async function cli(args, { run, cwd }) {
  let result;
  try {
    result = await run('npx', ['--no-install', 'openspec', ...args], {
      cwd, shell: false, timeout: 12_000, maxBuffer: MAX_CLI_OUTPUT,
      encoding: 'utf8', env: { ...process.env, OPENSPEC_TELEMETRY: '0' },
    });
  } catch (error) {
    if (error?.killed || error?.code === 'ETIMEDOUT') throw new CollectorError('OpenSpec command timed out.');
    if (error?.code === 'ERR_CHILD_PROCESS_STDIO_MAXBUFFER') throw new CollectorError('OpenSpec command output exceeded its size limit.');
    throw new CollectorError('OpenSpec command failed. Check that the project has a locally installed OpenSpec CLI.');
  }
  requireValue(object(result) && typeof result.stdout === 'string', 'OpenSpec command returned no JSON output.');
  requireValue(Buffer.byteLength(result.stdout, 'utf8') <= MAX_CLI_OUTPUT, 'OpenSpec command output exceeded its size limit.');
  let value;
  try { value = JSON.parse(result.stdout); } catch { throw new CollectorError('OpenSpec command returned malformed JSON.'); }
  verifyRoot(value, cwd);
  return value;
}

function overview(value, workspace) {
  requireValue(Array.isArray(value.changes), 'OpenSpec returned an invalid change list.');
  const changes = value.changes.map(change => {
    requireValue(object(change) && slug(change.name), 'OpenSpec returned an invalid change name.');
    requireValue(count(change.completedTasks) && count(change.totalTasks) && change.completedTasks <= change.totalTasks,
      'OpenSpec returned invalid task counts.');
    requireValue(text(change.lastModified, 100) && Number.isFinite(Date.parse(change.lastModified)),
      'OpenSpec returned an invalid modification time.');
    const expected = change.totalTasks === 0 ? 'no-tasks' : change.completedTasks === change.totalTasks ? 'complete' : 'in-progress';
    requireValue(change.status === expected, 'OpenSpec returned an inconsistent change status.');
    return { name: change.name, completedTasks: change.completedTasks, totalTasks: change.totalTasks,
      lastModified: change.lastModified, status: change.status };
  });
  unique(changes.map(change => change.name), 'OpenSpec returned duplicate change names.');
  return { version: 1, kind: 'overview', workspace, generatedAt: new Date().toISOString(), changes };
}

function relativeArtifactPath(value) {
  return text(value, 2000) && !path.isAbsolute(value) && !value.includes('\\')
    && !value.split('/').includes('..');
}

function planning(value, workspace, name) {
  requireValue(value.changeName === name, 'OpenSpec returned a different change.');
  requireValue(text(value.schemaName, 100) && typeof value.isPlanningComplete === 'boolean' && Array.isArray(value.artifacts),
    'OpenSpec returned invalid planning status.');
  const artifacts = value.artifacts.map(artifact => {
    requireValue(object(artifact) && slug(artifact.id) && relativeArtifactPath(artifact.outputPath)
      && ['done', 'skipped', 'ready', 'blocked'].includes(artifact.status)
      && Array.isArray(artifact.requires) && artifact.requires.every(slug), 'OpenSpec returned an invalid planning artifact.');
    unique(artifact.requires, 'OpenSpec returned duplicate artifact requirements.');
    return { id: artifact.id, status: artifact.status, outputPath: artifact.outputPath, requires: [...artifact.requires] };
  });
  unique(artifacts.map(artifact => artifact.id), 'OpenSpec returned duplicate planning artifacts.');
  return { version: 1, kind: 'change', workspace, generatedAt: new Date().toISOString(), name,
    schemaName: value.schemaName, planningComplete: value.isPlanningComplete, artifacts,
    progress: null, tasks: [], applyState: 'unavailable', instruction: '' };
}

function taskEvidence(value, detail) {
  requireValue(value.changeName === detail.name && value.schemaName === detail.schemaName, 'OpenSpec returned a different change or schema.');
  requireValue(['blocked', 'ready', 'all_done'].includes(value.state) && typeof value.instruction === 'string'
    && typeof value.taskTrackingConfigured === 'boolean' && Array.isArray(value.tasks), 'OpenSpec returned invalid apply instructions.');
  const progress = value.progress;
  requireValue(object(progress) && count(progress.total) && count(progress.complete) && count(progress.remaining)
    && progress.complete <= progress.total && progress.remaining === progress.total - progress.complete,
  'OpenSpec returned invalid task progress.');
  const changeRoot = path.join(detail.workspace, 'openspec', 'changes', detail.name);
  const tasks = value.tasks.map(task => {
    requireValue(object(task) && text(task.id, 100) && text(task.description, MAX_OUTPUT)
      && typeof task.done === 'boolean' && text(task.sourcePath, 2000) && path.isAbsolute(task.sourcePath)
      && path.resolve(task.sourcePath).startsWith(changeRoot + path.sep)
      && Number.isSafeInteger(task.line) && task.line > 0, 'OpenSpec returned an invalid task or source location.');
    return { id: task.id, description: task.description, done: task.done, sourcePath: task.sourcePath, line: task.line };
  });
  unique(tasks.map(task => task.id), 'OpenSpec returned duplicate task IDs.');
  requireValue(tasks.length <= progress.total && tasks.filter(task => task.done).length <= progress.complete
    && tasks.filter(task => !task.done).length <= progress.remaining, 'OpenSpec task descriptions contradict the progress counts.');
  requireValue(value.state !== 'all_done' || (progress.total > 0 && progress.remaining === 0), 'OpenSpec returned an inconsistent completion state.');
  detail.applyState = value.state;
  detail.instruction = value.instruction;
  detail.tasks = tasks;
  // A schema without task tracking, or a blocked change with no tasks yet,
  // has no measurable completion percentage. Preserve that distinction.
  detail.progress = !value.taskTrackingConfigured || (value.state === 'blocked' && tasks.length === 0)
    ? null : { total: progress.total, complete: progress.complete, remaining: progress.remaining };
  if (Array.isArray(value.unavailableTrackingFiles) && value.unavailableTrackingFiles.length) {
    detail.progress = null;
    detail.taskError = 'Some task tracking files could not be read; completion is not verified.';
  }
  return detail;
}

function bounded(value) {
  requireValue(Buffer.byteLength(JSON.stringify(value), 'utf8') <= MAX_OUTPUT, 'Dashboard data exceeded the 128 KiB output limit.');
  return value;
}

function errorResult(error) {
  return { version: 1, kind: 'error', message: error instanceof CollectorError ? error.message : 'Could not read local OpenSpec progress.' };
}

async function collect(input, { run = execute, cwd = process.cwd() } = {}) {
  try {
    validateInput(input);
    requireValue(typeof cwd === 'string' && path.isAbsolute(cwd), 'Workspace must be an absolute local path.');
    const workspace = realpathSync(cwd);
    if (input.action === 'overview') return bounded(overview(await cli(['list', '--json'], { run, cwd: workspace }), workspace));
    const detail = planning(await cli(['status', '--change', input.change, '--json'], { run, cwd: workspace }), workspace, input.change);
    try {
      taskEvidence(await cli(['instructions', 'apply', '--change', input.change, '--json'], { run, cwd: workspace }), detail);
    } catch (error) {
      detail.taskError = errorResult(error).message;
    }
    return bounded(detail);
  } catch (error) {
    return errorResult(error);
  }
}

async function main() {
  let result;
  try {
    const encoded = process.argv[1];
    requireValue(typeof encoded === 'string' && encoded.length > 0 && encoded.length <= 8192
      && /^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(encoded), 'Expected one base64-encoded JSON input.');
    const decoded = Buffer.from(encoded, 'base64');
    requireValue(decoded.length <= 4096 && decoded.toString('base64') === encoded, 'Input exceeded its size limit or was not valid base64.');
    let input;
    try { input = JSON.parse(decoded.toString('utf8')); } catch { throw new CollectorError('Input was not valid JSON.'); }
    result = await collect(input);
  } catch (error) {
    result = errorResult(error);
  }
  process.stdout.write(JSON.stringify(result) + '\n');
  if (result.kind === 'error') process.exitCode = 1;
}

module.exports = { collect };
if (!module.parent) main();
