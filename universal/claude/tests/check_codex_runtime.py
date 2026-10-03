"""Check native Codex discovery without model calls; optional --live uses current home."""
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import threading

root = Path(__file__).resolve().parents[1]

def inspect(home):
    with tempfile.TemporaryDirectory() as cwd:
        env = {**os.environ, 'HOME': str(home), 'CODEX_HOME': str(home / '.codex')}
        process = subprocess.Popen(['codex', 'app-server', '--stdio'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, cwd=cwd, env=env)
        messages = queue.Queue()
        def reader():
            for line in process.stdout:
                try:
                    messages.put(json.loads(line))
                except ValueError:
                    pass
        threading.Thread(target=reader, daemon=True).start()
        def request(id, method, params):
            process.stdin.write(json.dumps({'id': id, 'method': method, 'params': params})+'\n')
            process.stdin.flush()
            while True:
                try:
                    message = messages.get(timeout=15)
                except queue.Empty as error:
                    raise RuntimeError("Codex initialization timed out. Use the default isolated check to avoid startup dependencies of the live configuration.") from error
                if message.get('id') == id:
                    if 'error' in message:
                        raise RuntimeError(message['error'])
                    return message['result']
        try:
            request(1, 'initialize', {'clientInfo': {'name': 'dotfiles-check', 'version': '1'}})
            process.stdin.write('{"method":"initialized"}\n')
            process.stdin.flush()
            hooks=request(2, 'hooks/list', {'cwds': [cwd]})
            skills=request(3, 'skills/list', {'cwds': [cwd], 'forceReload': True})
            entries=hooks['data']
            print(json.dumps({'hooks': [{'count':len(e['hooks']), 'errors':e['errors'], 'warnings':e['warnings'], 'trust':[h.get('trustStatus') for h in e['hooks']]} for e in entries]}))
            assert all(not e['errors'] for e in entries), hooks
            skills_data=skills['data']
            names=[s['name'] for e in skills_data for s in e['skills']]
            expected={p.name for p in (root/'stowed/.agents/skills').iterdir()}
            missing=expected-set(names)
            print(json.dumps({'authoredSkillsFound': sorted(expected-set(missing)), 'missing': sorted(missing), 'errors':[e.get('errors') for e in skills_data]}))
            assert not missing, missing
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

if len(sys.argv)>1:
    inspect(Path.home())
else:
    with tempfile.TemporaryDirectory() as tmp:
        home=Path(tmp)
        subprocess.run(['python3', str(root/'install.py'), '--agent', 'both', '--target-home', tmp], check=True, capture_output=True)
        inspect(home)
