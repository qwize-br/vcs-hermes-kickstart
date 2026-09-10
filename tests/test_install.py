#!/usr/bin/env python3
"""Real subprocess tests; no Hermes installation or host credentials used."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'install.sh'

class InstallerTests(unittest.TestCase):
    def setUp(self):
        (ROOT / 'outputs').mkdir(exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix='sandbox ', dir=ROOT / 'outputs')
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.home = self.base / 'fake home'
        self.home.mkdir()
        self.sentinel = self.home / '.hermes' / 'profiles' / 'existing' / 'keep.txt'
        self.sentinel.parent.mkdir(parents=True)
        self.sentinel.write_text('DO NOT CHANGE')
        self.dest = self.base / 'new workspace'
        self.env = dict(os.environ, HOME=str(self.home), HERMES_HOME=str(self.sentinel.parent), PYTHONDONTWRITEBYTECODE='1')
    def run_install(self, *args):
        result = subprocess.run(['bash', str(SCRIPT), '--workspace', str(self.dest), *map(str,args)], env=self.env, text=True, capture_output=True)
        self.assertEqual(self.sentinel.read_text(), 'DO NOT CHANGE')
        return result
    def test_validation_dry_run_copy_and_no_clobber(self):
        result = self.run_install('--dry-run')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.dest.exists())
        for path in ['relative', '/', str(self.home / '.hermes' / 'new'), str(self.base / 'absent' / 'new'), str(self.base) + '/../unsafe', str(self.base / 'bad\nname')]:
            with self.subTest(path=path):
                self.assertNotEqual(self.run_install('--workspace', path).returncode, 0)
        link = self.base / 'linked parent'
        link.symlink_to(self.home, target_is_directory=True)
        self.assertNotEqual(self.run_install('--workspace', link / 'new').returncode, 0)
        source = self.base / 'vault source'
        source.mkdir()
        (source / '.hidden.md').write_text('private sample')
        (source / 'AGENTS.md').write_text('untrusted instructions')
        (source / 'note.md').write_text('Original')
        self.assertNotEqual(self.run_install('--vault-source', source / 'missing').returncode, 0)
        (source / 'outside').symlink_to(self.sentinel)
        self.assertNotEqual(self.run_install('--vault-source', source).returncode, 0)
        self.assertFalse(self.dest.exists())
        (source / 'outside').unlink()
        result = self.run_install('--vault-source', source)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.dest / 'vault' / '.hidden.md').read_text(), 'private sample')
        self.assertEqual((self.dest / 'vault' / 'AGENTS.md').read_text(), 'untrusted instructions')
        self.assertFalse((self.dest / 'vault' / 'README.md').exists())
        before = {str(f.relative_to(self.dest)): f.read_bytes() for f in self.dest.rglob('*') if f.is_file()}
        self.assertNotEqual(self.run_install('--vault-source', source).returncode, 0)
        after = {str(f.relative_to(self.dest)): f.read_bytes() for f in self.dest.rglob('*') if f.is_file()}
        self.assertEqual(before, after)
        self.assertEqual((source / 'note.md').read_text(), 'Original')

    def mock_tools(self):
        import json
        tools = self.base / 'mock bin'
        tools.mkdir()
        payload = self.base / 'upstream-fixture.sh'
        payload.write_text('''#!/usr/bin/env bash
set -eu
printf '%s\\n' "$HOME" "$HERMES_HOME" "$@" > "$HOME/upstream-call.txt"
mkdir -p "$HOME/.local/bin"
printf '#!/usr/bin/env bash\\nprintf "fixture-version\\\\n"\\n' > "$HOME/.local/bin/hermes"
chmod +x "$HOME/.local/bin/hermes"
''')
        curl = tools / 'curl'
        curl.write_text('#!/usr/bin/env python3\nimport pathlib, sys\n' +
                        'base = pathlib.Path(' + repr(str(self.base)) + ')\n' +
                        '(base / "download.called").write_text("called")\n' +
                        'if (base / "download.fail").exists(): sys.exit(22)\n' +
                        'sys.stdout.buffer.write((base / "upstream-fixture.sh").read_bytes())\n')
        curl.chmod(0o700)
        self.env['PATH'] = str(tools) + os.pathsep + os.environ['PATH']
        return payload

    def test_opt_in_and_isolated_launcher(self):
        self.mock_tools()
        result = self.run_install('--install-hermes', '--dry-run')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.base / 'download.called').exists())
        result = self.run_install('--install-hermes')
        self.assertEqual(result.returncode, 0, result.stderr)
        runtime = self.dest / 'runtime-user'
        call = (runtime / 'upstream-call.txt').read_text()
        self.assertIn(str(runtime), call)
        self.assertIn(str(self.dest / 'hermes-home'), call)
        self.assertIn('--skip-setup', call)
        self.assertFalse((self.dest / 'outputs' / 'INCOMPLETE').exists())
        self.assertTrue((self.dest / 'outputs' / 'bootstrap.json').exists())
        launcher = self.dest / 'bin' / 'hermes-workspace'
        result = subprocess.run([str(launcher), '--version'], env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('fixture-version', result.stdout)
        self.assertNotEqual(subprocess.run([str(launcher), '--profile', 'default'], env=self.env, capture_output=True).returncode, 0)

    def test_download_failure_leaves_evidence_without_success(self):
        self.mock_tools()
        (self.base / 'download.fail').touch()
        result = self.run_install('--install-hermes')
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue((self.dest / 'outputs' / 'INCOMPLETE').exists())
        self.assertFalse((self.dest / 'outputs' / 'bootstrap.json').exists())
        self.assertFalse((self.dest / 'runtime-user' / 'upstream-call.txt').exists())

    def test_upstream_failure_is_not_success(self):
        payload = self.mock_tools()
        payload.write_text('#!/usr/bin/env bash\nexit 42\n')
        result = self.run_install('--install-hermes')
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue((self.dest / 'outputs' / 'INCOMPLETE').exists())
        self.assertFalse((self.dest / 'outputs' / 'bootstrap.json').exists())

    def test_no_opt_in_no_network_and_clean_environment(self):
        self.mock_tools()
        result = self.run_install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.base / 'download.called').exists())
        fake = self.dest / 'runtime-user' / '.local' / 'bin' / 'hermes'
        fake.parent.mkdir(parents=True, exist_ok=True)
        fake.write_text('#!/usr/bin/env python3\nimport json, os\nprint(json.dumps(dict(os.environ)))\n')
        fake.chmod(0o700)
        self.env['TELEGRAM_BOT_TOKEN'] = 'must-not-inherit'
        self.env['HERMES_PROFILE'] = 'existing'
        result = subprocess.run([str(self.dest / 'bin' / 'hermes-workspace'), 'config', 'path'], env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        import json
        env = json.loads(result.stdout)
        self.assertEqual(env['HERMES_HOME'], str(self.dest / 'hermes-home'))
        self.assertEqual(env['HOME'], str(self.dest / 'runtime-user'))
        self.assertNotIn('TELEGRAM_BOT_TOKEN', env)
        self.assertNotIn('HERMES_PROFILE', env)

    def test_skill_templates_and_launch_syntax(self):
        result = self.run_install()
        self.assertEqual(result.returncode, 0, result.stderr)
        skills = sorted((self.dest / 'hermes-home' / 'skills').glob('*/SKILL.md'))
        self.assertEqual(len(skills), 3)
        for skill in skills:
            content = skill.read_text()
            self.assertTrue(content.startswith('---\n'))
            self.assertIn('version: 0.1.0', content)
            self.assertIn('## Verificação', content)
            self.assertIn('## Limites', content)
        self.assertEqual(subprocess.run(['bash', '-n', str(self.dest / 'bin' / 'hermes-workspace')]).returncode, 0)

    def test_reject_special_files_existing_empty_and_bad_options(self):
        self.dest.mkdir()
        self.assertNotEqual(self.run_install().returncode, 0)
        self.assertEqual(list(self.dest.iterdir()), [])
        self.dest.rmdir()
        for options in [('--unknown',), ('--vault-source',), ('--workspace', '')]:
            self.assertNotEqual(self.run_install(*options).returncode, 0)
            self.assertFalse(self.dest.exists())
        source = self.base / 'source'
        source.mkdir()
        os.mkfifo(source / 'pipe')
        self.assertNotEqual(self.run_install('--vault-source', source).returncode, 0)
        self.assertFalse(self.dest.exists())

    def test_no_root_via_user_namespace_when_available(self):
        import shutil
        unshare = shutil.which('unshare')
        if not unshare:
            self.skipTest('unshare não disponível; recusa root não exercitada')
        probe = subprocess.run([unshare, '--user', '--map-root-user', 'id', '-u'], capture_output=True)
        if probe.returncode != 0:
            self.skipTest('host bloqueia user namespace; recusa root não exercitada')
        result = subprocess.run([unshare, '--user', '--map-root-user', 'bash', str(SCRIPT), '--workspace', str(self.dest)], env=self.env, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('root', result.stderr)
        self.assertFalse(self.dest.exists())

    def test_starter_and_spaces(self):
        result = self.run_install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('modelo didático', (self.dest / 'vault' / 'README.md').read_text())
        self.assertTrue((self.dest / 'hermes-home' / 'skills' / 'kickstart-comms' / 'SKILL.md').is_file())
        self.assertTrue((self.dest / 'bin' / 'hermes-workspace').is_file())
        self.assertFalse((self.home / '.bashrc').exists())

if __name__ == '__main__':
    if os.geteuid() == 0:
        raise SystemExit('Execute os testes como usuário comum; o instalador recusa root.')
    unittest.main(verbosity=2)
