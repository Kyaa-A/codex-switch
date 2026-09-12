import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
TOOL = 'claude-switch' if (REPO / 'claude-switch').is_file() else 'codex-switch'
CLAUDE = TOOL == 'claude-switch'


class SwitchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='switch-test-')
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name) / "user home"
        self.root = self.home / ('.claude' if CLAUDE else '.codex')
        self.root.mkdir(parents=True)
        self.auth = self.root / ('.credentials.json' if CLAUDE else 'auth.json')
        self.saved_name = 'credentials.json' if CLAUDE else 'auth.json'
        self.profiles = self.root / '.profiles'
        self.bin = Path(self.tmp.name) / 'bin'
        self.bin.mkdir()
        self.env = dict(os.environ, HOME=str(self.home), PATH=f'{self.bin}:/usr/bin:/bin',
                        NO_COLOR='1', PYTHONPATH=str(self.bin))
        for name in ('CODEX_HOME', 'CLAUDE_CONFIG_DIR', 'CLAUDE_SECURESTORAGE_CONFIG_DIR'):
            self.env.pop(name, None)
        # Deny all real HTTP while exercising the embedded Python renderers.
        (self.bin / 'sitecustomize.py').write_text(
            'import urllib.request, urllib.error, os\n'
            'def offline(req, *args, **kwargs):\n'
            '    if getattr(req, "data", None):\n'
            '        open(os.path.join(os.environ["HOME"], "unexpected-post"), "w").close()\n'
            '    raise urllib.error.HTTPError(req.full_url, 401, "test", {}, None)\n'
            'urllib.request.urlopen = offline\n')
        self.stub('claude', 'if [[ "$*" == "auth status --json" ]]; then echo \'{"loggedIn":true,"email":"test@example.test"}\'; fi\n')
        self.stub('codex', 'if [[ "$*" == "login status" ]]; then echo "Logged in"; fi\n')
        self.write_auth('A')

    def stub(self, name, body):
        path = self.bin / name
        path.write_text('#!/bin/bash\n' + body)
        path.chmod(0o755)

    def payload(self, account):
        if CLAUDE:
            return {'claudeAiOauth': {'accessToken': 'fake-' + account,
                    'refreshToken': 'fake-refresh-' + account, 'expiresAt': 9999999999999}}
        return {'auth_mode': 'chatgpt', 'tokens': {'access_token': 'fake-' + account,
                'refresh_token': 'fake-refresh-' + account, 'account_id': account}}

    def write_auth(self, account):
        self.auth.write_text(json.dumps(self.payload(account)))

    def profile(self, name, account):
        folder = self.profiles / name
        folder.mkdir(parents=True, exist_ok=True)
        (folder / self.saved_name).write_text(json.dumps(self.payload(account)))
        return folder / self.saved_name

    def run_tool(self, *args, input='', check=True):
        result = subprocess.run(['bash', str(REPO / TOOL), *args], env=self.env,
                                input=input, text=True, capture_output=True,
                                timeout=10, start_new_session=True)
        if check:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def test_round_trip_preserves_refresh_and_history(self):
        history = self.root / ('projects' if CLAUDE else 'sessions') / 'test.jsonl'
        history.parent.mkdir()
        history.write_text('history sentinel\n')
        self.run_tool('save', 'work')
        self.profile('personal', 'B')
        self.write_auth('A-refreshed')
        self.run_tool('use', 'personal')
        self.assertEqual(json.loads(self.auth.read_text()), self.payload('B'))
        self.run_tool('use', 'work')
        self.assertEqual(json.loads(self.auth.read_text()), self.payload('A-refreshed'))
        self.run_tool('rename', 'work', 'renamed')
        self.assertEqual((self.profiles / '.active').read_text().strip(), 'renamed')
        self.run_tool('delete', 'personal', input='y\n')
        self.assertFalse((self.profiles / 'personal').exists())
        self.assertEqual(history.read_text(), 'history sentinel\n')

    def test_invalid_names_are_rejected_without_mutation(self):
        self.profile('good', 'A')
        outside = self.root / self.saved_name
        outside.write_text(json.dumps(self.payload('outside')))
        for args in [('save', 'bad/name'), ('save', 'all'), ('use', '..'),
                     ('rename', '..', 'moved'), ('rename', 'good', 'bad/name'),
                     ('delete', '..'), ('usage', '..')]:
            with self.subTest(args=args):
                result = self.run_tool(*args, input='y\n', check=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertTrue(outside.exists())
                self.assertTrue((self.profiles / 'good').exists())

    def test_saved_credentials_are_private(self):
        self.auth.chmod(0o644)
        self.run_tool('save', 'work')
        self.assertEqual((self.profiles.stat().st_mode & 0o777), 0o700)
        self.assertEqual(((self.profiles / 'work').stat().st_mode & 0o777), 0o700)
        self.assertEqual(((self.profiles / 'work' / self.saved_name).stat().st_mode & 0o777), 0o600)

    def test_bad_credentials_do_not_replace_current_login(self):
        target = self.profile('broken', 'B')
        target.write_text('{broken json')
        before = self.auth.read_bytes()
        result = self.run_tool('use', 'broken', check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.auth.read_bytes(), before)

    def test_empty_credentials_cannot_be_saved(self):
        self.auth.write_text('{}')
        self.assertNotEqual(self.run_tool('save', 'empty', check=False).returncode, 0)
        self.assertFalse((self.profiles / 'empty').exists())

    def test_eof_does_not_confirm_overwrite(self):
        saved = self.profile('work', 'B')
        before = saved.read_bytes()
        self.run_tool('save', 'work', check=False)
        self.assertEqual(saved.read_bytes(), before)

    def test_menu_eof_does_not_select_first_profile(self):
        self.profile('work', 'B')
        before = self.auth.read_bytes()
        self.run_tool('use', check=False)
        self.assertEqual(self.auth.read_bytes(), before)

    def test_symlink_profile_is_rejected(self):
        outside = self.home / 'outside'
        outside.mkdir()
        saved = outside / self.saved_name
        saved.write_text(json.dumps(self.payload('outside')))
        self.profiles.mkdir()
        (self.profiles / 'linked').symlink_to(outside, target_is_directory=True)
        result = self.run_tool('save', 'linked', input='y\n', check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(saved.read_text()), self.payload('outside'))

    def test_corrupt_active_marker_cannot_escape_profiles(self):
        self.profile('work', 'B')
        (self.profiles / '.active').write_text('../outside')
        self.run_tool('use', 'work', check=False)
        self.assertFalse((self.root / 'outside').exists())

    def test_same_profile_restores_missing_auth(self):
        self.profile('work', 'A')
        (self.profiles / '.active').write_text('work')
        self.auth.unlink()
        self.run_tool('use', 'work')
        self.assertEqual(json.loads(self.auth.read_text()), self.payload('A'))

    def test_skipped_login_save_does_not_overwrite_previous_profile(self):
        saved = self.profile('work', 'A')
        (self.profiles / '.active').write_text('work')
        auth_expr = '"$HOME/.claude/.credentials.json"' if CLAUDE else '"$HOME/.codex/auth.json"'
        self.stub('claude' if CLAUDE else 'codex',
                  'if [[ "$*" == "auth login" || "$*" == "login" ]]; then\n'
                  "cat > " + auth_expr + " <<'JSON'\n" + json.dumps(self.payload('B')) + '\nJSON\nfi\n')
        self.run_tool('login', input='\n', check=False)
        self.assertFalse((self.profiles / '.active').exists())
        self.profile('third', 'C')
        self.run_tool('use', 'third')
        self.assertEqual(json.loads(saved.read_text()), self.payload('A'))
        backups = list(self.profiles.glob('.unsaved-*'))
        self.assertTrue(any(json.loads(p.read_text()) == self.payload('B') for p in backups))

    def test_failed_login_restores_previous_credentials(self):
        self.profile('work', 'A')
        (self.profiles / '.active').write_text('work')
        auth_expr = '"$HOME/.claude/.credentials.json"' if CLAUDE else '"$HOME/.codex/auth.json"'
        self.stub('claude' if CLAUDE else 'codex',
                  'if [[ "$*" == "auth login" || "$*" == "login" ]]; then\n'
                  'echo broken > ' + auth_expr + '\nexit 7\nfi\n')
        self.assertNotEqual(self.run_tool('login', check=False).returncode, 0)
        self.assertEqual(json.loads(self.auth.read_text()), self.payload('A'))
        self.assertEqual((self.profiles / '.active').read_text().strip(), 'work')

    def test_list_never_refreshes_tokens_or_prints_ansi_when_piped(self):
        self.profile('work', 'A')
        before = (self.profiles / 'work' / self.saved_name).read_bytes()
        result = self.run_tool('list')
        self.assertFalse((self.home / 'unexpected-post').exists())
        self.assertEqual((self.profiles / 'work' / self.saved_name).read_bytes(), before)
        self.assertNotIn('\x1b', result.stdout)

    def test_custom_config_directory(self):
        custom = self.home / "custom's config"
        custom.mkdir()
        custom_auth = custom / self.auth.name
        custom_auth.write_text(self.auth.read_text())
        self.auth.unlink()
        self.env['CLAUDE_CONFIG_DIR' if CLAUDE else 'CODEX_HOME'] = str(custom)
        self.run_tool('save', 'custom')
        self.assertTrue((custom / '.profiles' / 'custom' / self.saved_name).exists())

    def test_failed_install_preserves_existing_binary(self):
        installed = self.home / '.local/bin' / TOOL
        installed.parent.mkdir(parents=True)
        installed.write_text('working binary sentinel')
        self.stub('curl', 'while [[ $# -gt 0 ]]; do\nif [[ "$1" == "-o" ]]; then echo partial > "$2"; break; fi\nshift\ndone\nexit 22\n')
        result = subprocess.run(['bash', str(REPO / 'install.sh')], env=self.env,
                                text=True, capture_output=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(installed.read_text(), 'working binary sentinel')

    def test_busy_profile_store_rejects_mutation(self):
        self.profiles.mkdir()
        (self.profiles / '.lock').mkdir()
        before = self.auth.read_bytes()
        result = self.run_tool('save', 'work', check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.profiles / 'work').exists())
        self.assertEqual(self.auth.read_bytes(), before)
        self.run_tool('help')

    def test_failed_credential_replace_preserves_live_file(self):
        self.profile('work', 'A')
        self.profile('personal', 'B')
        (self.profiles / '.active').write_text('work')
        self.stub('mv', 'for arg in "$@"; do last="$arg"; done\n'
                  'if [[ "$last" == "$HOME/.claude/.credentials.json" || "$last" == "$HOME/.codex/auth.json" ]]; then exit 73; fi\n'
                  'exec /bin/mv "$@"\n')
        before = self.auth.read_bytes()
        result = self.run_tool('use', 'personal', check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.auth.read_bytes(), before)
        self.assertEqual((self.profiles / '.active').read_text().strip(), 'work')
        self.assertFalse(list(self.root.glob('*.tmp.*')))
        self.assertFalse((self.profiles / '.lock').exists())

    def test_install_validates_download_and_supports_fish(self):
        installed = self.home / '.local/bin' / TOOL
        self.env['SHELL'] = '/usr/bin/fish'
        self.stub('curl', 'while [[ $# -gt 0 ]]; do\nif [[ "$1" == "-o" ]]; then printf \'#!/usr/bin/env bash\\necho installed\\n\' > "$2"; break; fi\nshift\ndone\n')
        result = subprocess.run(['bash', str(REPO / 'install.sh')], env=self.env,
                                text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(os.access(installed, os.X_OK))
        self.assertTrue((self.home / '.config/fish/config.fish').exists())
        before = installed.read_bytes()
        self.stub('curl', 'while [[ $# -gt 0 ]]; do\nif [[ "$1" == "-o" ]]; then echo "<html>failure</html>" > "$2"; break; fi\nshift\ndone\n')
        result = subprocess.run(['bash', str(REPO / 'install.sh')], env=self.env,
                                text=True, capture_output=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(installed.read_bytes(), before)

    def test_help_and_version_do_not_create_profile_store(self):
        self.run_tool('help')
        self.run_tool('--version')
        self.assertFalse(self.profiles.exists())

    @unittest.skipUnless(CLAUDE, 'Claude status metadata only')
    def test_status_snapshot_does_not_follow_symlink(self):
        self.profile('work', 'A')
        outside = self.home / 'outside-status'
        outside.write_text('sentinel')
        (self.profiles / 'work/status.json').symlink_to(outside)
        self.run_tool('save', 'work', input='y\n', check=False)
        self.assertEqual(outside.read_text(), 'sentinel')

    def test_marker_write_failure_does_not_misattribute_credentials(self):
        saved = self.profile('work', 'A')
        self.profile('personal', 'B')
        (self.profiles / '.active').write_text('work')
        self.stub('mktemp', 'if [[ "$*" == *"/.active."* ]]; then exit 73; fi\nexec /bin/mktemp "$@"\n')
        self.assertNotEqual(self.run_tool('use', 'personal', check=False).returncode, 0)
        marker = self.profiles / '.active'
        if marker.exists():
            self.assertEqual(json.loads(self.auth.read_text()), self.payload('A'))
        self.assertEqual(json.loads(saved.read_text()), self.payload('A'))

    def test_interrupted_login_restores_previous_credentials(self):
        self.profile('work', 'A')
        (self.profiles / '.active').write_text('work')
        auth_expr = '"$HOME/.claude/.credentials.json"' if CLAUDE else '"$HOME/.codex/auth.json"'
        self.stub('claude' if CLAUDE else 'codex',
                  'if [[ "$*" == "auth login" || "$*" == "login" ]]; then\n'
                  'echo broken > ' + auth_expr + '\nkill -TERM "$PPID"\nexit 7\nfi\n')
        self.assertNotEqual(self.run_tool('login', check=False).returncode, 0)
        self.assertEqual(json.loads(self.auth.read_text()), self.payload('A'))
        self.assertEqual((self.profiles / '.active').read_text().strip(), 'work')
        self.assertFalse((self.profiles / '.lock').exists())


if __name__ == '__main__':
    unittest.main()
