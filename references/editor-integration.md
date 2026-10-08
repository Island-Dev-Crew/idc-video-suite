# Editor integration and migration

1. Pin this package to a Git commit and record `package.json` version plus bundle checksum. Build with `python3 scripts/package.py bundle /new/path/idc-video-suite-2.0.0.zip`.
2. Extract under the editor's `skills/idc-video-suite` without flattening its files. Run `python3 skills/idc-video-suite/scripts/package.py verify skills/idc-video-suite`. This checks packaged bytes and completeness; it is not a signature or an independent trust decision.
3. Load the root conductor explicitly; it routes to child seats by file path. Nested-seat autodiscovery differs by harness and is not claimed. For a direct installation, use `python3 scripts/package.py install /new/skill-root/idc-video-suite`. Existing destinations are never overwritten. To update a current install, stage a new version, compare it, then choose the swap explicitly.
4. The editor keeps its own canonical recipe parser. Use its actual CLI to prepare the proposed edit:

```text
python3 story_edit.py prepare recipe.json --bindings sources.json --output out/new-story
```

This interface is the v2 integration target. Check the installed editor's help before running it. Preparation is not render completion. Follow its generated plan into the existing `production_preview.py preview` entry point with `--project` and `--render`; use the installed command's exact arguments. Do not claim recipe-to-render integration from a suite validation result.

5. Feed only accepted reusable feedback into a project-local style file. Keep unresolved comments in their feedback document. Use version control to inspect rule changes; project-specific exceptions override general rules.
6. Record a short rendered hook and timestamp feedback before spending time on the whole master. Existing owner acceptance of an unchanged hook carries forward. Final export follows the owner's requested review gate; this package adds no new approval keyword.

Version 1 compatibility: retain `project.lock.json`, `keepers.json`, `broll.catalog.json` and `edit.spec.md` as evidence. Convert source seconds to rounded integer milliseconds once, assign stable source IDs, and preserve keeper order. A-roll selection is explicit across all cameras. `warehouse` remains a named listen-along layout, not the default for documentary edits. A no-music project carries that preference through every cutdown. There are no bundled paid-service adapters, credentials or proprietary assets.
