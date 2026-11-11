"""Publication guards for both historical evidence and the nine-contender method."""
from pathlib import Path
import copy
import importlib.util
import json
import statistics
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit import audit
spec = importlib.util.spec_from_file_location('add_libraries', Path(__file__).resolve().parents[1] / 'add-libraries.py')
add_libraries = importlib.util.module_from_spec(spec)
spec.loader.exec_module(add_libraries)

ORIGINAL = ['crab', 'webman', 'hyperf', 'symfony', 'spiral', 'laravel', 'tempest']
CASES = [('hello', 64), ('hello', 256), ('db', 64), ('validate', 64)]


class AuditTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)

    def save(self, name, data):
        (self.directory / name).write_text(json.dumps(data))

    def fixture(self, expanded=True):
        services = ORIGINAL + (['reactphp', 'amphp'] if expanded else [])
        metadata = {'full_method': True, 'valid': True, 'completed_utc': '2026-11-11T12:00:00Z',
                    'warmup_seconds': 5, 'duration_seconds': 15, 'trials': 5,
                    'sources': {'apps': {service: {} for service in services}}}
        if expanded:
            metadata['services'] = services
        self.save('metadata.json', metadata)
        trials, warmups, summary, checks = [], [], [], []
        for kind, connections in CASES:
            for service in services:
                checks.append({'case': f'{kind}-{connections}', 'service': service, 'ok': True,
                               'metadata': {'php': '8.5.12', 'debug': False, 'jit': {'on': False}}})
                records = []
                for trial in range(1, 6):
                    raw = {'workload': kind, 'duration_us': 15000000, 'requests': 1500 * trial,
                           'rps': 100 * trial, 'p50_us': 10, 'p99_us': 20,
                           'errors': dict.fromkeys(['connect', 'read', 'write', 'timeout'], 0),
                           'bad_response': 0, 'bad_body': 0}
                    for phase, collection in [('trial', trials), ('warmup', warmups)]:
                        label = f'{kind}-{connections}-{service}-{phase}-{trial}'
                        (self.directory / (label + '.log')).write_text('BENCH_JSON ' + json.dumps(raw) + '\n')
                        record = dict(raw, kind=kind, connections=connections, service=service,
                                      label=label, error_count=0)
                        if phase == 'trial':
                            record['trial'] = trial
                            records.append(record)
                        collection.append(record)
                summary.append({'case': kind, 'connections': connections, 'service': service, 'runs': 5,
                                'rps': statistics.median(r['rps'] for r in records),
                                'rps_min': 100, 'rps_max': 500, 'p50_ms': .01, 'p99_ms': .02, 'errors': 0})
        for name, value in [('trials.json', trials), ('warmups.json', warmups),
                            ('summary.json', summary), ('preflight.json', checks)]:
            self.save(name, value)

    def library_fixture(self):
        self.fixture()
        metadata = json.loads((self.directory / 'metadata.json').read_text())
        metadata['services'] = ['reactphp', 'amphp']
        metadata['full_method'] = False
        self.save('metadata.json', metadata)
        for filename in ['trials.json', 'warmups.json', 'summary.json', 'preflight.json']:
            rows = json.loads((self.directory / filename).read_text())
            if filename == 'preflight.json':
                rows = [r for r in rows if r['service'] in metadata['services'] and r['case'] in ['hello-64', 'db-64']]
            else:
                rows = [r for r in rows if r['service'] in metadata['services']
                        and (r.get('kind', r.get('case')), r['connections']) in [('hello', 64), ('db', 64)]]
            self.save(filename, rows)

    def test_two_library_supplement(self):
        self.library_fixture()
        result = audit(self.directory, require_libraries=True)
        self.assertEqual(result['verified_trials'], 20)
        self.assertEqual(result['verified_warmups'], 20)
        self.assertEqual(result['verified_summary_rows'], 4)
        self.assertFalse(result['full_method'])
        with self.assertRaises(AssertionError):
            audit(self.directory, require_full=True)

    def test_supplement_rejects_smoke_settings(self):
        self.library_fixture()
        metadata = json.loads((self.directory / 'metadata.json').read_text())
        metadata['duration_seconds'] = 2
        self.save('metadata.json', metadata)
        with self.assertRaises(AssertionError):
            audit(self.directory, require_libraries=True)

    def test_supplement_rejects_errors(self):
        self.library_fixture()
        trials = json.loads((self.directory / 'trials.json').read_text())
        trial = trials[0]
        trial['bad_response'] = trial['bad_body'] = trial['error_count'] = 1
        path = self.directory / (trial['label'] + '.log')
        raw = json.loads(path.read_text().removeprefix('BENCH_JSON '))
        raw['bad_response'] = raw['bad_body'] = 1
        path.write_text('BENCH_JSON ' + json.dumps(raw) + '\n')
        self.save('trials.json', trials)
        with self.assertRaises(AssertionError):
            audit(self.directory, require_libraries=True)

    def test_supplement_rejects_missing_trials(self):
        self.library_fixture()
        trials = json.loads((self.directory / 'trials.json').read_text())
        self.save('trials.json', trials[:-1])
        with self.assertRaises(AssertionError):
            audit(self.directory, require_libraries=True)

    def supplement_site(self):
        root = self.directory
        baseline, supplement, site = (root / name for name in ['baseline', 'supplement', 'site'])
        for path in [baseline, supplement, site]:
            path.mkdir()
        self.directory = baseline
        self.fixture(expanded=False)
        self.directory = supplement
        self.library_fixture()
        for directory, date in [(baseline, '2026-11-10'), (supplement, '2026-11-11')]:
            self.directory = directory
            metadata = json.loads((directory / 'metadata.json').read_text())
            metadata.update(started_utc=date + 'T11:00:00Z', cpu='Model name: Test CPU', host='Test host', images='Pinned images')
            for service in metadata['sources']['apps']:
                metadata['sources']['apps'][service]['version'] = 'v1.0.0'
            self.save('metadata.json', metadata)
            self.save('versions.json', {s: {'metadata': {'php': '8.5.12'}} for s in ORIGINAL + ['reactphp', 'amphp']})
        old = json.loads((baseline / 'metadata.json').read_text())
        summary = json.loads((baseline / 'summary.json').read_text())
        rows = [add_libraries.row_for(s, old, summary) for s in ORIGINAL]
        (site / 'index.html').write_text('BEFORE\n      <section class="section" aria-labelledby="benchmarks">\n' + '\n'.join(rows) + '\n      </section>\nAFTER')
        return baseline, supplement, site, rows

    def test_supplement_preserves_baseline_rows_and_discloses_separate_runs(self):
        baseline, supplement, site, rows = self.supplement_site()
        add_libraries.publish(supplement, baseline, site)
        text = (site / 'index.html').read_text()
        self.assertTrue(all(row in text for row in rows))
        self.assertEqual(text.count('<th scope="row">'), 9)
        self.assertIn('Frameworks tested 2026-11-10; ReactPHP and AMP tested separately 2026-11-11', text)
        self.assertIn('Separate runs, not a simultaneous comparison', text)
        self.assertIn('results/baseline', text)
        self.assertIn('results/supplement', text)
        self.assertTrue(text.startswith('BEFORE\n') and text.endswith('\nAFTER'))

    def test_supplement_refuses_to_overwrite_a_changed_baseline(self):
        baseline, supplement, site, rows = self.supplement_site()
        path = site / 'index.html'
        changed = path.read_text().replace('Crab 1.0.0', 'Crab 9.9.9')
        path.write_text(changed)
        with self.assertRaises(AssertionError):
            add_libraries.publish(supplement, baseline, site)
        self.assertEqual(path.read_text(), changed)

    def test_supplement_refuses_different_php(self):
        baseline, supplement, site, rows = self.supplement_site()
        versions = json.loads((supplement / 'versions.json').read_text())
        versions['reactphp']['metadata']['php'] = '8.5.99'
        self.save('versions.json', versions)
        with self.assertRaises(AssertionError):
            add_libraries.publish(supplement, baseline, site)

    def test_nine_contender_reference(self):
        self.fixture()
        result = audit(self.directory, require_full=True)
        self.assertEqual(result['verified_trials'], 180)
        self.assertEqual(result['verified_warmups'], 180)
        self.assertEqual(result['verified_summary_rows'], 36)

    def test_historical_seven_contender_reference(self):
        self.fixture(expanded=False)
        self.assertEqual(audit(self.directory, require_full=True)['verified_trials'], 140)

    def test_missing_contender_cannot_publish(self):
        self.fixture()
        metadata = json.loads((self.directory / 'metadata.json').read_text())
        metadata['services'].remove('amphp')
        self.save('metadata.json', metadata)
        with self.assertRaises(AssertionError):
            audit(self.directory, require_full=True)

    def test_duplicate_preflight_cannot_hide_missing_check(self):
        self.fixture()
        checks = json.loads((self.directory / 'preflight.json').read_text())
        checks[-1] = copy.deepcopy(checks[0])
        self.save('preflight.json', checks)
        with self.assertRaises(AssertionError):
            audit(self.directory, require_full=True)

    def test_duplicate_warmup_cannot_hide_missing_trial(self):
        self.fixture()
        warmups = json.loads((self.directory / 'warmups.json').read_text())
        warmups[-1] = copy.deepcopy(warmups[0])
        self.save('warmups.json', warmups)
        with self.assertRaises(AssertionError):
            audit(self.directory, require_full=True)

    def test_changed_raw_log_fails_audit(self):
        self.fixture()
        path = self.directory / 'hello-64-amphp-trial-1.log'
        path.write_text(path.read_text().replace('"rps": 100', '"rps": 101'))
        with self.assertRaises(AssertionError):
            audit(self.directory, require_full=True)

    def test_expanded_site_uses_nine_measured_rows_and_preserves_surroundings(self):
        self.fixture()
        metadata = json.loads((self.directory / 'metadata.json').read_text())
        metadata['started_utc'] = '2026-11-11T11:00:00Z'
        metadata['cpu'] = 'Model name: Test CPU @ 3.0GHz\n'
        for service in metadata['sources']['apps']:
            metadata['sources']['apps'][service]['version'] = 'v1.0.0'
        self.save('metadata.json', metadata)
        self.save('versions.json', {'crab': {'metadata': {'php': '8.5.12'}}})
        # A competitor win must appear above Crab rather than being hidden by a fixed order.
        trials = json.loads((self.directory / 'trials.json').read_text())
        for trial in trials:
            if (trial['kind'], trial['connections'], trial['service']) == ('hello', 64, 'amphp'):
                trial['rps'] *= 2
                path = self.directory / (trial['label'] + '.log')
                raw = json.loads(path.read_text().removeprefix('BENCH_JSON '))
                raw['rps'] = trial['rps']
                path.write_text('BENCH_JSON ' + json.dumps(raw) + '\n')
        self.save('trials.json', trials)
        summary = json.loads((self.directory / 'summary.json').read_text())
        for row in summary:
            if (row['case'], row['connections'], row['service']) == ('hello', 64, 'amphp'):
                for key in ['rps', 'rps_min', 'rps_max']:
                    row[key] *= 2
        self.save('summary.json', summary)
        site = self.directory / 'site'
        site.mkdir()
        (site / 'index.html').write_text('BEFORE\n      <section class="section" aria-labelledby="benchmarks">\nold\n      </section>\nAFTER')
        script = Path(__file__).resolve().parents[1] / 'update-site.py'
        result = subprocess.run([sys.executable, str(script), str(self.directory), '--site', str(site)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        text = (site / 'index.html').read_text()
        self.assertTrue(text.startswith('BEFORE\n'))
        self.assertTrue(text.endswith('\nAFTER'))
        self.assertEqual(text.count('<th scope="row">'), 9)
        self.assertIn('ReactPHP HTTP 1.0.0', text)
        self.assertIn('AMP HTTP Server 1.0.0', text)
        self.assertLess(text.index('AMP HTTP Server 1.0.0'), text.index('Crab 1.0.0'))
        self.assertIn('Framework / server', text)
        self.assertIn('HTTP libraries, not full application frameworks', text)

    def test_historical_run_cannot_refresh_expanded_site(self):
        self.fixture(expanded=False)
        self.save('versions.json', {'crab': {'metadata': {'php': '8.5.12'}}})
        site = self.directory / 'site'
        site.mkdir()
        (site / 'index.html').write_text('unchanged')
        script = Path(__file__).resolve().parents[1] / 'update-site.py'
        result = subprocess.run([sys.executable, str(script), str(self.directory), '--site', str(site)],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('fresh complete nine-contender run', result.stderr)
        self.assertEqual((site / 'index.html').read_text(), 'unchanged')


if __name__ == '__main__':
    unittest.main()
