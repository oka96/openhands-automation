"""Bounded native Automation bridge. Executed inside Agent Server, never Canvas.

Only explicit setup installs the fixed repository's bundles. Only dispatch sends
an event. Credentials remain in this process and private, per-backend state.
"""
import base64
import contextlib
import fcntl
import hashlib
import hmac
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import secrets
import sys
import tarfile
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import uuid

REPOSITORY = Path('/Users/oka/Desktop/openhands-automation')
SOURCE = 'openspec-role-dashboard'
SCHEMA = SOURCE + '/v3'
ACTIONS = json.loads(Path(__file__).with_name('actions.json').read_text())
STAGES = tuple(action['id'] for action in ACTIONS)
_delivery_spec = importlib.util.spec_from_file_location('role_delivery', Path(__file__).with_name('delivery.py'))
delivery = importlib.util.module_from_spec(_delivery_spec)
_delivery_spec.loader.exec_module(delivery)
ROLES = ('SA', 'Frontend', 'Backend', 'QA')
ROLE_PREFIXES = {'SA': 'SA', 'Frontend': 'FE', 'Backend': 'BE', 'QA': 'QA'}
PAIRS = tuple((role, stage) for role in ROLES for stage in STAGES)
STATUSES = ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', 'SKIPPED')
BUNDLE_FILES = ('config.json', 'prompt.md', 'run.py', 'delivery.py', 'actions.json')
SOURCE_NAME = 'OpenSpec role dashboard · explicit skill requests'


class BridgeError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise BridgeError(message)


def identifier(value):
    try:
        return isinstance(value, str) and str(uuid.UUID(value)) == value
    except (ValueError, AttributeError):
        return False


def slug(value):
    return isinstance(value, str) and len(value) <= 100 and re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', value)


def local_path(value):
    require(isinstance(value, str) and 1 < len(value) <= 4096 and value.startswith('/')
            and not any(char in value for char in '\x00\r\n\\') and not value.endswith('/')
            and '//' not in value and not set(Path(value).parts) & {'.', '..', '.local'}
            and '/./' not in value, 'Expected a canonical absolute local directory')
    path = Path(value)
    require(path.resolve() == path, 'Symlinked source directories are not supported')
    return path


def encode(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode()


def read_bytes(path, limit=128 * 1024):
    require(path.resolve() == path and path.is_file() and not path.is_symlink(), 'Missing or symlinked local source file')
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(descriptor, 'rb') as stream:
        raw = stream.read(limit + 1)
    require(len(raw) <= limit, 'Local source file exceeded its size limit')
    return raw


def read_json(path, limit=128 * 1024):
    try:
        return json.loads(read_bytes(path, limit).decode('utf-8'))
    except (UnicodeError, ValueError):
        raise BridgeError('Invalid JSON in a local Automation source file') from None


def atomic_json(path, value):
    descriptor, temporary = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(encode(value))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request_json(url, *, method='GET', body=None, headers=None):
    raw = body if isinstance(body, bytes) else None if body is None else encode(body)
    request = urllib.request.Request(url, data=raw, method=method,
                                    headers={'Content-Type': 'application/json', **(headers or {})})
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=5) as response:
            result = response.read(1_000_001)
        require(len(result) <= 1_000_000, 'Automation response exceeded its size limit')
        if method == 'DELETE' and not result:
            return None
        return json.loads(result)
    except urllib.error.HTTPError as error:
        status = error.code
        error.close()
        raise BridgeError(f'Automation request failed (HTTP {status}); inspect its history before retrying') from None
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        raise BridgeError('Automation request outcome is unknown; inspect its history before retrying') from None


def trigger(role, stage):
    return {'type': 'event', 'source': SOURCE, 'on': stage + '.requested',
            'filter': f"schema == '{SCHEMA}' && stage == '{stage}' && approval == '{stage}' && role == '{role}'"}


def automation_name(role, stage):
    label = next(action['label'] for action in ACTIONS if action['id'] == stage)
    return f'OpenSpec {role} · {label}'


def pair_key(role, stage):
    return role + ':' + stage


def retired_definitions(inventory):
    """Recognize only the ten definitions superseded by the dedicated workflow."""
    expected = {f'OpenSpec {number:02d} · {stage.title()}':
                ('openspec-dashboard', 'explore.requested') if stage == 'explore' else ('openspec-manual', 'manual-only')
                for number, stage in enumerate(('explore', 'propose', 'update', 'apply', 'verify', 'sync', 'archive'), 1)}
    expected.update({f'OpenSpec Role · {stage.title()}': (SOURCE, stage + '.requested') for stage in ('propose', 'update', 'apply')})
    result = []
    for name, (source, event) in expected.items():
        rows = [row for row in inventory if row.get('name') == name]
        require(len(rows) <= 1, 'Duplicate superseded automation names; inspect native definitions')
        if rows:
            row = rows[0]
            routing = row.get('trigger')
            require(identifier(row.get('id')) and isinstance(routing, dict)
                    and routing.get('source') == source and routing.get('on') == event,
                    'A superseded name has unfamiliar routing; inspect it before removal')
            result.append(row)
    return result


class Bridge:
    def __init__(self, service, home, *, env=None, requester=request_json, repository=None):
        env = os.environ if env is None else env
        require(isinstance(service, dict), 'This backend has no advertised Automation service')
        origin = service.get('url_from_agent')
        try:
            parsed = urllib.parse.urlsplit(origin)
            parsed.port
        except (ValueError, TypeError, AttributeError):
            raise BridgeError('Invalid Automation service address') from None
        require(parsed.scheme in ('http', 'https') and parsed.hostname in ('localhost', '127.0.0.1', '::1')
                and not parsed.username and not parsed.password and parsed.path in ('', '/')
                and not parsed.query and not parsed.fragment, 'Only the advertised local Automation service is supported')
        require(service.get('api_prefix') == '/api/automation' and service.get('auth_env_var') == 'OPENHANDS_AUTOMATION_API_KEY',
                'Unsupported Automation API prefix or authentication')
        self.key = env.get('OPENHANDS_AUTOMATION_API_KEY')
        require(isinstance(self.key, str) and self.key, 'Agent Server has no injected Automation key; use the native local launcher')
        self.home = local_path(home)
        require(self.home == Path.home().resolve(), 'Agent Server home does not match the helper home')
        self.base = origin.rstrip('/') + '/api/automation/v1'
        self.root = self.home / '.openhands/apps/openspec-progress/role-automation' / hashlib.sha256(self.base.encode()).hexdigest()[:16]
        require(self.root.resolve() == self.root, 'Symlinked bridge state directories are not supported')
        self.repository = local_path(str(REPOSITORY if repository is None else repository))
        self.requester = requester
        self.config = self.load_config()

    def api(self, path='', *, method='GET', body=None, headers=None):
        return self.requester(self.base + path, method=method, body=body,
                              headers={'X-Session-API-Key': self.key, **(headers or {})})

    def load_config(self):
        config = read_json(self.repository / 'role-workflow.json')
        fields = {'workspace', 'spec_store', 'store_id', 'skill_root', 'profile', 'timeout_seconds', 'canvas_url'}
        require(isinstance(config, dict) and fields <= set(config) and set(config) <= fields | {'version'}
                and type(config.get('version', 1)) is int and config.get('version', 1) == 1, 'Invalid role-workflow.json configuration')
        for field in ('workspace', 'spec_store', 'skill_root'):
            directory = local_path(config[field])
            require(field == 'workspace' or directory.is_dir(), 'A configured role workflow directory is missing')
        require(slug(config['store_id']) and isinstance(config['profile'], str) and 0 < len(config['profile']) <= 200
                and '\x00' not in config['profile'] and type(config['timeout_seconds']) is int
                and 60 <= config['timeout_seconds'] <= 1800, 'Invalid role workflow store, profile, or timeout')
        try:
            canvas = urllib.parse.urlsplit(config['canvas_url'])
            canvas.port
        except (ValueError, TypeError, AttributeError):
            raise BridgeError('Invalid role workflow Canvas address') from None
        require(canvas.scheme in ('http', 'https') and canvas.hostname in ('localhost', '127.0.0.1', '::1')
                and not canvas.username and not canvas.password and canvas.path in ('', '/')
                and not canvas.query and not canvas.fragment, 'Role workflow Canvas must be a local origin')
        return config

    def safe_config(self):
        return {key: self.config[key] for key in ('workspace', 'spec_store', 'store_id', 'profile', 'skill_root', 'timeout_seconds')} | {'repository': str(self.repository)}

    def inventory(self, endpoint='', key='automations'):
        value = self.api(endpoint + '?limit=100')
        require(isinstance(value, dict) and isinstance(value.get(key), list) and type(value.get('total')) is int
                and len(value[key]) == value['total'] <= 100 and all(isinstance(row, dict) for row in value[key]),
                'Cannot inspect the complete local Automation inventory (maximum 100)')
        return value[key]

    def selected(self, inventory, *, allow_retired=False):
        result = {}
        for role, stage in PAIRS:
            rows = [row for row in inventory if row.get('name') == automation_name(role, stage)]
            require(len(rows) <= 1, 'Duplicate role automation names; inspect native Automation definitions')
            if rows:
                require(identifier(rows[0].get('id')), 'Invalid role automation identity')
                result[pair_key(role, stage)] = rows[0]
        ids = {row['id'] for row in result.values()}
        require(len(ids) == len(result), 'Duplicate role automation identities')
        if allow_retired:
            ids.update(row['id'] for row in retired_definitions(inventory))
        require(not any(row.get('enabled') and isinstance(row.get('trigger'), dict)
                        and row['trigger'].get('source') == SOURCE and row.get('id') not in ids for row in inventory),
                'Another enabled automation uses the role dashboard source; resolve routing first')
        return result

    def bundles(self):
        bundles = {}
        for role, stage in PAIRS:
            root = self.repository / 'automations' / f'openspec-{role.lower()}-{stage}'
            definition = read_json(root / 'automation.yaml')
            expected = {'name': automation_name(role, stage), 'state': 'ACTIVE', 'enabled': True,
                        'trigger': trigger(role, stage), 'entrypoint': 'python3 run.py',
                        'timeout': self.config['timeout_seconds'], 'keep_alive': False}
            require(isinstance(definition, dict) and all(definition.get(key) == value for key, value in expected.items())
                    and set(definition) <= set(expected) | {'tarball_source'}
                    and definition.get('tarball_source') == {'type': 'internal'}, 'Role bundles are stale or invalid; run npm run build in the automation repository')
            directory = root / 'tarball'
            require(directory.resolve() == directory and directory.is_dir()
                    and {file.name for file in directory.iterdir()} == set(BUNDLE_FILES), 'Unexpected role bundle files')
            files = {name: read_bytes(directory / name, 512 * 1024) for name in BUNDLE_FILES}
            try:
                generated = json.loads(files['config.json'])
            except (ValueError, UnicodeError):
                raise BridgeError('Invalid generated role configuration') from None
            require(isinstance(generated, dict) and generated.get('mode') == 'role' and generated.get('stage') == stage
                    and generated.get('role') == role
                    and all(generated.get(key) == value for key, value in self.config.items()),
                    'Generated role configuration is stale; rebuild the automation repository')
            digest = hashlib.sha256(encode(expected))
            buffer = io.BytesIO()
            with tarfile.open(fileobj=buffer, mode='w:gz') as archive:
                for name, content in files.items():
                    digest.update(name.encode() + b'\0' + content)
                    item = tarfile.TarInfo(name)
                    item.size, item.mode, item.mtime = len(content), 0o600, 0
                    archive.addfile(item, io.BytesIO(content))
            require(buffer.tell() <= 1024 * 1024, 'Role bundle exceeds the native 1 MiB upload limit')
            bundles[pair_key(role, stage)] = {'definition': expected, 'hash': digest.hexdigest(), 'tarball': buffer.getvalue()}
        return bundles

    def state(self):
        path = self.root / 'connection.json'
        if not path.exists():
            return {'version': 2, 'bindings': {}, 'source': None}
        state = read_json(path)
        if isinstance(state, dict) and state.get('version') == 1:
            require(isinstance(state.get('stages'), dict) and set(state['stages']) <= set(STAGES)
                    and all(isinstance(item, dict) and item.get('state') == 'ready' for item in state['stages'].values()),
                    'Resolve the incomplete previous connection before migration')
            return {'version': 2, 'bindings': {}, 'source': state.get('source')}
        require(isinstance(state, dict) and state.get('version') == 2 and isinstance(state.get('bindings'), dict)
                and set(state['bindings']) <= {pair_key(*pair) for pair in PAIRS}, 'Invalid private connection state; inspect the local setup')
        return state

    def save(self, state):
        atomic_json(self.root / 'connection.json', state)

    @contextlib.contextmanager
    def lock(self):
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        require(self.root.resolve() == self.root, 'Symlinked bridge state is not supported')
        os.chmod(self.root, 0o700)
        descriptor = os.open(self.root / '.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        with os.fdopen(descriptor, 'a') as stream:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise BridgeError('Another role Automation operation is running; check its result first') from None
            yield

    @staticmethod
    def definition_matches(row, desired):
        return all((isinstance(row.get('trigger'), dict) and all(row['trigger'].get(k) == v for k, v in value.items())
                    and row['trigger'].get('destination', 'dispatch_run') == 'dispatch_run'
                    and row['trigger'].get('subject_key_expr') is None and row['trigger'].get('turn_text_expr') is None
                    and row['trigger'].get('wake_agent', True) is True
                    and set(row['trigger']) <= set(value) | {'destination', 'subject_key_expr', 'turn_text_expr', 'wake_agent'}) if key == 'trigger'
                   else row.get(key) == value for key, value in desired.items())

    def source_ready(self, source, webhooks):
        rows = [row for row in webhooks if row.get('source') == SOURCE]
        require(len(rows) <= 1, 'Duplicate role dashboard sources; inspect native Automation sources')
        if not isinstance(source, dict) or source.get('state') != 'ready' or not rows or not isinstance(source.get('secret'), str) or not 8 <= len(source['secret']) <= 255:
            return False
        row = rows[0]
        return (row.get('id') == source.get('id') and row.get('org_id') == source.get('org_id')
                and row.get('enabled') is True and row.get('event_key_expr') == 'type'
                and row.get('signature_header') == 'X-Signature-256' and row.get('signature_scheme') == 'hmac_sha256_hex')

    def readiness(self, selected, bundles, state, webhooks):
        if len(selected) != len(PAIRS) or not self.source_ready(state.get('source'), webhooks):
            return False
        for stage, bundle in bundles.items():
            saved = state['bindings'].get(stage, {})
            desired = bundle['definition'] | {'tarball_path': saved.get('tarball_path')}
            if saved.get('state') != 'ready' or saved.get('hash') != bundle['hash'] or saved.get('id') != selected[stage]['id'] or not self.definition_matches(selected[stage], desired):
                return False
        return True

    def result(self, kind, ready, selected):
        return {'kind': kind, 'ready': ready, 'automations': [
                {'id': selected[pair_key(role, stage)]['id'], 'name': automation_name(role, stage), 'stage': stage, 'role': role}
                for role, stage in PAIRS if pair_key(role, stage) in selected], 'configuration': self.safe_config(),
                'message': f'Connected to all {len(PAIRS)} role automations.' if ready else
                'Connect automations to install dedicated role automations and remove superseded OpenSpec definitions.'}

    def probe(self):
        inventory = self.inventory()
        selected = self.selected(inventory, allow_retired=True)
        ready = self.readiness(selected, self.bundles(), self.state(), self.inventory('/webhooks', 'webhooks')) and not retired_definitions(inventory)
        return self.result('probe', ready, selected)

    def setup(self):
        bundles = self.bundles()
        with self.lock():
            state = self.state()
            inventory = self.inventory()
            selected = self.selected(inventory, allow_retired=True)
            retired = retired_definitions(inventory)
            webhooks = self.inventory('/webhooks', 'webhooks')
            source = state.get('source')
            existing_sources = [row for row in webhooks if row.get('source') == SOURCE]
            require(not existing_sources or self.source_ready(source, webhooks),
                    'The role source exists without a verified saved connection; do not overwrite its secret')
            require(not source or source.get('state') == 'ready',
                    'Source registration outcome is unknown; inspect the local connection before retrying')
            # Validate every candidate before any retirement, upload or installation.
            for row in retired:
                history = self.api('/' + row['id'] + '/runs?limit=100&offset=0')
                counts = history.get('status_counts') if isinstance(history, dict) else None
                require(isinstance(counts, dict) and set(counts) <= set(STATUSES)
                        and all(type(count) is int and count >= 0 for count in counts.values())
                        and history.get('total') == sum(counts.values()), 'Cannot verify superseded automation activity')
                require(counts.get('PENDING', 0) == counts.get('RUNNING', 0) == 0,
                        'A superseded automation has pending or running work; let it finish before reconnecting')
            for row in retired:
                self.api('/' + row['id'], method='DELETE')
            require(not retired_definitions(self.inventory()), 'Superseded definitions remain; reconnect before running')
            for stage, bundle in bundles.items():
                saved = state['bindings'].get(stage)
                current = selected.get(stage)
                if saved and saved.get('hash') != bundle['hash']:
                    require(saved.get('state') == 'ready', 'An earlier setup is incomplete; resolve it before changing bundles')
                    saved = None
                if saved and saved.get('state') == 'ready' and current and self.definition_matches(current, bundle['definition'] | {'tarball_path': saved.get('tarball_path')}):
                    require(saved.get('id') == current['id'], 'The installed role automation identity changed')
                    continue
                if not saved:
                    saved = {'state': 'uploading', 'hash': bundle['hash'], 'id': current['id'] if current else None}
                    state['bindings'][stage] = saved
                    self.save(state)
                    uploaded = self.api('/uploads?name=' + urllib.parse.quote('openspec-role-' + stage), method='POST',
                                        body=bundle['tarball'], headers={'Content-Type': 'application/gzip'})
                    require(isinstance(uploaded, dict) and uploaded.get('status') == 'COMPLETED'
                            and isinstance(uploaded.get('tarball_path'), str)
                            and uploaded['tarball_path'].startswith('oh-internal://uploads/')
                            and identifier(uploaded['tarball_path'].removeprefix('oh-internal://uploads/')), 'Bundle upload did not complete; inspect native Automation uploads')
                    saved.update(state='uploaded', tarball_path=uploaded['tarball_path'])
                    self.save(state)
                require(saved.get('state') != 'uploading', 'Bundle upload outcome is unknown; inspect native Automation uploads before retrying')
                desired = bundle['definition'] | {'tarball_path': saved['tarball_path']}
                if current and self.definition_matches(current, desired):
                    require(saved.get('id') in (None, current['id']), 'Role automation identity changed during setup')
                    installed = current
                else:
                    require(not (saved.get('state') == 'installing' and saved.get('id') is None),
                            'Automation creation outcome is unknown; inspect its history before retrying')
                    require(not current or saved.get('id') == current['id'], 'Role automation identity changed during setup')
                    saved['state'] = 'installing'
                    self.save(state)
                    installed = self.api('/' + current['id'] if current else '', method='PATCH' if current else 'POST', body=desired)
                    require(isinstance(installed, dict) and identifier(installed.get('id')) and self.definition_matches(installed, desired)
                            and (not current or installed['id'] == current['id']), 'Native installation returned unexpected data; inspect definitions before retrying')
                saved.update(state='ready', id=installed['id'])
                selected[stage] = installed
                self.save(state)
            if not source:
                source = {'state': 'registering', 'secret': secrets.token_urlsafe(32)}
                state['source'] = source
                self.save(state)
                created = self.api('/webhooks', method='POST', body={'name': SOURCE_NAME, 'source': SOURCE,
                    'event_key_expr': 'type', 'signature_header': 'X-Signature-256', 'signature_scheme': 'hmac_sha256_hex',
                    'webhook_secret': source['secret']})
                require(isinstance(created, dict) and identifier(created.get('id')) and identifier(created.get('org_id'))
                        and created.get('source') == SOURCE, 'Source registration returned unexpected data; inspect the local connection')
                source.update(state='ready', id=created['id'], org_id=created['org_id'])
                self.save(state)
            selected = self.selected(self.inventory())
            ready = self.readiness(selected, bundles, state, self.inventory('/webhooks', 'webhooks'))
            require(ready, 'Role automation setup changed or is incomplete; inspect native definitions and sources')
            return self.result('setup', True, selected)

    def validate_input(self, data, *, context=True):
        fields = {'automation_id', 'request_id', 'stage', 'spec_store', 'requirement_id', 'context_change', 'role', 'spec_id', 'change', 'request'}
        require(isinstance(data, dict) and fields <= set(data) and set(data) <= fields | {'application_id', 'applications', 'target', 'review_id', 'message'}, 'Unexpected role automation input fields')
        if 'application_id' in data:
            require(slug(data['application_id']) and len(data['application_id']) <= 80, 'Invalid application selection')
        require(identifier(data['automation_id']) and identifier(data['request_id']), 'Invalid automation or request ID')
        require(data['stage'] in STAGES and data['role'] in ROLES, 'Unsupported automation or role')
        require(local_path(data['spec_store']) == Path(self.config['spec_store']), 'Selected store does not match the configured role workflow')
        require(isinstance(data['requirement_id'], str) and re.fullmatch(r'[A-Z][A-Z0-9]*-[0-9]+', data['requirement_id']), 'Invalid requirement ID')
        prefix = ROLE_PREFIXES[data['role']] + '-' + data['requirement_id'] + '-'
        require(isinstance(data['spec_id'], str) and len(data['spec_id']) <= 160 and data['spec_id'].startswith(prefix)
                and re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', data['spec_id'][len(prefix):]), 'Spec ID must match the requirement and role')
        context_match = re.fullmatch(r'(SA|FE|BE|QA)-([A-Z][A-Z0-9]*-[0-9]+)-([a-z0-9]+(?:-[a-z0-9]+)*)', data['context_change']) if isinstance(data['context_change'], str) else None
        new_requirement = data['stage'] == 'propose' and data['role'] == 'SA' and data['context_change'] == ''
        require((new_requirement or context_match and len(data['context_change']) <= 160 and context_match[2] == data['requirement_id'])
                and data['change'] == data['spec_id'] and (data['stage'] == 'propose' or data['context_change'] == data['change']),
                'Role actions must use canonical changes in the selected requirement')
        require(isinstance(data['request'], str) and len(data['request']) <= 10000 and '\x00' not in data['request']
                and (data['stage'] not in ('propose', 'update') or data['request'].strip()), 'Propose and Update require a prompt; maximum 10000 characters')
        if data['stage'] in ('review', 'commit', 'merge-request'):
            require(data.get('target') in ('specs', 'code') and not (data['role'] == 'SA' and data['target'] == 'code'), 'SA can deliver specifications only')
            if data['stage'] != 'review':
                require(identifier(data.get('review_id')) and isinstance(data.get('message'), str)
                        and 0 < len(data['message'].strip()) <= 500 and not re.search(r'[\x00-\x1f]', data['message']),
                        'Select a review and enter a one-line commit message or PR title')
        else:
            require(not any(key in data for key in ('target', 'review_id', 'message')), 'Unexpected delivery inputs')
        require('applications' not in data or new_requirement, 'Applications are only accepted for a new SA requirement')
        if new_requirement:
            require(isinstance(data.get('applications'), list) and 1 <= len(data['applications']) <= 20
                    and len(encode(data['applications'])) <= 20000, 'New SA requirements need bounded application bindings')
        if not context:
            return
        changes = Path(self.config['spec_store']) / 'openspec/changes'
        require(changes.resolve() == changes and changes.is_dir(), 'The changes directory is missing or symlinked')
        entries = list(changes.iterdir())
        require(len(entries) <= 1000, 'The changes directory exceeded its entry limit')
        groups = {}
        for entry in entries:
            if entry.name == 'archive':
                continue
            require(not entry.is_symlink(), 'Symlinked change paths are not supported')
            match = re.fullmatch(r'(SA|FE|BE|QA)-([A-Z][A-Z0-9]*-[0-9]+)-([a-z0-9]+(?:-[a-z0-9]+)*)', entry.name)
            if not match:
                require(not re.match(r'(SA|FE|BE|QA)-', entry.name, re.IGNORECASE), 'Malformed role change folder')
                continue
            require(len(entry.name) <= 160 and entry.is_dir(), 'Invalid role change directory')
            groups.setdefault(match[2], []).append(entry.name)
        require(len(groups) <= 50 and all(len(names) <= 20 for names in groups.values()), 'Store role change limits exceeded')
        members = groups.get(data['requirement_id'], [])
        require(not members if new_requirement else data['context_change'] in members,
                'Requirement already exists or its context change is missing; refresh the board')
        root = changes / data['change']
        require(root.resolve() == root, 'Role change must not use symlinks')
        if data['stage'] == 'propose':
            require(not root.exists() and not root.is_symlink(), 'Propose refuses to overwrite an existing change')
            require(len(members) < 20, 'The requirement has reached its 20 spec limit')
        else:
            require(data['change'] in members, 'The requirement, role or change no longer matches the store; refresh the board')
            if data['stage'] == 'apply':
                read_bytes(root / 'tasks.md', 64 * 1024)
                require((root / 'specs').resolve() == root / 'specs' and (root / 'specs').is_dir(), 'Apply requires specification artifacts')

    def dispatch(self, data):
        self.validate_input(data, context=False)
        fingerprint = hashlib.sha256(encode(data)).hexdigest()
        with self.lock():
            journal = self.root / (data['request_id'] + '.json')
            if journal.exists():
                saved = read_json(journal)
                require(saved.get('fingerprint') == fingerprint, 'This request ID belongs to different inputs')
                require(saved.get('state') == 'dispatched', 'This request may already have started; inspect native Automation history')
                return {'kind': 'dispatch', **{key: saved[key] for key in ('automation_id', 'request_id', 'run_id')}}
            self.validate_input(data)
            selected = self.selected(self.inventory())
            state = self.state()
            require(self.readiness(selected, self.bundles(), state, self.inventory('/webhooks', 'webhooks')), 'Connect or update the role automations before running')
            require(selected[pair_key(data['role'], data['stage'])]['id'] == data['automation_id'], 'Selected role automation changed; reconnect first')
            event = {'schema': SCHEMA, 'type': data['stage'] + '.requested', 'approval': data['stage'],
                     **{key: value for key, value in data.items() if key != 'automation_id'}}
            saved = {'state': 'dispatching', 'fingerprint': fingerprint, 'automation_id': data['automation_id'], 'request_id': data['request_id']}
            atomic_json(journal, saved)
            raw = encode(event)
            source = state['source']
            signature = 'sha256=' + hmac.new(source['secret'].encode(), raw, hashlib.sha256).hexdigest()
            result = self.requester(self.base + f"/events/{source['org_id']}/{SOURCE}", method='POST', body=raw, headers={'X-Signature-256': signature})
            require(isinstance(result, dict) and result.get('received') is True and result.get('matched') == 1
                    and isinstance(result.get('runs_created'), list) and len(result['runs_created']) == 1 and identifier(result['runs_created'][0]),
                    'Expected exactly one role automation run; inspect native history before retrying')
            saved.update(state='dispatched', run_id=result['runs_created'][0])
            atomic_json(journal, saved)
            return {'kind': 'dispatch', **{key: saved[key] for key in ('automation_id', 'request_id', 'run_id')}}

    def run_report(self, row, role, stage):
        """Local runner diagnostics never override native lifecycle or expose raw metadata."""
        if row['status'] not in ('COMPLETED', 'FAILED'):
            return None
        try:
            report = read_json(self.home / '.openhands/apps/openspec-progress/role-results' / (row['id'] + '.json'), 64 * 1024)
            require(isinstance(report, dict) and set(report) == {'version', 'run_id', 'conversation_id', 'role', 'stage',
                    'requirement_id', 'spec_id', 'configuration', 'outcome'} and type(report['version']) is int and report['version'] == 1,
                    'Invalid role result')
            require(report['run_id'] == row['id'] and report['conversation_id'] == row.get('conversation_id')
                    and report['role'] == role and report['stage'] == stage, 'Role result identity mismatch')
            req, spec = report['requirement_id'], report['spec_id']
            require((req is None and spec is None and report['conversation_id'] is None) or
                    (isinstance(req, str) and re.fullmatch(r'[A-Z][A-Z0-9]*-[0-9]+', req) and isinstance(spec, str)
                     and len(spec) <= 160 and spec.startswith(ROLE_PREFIXES[role] + '-' + req + '-')
                     and re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', spec[len(ROLE_PREFIXES[role] + '-' + req + '-'):])),
                    'Invalid role result target')
            config = report['configuration']
            require(isinstance(config, dict) and set(config) == {'workspace', 'spec_store', 'store_id', 'profile', 'skill_root', 'timeout_seconds'}
                    and all(config[key] == self.config[key] for key in ('spec_store', 'store_id'))
                    and isinstance(config['profile'], str) and 0 < len(config['profile']) <= 200 and '\x00' not in config['profile']
                    and type(config['timeout_seconds']) is int and 60 <= config['timeout_seconds'] <= 1800,
                    'Invalid role result configuration')
            actual = local_path(config['workspace'])
            parent = Path(self.config['workspace'])
            valid_workspace = actual == parent
            if spec and actual.parent == parent / spec:
                valid_workspace = actual.name == 'planning' if role == 'SA' else slug(actual.name)
            require(valid_workspace, 'Invalid role result workspace')
            local_path(config['skill_root'])
            outcome = report['outcome']
            require(isinstance(outcome, dict) and set(outcome) == {'status', 'blocker_type', 'summary', 'findings', 'audit_errors', 'next_action', 'agent_status'}
                    and outcome['status'] in ('completed', 'blocked', 'needs_review', 'execution_error')
                    and outcome['blocker_type'] in (None, 'dependency', 'input')
                    and (outcome['status'] == 'blocked' or outcome['blocker_type'] is None)
                    and outcome['agent_status'] in (None, 'completed', 'blocked', 'findings'), 'Invalid role outcome')
            for key, limit in (('summary', 2000), ('next_action', 1000)):
                require(isinstance(outcome[key], str) and 0 < len(outcome[key]) <= limit and '\x00' not in outcome[key], 'Invalid role outcome text')
            for key in ('findings', 'audit_errors'):
                require(isinstance(outcome[key], list) and len(outcome[key]) <= 8 and all(
                    isinstance(value, str) and len(value) <= 1000 and '\x00' not in value for value in outcome[key]), 'Invalid role outcome details')
            require((row['status'] == 'COMPLETED') == (outcome['status'] == 'completed'), 'Conflicting role result lifecycle')
            # Only fields validated above may cross the server/browser boundary.
            return {key: report[key] for key in ('role', 'stage', 'requirement_id', 'spec_id', 'configuration', 'outcome')}
        except (BridgeError, OSError, ValueError, TypeError, KeyError):
            return None

    def status(self, data):
        require(isinstance(data, dict) and set(data) == {'automation_id', 'run_id'} and all(identifier(value) for value in data.values()), 'Invalid role run status request')
        rows = self.selected(self.inventory())
        require(any(row['id'] == data['automation_id'] for row in rows.values()), 'The selected role automation is unavailable')
        # Bound both history lookup and returned data; never expose raw run metadata.
        for offset in range(0, 1000, 100):
            page = self.api(f"/{data['automation_id']}/runs?limit=100&offset={offset}")
            require(isinstance(page, dict) and isinstance(page.get('runs'), list) and len(page['runs']) <= 100
                    and type(page.get('total')) is int and page['total'] >= offset + len(page['runs']), 'Invalid native Automation history')
            found = [row for row in page['runs'] if isinstance(row, dict) and row.get('id') == data['run_id']]
            require(len(found) <= 1, 'Duplicate run identities in native history')
            if found:
                row = found[0]
                require(row.get('automation_id') == data['automation_id'] and row.get('status') in STATUSES
                        and (row.get('conversation_id') is None or identifier(row['conversation_id'])), 'Invalid native role run status')
                # Service errors may contain environment or model details. Keep those in
                # native history; display only an actionable, fixed summary in Canvas.
                error = 'This run needs attention. Open native Automation history for details.' if row.get('error_detail') or row['status'] == 'FAILED' else None
                pair = next(pair for pair in PAIRS if rows.get(pair_key(*pair), {}).get('id') == data['automation_id'])
                report = self.run_report(row, *pair)
                return {'kind': 'status', **data, 'status': row['status'], 'conversation_id': row.get('conversation_id'),
                        'error': None if report else error, 'report': report}
            if offset + len(page['runs']) >= page['total']:
                break
            require(len(page['runs']) == 100, 'Incomplete native Automation history')
        raise BridgeError('Run was not found in the latest 1000 entries; inspect native Automation history')

    def evidence(self, data, *, record=False):
        fields = {'spec_store', 'role', 'requirement_id', 'spec_id'} | ({'kind', 'id'} if record else set())
        require(isinstance(data, dict) and set(data) == fields and data['spec_store'] == self.config['spec_store'],
                'Evidence request must select this store and one role spec')
        context = {**self.config, **{key: data[key] for key in ('role', 'requirement_id', 'spec_id')}}
        try:
            value = delivery.load_record(context, data['kind'], data['id']) if record else delivery.history(context)
        except delivery.DeliveryError as error:
            raise BridgeError(str(error)) from None
        return {'kind': 'record' if record else 'history', 'data': value}


def handle(value):
    require(isinstance(value, dict) and set(value) <= {'action', 'service', 'home', 'input'}
            and value.get('action') in ('probe', 'setup', 'dispatch', 'status', 'history', 'record'), 'Invalid role bridge request')
    bridge = Bridge(value.get('service'), value.get('home'))
    action = value['action']
    if action in ('history', 'record'):
        return bridge.evidence(value.get('input'), record=action == 'record')
    if action in ('dispatch', 'status'):
        return getattr(bridge, action)(value.get('input'))
    require('input' not in value, 'Unexpected role bridge inputs')
    return getattr(bridge, action)()


if __name__ == '__main__':
    try:
        require(len(sys.argv) == 2 and len(sys.argv[1]) <= 100000, 'Invalid role bridge input')
        result = handle(json.loads(base64.b64decode(sys.argv[1], validate=True)))
        print(json.dumps({'version': 1, **result}, ensure_ascii=False))
    except BridgeError as error:
        print(json.dumps({'version': 1, 'kind': 'error', 'message': str(error)[:600]}))
        sys.exit(1)
    except Exception:
        print(json.dumps({'version': 1, 'kind': 'error', 'message': 'Could not complete the role Automation request; inspect native history before retrying'}))
        sys.exit(1)
