# IDC Video Suite 2

An installable local editing skills package for documentary stories, motion hooks, listen-alongs and platform cutdowns. Version 2 adds transcript intake checks, durable timestamp feedback, export evidence and a verified portable bundle. It preserves the source story and keeps no added music and native Remotion as defaults.

## Use

Load `SKILL.md` as the conductor, or name a seat. The ten seats are ingest-project, transcript, cut, ingest-broll, oracle-spec, hook, style-feedback, assemble, quality-check and cutdowns. A seat is a responsibility, not an instruction to spawn an agent.

```text
Load IDC Video Suite. Ingest this project folder.
Build a documentary spine from all camera transcripts.
Keep the full story; make the launch cut a separate shorter edit.
```

The conductor reads child skills explicitly. No claim is made that every harness discovers nested skills automatically. Every skill has frontmatter and a Codex metadata sidecar.

## Executable checks

Python 3.10 or newer, with no Python dependencies. Export probing additionally requires `ffprobe` on PATH.

```sh
python3 scripts/video_suite.py transcript examples/transcript.json
python3 scripts/video_suite.py style examples/feedback.json
python3 scripts/video_suite.py bindings /path/sources.json --project /path/to/project --verify-media
python3 scripts/video_suite.py quality /path/export.mp4 --expected-ms 10000
python3 -m unittest discover -s tests -v
```

These tools are deliberately narrow. They do not transcribe audio, render Remotion, certify lip sync or upload to a platform. The recipe and runtime style profile remain owned by the editor's canonical validator; the portable style ledger is advisory and is not automatically applied to a renderer.

## Package and install

```sh
python3 scripts/package.py bundle /new/path/idc-video-suite-2.0.0.zip
python3 scripts/package.py install /new/skill-root/idc-video-suite
python3 scripts/package.py verify /new/skill-root/idc-video-suite
```

Existing destinations are refused. Bundle checksums establish byte identity and completeness, not authenticity or successful harness invocation. Pin the source commit when vendoring into the editor. [Integration](references/editor-integration.md) describes the recipe handoff, installation limits and v1 migration. [Contracts](references/contracts.md) specifies bounded JSON inputs. [Tutorial lessons](references/tutorial-lessons.md) traces the general workflow ideas adopted from the reviewed video.

## What changed

- All camera transcripts and source clocks are explicit; longest recording no longer silently wins.
- Documentary keepers are separate from scripted retakes and from the optional held-image warehouse layout.
- Review a short hook; preserve accepted reusable feedback with cut and timestamp provenance.
- Real product art and thumbnail variants remain separate.
- Missing evidence is recorded honestly; structural, visual, audio and publication checks remain distinct.
- No new magic approval keyword, paid-service connector or proprietary asset is bundled.

MIT © 2026 Island Development Crew. See [NOTICE](NOTICE.md).
