import assert from "node:assert/strict";
import { copyFile, mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { JSDOM } from "jsdom";
import { validateApp } from "../scripts/validate.mjs";
import { activate } from "../extension.js";

const appRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

async function validationFixture(t, source = "export function activate() {}\n") {
  const root = await mkdtemp(path.join(os.tmpdir(), "openspec-app-test-"));
  t.after(() => rm(root, { recursive: true, force: true }));
  await writeFile(path.join(root, "package.json"), JSON.stringify({ type: "module" }));
  await copyFile(path.join(appRoot, "canvas-extension.json"), path.join(root, "canvas-extension.json"));
  await mkdir(path.join(root, "dist"));
  await writeFile(path.join(root, "dist", "extension.js"), source);
  return root;
}

test("the published browser bundle matches the validated single-file build", async () => {
  await validateApp(appRoot);
  await validateApp(appRoot, { dist: true });
  const [published, built] = await Promise.all([
    readFile(path.join(appRoot, "extension.js")),
    readFile(path.join(appRoot, "dist", "extension.js")),
  ]);
  assert.deepEqual(published, built);
});

test("validation rejects runtime imports, Node globals, and extra assets", async t => {
  const invalidModules = [
    'import value from "external-library"; export function activate() {}',
    'export function activate() { return import("./chunk.js"); }',
    'export function activate() { return process.env.KEY; }',
    'export function activate() { return require("node:fs"); }',
  ];
  for (const source of invalidModules) {
    const root = await validationFixture(t, source);
    await assert.rejects(validateApp(root, { dist: true }));
  }
  const root = await validationFixture(t);
  await writeFile(path.join(root, "dist", "extra.css"), "body {}");
  await assert.rejects(validateApp(root, { dist: true }), /exactly/);
});

test("validation rejects broken syntax and undeclared entrypoints", async t => {
  const root = await validationFixture(t, "export function activate( {\n");
  await assert.rejects(validateApp(root, { dist: true }));
  await writeFile(path.join(root, "dist", "extension.js"), "export function somethingElse() {}\n");
  await assert.rejects(validateApp(root, { dist: true }), /activate/);
  const manifestPath = path.join(root, "canvas-extension.json");
  const manifest = JSON.parse(await readFile(manifestPath, "utf8"));
  manifest.entrypoint = "../outside.js";
  await writeFile(manifestPath, JSON.stringify(manifest));
  await assert.rejects(validateApp(root, { dist: true }), /metadata/);
});

const WORKSPACE = "/Users/oka/Desktop/openHanda-demo";
const GENERATED_AT = "2026-10-03T08:00:00.000Z";
const CHANGE = "add-task-completion";

function overview(changes = [{
  name: CHANGE, completedTasks: 1, totalTasks: 2,
  lastModified: GENERATED_AT, status: "in-progress",
}]) {
  return { version: 1, kind: "overview", workspace: WORKSPACE, generatedAt: GENERATED_AT, changes };
}

function change(overrides = {}) {
  return {
    version: 1, kind: "change", workspace: WORKSPACE, generatedAt: GENERATED_AT,
    name: CHANGE, schemaName: "spec-driven", planningComplete: true,
    artifacts: [
      { id: "proposal", status: "done", outputPath: "proposal.md", requires: [] },
      { id: "tasks", status: "done", outputPath: "tasks.md", requires: ["proposal"] },
    ],
    progress: { total: 2, complete: 1, remaining: 1 },
    tasks: [
      { id: "1.1", description: "<img src=x onerror=globalThis.pwned=true>", done: true,
        sourcePath: `${WORKSPACE}/openspec/changes/${CHANGE}/tasks.md`, line: 3 },
      { id: "1.2", description: "Verify task completion", done: false,
        sourcePath: `${WORKSPACE}/openspec/changes/${CHANGE}/tasks.md`, line: 4 },
    ],
    applyState: "ready", instruction: "Complete the remaining task.", ...overrides,
  };
}

function response(data, overrides = {}) {
  return { stdout: JSON.stringify(data), stderr: "", exit_code: 0, order: 0, ...overrides };
}

async function eventually(condition, label = "expected state") {
  const deadline = Date.now() + 1500;
  while (!condition()) {
    if (Date.now() > deadline) assert.fail(`Timed out waiting for ${label}`);
    await new Promise(resolve => setTimeout(resolve, 5));
  }
}

function mountApp(t, { route = "", kind = "local", request, automation } = {}) {
  const dom = new JSDOM("<!doctype html><main></main>", { url: "http://localhost/" });
  const saved = new Map();
  for (const key of ["window", "document", "HTMLElement", "Node", "Event", "CustomEvent", "localStorage"]) {
    saved.set(key, Object.getOwnPropertyDescriptor(globalThis, key));
    Object.defineProperty(globalThis, key, { configurable: true, writable: true, value: dom.window[key] });
  }
  const container = dom.window.document.querySelector("main");
  const requests = [];
  const navigations = [];
  let mount;
  let unregistered = 0;
  const host = {
    apiVersion: "1", extension: { name: "openspec-progress" }, backend: { id: "test-local", kind },
    registerPage(id, handler) {
      assert.equal(id, "progress");
      mount = handler;
      return () => { unregistered++; };
    },
    agentServer: {
      async request(options) {
        if (automation && (options.method === 'GET' || options.body?.command.startsWith('python3 '))) {
          const encoded = options.body?.command.match(/'([A-Za-z0-9+/=]+)'$/)?.[1];
          const input = encoded ? JSON.parse(Buffer.from(encoded, 'base64').toString('utf8')) : undefined;
          requests.push({ ...options, input });
          return automation(options, input);
        }
        assert.equal(options.method, "POST");
        assert.equal(options.path, "/api/bash/execute_bash_command");
        assert.equal(options.body.timeout, 30);
        assert.match(options.body.command, /^node -e '/);
        const encoded = options.body.command.match(/'([A-Za-z0-9+/=]+)'$/)?.[1];
        assert.ok(encoded, "collector input is a separate base64-encoded argument");
        const input = JSON.parse(Buffer.from(encoded, "base64").toString("utf8"));
        requests.push({ ...options, input });
        return request ? request(input, options, requests.length)
          : response(input.action === "overview" ? overview() : change());
      },
    },
  };
  const deactivate = activate(host);
  assert.equal(typeof mount, "function");
  const render = (path = route) => mount({ container, path, navigate: value => navigations.push(value) });
  const unmount = render();
  t.after(() => {
    deactivate();
    dom.window.close();
    for (const [key, descriptor] of saved) {
      if (descriptor) Object.defineProperty(globalThis, key, descriptor);
      else delete globalThis[key];
    }
  });
  return { dom, container, requests, navigations, unmount, render, deactivate,
    get unregistered() { return unregistered; } };
}

test("the page reads progress safely without dispatching work on mount", async t => {
  const app = mountApp(t);
  await eventually(() => app.container.querySelectorAll(".osp-task").length === 2, "task list");
  assert.equal(app.container.querySelector("h1").textContent, "OpenSpec progress");
  assert.deepEqual(app.requests.map(item => item.input), [
    { action: "overview" }, { action: "change", change: CHANGE },
  ]);
  assert.ok(app.requests.every(item => item.body.cwd === WORKSPACE));
  assert.match(app.container.textContent, /1 \/ 2 checked/);
  assert.match(app.container.textContent, /<img src=x onerror=globalThis.pwned=true>/);
  assert.equal(app.container.querySelectorAll("img, input[type=checkbox]").length, 0);
  assert.deepEqual([...app.container.querySelectorAll("button")].map(item => item.textContent), ["Refresh", "Load project", "Connect Explore", "Run Explore", "Start another request"]);
  assert.equal(app.container.querySelector('.osp-automation').open, false);
  assert.match(app.container.textContent, /do not certify tests, review, or release readiness/);
  app.container.querySelector(".osp-change").click();
  assert.deepEqual(app.navigations, [`/extensions/openspec-progress/progress/changes/${CHANGE}`]);
});

const AUTOMATION = { id: '9b24e837-4810-4c43-acbb-31c690980755', name: 'OpenSpec 01 · Explore' };
const RUN_ID = 'ac739731-e649-4f7c-b242-1b877bab83e4';
const SERVICE = { url_from_agent: 'http://localhost:18021', api_prefix: '/api/automation', auth_env_var: 'OPENHANDS_AUTOMATION_API_KEY' };

function automationStub(actions, { ready = true, dispatch, advertised = true } = {}) {
  return async (options, input) => {
    if (options.path === '/server_info') return advertised ? { runtime_services: { services: { automation: SERVICE } } } : {};
    if (options.path === '/api/file/home') return { home: '/Users/oka' };
    assert.equal(options.path, '/api/bash/execute_bash_command');
    assert.equal(options.body.cwd, '/Users/oka');
    assert.deepEqual(input.service, SERVICE);
    actions.push(input);
    if (input.action === 'dispatch') return dispatch ? dispatch(input) : response({ version: 1, kind: 'dispatch',
      automation_id: input.input.automation_id, request_id: input.input.request_id, run_id: RUN_ID });
    return response({ version: 1, kind: input.action, automation: AUTOMATION,
      ready: input.action === 'setup' || ready, message: 'Connect the existing automation.' });
  };
}

async function openAutomation(app) {
  await eventually(() => app.container.querySelectorAll('.osp-task').length === 2);
  app.container.querySelector('.osp-automation').open = true;
  await eventually(() => app.container.querySelector('.osp-automation-connection p').textContent.match(/Connected|Connect the|does not advertise/));
}

function submitExplore(app, params = '{"focus":"无障碍","limit":3}') {
  app.container.querySelector('[aria-label="Requirement / prompt"]').value = 'Explore 标签; keep $(commands) and quotes \' as data.';
  app.container.querySelector('[aria-label="Parameters (optional JSON object)"]').value = params;
  app.container.querySelector('.osp-explore-form').dispatchEvent(new app.dom.window.Event('submit', { cancelable: true }));
}

test('Explore connects only on explicit action and sends Unicode inputs to the existing automation', async t => {
  const actions = [];
  const app = mountApp(t, { automation: automationStub(actions, { ready: false }) });
  await openAutomation(app);
  assert.deepEqual(actions.map(a => a.action), ['probe']);
  app.container.querySelector('.osp-automation-connection button').click();
  await eventually(() => !app.container.querySelector('.osp-explore-form button').disabled);
  assert.deepEqual(actions.map(a => a.action), ['probe', 'setup']);
  submitExplore(app);
  await eventually(() => app.container.querySelector('.osp-run-link'));
  const input = actions.at(-1).input;
  assert.equal(input.automation_id, AUTOMATION.id);
  assert.equal(input.workspace, WORKSPACE);
  assert.equal(input.change, CHANGE);
  assert.match(input.request, /标签.*\$\(commands\)/);
  assert.deepEqual(input.parameters, { focus: '无障碍', limit: 3 });
  assert.ok(actions.at(-1).home === '/Users/oka');
  app.container.querySelector('.osp-run-link').click();
  assert.equal(app.navigations.at(-1), `/automations/${AUTOMATION.id}?run=${RUN_ID}`);
  const stored = app.dom.window.localStorage.getItem('openhands.apps.openspec-progress:test-local:last-explore');
  assert.doesNotMatch(stored, /标签|focus|request"|secret/);
  app.unmount();
  app.render();
  await openAutomation(app);
  assert.match(app.container.querySelector('.osp-automation-result').textContent, /Explore was submitted/);
  assert.equal(app.container.querySelector('.osp-explore-form button').disabled, true);
  assert.equal(actions.filter(a => a.action === 'dispatch').length, 1);
});

test('invalid input cannot dispatch and duplicate submits or late results cannot recreate an unmounted page', async t => {
  const actions = [];
  let finish;
  const app = mountApp(t, { automation: automationStub(actions, { dispatch: input => new Promise(resolve => {
    finish = () => resolve(response({ version: 1, kind: 'dispatch', automation_id: AUTOMATION.id,
      request_id: input.input.request_id, run_id: RUN_ID }));
  }) }) });
  await openAutomation(app);
  for (const params of ['broken JSON', '[]', 'null']) {
    submitExplore(app, params);
    assert.equal(actions.filter(a => a.action === 'dispatch').length, 0);
    assert.match(app.container.querySelector('.osp-automation-result').textContent, /Parameters must/);
  }
  submitExplore(app);
  submitExplore(app);
  await eventually(() => finish);
  assert.equal(actions.filter(a => a.action === 'dispatch').length, 1);
  app.unmount();
  finish();
  await new Promise(resolve => setTimeout(resolve, 10));
  assert.equal(app.container.children.length, 0);
});

test('uncertain dispatch requires history inspection and never retries on refresh', async t => {
  const actions = [];
  const app = mountApp(t, { automation: automationStub(actions, { dispatch: async () => { throw new Error('connection lost'); } }) });
  await openAutomation(app);
  submitExplore(app);
  await eventually(() => app.container.querySelector('.osp-run-link'));
  assert.match(app.container.querySelector('.osp-automation-result').textContent, /may already have started/);
  app.unmount();
  app.render();
  await openAutomation(app);
  submitExplore(app);
  assert.equal(actions.filter(a => a.action === 'dispatch').length, 1);
});

test('unadvertised Automation service cannot execute a helper or guess an endpoint', async t => {
  const actions = [];
  const app = mountApp(t, { automation: automationStub(actions, { advertised: false }) });
  await openAutomation(app);
  assert.equal(actions.length, 0);
  assert.equal(app.container.querySelector('.osp-explore-form button').disabled, true);
});

test("invalid project paths cannot send an Agent Server command", async t => {
  const app = mountApp(t);
  await eventually(() => app.requests.length === 2 && app.container.querySelector('[aria-busy="false"]'));
  const input = app.container.querySelector('[aria-label="Project directory"]');
  input.value = "../not-an-absolute-project";
  app.container.querySelector("form").dispatchEvent(new app.dom.window.Event("submit", { bubbles: true, cancelable: true }));
  assert.equal(app.requests.length, 2);
  assert.match(app.container.querySelector('[role="alert"]').textContent, /absolute project directory/);
});

test("unknown routes and non-local backends do not query the Agent Server", async t => {
  await t.test("unknown route", async child => {
    const app = mountApp(child, { route: "changes/../escape" });
    assert.equal(app.requests.length, 0);
    assert.match(app.container.textContent, /Page not found/);
    app.container.querySelector("button").click();
    assert.deepEqual(app.navigations, ["/extensions/openspec-progress/progress"]);
  });
  await t.test("non-local backend", async child => {
    const app = mountApp(child, { kind: "cloud" });
    assert.equal(app.requests.length, 0);
    assert.match(app.container.textContent, /supported Agent Server/);
  });
});

test("unavailable task progress never becomes a fabricated zero percent", async t => {
  const app = mountApp(t, {
    request: async input => response(input.action === "overview"
      ? overview([{ name: CHANGE, completedTasks: 0, totalTasks: 0, lastModified: GENERATED_AT, status: "no-tasks" }])
      : change({ planningComplete: false, progress: null, tasks: [], applyState: "blocked", instruction: "Write the tasks artifact first." })),
  });
  await eventually(() => app.container.textContent.includes("Write the tasks artifact first."));
  assert.match(app.container.textContent, /No tracked tasks/);
  assert.doesNotMatch(app.container.querySelector(".osp-metrics").textContent, /0%/);
  assert.doesNotMatch(app.container.querySelector(".osp-detail").textContent, /0%/);
  assert.equal(app.container.querySelectorAll(".osp-task").length, 0);
});

test("partial task evidence retains planning artifacts and labels unavailable tracking", async t => {
  const app = mountApp(t, {
    request: async input => response(input.action === "overview" ? overview() : change({
      progress: null,
      tasks: change().tasks.slice(0, 1),
      taskError: "Some task tracking files could not be read; completion is not verified.",
    })),
  });
  await eventually(() => app.container.querySelectorAll(".osp-artifact").length === 2, "planning artifacts");
  assert.match(app.container.querySelector(".osp-detail").textContent, /completion is not verified/);
  assert.equal(app.container.querySelector('[role="alert"]'), null);
  assert.doesNotMatch(app.container.querySelector(".osp-detail").textContent, /1 \/ 2 checked/);
});

test("an overview refresh failure explicitly labels the retained snapshot", async t => {
  let failed = false;
  const app = mountApp(t, {
    request: async input => {
      if (failed) throw new Error("network failed");
      return response(input.action === "overview" ? overview() : change());
    },
  });
  await eventually(() => app.container.querySelectorAll(".osp-task").length === 2);
  failed = true;
  app.container.querySelector(".osp-primary").click();
  await eventually(() => app.container.querySelector('[role="alert"]'));
  assert.match(app.container.querySelector('[role="alert"]').textContent, /Refresh failed.*previous snapshot/);
  assert.equal(app.container.querySelectorAll(".osp-task").length, 2);
});

test("a detail refresh failure clears old tasks while preserving the fresh overview", async t => {
  let failDetails = false;
  const app = mountApp(t, {
    request: async input => {
      if (failDetails && input.action === "change") throw new Error("detail unavailable");
      return response(input.action === "overview" ? overview() : change());
    },
  });
  await eventually(() => app.container.querySelectorAll(".osp-task").length === 2);
  failDetails = true;
  app.container.querySelector(".osp-primary").click();
  await eventually(() => app.container.querySelector('[role="alert"]'));
  assert.equal(app.container.querySelectorAll(".osp-task").length, 0);
  assert.equal(app.container.querySelectorAll(".osp-metric").length, 3);
  assert.match(app.container.querySelector(".osp-detail").textContent, /Cannot read OpenSpec/);
  assert.doesNotMatch(app.container.querySelector('[role="alert"]').textContent, /previous snapshot/);
});

for (const [label, result, expected] of [
  ["unfinished command", response(overview(), { exit_code: -1 }), /could not be read reliably/],
  ["missing earlier output", response(overview(), { order: 1 }), /complete output/],
  ["malformed JSON", response(overview(), { stdout: "not JSON" }), /invalid output/],
  ["collector error", response({ version: 1, kind: "error", message: "Project root does not match." }, { exit_code: 1 }), /Project root does not match/],
]) {
  test(`${label} cannot render successful progress`, async t => {
    const app = mountApp(t, { request: async () => result });
    await eventually(() => app.container.querySelector('[role="alert"]'));
    assert.match(app.container.querySelector('[role="alert"]').textContent, expected);
    assert.equal(app.container.querySelectorAll(".osp-task, .osp-metric").length, 0);
    assert.equal(app.requests.length, 1);
  });
}

test("unmount ignores late results and remount creates one fresh view", async t => {
  let finishFirst;
  const app = mountApp(t, {
    request: (input, options, number) => number === 1
      ? new Promise(resolve => { finishFirst = resolve; })
      : response(input.action === "overview" ? overview() : change()),
  });
  assert.equal(app.requests.length, 1);
  app.unmount();
  assert.equal(app.container.children.length, 0);
  finishFirst(response(overview()));
  await new Promise(resolve => setTimeout(resolve, 10));
  assert.equal(app.container.children.length, 0);
  assert.equal(app.requests.length, 1);
  const unmountAgain = app.render();
  await eventually(() => app.container.querySelectorAll(".osp-task").length === 2);
  assert.equal(app.requests.length, 3);
  assert.equal(app.container.querySelectorAll(".osp-root").length, 1);
  assert.equal(app.container.querySelectorAll("style[data-openspec-progress]").length, 1);
  unmountAgain();
  assert.equal(app.container.children.length, 0);
});
