# B02 sparse local candidate

This is a new local frontend path for the reviewed C19/R01 payload. It is not a
full builder port or standalone offline release. Cards, sidecars, historical
audits and media stay at their original physical paths and are read-only.

Only six frontend files and a small explicit `paths.js` are received. Index data
scripts, lazy card loading and images use real relative paths to the fixed source
data/media roots. No route aliases, media copies, hardlinks or junctions are used.
The repository-root loopback service was accepted in a real HTTP browser.
Relative file paths resolve to the declared data/media roots, but `file://`
browser behavior is **UNTESTED**: the available Browser Use tool accepts only
HTTP/HTTPS and rejected that scheme. No policy bypass or double-click/offline
browser acceptance is claimed.

```powershell
& ./.venv/Scripts/python.exe -B scripts/project_layout/b02_candidate/adapter.py preflight
& ./.venv/Scripts/python.exe -B scripts/project_layout/b02_candidate/adapter.py receive --run-id receive01
& ./.venv/Scripts/python.exe -B scripts/project_layout/b02_candidate/adapter.py validate --run-id validate01 --receive-run receive01
& ./.venv/Scripts/python.exe -B scripts/project_layout/b02_candidate/adapter.py serve --port 8779 --receive-run receive01
```

`receive` refuses an existing candidate. Every run refuses an existing report
directory. New reports go to `projects/reader/reports/b02-20261108-v1/<run-id>/`.
Existing receive receipts under `output/project-layout/b02-20261108-v1/`
remain readable, and their run IDs remain reserved.
The combined size of this source directory, candidate, reports and parent B02
docs is limited to 9 MiB, leaving integration headroom under the 10 MiB task
budget. The adapter reserves space before its own frontend/receipt writes;
service access logs and parent browser artifacts are included in final task
measurements. No old outputs are deleted to make room.

Receive/validate use read-only original reviewed proof functions, bytecode disabled, and
a filesystem audit hook that refuses writes outside the new run/candidate roots.
Actual project reads are hashed before first read and rechecked after the run.
The original branch-wiring CLI receives explicit source data and candidate
frontend without its optional report flag, so it writes no file. Compact stdout,
stderr and real exit codes are retained by Python. Preflight/serve are read-only;
their reads are not recorded by the receive/validate audit hook. The hook is not
a subprocess sandbox. Validate/serve both require the explicit receive run and
reject a source/frontend identity change since receipt.

Validation has separate claims: (1) source runtime hashes and original adaptation
identity/source hashes checked read-only, and (2) actual candidate frontend paths,
hashes, syntax and branch wiring against that payload. A new composition receipt
binds candidate frontend hashes to source runtime hashes and the original source
adaptation. The full/C19/R01/V01 semantic proofs are inherited with original scope
and are not rerun. Historical PASS/seal files never become a new candidate PASS.
Browser validation is performed and recorded by the integrating parent.

The preview binds only 127.0.0.1 and refuses port 8768, directory listings,
reparse points and paths outside candidate frontend, selected source runtime
files and media. Entry: `/projects/reader/site/b02-20261108-v1/index.html`.
