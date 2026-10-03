import styles from './styles.css';
import { loadOverview, loadChange, validateWorkspace } from './client.js';
import { mountAutomation } from './automation.js';

const DEFAULT_WORKSPACE = '/Users/oka/Desktop/openHanda-demo';
const STATE_LABELS = { done: 'Done', ready: 'Ready to write', blocked: 'Blocked', skipped: 'Skipped' };

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
function button(text, className, handler) {
  const node = el('button', className, text);
  node.type = 'button';
  node.addEventListener('click', handler);
  return node;
}
function formatDate(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Unknown' : date.toLocaleString(undefined, {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}
function progressBar(done, total, label) {
  const bar = el('div', 'osp-progress');
  bar.setAttribute('role', 'progressbar');
  bar.setAttribute('aria-label', label);
  bar.setAttribute('aria-valuemin', '0');
  bar.setAttribute('aria-valuemax', String(total || 1));
  bar.setAttribute('aria-valuenow', String(done));
  const fill = el('span');
  fill.style.width = `${total ? Math.round(done / total * 100) : 0}%`;
  bar.append(fill);
  return bar;
}

export function activate(host) {
  if (host.apiVersion !== '1') throw new Error('OpenSpec progress requires Canvas host API 1.');
  const base = `/extensions/${encodeURIComponent(host.extension.name)}/progress`;
  const storageKey = `openhands.apps.openspec-progress:${host.backend.id}:workspace`;
  let remembered = DEFAULT_WORKSPACE;
  try { remembered = validateWorkspace(localStorage.getItem(storageKey) || DEFAULT_WORKSPACE); } catch { /* Use the default. */ }
  const disposers = new Set();

  const unregister = host.registerPage('progress', ({ container, path, navigate }) => {
    let disposed = false;
    let generation = 0;
    let workspace = remembered;
    let snapshot = null;
    let detail = null;
    let busy = false;
    let disposeAutomation;
    const requested = path ? /^changes\/([a-z0-9]+(?:-[a-z0-9]+)*)$/.exec(path) : null;
    const root = el('section', 'osp-root');
    const style = el('style');
    style.dataset.openspecProgress = 'true';
    style.textContent = styles;
    root.append(style);
    container.append(root);

    function dispose() {
      disposed = true;
      generation++;
      disposeAutomation?.();
      root.remove();
      disposers.delete(dispose);
    }
    disposers.add(dispose);

    if (path && !requested) {
      root.append(el('h1', '', 'Page not found'), el('p', 'osp-muted', 'This OpenSpec progress route is not available.'),
        button('Back to progress', 'osp-button', () => navigate(base)));
      return dispose;
    }
    if (host.backend.kind !== 'local') {
      root.append(el('h1', '', 'OpenSpec progress'),
        el('p', 'osp-error', 'Connect a supported Agent Server with a local OpenSpec workspace to view progress.'));
      return dispose;
    }

    const header = el('header', 'osp-header');
    const heading = el('div');
    heading.append(el('p', 'osp-eyebrow', 'PROJECT WORKSPACE'), el('h1', '', 'OpenSpec progress'),
      el('p', 'osp-subtitle', 'Planning artifacts and implementation checklists, directly from OpenSpec.'));
    const actions = el('div', 'osp-actions');
    const refresh = button('Refresh', 'osp-button osp-primary', () => refreshData());
    actions.append(el('span', 'osp-readonly', 'Manual actions'), refresh);
    header.append(heading, actions);

    const form = el('form', 'osp-project');
    const label = el('label', 'osp-field');
    label.append(el('span', 'osp-label', 'Project directory'));
    const input = el('input');
    input.type = 'text';
    input.value = workspace;
    input.spellcheck = false;
    input.setAttribute('aria-label', 'Project directory');
    input.autocomplete = 'off';
    label.append(input);
    const load = el('button', 'osp-button', 'Load project');
    load.type = 'submit';
    form.append(label, load);
    form.addEventListener('submit', event => {
      event.preventDefault();
      if (busy) return;
      try {
        workspace = validateWorkspace(input.value.trim());
        remembered = workspace;
        try { localStorage.setItem(storageKey, workspace); } catch { /* Persistence is optional. */ }
        if (path) { navigate(base); return; }
        snapshot = null;
        detail = null;
        refreshData();
      } catch (error) { showError(error.message); }
    });

    const notice = el('div', 'osp-notice');
    notice.setAttribute('role', 'status');
    notice.setAttribute('aria-live', 'polite');
    const metrics = el('div', 'osp-metrics');
    const columns = el('div', 'osp-columns');
    const changePanel = el('section', 'osp-changes');
    const detailPanel = el('section', 'osp-detail');
    detailPanel.setAttribute('aria-label', 'Change details');
    columns.append(changePanel, detailPanel);
    const footer = el('footer', 'osp-footer', 'Task counts reflect OpenSpec checkboxes. They do not certify tests, review, or release readiness.');
    root.append(header, form, notice, metrics, columns, footer);
    const automationPanel = el('div');
    root.insertBefore(automationPanel, metrics);
    disposeAutomation = mountAutomation({ host, container: automationPanel, navigate,
      getWorkspace: () => snapshot?.workspace || '',
      getChange: () => requested?.[1] || snapshot?.changes[0]?.name || '',
    });

    function setBusy(value) {
      busy = value;
      refresh.disabled = value;
      load.disabled = value;
      input.disabled = value;
      refresh.textContent = value ? 'Refreshing…' : 'Refresh';
      root.setAttribute('aria-busy', String(value));
    }
    function showError(message, prefix = '') {
      notice.className = 'osp-notice osp-error';
      notice.setAttribute('role', 'alert');
      notice.textContent = prefix + message;
    }
    function renderOverview(selected) {
      metrics.replaceChildren();
      const changes = snapshot.changes;
      const total = changes.reduce((sum, change) => sum + change.totalTasks, 0);
      const complete = changes.reduce((sum, change) => sum + change.completedTasks, 0);
      for (const [labelText, value, hint] of [
        ['Active changes', String(changes.length), 'Not archived'],
        ['Tasks checked', `${complete} / ${total}`, total ? `${Math.round(complete / total * 100)}% of tracked tasks` : 'No tracked tasks'],
        ['Remaining tasks', String(total - complete), 'Across active changes'],
      ]) {
        const metric = el('div', 'osp-metric');
        metric.append(el('span', 'osp-label', labelText), el('strong', '', value), el('span', 'osp-muted', hint));
        metrics.append(metric);
      }
      changePanel.replaceChildren(el('h2', 'osp-panel-title', 'Active changes'));
      if (!changes.length) {
        changePanel.append(el('p', 'osp-empty', 'No active changes. Create a proposal with your OpenSpec skill, then refresh.'));
        return;
      }
      const list = el('ul', 'osp-change-list');
      for (const change of changes) {
        const item = el('li');
        const link = el('a', `osp-change${selected === change.name ? ' osp-selected' : ''}`);
        link.href = `${base}/changes/${encodeURIComponent(change.name)}`;
        if (selected === change.name) link.setAttribute('aria-current', 'page');
        link.addEventListener('click', event => { event.preventDefault(); navigate(link.getAttribute('href')); });
        const state = change.totalTasks === 0 ? 'No tasks yet' : change.completedTasks === change.totalTasks ? 'Tasks complete' : 'In progress';
        link.append(el('strong', 'osp-change-name', change.name),
          el('span', 'osp-muted', `${change.completedTasks} of ${change.totalTasks} tasks · ${state}`),
          progressBar(change.completedTasks, change.totalTasks, `${change.name} task progress`),
          el('span', 'osp-date', `Updated ${formatDate(change.lastModified)}`));
        item.append(link);
        list.append(item);
      }
      changePanel.append(list);
    }
    function renderDetail() {
      detailPanel.replaceChildren();
      if (!detail) return;
      const head = el('div', 'osp-detail-header');
      const title = el('div');
      title.append(el('p', 'osp-eyebrow', detail.schemaName), el('h2', '', detail.name));
      head.append(title, el('span', `osp-badge ${detail.planningComplete ? 'osp-done' : 'osp-ready'}`,
        detail.planningComplete ? 'Planning complete' : 'Planning in progress'));
      detailPanel.append(head, el('h3', 'osp-section-title', 'Planning artifacts'));
      const artifacts = el('ol', 'osp-artifacts');
      for (const artifact of detail.artifacts) {
        const item = el('li', 'osp-artifact');
        const content = el('div');
        content.append(el('strong', '', artifact.id), el('code', 'osp-artifact-path', artifact.outputPath));
        if (artifact.requires.length) content.append(el('span', 'osp-date', `Requires ${artifact.requires.join(', ')}`));
        item.append(content, el('span', `osp-badge osp-${artifact.status}`, STATE_LABELS[artifact.status]));
        artifacts.append(item);
      }
      detailPanel.append(artifacts);
      const taskHeader = el('div', 'osp-task-header');
      taskHeader.append(el('h3', 'osp-section-title', 'Implementation tasks'));
      if (detail.progress) taskHeader.append(el('span', 'osp-muted', `${detail.progress.complete} / ${detail.progress.total} checked`));
      detailPanel.append(taskHeader);
      if (detail.progress === null) {
        detailPanel.append(el('p', 'osp-empty', detail.taskError || detail.instruction || 'Task progress is not available yet. Complete the planning artifacts first.'));
      } else if (!detail.tasks.length) {
        detailPanel.append(el('p', 'osp-empty', 'No tasks are tracked for this change.'));
      } else {
        if (detail.tasks.length < detail.progress.total) {
          detailPanel.append(el('p', 'osp-muted', 'Only available task descriptions are listed below.'));
        }
        const tasks = el('ul', 'osp-tasks');
        for (const task of detail.tasks) {
          const item = el('li', 'osp-task');
          const mark = el('span', task.done ? 'osp-check osp-checked' : 'osp-check', task.done ? '✓' : '○');
          mark.setAttribute('aria-label', task.done ? 'Complete' : 'Remaining');
          const text = el('div');
          text.append(el('span', '', task.description));
          const relative = task.sourcePath.startsWith(snapshot.workspace + '/') ? task.sourcePath.slice(snapshot.workspace.length + 1) : task.sourcePath;
          text.append(el('code', 'osp-task-source', `${relative}:${task.line}`));
          item.append(mark, text);
          tasks.append(item);
        }
        detailPanel.append(tasks);
      }
      const next = el('div', 'osp-next');
      const nextText = !detail.planningComplete ? 'Continue planning in an OpenHands conversation.' :
        detail.progress === null ? 'Resolve the task-tracking issue before starting implementation.' :
        detail.progress.remaining ? 'Continue Apply after reviewing the planning artifacts.' :
        'Review implementation and verification evidence before syncing or archiving.';
      next.append(el('strong', '', 'Next human decision'), el('p', '', nextText));
      detailPanel.append(next);
    }

    async function refreshData() {
      if (busy || disposed) return;
      const version = ++generation;
      const current = () => !disposed && version === generation;
      let overviewUpdated = false;
      setBusy(true);
      notice.className = 'osp-notice';
      notice.setAttribute('role', 'status');
      notice.textContent = snapshot ? 'Refreshing the OpenSpec snapshot…' : 'Reading OpenSpec from the connected Agent Server…';
      if (!snapshot) detailPanel.replaceChildren(el('p', 'osp-empty', 'Loading project progress…'));
      try {
        const overview = await loadOverview(host, workspace);
        if (!current()) return;
        snapshot = overview;
        overviewUpdated = true;
        detail = null;
        const selected = requested?.[1] || overview.changes[0]?.name;
        renderOverview(selected);
        if (!selected) {
          detailPanel.replaceChildren(el('div', 'osp-empty', 'Your active change details will appear here.'));
        } else if (!overview.changes.some(change => change.name === selected)) {
          detailPanel.replaceChildren(el('h2', '', 'Change not found'),
            el('p', 'osp-empty', 'This change may have been archived or removed. Choose another active change.'));
        } else {
          detailPanel.replaceChildren(el('p', 'osp-empty', `Loading ${selected}…`));
          try {
            const change = await loadChange(host, workspace, selected);
            if (!current()) return;
            detail = change;
            renderDetail();
          } catch (error) {
            if (!current()) return;
            detailPanel.replaceChildren(el('h2', '', selected), el('p', 'osp-error', error.message));
            throw error;
          }
        }
        notice.textContent = `Snapshot updated ${formatDate(detail?.generatedAt || snapshot.generatedAt)} · ${snapshot.workspace}`;
      } catch (error) {
        if (current()) showError(error.message, overviewUpdated ? 'Change details unavailable. ' :
          snapshot ? 'Refresh failed. Showing the previous snapshot. ' : '');
      } finally {
        if (current()) setBusy(false);
      }
    }
    refreshData();
    return dispose;
  });
  return () => {
    for (const dispose of [...disposers]) dispose();
    unregister();
  };
}
