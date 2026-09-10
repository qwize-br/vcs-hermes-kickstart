#!/usr/bin/env python3
"""Execute offline tests and preserve real stdout, status and artifact hashes."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'outputs'
OUTPUT.mkdir(exist_ok=True)
if os.geteuid() == 0:
    raise SystemExit('Execute como usuário comum, não root.')
commands = [['bash', '-n', 'install.sh'], [sys.executable, 'tests/test_install.py']]
results = []
for command in commands:
    process = subprocess.run(command, cwd=ROOT, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    results.append({'command': command, 'exit_code': process.returncode, 'output': process.stdout})
    print('$', ' '.join(command), '\n' + process.stdout, 'exit_code =', process.returncode)
report = {'timestamp_utc': datetime.now(timezone.utc).isoformat(), 'platform': platform.platform(),
          'python': sys.version, 'bash': subprocess.run(['bash', '--version'], capture_output=True, text=True).stdout,
          'results': results,
          'limitations': ['Upstream/download mocked only for opt-in tests; no real Hermes installation.',
                          'No provider authentication or Telegram connectivity tested.',
                          'Only the reported host OS was exercised. Root test may be skipped when unshare is blocked.'],
          'sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in [ROOT / 'install.sh', ROOT / 'README.md', ROOT / 'tests/test_install.py', Path(__file__).resolve()]}}
(OUTPUT / 'test-report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
(OUTPUT / 'test-report.txt').write_text('\n\n'.join('$ ' + ' '.join(r['command']) + '\n' + r['output'] + '\nexit_code=' + str(r['exit_code']) for r in results) + '\n')
raise SystemExit(0 if all(r['exit_code'] == 0 for r in results) else 1)
