import collectorSource from './collector.cjs?raw';

const SLUG = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const LIMIT = 128 * 1024;

export function validateWorkspace(value) {
  if (typeof value !== 'string' || !value.startsWith('/') || value.length > 4096 || /[\0\r\n]/.test(value)) {
    throw new Error('Enter an absolute project directory on the connected Agent Server.');
  }
  return value.replace(/\/+$/, '') || '/';
}

function count(value) { return Number.isSafeInteger(value) && value >= 0; }
function object(value) { return value !== null && typeof value === 'object' && !Array.isArray(value); }

function validateOverview(data) {
  if (!Array.isArray(data.changes) || data.changes.some(change =>
    !object(change) || typeof change.name !== 'string' || !SLUG.test(change.name) || !count(change.totalTasks) ||
    !count(change.completedTasks) || change.completedTasks > change.totalTasks ||
    typeof change.lastModified !== 'string') ||
    new Set(data.changes.map(change => change.name)).size !== data.changes.length) {
    throw new Error('OpenSpec returned an invalid change inventory.');
  }
}

function validateChange(data, name) {
  if (data.name !== name || typeof data.schemaName !== 'string' ||
      typeof data.planningComplete !== 'boolean' || !Array.isArray(data.artifacts) ||
      data.artifacts.some(item => !object(item) || typeof item.id !== 'string' ||
        !['done', 'ready', 'blocked', 'skipped'].includes(item.status) ||
        typeof item.outputPath !== 'string' || !Array.isArray(item.requires) ||
        item.requires.some(id => typeof id !== 'string')) || !Array.isArray(data.tasks)) {
    throw new Error('OpenSpec returned invalid artifact or task data.');
  }
  if (data.tasks.some(task => !object(task) || typeof task.id !== 'string' ||
      typeof task.description !== 'string' || typeof task.done !== 'boolean' ||
      typeof task.sourcePath !== 'string' || !Number.isSafeInteger(task.line) || task.line < 1)) {
    throw new Error('OpenSpec returned invalid task details.');
  }
  if (data.progress === null) return;
  const p = data.progress;
  if (!object(p) || !count(p.total) || !count(p.complete) || !count(p.remaining) ||
      p.complete + p.remaining !== p.total || data.tasks.length > p.total ||
      data.tasks.filter(task => task.done).length > p.complete ||
      data.tasks.filter(task => !task.done).length > p.remaining) {
    throw new Error('OpenSpec returned inconsistent task counts.');
  }
}

async function query(host, workspace, input) {
  const cwd = validateWorkspace(workspace);
  // Only this fixed collector executes. Variable input is data, never shell source.
  const encoded = btoa(JSON.stringify(input));
  const quote = value => "'" + value.replaceAll("'", "'\\''") + "'";
  const command = `node -e ${quote(collectorSource)} ${quote(encoded)}`;
  let response;
  try {
    response = await host.agentServer.request({
      method: 'POST', path: '/api/bash/execute_bash_command',
      body: { command, cwd, timeout: 30 },
    });
  } catch {
    throw new Error('Cannot read OpenSpec from this Agent Server. Check its connection and project directory, then refresh.');
  }
  if (!object(response) || typeof response.stdout !== 'string' || response.stdout.length > LIMIT ||
      !Number.isInteger(response.order) || response.order !== 0 || !Number.isInteger(response.exit_code)) {
    throw new Error('The progress query did not return complete output. Try a smaller project or inspect the Agent Server.');
  }
  let data;
  try { data = JSON.parse(response.stdout); }
  catch { throw new Error('The progress query returned invalid output. Ensure Node.js and the project-pinned OpenSpec CLI are installed.'); }
  if (object(data) && data.version === 1 && data.kind === 'error' && typeof data.message === 'string') {
    throw new Error(data.message.slice(0, 600));
  }
  if (response.exit_code !== 0 || !object(data) || data.version !== 1 ||
      data.kind !== (input.action === 'overview' ? 'overview' : 'change') ||
      typeof data.workspace !== 'string' || typeof data.generatedAt !== 'string' ||
      !Number.isFinite(Date.parse(data.generatedAt))) {
    throw new Error('OpenSpec progress could not be read reliably. Refresh to try again.');
  }
  if (input.action === 'overview') validateOverview(data);
  else validateChange(data, input.change);
  return data;
}

export function loadOverview(host, workspace) {
  return query(host, workspace, { action: 'overview' });
}

export function loadChange(host, workspace, change) {
  if (typeof change !== 'string' || !SLUG.test(change)) throw new Error('Invalid OpenSpec change name.');
  return query(host, workspace, { action: 'change', change });
}
