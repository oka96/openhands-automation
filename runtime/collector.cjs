'use strict';

// Automation-owned, read-only collection entrypoint for visual clients.
const fs = require('node:fs');
const path = require('node:path');


// Pure contract validation; callers supply already bounded, non-linked sources.
const ROLE_SCHEMAS = { SA: 'sa', Frontend: 'frontend', Backend: 'backend', QA: 'qa' };
const UPSTREAM_ROLES = { SA: [], Frontend: ['SA'], Backend: ['SA'], QA: ['SA', 'Frontend', 'Backend'] };
function scopeIdentity(id) {
  const match = typeof id === 'string' && id.length <= 160 && id.match(/^(SA|FE|BE|QA)-([A-Z][A-Z0-9]*-[0-9]+)-([a-z0-9]+(?:-[a-z0-9]+)*)$/);
  return match && { role: { SA: 'SA', FE: 'Frontend', BE: 'Backend', QA: 'QA' }[match[1]], requirement: match[2] };
}
function validateRepositoryScope(scope, id, lookup = null, seen = new Set()) {
  const fail = message => { throw new Error(`${id}: ${message}`); };
  const identity = scopeIdentity(id);
  if (!identity || seen.has(id)) fail('invalid or cyclic scope identity');
  const exact = (value, keys) => value && typeof value === 'object' && !Array.isArray(value) && Object.keys(value).sort().join(',') === keys.sort().join(',');
  if (!exact(scope, ['version', 'applications', 'references']) || scope.version !== 1) fail('invalid scope.json version or fields');
  const apps = scope.applications, refs = scope.references, required = UPSTREAM_ROLES[identity.role];
  if (!Array.isArray(apps) || !apps.length || apps.length > 20 || (identity.role !== 'SA' && apps.length !== 1)) fail('role requires exactly one repository; SA permits 1 to 20');
  for (const app of apps) {
    if (!exact(app, ['id', 'name', 'role', 'repository']) || typeof app.id !== 'string' || app.id.length > 80 || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(app.id)
      || typeof app.name !== 'string' || !app.name.trim() || app.name.length > 200 || /[\x00-\x1f]/.test(app.name)
      || !['Frontend', 'Backend', 'QA'].includes(app.role) || (identity.role !== 'SA' && app.role !== identity.role)
      || typeof app.repository !== 'string' || app.repository.length > 500
      || !/^https:\/\/github\.com\/[A-Za-z0-9][A-Za-z0-9-]*\/[A-Za-z0-9_-][A-Za-z0-9_.-]*\.git$/.test(app.repository)) fail('invalid application identity, role or HTTPS GitHub repository');
  }
  if (new Set(apps.map(app => app.id)).size !== apps.length || new Set(apps.map(app => app.repository.toLowerCase())).size !== apps.length) fail('duplicate applications or repositories');
  if (!Array.isArray(refs) || refs.length > 20 || new Set(refs).size !== refs.length || (identity.role === 'SA' && refs.length)) fail('invalid upstream references');
  const upstream = refs.map(ref => {
    const value = scopeIdentity(ref);
    if (!value || value.requirement !== identity.requirement || !required.includes(value.role)) fail('upstream reference must belong to a required role in this requirement');
    return value;
  });
  if (required.some(role => !upstream.some(value => value.role === role))) fail('missing required upstream role reference');
  if (lookup) {
    const next = new Set(seen).add(id);
    const sources = refs.map(ref => {
      const source = lookup(ref);
      if (!source) fail(`missing upstream scope ${ref}`);
      validateRepositoryScope(source, ref, lookup, next);
      return { ...scopeIdentity(ref), scope: source };
    });
    if (identity.role !== 'SA' && !sources.filter(source => source.role === 'SA').some(source => source.scope.applications.some(app => JSON.stringify(app) === JSON.stringify(apps[0])
      || ['id', 'name', 'role', 'repository'].every(key => app[key] === apps[0][key])))) fail('repository binding is not declared by referenced SA');
    if (identity.role === 'QA') {
      const saRefs = new Set(refs.filter(ref => scopeIdentity(ref).role === 'SA'));
      if (sources.some(source => source.role !== 'SA' && !source.scope.references.some(ref => saRefs.has(ref)))) fail('QA upstream implementations must share a referenced SA contract');
    }
  }
  return scope;
}

const ROLE_IDS = ['SA', 'Frontend', 'Backend', 'QA'];
const ROLE_LABELS = ['Solution Architect', 'Frontend', 'Backend', 'Quality Assurance'];
const MAX_FILE = 64 * 1024;
const MAX_METADATA = 128 * 1024;
const MAX_OUTPUT = 512 * 1024;
const MAX_REQUIREMENTS = 50;
const MAX_TASKS = 500;
class CollectorError extends Error {}

function requireValue(condition, message) {
  if (!condition) throw new CollectorError(message);
}
function object(value) { return value !== null && typeof value === 'object' && !Array.isArray(value); }
function text(value, limit = 2000, empty = false) {
  return typeof value === 'string' && (empty || value.trim().length > 0) && value.length <= limit && !value.includes('\0');
}
function fields(value, names) { return Object.keys(value).every(key => names.includes(key)); }
function unique(values, message) { requireValue(new Set(values).size === values.length, message); }
function contained(root, target) { return target === root || target.startsWith(root + path.sep); }
function localSegment(value) { return value.split(path.sep).includes('.local'); }

// Resolve before reading. Refuse symlink aliases as well as escapes so each source location
// shown in the app identifies exactly the file that supplied its evidence.
function safePath(target, root) {
  requireValue(contained(root, target) && !localSegment(target), 'Source path is outside the permitted store.');
  let canonical;
  try {
    requireValue(!fs.lstatSync(target).isSymbolicLink(), 'Symlinked or escaping source paths are not supported.');
    canonical = fs.realpathSync(target);
  }
  catch (error) { if (error.code === 'ENOENT') return false; throw error; }
  requireValue(canonical === target && contained(root, canonical) && !localSegment(canonical),
    'Symlinked or escaping source paths are not supported.');
  return true;
}

function readFile(target, root, limit = MAX_FILE) {
  if (!safePath(target, root)) return null;
  let descriptor;
  try {
    descriptor = fs.openSync(target, fs.constants.O_RDONLY | fs.constants.O_NOFOLLOW);
    const stat = fs.fstatSync(descriptor);
    requireValue(stat.isFile(), 'Expected a regular source file.');
    requireValue(stat.size <= limit, 'A store source file exceeded its size limit.');
    // Read at most limit+1 bytes even if the file grows after fstat.
    const buffer = Buffer.alloc(limit + 1);
    let length = 0;
    while (length < buffer.length) {
      const read = fs.readSync(descriptor, buffer, length, buffer.length - length, null);
      if (!read) break;
      length += read;
    }
    requireValue(length <= limit, 'A store source file exceeded its size limit.');
    const content = buffer.subarray(0, length);
    const decoded = content.toString('utf8');
    requireValue(Buffer.from(decoded, 'utf8').equals(content) && !decoded.includes('\0'), 'A store source file is not valid UTF-8 text.');
    return decoded;
  } finally { if (descriptor !== undefined) fs.closeSync(descriptor); }
}

function parseTasks(content, sourcePath) {
  const tasks = [];
  (content || '').split(/\r?\n/).forEach((line, index) => {
    // Match OpenSpec 1.14 task-progress semantics, including unusual/empty markers,
    // nested/ordered lists and fenced examples. Only x means done; links stay links.
    const match = line.match(/^\s*(?:[-*+]|\d{1,9}[.)])\s*\[(?:\s*([^\]\s]?)\s*\](?![([])|\s+\])\s*(.*)/);
    if (!match) return;
    let description = match[2].trim();
    let id = `line-${index + 1}`;
    let role = null;
    const number = description.match(/^(\d+(?:\.\d+)+|\d+)\.?\s+/);
    if (number) { id = number[1]; description = description.slice(number[0].length); }
    const rolePrefix = description.match(/^\[(SA|Frontend|Backend|QA|FE|BE)\]\s*/);
    if (rolePrefix) {
      role = ({ FE: 'Frontend', BE: 'Backend' })[rolePrefix[1]] || rolePrefix[1];
      description = description.slice(rolePrefix[0].length);
      if (!number) {
        const after = description.match(/^(\d+(?:\.\d+)+|\d+)\.?\s+/);
        if (after) { id = after[1]; description = description.slice(after[0].length); }
      }
    }
    requireValue(text(description, 4000), 'A task has an empty or oversized description.');
    tasks.push({ id, description, done: (match[1] || '').toLowerCase() === 'x', line: index + 1, sourcePath, role });
    requireValue(tasks.length <= MAX_TASKS, 'A requirement exceeded the 500-task limit.');
  });
  unique(tasks.map(task => task.id), 'Duplicate task IDs in a requirement.');
  return tasks;
}

function artifact(id, target, root, warnings) {
  const content = readFile(target, root);
  if (content === null) warnings.push(`Missing ${id} artifact: ${path.relative(root, target)}.`);
  return { id, path: target, status: content === null ? 'missing' : 'present', content: content || '' };
}

function specsArtifact(changeRoot, workspace, warnings) {
  const target = path.join(changeRoot, 'specs');
  const pieces = [];
  let combinedBytes = 0;
  let entryCount = 0;
  function scan(directory, depth) {
    requireValue(depth <= 8, 'A requirement exceeded the specification directory depth limit.');
    requireValue(safePath(directory, workspace) && fs.statSync(directory).isDirectory(), 'Expected a specs directory.');
    const entries = fs.readdirSync(directory, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name));
    entryCount += entries.length;
    requireValue(entryCount <= 500, 'A requirement exceeded the specification directory entry limit.');
    for (const entry of entries) {
      requireValue(!entry.isSymbolicLink(), 'Symlinked specification paths are not supported.');
      const file = path.join(directory, entry.name);
      if (entry.isDirectory()) {
        requireValue(/^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$/.test(entry.name), 'Invalid specification directory name.');
        scan(file, depth + 1);
      } else if (entry.name === 'spec.md') {
        const content = readFile(file, workspace);
        requireValue(content !== null, 'A specification changed while it was being read; refresh to try again.');
        if (!content.trim()) warnings.push(`Empty specification: ${path.relative(workspace, file)}.`);
        const piece = `# ${path.relative(workspace, file)}\n\n${content}`;
        combinedBytes += Buffer.byteLength(piece, 'utf8') + (pieces.length ? 7 : 0);
        requireValue(combinedBytes <= MAX_METADATA, 'Combined requirement specifications exceeded the 128 KiB limit.');
        pieces.push(piece);
        requireValue(pieces.length <= 20, 'A role change exceeded the 20-capability limit.');
      }
    }
  }
  if (safePath(target, workspace)) scan(target, 0);
  if (!pieces.length) warnings.push('Missing specs artifact: no capability spec.md files found.');
  const content = pieces.join('\n\n---\n\n');
  requireValue(Buffer.byteLength(content, 'utf8') <= MAX_METADATA, 'Combined requirement specifications exceeded the 128 KiB limit.');
  return { id: 'specs', path: target, status: pieces.length ? 'present' : 'missing', content };
}

const CHANGE = /^(SA|FE|BE|QA)-([A-Z][A-Z0-9]*)-([0-9]+)-([a-z0-9]+(?:-[a-z0-9]+)*)$/;
const PREFIX_ROLE = { SA: 'SA', FE: 'Frontend', BE: 'Backend', QA: 'QA' };
function context(content) {
  const labels = { 'Requirement title': 200, 'Requirement summary': 4000, 'Spec title': 200,
    Owner: 200, 'Role note': 4000, State: 20, Note: 4000 };
  const result = {}; let active = false, key = null, seen = false, fenced = false;
  for (const line of content.split(/\r?\n/)) {
    if (/^\s*(`{3,}|~{3,})/.test(line)) { fenced = !fenced; continue; }
    if (fenced) continue;
    if (line.trim() === '## Kanban') { requireValue(!seen, 'Duplicate Kanban section.'); active = seen = true; key = null; continue; }
    if (/^#{1,2}\s/.test(line)) { active = false; key = null; }
    if (!active) continue;
    const field = line.match(/^[-*+] ([^:]+):(?: (.*))?$/);
    if (field && Object.hasOwn(labels, field[1])) {
      key = field[1]; requireValue(!Object.hasOwn(result, key), `Duplicate Kanban ${key} field.`); result[key] = field[2] || '';
    } else if (field) key = null;
    else if (/^  /.test(line) && key) result[key] += '\n' + line.slice(2);
    else if (line.trim()) key = null;
  }
  for (const [name, value] of Object.entries(result)) requireValue(text(value, labels[name], true), `Invalid Kanban ${name} field.`);
  requireValue(!Object.hasOwn(result, 'State') || ['backlog', 'in_progress', 'blocked'].includes(result.State), 'Invalid Kanban State field.');
  return result;
}
function roleChange(name, match, workspace) {
  const root = path.join(workspace, 'openspec', 'changes', name), warnings = [];
  const artifacts = [artifact('proposal', path.join(root, 'proposal.md'), workspace, warnings),
    artifact('design', path.join(root, 'design.md'), workspace, warnings), specsArtifact(root, workspace, warnings),
    artifact('tasks', path.join(root, 'tasks.md'), workspace, warnings)];
  const display = context(artifacts[0].content), role = PREFIX_ROLE[match[1]];
  const metadata = readFile(path.join(root, '.openspec.yaml'), workspace) || '';
  const schema = metadata.match(/^schema:\s*([a-z-]+)\s*$/m)?.[1] || 'spec-driven';
  requireValue(['spec-driven', ROLE_SCHEMAS[role]].includes(schema), `${name}: schema must match role.`);
  const source = readFile(path.join(root, 'scope.json'), workspace);
  let scope = null;
  requireValue(source !== null || schema === 'spec-driven', `${name}: missing scope.json.`);
  if (source !== null) {
    try { scope = validateRepositoryScope(JSON.parse(source), name); }
    catch (error) { throw new CollectorError(error.message); }
  }
  const tasks = parseTasks(artifacts[3].content, artifacts[3].path).map(task => {
    requireValue(task.role === null || task.role === role, `Every task in ${name} must belong to ${role}.`);
    return { ...task, role, specId: name };
  });
  const complete = tasks.filter(task => task.done).length;
  if (!tasks.length) warnings.push('No tracked tasks; completion is unverified.');
  if (artifacts.some(item => !item.content.trim())) warnings.push('Planning or task content is missing or empty; completion is unverified.');
  const state = tasks.length && complete === tasks.length && !warnings.length ? 'done'
    : display.State === 'blocked' ? 'blocked' : complete || display.State === 'in_progress' ? 'in_progress' : 'backlog';
  return { display, spec: { id: name, change: name, title: display['Spec title'] || match[4].replaceAll('-', ' '), role,
    schema, scope, state, note: display.Note || '', complete, total: tasks.length, tasks, artifacts, warnings } };
}
function requirement(id, entries) {
  const specs = entries.map(entry => entry.spec).sort((a, b) => ROLE_IDS.indexOf(a.role) - ROLE_IDS.indexOf(b.role) || (a.id < b.id ? -1 : 1)), warnings = specs.flatMap(spec => spec.warnings.map(w => `${spec.id}: ${w}`));
  const displayValue = (label, fallback) => {
    const values = [...new Set(entries.map(entry => entry.display[label]).filter(Boolean))];
    if (values.length > 1) warnings.push(`Conflicting ${label} values; using the first change in folder-name order.`);
    return values[0] || fallback;
  };
  const title = displayValue('Requirement title', id), summary = displayValue('Requirement summary', '');
  const tasks = specs.flatMap(spec => spec.tasks);
  requireValue(specs.length <= 20, 'A requirement exceeded the 20-spec limit.');
  requireValue(tasks.length <= MAX_TASKS, 'A requirement exceeded the 500-task limit.');
  const roles = ROLE_IDS.map((id, index) => {
    const own = entries.filter(entry => entry.spec.role === id), ownSpecs = own.map(entry => entry.spec), ownTasks = ownSpecs.flatMap(spec => spec.tasks);
    if (!own.length) warnings.push(`${id} has no role changes; completion is unverified.`);
    const state = own.length && ownSpecs.every(spec => spec.state === 'done') ? 'done' : ownSpecs.some(spec => spec.state === 'blocked') ? 'blocked'
      : ownSpecs.some(spec => ['done', 'in_progress'].includes(spec.state)) ? 'in_progress' : 'backlog';
    const values = key => [...new Set(own.map(entry => entry.display[key]).filter(Boolean))].join(' · ');
    const owner = values('Owner') || 'Unassigned', note = values('Role note');
    requireValue(text(owner, 4000) && text(note, 80000, true), 'Aggregated role context exceeds its limit.');
    return { id, label: ROLE_LABELS[index], owner, note, state, specs: ownSpecs.map(spec => spec.id), tasks: ownTasks,
      complete: ownTasks.filter(task => task.done).length, total: ownTasks.length };
  });
  const rolesComplete = roles.filter(role => role.state === 'done').length;
  const stage = roles.some(role => role.state === 'blocked') ? 'blocked' : rolesComplete === 4 ? 'done'
    : roles.every(role => role.state === 'backlog') ? 'backlog' : roles[0].state !== 'done' ? 'sa'
      : roles[1].state !== 'done' || roles[2].state !== 'done' ? 'implementation' : 'qa';
  return { id, title, summary, stage, roles, complete: tasks.filter(task => task.done).length, total: tasks.length,
    rolesComplete, tasks, warnings, specs };
}

function errorResult(error) {
  return { version: 1, kind: 'error', message: error instanceof CollectorError ? error.message : 'Could not read the local OpenSpec store. Check its directory and file permissions.' };
}

async function collect(input, { cwd = process.cwd() } = {}) {
  try {
    requireValue(object(input) && fields(input, ['action']) && input.action === 'board', 'Unsupported collector request.');
    requireValue(text(cwd, 4096) && path.isAbsolute(cwd) && !/[\r\n]/.test(cwd) && !localSegment(cwd), 'Workspace must be an absolute local store path.');
    const workspace = path.resolve(cwd);
    requireValue(safePath(workspace, workspace) && fs.statSync(workspace).isDirectory(), 'Store directory is unavailable.');
    const changes = path.join(workspace, 'openspec', 'changes');
    requireValue(safePath(changes, workspace) && fs.statSync(changes).isDirectory(), 'Missing openspec/changes directory. Select an OpenSpec store directory.');
    const entries = fs.readdirSync(changes, { withFileTypes: true }).sort((a, b) => a.name < b.name ? -1 : a.name > b.name ? 1 : 0);
    requireValue(entries.length <= 1000, 'The changes directory exceeded its entry limit.');
    const groups = new Map();
    for (const entry of entries) {
      if (entry.name === 'archive') continue;
      requireValue(!entry.isSymbolicLink(), 'Symlinked change paths are not supported.');
      const match = entry.name.match(CHANGE);
      if (!match) { requireValue(!/^(?:SA|FE|BE|QA)-/i.test(entry.name), `Malformed role change folder: ${entry.name}.`); continue; }
      requireValue(entry.isDirectory() && entry.name.length <= 160, 'Role change must be a directory with an identity of at most 160 characters.');
      const id = `${match[2]}-${match[3]}`;
      if (!groups.has(id)) groups.set(id, []);
      groups.get(id).push(roleChange(entry.name, match, workspace));
      requireValue(groups.size <= MAX_REQUIREMENTS, 'The store exceeded the 50-requirement limit.');
    }
    const scoped = new Map([...groups.values()].flat().map(entry => [entry.spec.id, entry.spec.scope]));
    for (const [id, scope] of scoped) if (scope) {
      try { validateRepositoryScope(scope, id, ref => scoped.get(ref)); }
      catch (error) { throw new CollectorError(error.message); }
    }
    const result = { version: 3, kind: 'board', workspace, name: path.basename(workspace) || 'OpenSpec store',
      description: 'Requirements discovered from role change folders', generatedAt: new Date().toISOString(),
      requirements: [...groups].sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0).map(([id, items]) => requirement(id, items)) };
    requireValue(Buffer.byteLength(JSON.stringify(result), 'utf8') <= MAX_OUTPUT, 'Store data exceeded the 512 KiB output limit.');
    return result;
  } catch (error) { return errorResult(error); }
}

async function main(encoded = process.argv[module.id === '[eval]' ? 1 : 2]) {
  let result;
  try {
    requireValue(typeof encoded === 'string' && encoded.length > 0 && encoded.length <= 4096
      && /^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(encoded), 'Expected one base64-encoded JSON input.');
    const decoded = Buffer.from(encoded, 'base64');
    requireValue(decoded.toString('base64') === encoded && Buffer.from(decoded.toString('utf8'), 'utf8').equals(decoded), 'Invalid input encoding.');
    let input;
    try { input = JSON.parse(decoded.toString('utf8')); } catch { throw new CollectorError('Input was not valid JSON.'); }
    result = await collect(input);
  } catch (error) { result = errorResult(error); }
  process.stdout.write(JSON.stringify(result) + '\n');
  if (result.kind === 'error') process.exitCode = 1;
}

module.exports = { collect, main };
if (require.main === module || module.id === '[eval]') main();
