# New projects and Claude handoff

The editor owns project initialization. At the start of every new video edit, run this from the **video-editor checkout**, not from the skills package:

```sh
python3 video_project.py init /absolute/path/to/new-project --title 'Project title'
```

The destination must be new; the initializer must refuse an existing directory or file. Resume an existing project by reading its records instead of rerunning initialization. Preserve original recordings; place imported copies in the appropriate source folders and register their identities before editing. An unavailable initializer is a reported capability gap, not permission to claim an initialized project.

The workspace separates inputs, editorial state, previews and delivery:

```text
brief/
media/
  originals/{camera-a,camera-b,camera-c,screen,audio}/
  broll/{captured,licensed,generated}/
  stills/
assets/
  brand/{motion,thumbnails}/
  fonts/
  graphics/
transcripts/{raw,corrected,words}/
edits/{spine,sync,profiles,notes}/
out/{proxies,frames,handoffs,previews,quality}/
delivery/{youtube,tiktok,shorts,linkedin,x}/
project.json                         # idc.video-project/1
project.lock.json                    # idc.video-project-lock/1, initialized/unverified
media/source-register.csv
edits/notes/decisions.md
brief/BRIEF.md
brief/corrections.json
delivery/deliverables.csv
HANDOFF.md
AGENTS.md
CLAUDE.md
```

Use `media/source-register.csv` for actual imported recordings, `edits/notes/decisions.md` for editorial choices and `delivery/deliverables.csv` for delivered files. Paths in project records are project-relative. Initialization creates records and folders only; it copies no original media. Empty camera, transcript, sync and provider-related folders do not imply populated sources or automated capabilities. Camera alignment, transcription and external generation remain separate explicitly run steps. No added music and native Remotion remain defaults, subject to the owner's brief.

Inspect the workspace without changing it with `python3 video_project.py inspect /absolute/path/to/new-project`. Open its shared editor Home with `python3 video_project.py open /absolute/path/to/new-project --port 4314 --no-open`; `--no-open` leaves browser navigation to the caller while starting the local server.

For a Claude continuation, open the initialized project and direct Claude to read `CLAUDE.md`, `AGENTS.md`, `HANDOFF.md`, `brief/BRIEF.md`, the lock, source register and decisions before editing. Keep current user instructions and prior accepted decisions intact. Write a concise handoff under `out/handoffs/` that names the editor checkout, installed suite version, current source IDs, latest recipe/preview paths, accepted style decisions, incomplete checks and next action. A generated handoff is context for a future run; creating it does not launch Claude, send a message or prove Claude used the package.

Initialization is complete only when the command succeeds and its generated files exist. Media intake is complete only when the source register reflects actual recordings; an empty scaffold is still a project awaiting input. The overwrite refusal is enforced by the editor's initializer. This package's routing and handoff workflow are advisory instructions.

# Package integration and migration

1. Pin this package to a Git commit and record `package.json` version plus bundle checksum. Build with `python3 scripts/package.py bundle /new/path/idc-video-suite-2.1.0.zip`.
2. Extract under the editor's `skills/idc-video-suite` without flattening its files. Run `python3 skills/idc-video-suite/scripts/package.py verify skills/idc-video-suite`. This checks packaged bytes and completeness; it is not a signature or an independent trust decision.
3. Load the root conductor explicitly; it routes to child seats by file path. Nested-seat autodiscovery differs by harness and is not claimed. For a direct installation, use `python3 scripts/package.py install /new/skill-root/idc-video-suite`. Existing destinations are never overwritten. To update a current install, stage a new version, compare it, then choose the swap explicitly.
4. The editor keeps its own canonical recipe parser. Use its actual CLI to prepare the proposed edit:

```text
python3 story_edit.py check recipe.json
python3 story_edit.py prepare recipe.json --bindings sources.json --project /path/to/project --output out/new-story
```

This interface is the v2 integration target. Check the installed editor's help before running it. Preparation is not render completion. Follow its generated plan into the existing `production_preview.py preview` entry point with `--project` and `--render`; use the installed command's exact arguments. Do not claim recipe-to-render integration from a suite validation result.

5. Feed only accepted reusable feedback into a project-local style file. Keep unresolved comments in their feedback document. Use version control to inspect rule changes; project-specific exceptions override general rules.
6. Record a short rendered hook and timestamp feedback before spending time on the whole master. Existing owner acceptance of an unchanged hook carries forward. Final export follows the owner's requested review gate; this package adds no new approval keyword.

Version 1 compatibility: retain `project.lock.json`, `keepers.json`, `broll.catalog.json` and `edit.spec.md` as evidence. Convert source seconds to rounded integer milliseconds once, assign stable source IDs, and preserve keeper order. A-roll selection is explicit across all cameras. `warehouse` remains a named listen-along layout, not the default for documentary edits. A no-music project carries that preference through every cutdown. There are no bundled paid-service adapters, credentials or proprietary assets.
