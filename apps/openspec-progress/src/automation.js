import bridgeSource from './automation_bridge.py?raw';

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const quote = value => "'" + value.replaceAll("'", "'\\''") + "'";

export function validateExploreInput({ workspace, change, request, parameters }) {
  if (typeof workspace !== 'string' || !workspace.startsWith('/') || /[\0\r\n]/.test(workspace)) {
    throw new Error('Load a valid local OpenSpec project first.');
  }
  if (typeof change !== 'string' || change.length > 100 || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(change)) {
    throw new Error('Enter a kebab-case change name, such as add-task-labels.');
  }
  if (typeof request !== 'string' || !request.trim() || request.length > 10000) {
    throw new Error('Enter an Explore prompt of at most 10000 characters.');
  }
  if (!parameters || typeof parameters !== 'object' || Array.isArray(parameters) ||
      new TextEncoder().encode(JSON.stringify(parameters)).length > 8192) {
    throw new Error('Parameters must be a JSON object of at most 8 KiB.');
  }
  return { workspace, change, request, parameters };
}

export async function callAutomation(host, action, input) {
  // The owning backend supplies service coordinates. The fixed helper uses the
  // launcher's injected key entirely server-side; the browser never reads it.
  const [info, home] = await Promise.all([
    host.agentServer.request({ method: 'GET', path: '/server_info' }),
    host.agentServer.request({ method: 'GET', path: '/api/file/home' }),
  ]);
  const service = info?.runtime_services?.services?.automation;
  if (!service || typeof home?.home !== 'string') {
    throw new Error('This backend does not advertise a supported local Automation service. Open the app through the native Canvas stack.');
  }
  const payload = { action, service, home: home.home, ...(input ? { input } : {}) };
  const encoded = btoa(Array.from(new TextEncoder().encode(JSON.stringify(payload)), byte => String.fromCharCode(byte)).join(''));
  const output = await host.agentServer.request({
    method: 'POST', path: '/api/bash/execute_bash_command',
    body: { command: `python3 -c ${quote(bridgeSource)} ${quote(encoded)}`, cwd: home.home, timeout: 30 },
  });
  if (!output || output.order !== 0 || !Number.isInteger(output.exit_code) ||
      typeof output.stdout !== 'string' || output.stdout.length > 128 * 1024) {
    throw new Error('The Automation request did not return complete output. Inspect Automation history before starting another request.');
  }
  let data;
  try { data = JSON.parse(output.stdout); }
  catch { throw new Error('Invalid Automation response. Inspect Automation history before starting another request.'); }
  if (data?.version === 1 && data.kind === 'error' && typeof data.message === 'string') throw new Error(data.message.slice(0, 600));
  if (output.exit_code !== 0 || data?.version !== 1 || data.kind !== action) throw new Error('Unexpected Automation response. Inspect its history before retrying.');
  if (action === 'dispatch') {
    if (!UUID.test(data.run_id) || data.automation_id !== input.automation_id || data.request_id !== input.request_id) {
      throw new Error('The returned run does not match this request. Inspect Automation history.');
    }
  } else if (typeof data.ready !== 'boolean' || !UUID.test(data.automation?.id) || typeof data.automation?.name !== 'string') {
    throw new Error('Invalid Automation connection details.');
  }
  return data;
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

export function mountAutomation({ host, container, navigate, getWorkspace, getChange }) {
  let disposed = false;
  let connected = null;
  let busy = false;
  let opened = false;
  let last = null;
  const key = `openhands.apps.openspec-progress:${host.backend.id}:last-explore`;
  try {
    const stored = JSON.parse(localStorage.getItem(key));
    if (stored && UUID.test(stored.request_id) && UUID.test(stored.automation_id) &&
        (!stored.run_id || UUID.test(stored.run_id))) last = stored;
  } catch { /* Storage is optional. */ }
  const remember = value => {
    last = value;
    try { if (value) localStorage.setItem(key, JSON.stringify(value)); else localStorage.removeItem(key); } catch { /* Optional. */ }
  };
  const panel = el('details', 'osp-automation');
  panel.append(el('summary', '', 'Run Explore automation'));
  const body = el('div', 'osp-automation-body');
  body.append(el('p', 'osp-muted', 'Send a requirement to the existing OpenSpec Explore automation. It investigates and stops for your review.'));
  const connection = el('div', 'osp-automation-connection');
  const connectionText = el('p', 'osp-muted', 'Open this panel to check the connection.');
  const connect = el('button', 'osp-button', 'Connect Explore');
  connect.type = 'button';
  connect.disabled = true;
  connection.append(connectionText, connect);
  const disclosure = el('p', 'osp-disclosure', 'Connecting registers a signed local request source and saves its key privately on Agent Server. It adds no schedule and starts no agent.');
  const form = el('form', 'osp-explore-form');
  const changeLabel = el('label', 'osp-field');
  changeLabel.append(el('span', 'osp-label', 'Change name'));
  const change = el('input');
  change.setAttribute('aria-label', 'Change name');
  change.placeholder = 'add-task-labels';
  change.maxLength = 100;
  changeLabel.append(change);
  const promptLabel = el('label', 'osp-field');
  promptLabel.append(el('span', 'osp-label', 'Requirement / prompt'));
  const prompt = el('textarea');
  prompt.setAttribute('aria-label', 'Requirement / prompt');
  prompt.placeholder = 'Describe the requirement, questions, and constraints to explore…';
  prompt.maxLength = 10000;
  prompt.rows = 4;
  promptLabel.append(prompt);
  const paramLabel = el('label', 'osp-field');
  paramLabel.append(el('span', 'osp-label', 'Parameters (optional JSON object)'));
  const params = el('textarea');
  params.setAttribute('aria-label', 'Parameters (optional JSON object)');
  params.value = '{}';
  params.rows = 2;
  params.spellcheck = false;
  paramLabel.append(params);
  const controls = el('div', 'osp-actions');
  const submit = el('button', 'osp-button osp-primary', 'Run Explore');
  submit.type = 'submit';
  const another = el('button', 'osp-button', 'Start another request');
  another.type = 'button';
  another.hidden = true;
  controls.append(submit, another);
  form.append(changeLabel, promptLabel, paramLabel, el('p', 'osp-disclosure', 'This runs only Explore in this automation’s configured workspace and profile. Parameters are investigation context; they do not override execution settings.'), controls);
  const result = el('div', 'osp-automation-result');
  result.setAttribute('role', 'status');
  result.setAttribute('aria-live', 'polite');
  body.append(connection, disclosure, form, result);
  panel.append(body);
  container.append(panel);

  function updateControls() {
    submit.disabled = busy || !connected?.ready || Boolean(last);
    connect.disabled = busy || Boolean(connected?.ready);
    prompt.disabled = change.disabled = params.disabled = busy || Boolean(last);
    another.hidden = !last;
    another.disabled = busy;
    submit.textContent = busy ? 'Working…' : 'Run Explore';
  }
  function renderLast() {
    result.replaceChildren();
    if (!last) return;
    const link = el('a', 'osp-run-link', last.run_id ? 'Open automation run →' : 'Inspect automation history →');
    link.href = `/automations/${last.automation_id}${last.run_id ? `?run=${last.run_id}` : ''}`;
    link.addEventListener('click', event => { event.preventDefault(); navigate(link.getAttribute('href')); });
    result.append(el('p', '', last.run_id ? 'Explore was submitted. Open the run for status, logs, and its conversation.' :
      'This request may already have started. Inspect its history before starting another.'),
    el('code', 'osp-task-source', `Request ${last.request_id}`), link);
  }
  async function connectAction(action) {
    if (busy || disposed) return;
    busy = true;
    updateControls();
    connectionText.textContent = action === 'setup' ? 'Connecting the existing Explore automation…' : 'Checking the existing Explore automation…';
    try {
      const value = await callAutomation(host, action);
      if (disposed) return;
      connected = value;
      connectionText.textContent = value.ready ? `Connected · ${value.automation.name}` : value.message;
      if (value.ready) disclosure.hidden = true;
    } catch (error) {
      if (!disposed) connectionText.textContent = error.message || 'Cannot connect to the Automation service.';
    } finally {
      busy = false;
      if (!disposed) updateControls();
    }
  }
  panel.addEventListener('toggle', () => {
    if (!panel.open || opened) return;
    opened = true;
    change.value = getChange() || '';
    renderLast();
    connectAction('probe');
  });
  connect.addEventListener('click', () => connectAction('setup'));
  another.addEventListener('click', () => { remember(null); renderLast(); updateControls(); });
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (busy || last || !connected?.ready || disposed) return;
    let input;
    try {
      let parameters;
      try { parameters = JSON.parse(params.value); }
      catch { throw new Error('Parameters must be valid JSON, for example {"focus":"accessibility"}.'); }
      input = validateExploreInput({ workspace: getWorkspace(), change: change.value.trim(), request: prompt.value, parameters });
    } catch (error) { result.textContent = error.message; return; }
    busy = true;
    const attempt = { request_id: crypto.randomUUID(), automation_id: connected.automation.id };
    remember(attempt);
    updateControls();
    result.textContent = 'Submitting one Explore request…';
    try {
      const response = await callAutomation(host, 'dispatch', { ...input, ...attempt });
      remember({ ...attempt, run_id: response.run_id });
      if (!disposed) renderLast();
    } catch (error) {
      if (!disposed) {
        renderLast();
        result.prepend(el('p', 'osp-error', error.message || 'The request outcome is unknown. Inspect Automation history.'));
      }
    } finally {
      busy = false;
      if (!disposed) updateControls();
    }
  });
  updateControls();
  return () => { disposed = true; panel.remove(); };
}
