"""Read-only tar stream of the game's external files/cache; avoids ADB Unicode paths."""
import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--probe', type=Path, required=True)
    parser.add_argument('--snapshot', type=Path, required=True)
    args = parser.parse_args()
    probe = json.loads((args.probe/'probe.json').read_bytes())
    assert probe['status'] == 'PROBED' and probe['package'] == 'com.sega.chainchronicle'
    user = probe['android_user']
    assert isinstance(user, int) and user >= 0
    adb = str(Path('tools/platform-tools/adb.exe').resolve())
    devices = subprocess.check_output([adb, 'devices'], text=True)
    ready = [line.split()[0] for line in devices.splitlines()[1:] if line.split()[1:] == ['device']]
    assert len(ready) == 1, 'Need exactly one authorized device'
    args.snapshot.mkdir(parents=True, exist_ok=False)
    for name in ('probe.json', 'inventory.jsonl'):
        (args.snapshot/name).write_bytes((args.probe/name).read_bytes())
    report = {'status': 'COPYING', 'started_utc': datetime.now(timezone.utc).isoformat(),
              'scope': 'Accessible game external files/cache; private and server data not included',
              'method': 'adb exec-out tar; no device archive written', 'probe': probe,
              'archive': str(args.snapshot/'external_cache.tar')}
    report_path = args.snapshot/'acquisition.json'
    def save():
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    save()
    remote = f'/storage/emulated/{user}/Android/data/com.sega.chainchronicle'
    with (args.snapshot/'external_cache.tar').open('xb') as stream, (args.snapshot/'stderr.txt').open('xb') as err:
        try:
            result = subprocess.run([adb, '-s', ready[0], 'exec-out', f'tar -C {remote} -cf - files cache'],
                                    stdout=stream, stderr=err, timeout=3600)
            report['exit_code'] = result.returncode
        except subprocess.TimeoutExpired:
            report['exit_code'] = 124
    report.update(status='STREAM_COPIED_NEEDS_VALIDATION' if report['exit_code']==0 else 'COPY_FAILED_PARTIAL_PRESERVED',
                  ended_utc=datetime.now(timezone.utc).isoformat(),
                  archive_bytes=(args.snapshot/'external_cache.tar').stat().st_size)
    save()
    print(json.dumps({key: report[key] for key in ('status','exit_code','archive_bytes')}), flush=True)
    raise SystemExit(report['exit_code'])


if __name__ == '__main__':
    main()
