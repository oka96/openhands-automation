import copy
import hashlib
import hmac
import importlib.util
import io
import json
import shutil
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest import mock
import uuid

spec = importlib.util.spec_from_file_location('role_bridge', Path(__file__).resolve().parents[1] / 'runtime/control.py')
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


def identity():
    return str(uuid.uuid4())


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name).resolve()
        self.repository = self.home / 'automation'
        self.repository.mkdir()
        self.store = self.home / 'store'
        self.context = self.store / 'openspec/changes'
        self.context.mkdir(parents=True)
        self.config = {'workspace': str(self.home), 'spec_store': str(self.store), 'store_id': 'sample-store',
                       'skill_root': str(self.home), 'profile': 'saved-profile', 'timeout_seconds': 1800,
                       'canvas_url': 'http://127.0.0.1:8000'}
        (self.repository / 'role-workflow.json').write_text(json.dumps(self.config))
        for role in bridge.ROLES:
            for feature in ('first', 'second'):
                spec_id = bridge.ROLE_PREFIXES[role] + '-REQ-001-' + feature
                directory = self.context / spec_id
                (directory / 'specs' / spec_id).mkdir(parents=True)
                (directory / 'specs' / spec_id / 'spec.md').write_text('# Spec')
                (directory / 'tasks.md').write_text('- [ ] 1.1 [' + role + '] Work')
                (directory / 'proposal.md').write_text('# Proposal')
                (directory / 'design.md').write_text('# Design')
        for role, stage in bridge.PAIRS:
            root = self.repository / 'automations' / f'openspec-{role.lower()}-{stage}'
            (root / 'tarball').mkdir(parents=True)
            definition = {'name': bridge.automation_name(role, stage), 'state': 'ACTIVE', 'enabled': True,
                          'trigger': bridge.trigger(role, stage), 'entrypoint': 'python3 run.py', 'timeout': 1800,
                          'keep_alive': False, 'tarball_source': {'type': 'internal'}}
            (root / 'automation.yaml').write_text(json.dumps(definition))
            (root / 'tarball/config.json').write_text(json.dumps({**self.config, 'mode': 'role', 'stage': stage, 'role': role}))
            (root / 'tarball/prompt.md').write_text('Use the existing OpenSpec skills.')
            (root / 'tarball/run.py').write_text('print("role runner fixture")\n')
            (root / 'tarball/delivery.py').write_text('# delivery fixture\n')
            (root / 'tarball/actions.json').write_text(json.dumps(bridge.ACTIONS))
        self.service = {'url_from_agent': 'http://127.0.0.1:18021', 'api_prefix': '/api/automation', 'auth_env_var': 'OPENHANDS_AUTOMATION_API_KEY'}
        self.automations, self.webhooks, self.events, self.calls, self.runs = [], [], [], [], []
        self.failure = None
        self.secret = None
        self.patch = mock.patch.object(bridge.Path, 'home', return_value=self.home)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.client = self.new_client()

    def new_client(self, **overrides):
        return bridge.Bridge(overrides.get('service', self.service), overrides.get('home', str(self.home)),
                             env=overrides.get('env', {'OPENHANDS_AUTOMATION_API_KEY': 'session-secret'}),
                             requester=self.request, repository=self.repository)

    def request(self, url, *, method='GET', body=None, headers=None):
        self.calls.append((url, method, body, headers))
        route = url.split('/api/automation/v1', 1)[1]
        if '/events/' not in route:
            self.assertEqual(headers['X-Session-API-Key'], 'session-secret')
        if route == '?limit=100':
            return {'automations': copy.deepcopy(self.automations), 'total': len(self.automations)}
        if route == '/webhooks?limit=100':
            return {'webhooks': copy.deepcopy(self.webhooks), 'total': len(self.webhooks)}
        if route.startswith('/uploads?'):
            self.assertEqual(headers['Content-Type'], 'application/gzip')
            with tarfile.open(fileobj=io.BytesIO(body), mode='r:gz') as archive:
                self.assertEqual(archive.getnames(), list(bridge.BUNDLE_FILES))
                self.assertTrue(all(item.name[0] != '/' for item in archive.getmembers()))
            if self.failure == 'upload':
                raise bridge.BridgeError('lost upload response')
            return {'status': 'COMPLETED', 'tarball_path': 'oh-internal://uploads/' + identity()}
        if method == 'POST' and route == '':
            value = {'id': identity(), **copy.deepcopy(body)}
            value['trigger'].update(destination='dispatch_run', subject_key_expr=None, turn_text_expr=None, wake_agent=True)
            self.automations.append(value)
            if self.failure == 'create':
                self.failure = None
                raise bridge.BridgeError('lost creation response')
            return copy.deepcopy(value)
        if method == 'DELETE':
            self.automations = [row for row in self.automations if route != '/' + row['id']]
            if self.failure == 'delete':
                self.failure = None
                raise bridge.BridgeError('lost deletion response')
            return None
        if method == 'PATCH':
            value = next(item for item in self.automations if route == '/' + item['id'])
            value.update(copy.deepcopy(body))
            return copy.deepcopy(value)
        if route == '/webhooks' and method == 'POST':
            self.secret = body['webhook_secret']
            value = {key: content for key, content in body.items() if key != 'webhook_secret'}
            value.update(id=identity(), org_id=identity(), enabled=True)
            self.webhooks.append(value)
            if self.failure == 'source':
                self.failure = None
                raise bridge.BridgeError('lost source response')
            return copy.deepcopy(value)
        if route.startswith('/events/'):
            event = json.loads(body)
            expected = 'sha256=' + hmac.new(self.secret.encode(), body, hashlib.sha256).hexdigest()
            self.assertEqual(headers, {'X-Signature-256': expected})
            self.assertEqual(event['schema'], bridge.SCHEMA)
            self.assertEqual(event['type'], event['stage'] + '.requested')
            self.assertEqual(event['approval'], event['stage'])
            self.assertNotIn('automation_id', event)
            self.events.append(event)
            auto = next(row for row in self.automations if row['name'] == bridge.automation_name(event['role'], event['stage']))
            run = {'id': identity(), 'automation_id': auto['id'], 'status': 'PENDING', 'conversation_id': None, 'error_detail': None}
            self.runs.append(run)
            if self.failure == 'event':
                raise bridge.BridgeError('lost event response')
            return {'received': True, 'matched': 1, 'runs_created': [run['id']]}
        if '/runs?limit=100&offset=' in route:
            offset = int(route.rsplit('=', 1)[1])
            auto_id = route.split('/')[1]
            rows = [run for run in self.runs if run['automation_id'] == auto_id]
            return {'runs': copy.deepcopy(rows[offset:offset + 100]), 'total': len(rows), 'status_counts': {status: sum(row['status'] == status for row in rows) for status in bridge.STATUSES}}
        raise AssertionError((route, method))

    def input(self, stage='update', role='SA'):
        row = next(item for item in self.automations if item['name'] == bridge.automation_name(role, stage))
        spec_id = bridge.ROLE_PREFIXES[role] + '-REQ-001-' + ('new-feature' if stage == 'propose' else 'first')
        result = {'automation_id': row['id'], 'request_id': identity(), 'stage': stage, 'spec_store': str(self.store),
                'requirement_id': 'REQ-001', 'context_change': bridge.ROLE_PREFIXES[role] + '-REQ-001-first', 'role': role,
                'spec_id': spec_id, 'change': spec_id, 'request': 'Explore 标签; $(never-run)'}
        if stage in ('review', 'commit', 'merge-request'):
            result['target'] = 'specs' if role == 'SA' else 'code'
            if stage != 'review':
                result.update(review_id=identity(), message='Deliver changes')
        return result

    def count(self, route, method):
        return sum(url.split('/api/automation/v1', 1)[1] == route and verb == method for url, verb, *_ in self.calls)

    def test_revision_history_is_passive_and_bound_to_the_selected_role(self):
        context = {'spec_store': str(self.store), 'role': 'SA', 'requirement_id': 'REQ-001', 'spec_id': 'SA-REQ-001-first'}
        before = bridge.delivery.spec_snapshot(context)
        (self.context / context['spec_id'] / 'proposal.md').write_text('# Revised contract\n')
        revision = bridge.delivery.save_revision({**context, 'stage': 'update'}, before, 'completed', identity())
        history = self.client.evidence(context)
        self.assertEqual(history['data']['revisions'][0]['id'], revision['id'])
        record = self.client.evidence({**context, 'kind': 'revisions', 'id': revision['id']}, record=True)
        self.assertIn('+ Revised', ' '.join(file['diff'] for file in record['data']['files']).replace('#', ''))
        self.assertEqual(self.calls, [], 'History must not connect, dispatch or read remote automation state')
        with self.assertRaises(bridge.BridgeError):
            self.client.evidence({**context, 'role': 'Backend', 'kind': 'revisions', 'id': revision['id']}, record=True)
        with self.assertRaises(bridge.BridgeError):
            self.client.evidence({**context, 'spec_store': str(self.home)})

    def test_new_sa_requirement_event_carries_explicit_applications_and_prompt(self):
        self.client.setup()
        value = self.input('propose', 'SA')
        value.update(requirement_id='BOOK-002', context_change='', spec_id='SA-BOOK-002-booking', change='SA-BOOK-002-booking',
                     applications=[{'id': 'backend', 'name': 'Backend', 'role': 'Backend', 'repository': 'https://github.com/example/backend.git'}])
        self.client.dispatch(value)
        self.assertEqual(self.events[-1]['applications'], value['applications'])
        self.assertEqual(self.events[-1]['request'], value['request'])
        self.assertEqual(self.events[-1]['context_change'], '')

    def legacy_inventory(self):
        rows = []
        for number, stage in enumerate(('explore', 'propose', 'update', 'apply', 'verify', 'sync', 'archive'), 1):
            rows.append({'id': identity(), 'name': f'OpenSpec {number:02d} · {stage.title()}', 'enabled': True,
                         'trigger': {'source': 'openspec-dashboard' if stage == 'explore' else 'openspec-manual',
                                     'on': 'explore.requested' if stage == 'explore' else 'manual-only'}})
        rows.extend({'id': identity(), 'name': f'OpenSpec Role · {stage.title()}', 'enabled': True,
                     'trigger': {'source': bridge.SOURCE, 'on': stage + '.requested'}} for stage in ('propose', 'update', 'apply'))
        return rows

    def test_v1_connection_migrates_ten_definitions_preserving_source_and_history(self):
        self.client.setup()
        source = self.client.state()['source']
        old = self.legacy_inventory()
        unrelated = {'id': identity(), 'name': 'Personal report', 'enabled': True, 'trigger': {'source': 'other'}}
        self.automations = copy.deepcopy(old) + [unrelated]
        self.runs = [{'id': identity(), 'automation_id': row['id'], 'status': 'COMPLETED', 'conversation_id': identity()} for row in old]
        history = copy.deepcopy(self.runs)
        self.client.save({'version': 1, 'stages': {stage: {'state': 'ready'} for stage in bridge.STAGES}, 'source': source})
        before = len(self.calls)
        self.assertFalse(self.client.probe()['ready'])
        self.assertTrue(all(method == 'GET' for _, method, *_ in self.calls[before:]))
        self.assertTrue(self.client.setup()['ready'])
        self.assertEqual(len(self.automations), 25)
        self.assertIn(unrelated, self.automations)
        self.assertEqual(self.runs, history)
        self.assertEqual(self.client.state()['source'], source)
        self.assertEqual(self.client.state()['version'], 2)
        self.assertEqual(sum(method == 'DELETE' for _, method, *_ in self.calls), 10)

    def test_active_retired_work_and_unknown_subscriber_block_before_mutation(self):
        self.automations = self.legacy_inventory()
        for status in ('PENDING', 'RUNNING'):
            self.calls.clear()
            self.runs = [{'automation_id': self.automations[-1]['id'], 'status': status}]
            with self.assertRaisesRegex(bridge.BridgeError, 'pending or running'):
                self.client.setup()
            self.assertTrue(all(method == 'GET' for _, method, *_ in self.calls))
        self.runs = []
        self.automations.append({'id': identity(), 'name': 'Unknown subscriber', 'enabled': True, 'trigger': {'source': bridge.SOURCE}})
        self.calls.clear()
        with self.assertRaisesRegex(bridge.BridgeError, 'Another enabled'):
            self.client.setup()
        self.assertTrue(all(method == 'GET' for _, method, *_ in self.calls))

    def test_lost_retirement_response_resumes_from_inventory(self):
        old = self.legacy_inventory()
        self.automations = copy.deepcopy(old)
        self.failure = 'delete'
        with self.assertRaisesRegex(bridge.BridgeError, 'lost deletion'):
            self.client.setup()
        self.assertEqual(len(self.automations), 9)
        self.assertTrue(self.client.setup()['ready'])
        self.assertEqual(sum(method == 'DELETE' for _, method, *_ in self.calls), 10)
        self.assertEqual(len(self.automations), 24)

    def test_valid_role_cannot_use_another_roles_automation_id(self):
        self.client.setup()
        data = self.input('apply', 'SA')
        data['role'] = 'Backend'
        data.update(spec_id='BE-REQ-001-first', change='BE-REQ-001-first', context_change='BE-REQ-001-first')
        with self.assertRaisesRegex(bridge.BridgeError, 'Selected role automation'):
            self.client.dispatch(data)
        self.assertEqual(self.events, [])

    def test_http_delete_accepts_native_empty_204_response(self):
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = b''
        with mock.patch.object(bridge.urllib.request, 'build_opener') as opener:
            opener.return_value.open.return_value = response
            self.assertIsNone(bridge.request_json('http://127.0.0.1/example', method='DELETE'))

    def test_probe_is_read_only_and_setup_installs_exact_twelve_and_retires_recognized_legacy(self):
        legacy = {'id': identity(), 'name': 'OpenSpec 01 · Explore', 'enabled': True, 'trigger': {'source': 'openspec-dashboard', 'on': 'explore.requested'}}
        self.automations.append(copy.deepcopy(legacy))
        probe = self.client.probe()
        self.assertFalse(probe['ready'])
        self.assertIn('dedicated role automations', probe['message'])
        self.assertNotIn('skill', probe['message'].lower())
        self.assertEqual(probe['automations'], [])
        self.assertFalse(self.client.root.exists())
        self.assertTrue(all(method == 'GET' for _, method, *_ in self.calls))
        setup = self.client.setup()
        self.assertTrue(setup['ready'])
        self.assertEqual(setup['message'], 'Connected to all 24 role automations.')
        self.assertEqual(self.webhooks[0]['name'], 'OpenSpec role dashboard · explicit skill requests')
        self.assertEqual(len(setup['automations']), 24)
        self.assertNotIn(legacy, self.automations)
        self.assertEqual(setup['configuration']['spec_store'], str(self.store))
        self.assertNotIn('session-secret', json.dumps(setup))
        self.assertNotIn(self.secret, json.dumps(setup))
        self.assertEqual((self.client.root / 'connection.json').stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.client.root.stat().st_mode & 0o777, 0o700)
        self.assertTrue(self.client.probe()['ready'])
        self.client.setup()
        self.assertEqual(self.count('', 'POST'), 24)
        self.assertEqual(self.count('/webhooks', 'POST'), 1)

    def test_all_roles_and_skills_dispatch_exact_signed_per_run_inputs(self):
        self.client.setup()
        before = copy.deepcopy(self.automations)
        for role in bridge.ROLES:
            for stage in bridge.STAGES:
                data = self.input(stage, role)
                if stage == 'apply':
                    data['request'] = ''
                result = self.client.dispatch(data)
                self.assertEqual(result['automation_id'], data['automation_id'])
                self.assertEqual(self.client.dispatch(data), result)
                self.assertEqual(self.events[-1]['role'], role)
                self.assertEqual(self.events[-1]['request'], data['request'])
        self.assertEqual(len(self.events), 24)
        self.assertEqual(self.automations, before)

    def test_completed_propose_retry_survives_created_target_and_returns_same_run(self):
        self.client.setup()
        data = self.input('propose')
        result = self.client.dispatch(data)
        (self.context / 'SA-REQ-001-new-feature').mkdir()
        self.assertEqual(self.client.dispatch(data), result)
        self.assertEqual(len(self.events), 1)

    def test_unknown_dispatch_and_reused_id_never_start_another_run(self):
        self.client.setup()
        data = self.input()
        self.failure = 'event'
        with self.assertRaises(bridge.BridgeError):
            self.client.dispatch(data)
        with self.assertRaisesRegex(bridge.BridgeError, 'may already'):
            self.client.dispatch(data)
        with self.assertRaisesRegex(bridge.BridgeError, 'different inputs'):
            self.client.dispatch({**data, 'spec_id': 'SA-REQ-001-second', 'change': 'SA-REQ-001-second', 'context_change': 'SA-REQ-001-second'})
        self.assertEqual(len(self.events), 1)

    def test_partial_creation_recovers_known_tarball_without_duplicate_definition(self):
        self.failure = 'create'
        with self.assertRaises(bridge.BridgeError):
            self.client.setup()
        self.assertTrue(self.client.setup()['ready'])
        self.assertEqual(self.count('', 'POST'), 24)
        self.assertEqual(len(self.automations), 24)

    def test_unknown_source_registration_never_overwrites_or_registers_twice(self):
        self.failure = 'source'
        with self.assertRaises(bridge.BridgeError):
            self.client.setup()
        with self.assertRaisesRegex(bridge.BridgeError, 'secret'):
            self.client.setup()
        self.assertEqual(self.count('/webhooks', 'POST'), 1)

    def test_unknown_upload_is_not_repeated_automatically(self):
        self.failure = 'upload'
        with self.assertRaises(bridge.BridgeError):
            self.client.setup()
        with self.assertRaisesRegex(bridge.BridgeError, 'upload outcome'):
            self.client.setup()
        self.assertEqual(sum('/uploads?' in url for url, *_ in self.calls), 1)

    def test_updated_bundle_upserts_same_ids_and_preserves_source_secret(self):
        self.client.setup()
        ids = [item['id'] for item in self.automations]
        secret = self.secret
        prompt = self.repository / 'automations/openspec-sa-propose/tarball/prompt.md'
        prompt.write_text('Updated prompt')
        self.assertFalse(self.client.probe()['ready'])
        self.assertTrue(self.client.setup()['ready'])
        self.assertEqual([item['id'] for item in self.automations], ids)
        self.assertEqual(self.secret, secret)
        self.assertEqual(sum(method == 'PATCH' for _, method, *_ in self.calls), 1)

    def test_disabled_or_reconfigured_definition_is_not_dispatchable(self):
        self.client.setup()
        self.automations[1]['enabled'] = False
        self.assertFalse(self.client.probe()['ready'])
        with self.assertRaisesRegex(bridge.BridgeError, 'Connect or update'):
            self.client.dispatch(self.input())
        self.assertEqual(self.events, [])
        self.assertTrue(self.client.setup()['ready'])

    def test_duplicate_names_and_competing_routes_are_rejected_before_mutation(self):
        self.client.setup()
        duplicate = {**self.automations[0], 'id': identity()}
        self.automations.append(duplicate)
        with self.assertRaisesRegex(bridge.BridgeError, 'Duplicate'):
            self.client.probe()
        duplicate['name'] = 'Unexpected subscriber'
        with self.assertRaisesRegex(bridge.BridgeError, 'Another enabled'):
            self.client.dispatch(self.input())
        self.assertEqual(self.events, [])

    def test_nondefault_native_trigger_routes_and_extra_keys_cannot_dispatch(self):
        self.client.setup()
        current = copy.deepcopy(self.automations[1]['trigger'])
        for update in ({'destination': 'deliver_to_conversation'}, {'subject_key_expr': 'workspace'},
                       {'turn_text_expr': 'request'}, {'wake_agent': False}, {'unexpected': 'value'}):
            self.automations[1]['trigger'] = {**current, **update}
            with self.subTest(update=update), self.assertRaisesRegex(bridge.BridgeError, 'Connect or update'):
                self.client.dispatch(self.input())
        self.assertEqual(self.events, [])

    def test_inputs_cannot_override_role_stage_store_or_requirement_mapping(self):
        self.client.setup()
        for change in ({'role': 'Admin'}, {'stage': 'archive'}, {'request': ''}, {'request': 'x' * 10001},
                       {'spec_store': str(self.home)}, {'change': '../escape'}, {'context_change': 'other-change'},
                       {'requirement_id': 'REQ-999'}, {'automation_id': identity()}, {'profile': 'other'},
                       {'request_id': '../escape'}, {'change': 'different-change'},
                       {'spec_id': 'FE-REQ-001-first'}, {'spec_id': 'SA-REQ-002-first'}, {'spec_id': 'SA-REQ-001-unregistered'}):
            with self.subTest(change=change), self.assertRaises(bridge.BridgeError) as failure:
                self.client.dispatch({**self.input(), **change})
            if 'role' in change or 'stage' in change:
                self.assertEqual(str(failure.exception), 'Unsupported automation or role')
        self.assertFalse(self.events)

    def test_propose_refuses_existing_change_and_malformed_role_folder(self):
        self.client.setup()
        (self.context / 'SA-REQ-001-new-feature').mkdir()
        with self.assertRaisesRegex(bridge.BridgeError, 'overwrite'):
            self.client.dispatch(self.input('propose'))
        (self.context / 'SA-REQ-invalid').mkdir()
        with self.assertRaisesRegex(bridge.BridgeError, 'Malformed role'):
            self.client.dispatch(self.input())

    def test_second_spec_dispatch_is_distinct_and_stale_spec_is_rejected(self):
        self.client.setup()
        first = self.input('apply', 'Frontend')
        second = {**first, 'request_id': identity(), 'spec_id': 'FE-REQ-001-second', 'change': 'FE-REQ-001-second', 'context_change': 'FE-REQ-001-second'}
        self.client.dispatch(second)
        self.assertEqual(self.events[-1]['spec_id'], 'FE-REQ-001-second')
        shutil.rmtree(self.context / 'FE-REQ-001-second')
        with self.assertRaisesRegex(bridge.BridgeError, 'missing|no longer matches'):
            self.client.dispatch({**second, 'request_id': identity()})
        self.assertEqual(len(self.events), 1)

    def test_v3_reconnect_updates_existing_filters_and_preserves_all_ids(self):
        self.client.setup()
        ids = [row['id'] for row in self.automations]
        secret = self.secret
        for row in self.automations:
            row['trigger']['filter'] = row['trigger']['filter'].replace('/v3', '/v2')
        self.assertFalse(self.client.probe()['ready'])
        self.assertTrue(self.client.setup()['ready'])
        self.assertEqual([row['id'] for row in self.automations], ids)
        self.assertEqual(self.secret, secret)
        self.assertTrue(all('/v3' in row['trigger']['filter'] for row in self.automations))
        self.assertFalse(self.events)

    def test_registry_is_ignored_and_wrong_role_folder_cannot_dispatch(self):
        self.client.setup()
        (self.store / 'openspec/requirements.json').write_text('not JSON')
        self.client.dispatch(self.input())
        data = self.input()
        data.update(spec_id='FE-REQ-001-first', change='FE-REQ-001-first', context_change='FE-REQ-001-first')
        with self.assertRaisesRegex(bridge.BridgeError, 'match the requirement and role'):
            self.client.dispatch(data)
        self.assertEqual(len(self.events), 1)

    def test_symlinked_change_and_tampered_generated_bundle_are_rejected(self):
        original = self.home / 'original'
        (self.context / 'SA-REQ-001-first').rename(original)
        (self.context / 'SA-REQ-001-first').symlink_to(original)
        self.client.setup()
        with self.assertRaisesRegex(bridge.BridgeError, 'Symlinked'):
            self.client.dispatch(self.input())
        generated = self.repository / 'automations/openspec-sa-propose/tarball/config.json'
        generated.write_text(json.dumps({**self.config, 'mode': 'role', 'stage': 'apply'}))
        with self.assertRaisesRegex(bridge.BridgeError, 'stale'):
            self.client.probe()

    def test_partial_update_arbitrary_prefix_and_cross_role_propose_context(self):
        self.client.setup()
        folder = self.context / 'BE-STORY-7-contract'
        folder.mkdir()
        data = self.input('update', 'Backend')
        data.update(requirement_id='STORY-7', spec_id=folder.name, change=folder.name, context_change=folder.name)
        self.client.dispatch(data)
        proposed = self.input('propose', 'Frontend')
        proposed.update(requirement_id='STORY-7', spec_id='FE-STORY-7-editor', change='FE-STORY-7-editor', context_change=folder.name)
        self.client.dispatch(proposed)
        self.assertFalse((self.store / 'openspec/requirements.json').exists())
        self.assertEqual(len(self.events), 2)
        with self.assertRaises(bridge.BridgeError):
            self.client.dispatch({**proposed, 'request_id': identity(), 'context_change': 'BE-STORY-007-contract'})

    def test_service_home_and_config_validation_fail_closed(self):
        for change in ({'url_from_agent': 'https://example.com'}, {'url_from_agent': 'http://user:secret@localhost'},
                       {'url_from_agent': 'http://127.0.0.1:bad'}, {'api_prefix': '/other'}, {'auth_env_var': 'SECRET'}):
            with self.subTest(change=change), self.assertRaises(bridge.BridgeError):
                self.new_client(service={**self.service, **change})
        with self.assertRaises(bridge.BridgeError):
            self.new_client(home=str(self.repository))
        with self.assertRaises(bridge.BridgeError):
            self.new_client(env={})
        for value in ('/tmp/../store', '/tmp/.local/store', '/tmp/./store', '/tmp/a\npath', '/tmp/a\\path'):
            with self.subTest(value=value), self.assertRaises(bridge.BridgeError):
                bridge.local_path(value)
        (self.repository / 'role-workflow.json').write_text(json.dumps({**self.config, 'canvas_url': 'https://example.com'}))
        with self.assertRaises(bridge.BridgeError):
            self.new_client()

    def test_status_reports_native_pair_and_sanitizes_errors_and_metadata(self):
        self.client.setup()
        result = self.client.dispatch(self.input())
        target = {'automation_id': result['automation_id'], 'run_id': result['run_id']}
        for status in bridge.STATUSES:
            self.runs[0].update(status=status, error_detail='private-api-key', run_metadata={'secret': 'private-token'})
            value = self.client.status(target)
            self.assertEqual(value['status'], status)
            self.assertNotIn('private-', json.dumps(value))
        self.runs[0]['conversation_id'] = identity()
        self.assertEqual(self.client.status(target)['conversation_id'], self.runs[0]['conversation_id'])
        self.runs[0]['status'] = 'MADE_UP'
        with self.assertRaises(bridge.BridgeError):
            self.client.status(target)
        with self.assertRaises(bridge.BridgeError):
            self.client.status({**target, 'automation_id': self.automations[0]['id']})

    def test_status_paginates_and_missing_run_is_explicit(self):
        self.client.setup()
        result = self.client.dispatch(self.input())
        target = {'automation_id': result['automation_id'], 'run_id': result['run_id']}
        self.runs = [{**self.runs[0], 'id': identity()} for _ in range(100)] + self.runs
        self.assertEqual(self.client.status(target)['run_id'], target['run_id'])
        with self.assertRaisesRegex(bridge.BridgeError, 'not found'):
            self.client.status({**target, 'run_id': identity()})

    def completed_report(self, outcome='blocked', role='Frontend'):
        self.client.setup()
        request = self.input('apply', role)
        dispatched = self.client.dispatch(request)
        row = self.runs[0]
        row.update(status='COMPLETED' if outcome == 'completed' else 'FAILED', conversation_id=identity())
        report = {'version': 1, 'run_id': row['id'], 'conversation_id': row['conversation_id'], 'role': role, 'stage': 'apply',
                  'requirement_id': request['requirement_id'], 'spec_id': request['spec_id'],
                  'configuration': {key: self.config[key] for key in ('workspace', 'spec_store', 'store_id', 'profile', 'skill_root', 'timeout_seconds')},
                  'outcome': {'status': outcome, 'blocker_type': 'dependency' if outcome == 'blocked' else None,
                              'summary': 'Backend contract is missing', 'findings': ['Missing label API'], 'audit_errors': [],
                              'next_action': 'Finish Backend labels first', 'agent_status': None}}
        directory = self.home / '.openhands/apps/openspec-progress/role-results'
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / (row['id'] + '.json')
        path.write_text(json.dumps(report))
        return {'automation_id': dispatched['automation_id'], 'run_id': dispatched['run_id']}, path, report

    def test_report_separates_business_outcome_from_native_failure_and_snapshots_profile(self):
        target, path, report = self.completed_report()
        report['configuration']['profile'] = 'historical-profile'
        path.write_text(json.dumps(report))
        self.runs[0].update(error_detail='do-not-expose', run_metadata={'secret': 'do-not-expose'})
        value = self.client.status(target)
        self.assertEqual(value['status'], 'FAILED')
        self.assertEqual(value['report']['outcome']['status'], 'blocked')
        self.assertEqual(value['report']['configuration']['profile'], 'historical-profile')
        self.assertNotIn('do-not-expose', json.dumps(value))
        self.assertEqual(value['error'], None)
        self.assertEqual(self.client.probe()['configuration']['profile'], 'saved-profile')

    def test_managed_workspace_report_accepts_bound_child_and_rejects_other_change(self):
        target, path, report = self.completed_report()
        expected = str(Path(self.config['workspace']) / report['spec_id'] / 'sample-frontend')
        report['configuration']['workspace'] = expected
        path.write_text(json.dumps(report))
        self.assertEqual(self.client.status(target)['report']['configuration']['workspace'], expected)
        report['configuration']['workspace'] = str(Path(self.config['workspace']) / 'FE-REQ-999-other' / 'sample-frontend')
        path.write_text(json.dumps(report))
        self.assertIsNone(self.client.status(target)['report'])

    def test_sa_reports_accept_store_and_historical_planning_workspace(self):
        target, path, report = self.completed_report('completed', role='SA')
        for workspace in (self.store, Path(self.config['workspace']) / report['spec_id'] / 'planning'):
            report['configuration']['workspace'] = str(workspace)
            path.write_text(json.dumps(report))
            self.assertEqual(self.client.status(target)['report']['configuration']['workspace'], str(workspace))
        for workspace in (self.store / 'openspec', self.home / 'other-store',
                          Path(self.config['workspace']) / 'SA-REQ-999-other' / 'planning'):
            report['configuration']['workspace'] = str(workspace)
            path.write_text(json.dumps(report))
            self.assertIsNone(self.client.status(target)['report'])

    def test_downstream_report_cannot_claim_store_as_code_workspace(self):
        target, path, report = self.completed_report()
        report['configuration']['workspace'] = str(self.store)
        path.write_text(json.dumps(report))
        self.assertIsNone(self.client.status(target)['report'])

    def test_foreign_and_malformed_reports_fall_back_without_exposing_contents(self):
        target, path, report = self.completed_report()
        for edit in ({'run_id': identity()}, {'conversation_id': identity()}, {'role': 'Backend'}, {'stage': 'propose'},
                     {'spec_id': 'FE-REQ-002-other'}, {'version': True}, {'unexpected': 'secret'},
                     {'configuration': {**report['configuration'], 'spec_store': str(self.home)}},
                     {'outcome': {**report['outcome'], 'status': 'invented'}},
                     {'outcome': {**report['outcome'], 'summary': 'x' * 2001}},
                     {'outcome': {**report['outcome'], 'findings': [{'secret': 'secret'}]}}):
            path.write_text(json.dumps({**report, **edit}))
            value = self.client.status(target)
            self.assertIsNone(value['report'])
            self.assertEqual(value['status'], 'FAILED')
            self.assertNotIn('secret', json.dumps(value))
        for raw in ('{', 'x' * 65537):
            path.write_text(raw)
            self.assertIsNone(self.client.status(target)['report'])
        path.unlink()
        self.assertIsNone(self.client.status(target)['report'])
        source = self.home / 'foreign-result.json'
        source.write_text(json.dumps(report))
        path.symlink_to(source)
        self.assertIsNone(self.client.status(target)['report'])

    def test_native_lifecycle_overrides_local_business_report(self):
        target, path, report = self.completed_report()
        for status in ('PENDING', 'RUNNING', 'CANCELLED', 'SKIPPED', 'COMPLETED'):
            self.runs[0]['status'] = status
            self.assertIsNone(self.client.status(target)['report'])
        report['outcome'].update(status='completed', blocker_type=None)
        path.write_text(json.dumps(report))
        self.runs[0]['status'] = 'FAILED'
        self.assertIsNone(self.client.status(target)['report'])

    def test_runner_report_round_trip_uses_the_same_contract(self):
        target, path, report = self.completed_report()
        runtime_path = Path('/Users/oka/Desktop/openhands-automation/runtime/run.py')
        if not runtime_path.is_file():
            self.skipTest('Companion automation repository is not available')
        module_spec = importlib.util.spec_from_file_location('integration_runner', runtime_path)
        runtime = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(runtime)
        result = {'status': 'blocked', 'summary': 'Backend contract is missing', 'findings': ['Missing label API'], 'blocker_type': 'dependency'}
        runtime.save_role_outcome({**self.config, 'role': 'Frontend', 'stage': 'apply'}, report, result,
                                 {'AUTOMATION_RUN_ID': target['run_id']}, report['conversation_id'])
        self.assertEqual(self.client.status(target)['report']['outcome']['summary'], result['summary'])


if __name__ == '__main__':
    unittest.main()
