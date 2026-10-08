# Local contracts

All times are integer milliseconds on the named source, before speed changes. Preserve original transcript text in the evidence directory. Corrections go in the reviewed transcript; changing spelling never changes timestamps. The suite commands reject duplicate JSON keys, nonfinite numbers, malformed records and files over 8 MiB. Up to 100 sources and 100,000 total words are supported per transcript document. These are implemented limits, not claims about editorial quality.

`idc.video-transcript/1`:

```json
{"schemaVersion":"idc.video-transcript/1","sources":[{"id":"camera-a","name":"Computer camera","durationMs":5000,"words":[{"text":"Garnet","startMs":100,"endMs":500}]}]}
```

Words are source-relative, ordered by start time and within duration; overlapping speech is allowed. Every camera has its own time origin. Empty words can represent an explicitly untranscribed or silent source; record that reason outside this minimal contract. The validator does not transcribe, infer offsets or claim that an empty transcript is complete.

`idc.video-bindings/1`:

```json
{"schemaVersion":"idc.video-bindings/1","sources":[{"sourceId":"camera-a","localPath":"/absolute/path/camera-a.mp4","sha256":"64 lowercase hex characters","audioMode":"source"}]}
```

`audioMode` is `source` or `silent`. `bindings --verify-media` hashes files; individual files are bounded at 100 GiB. Binding structure alone does not prove media exists. The canonical editor additionally checks that bindings cover the actual recipe and probes source media. The suite never executes text from transcripts, feedback or filenames as commands.

`idc.video-feedback/1`:

```json
{"schemaVersion":"idc.video-feedback/1","feedback":[{"id":"f1","projectId":"garnet","targetId":"hook-v1","timestampMs":2400,"note":"The wordmark moves too much here.","status":"accepted","reusable":true,"rule":"Keep the wordmark still while the orb moves."}]}
```

`status` is `pending`, `accepted` or `rejected`. `reusable` is an explicit boolean. Acceptance is recorded from the owner's decision, never inferred from a view or a lack of reply. One-off accepted corrections use `reusable:false`. `style` emits `idc.video-style/1` and only accepted reusable records become rules, retaining project, target and time provenance. It does not mutate input or invent acceptance. Style output is advisory, subordinate to current explicit instructions; renderer enforcement is not implemented here.

The canonical edit recipe is **`idc.video-edit/2`**, owned and validated by the editor. Keepers reference source IDs with `startMs`, `endMs`, `label`; array order is edit order. The suite does not maintain a competing recipe validator. Read the installed editor's `story_edit.py --help` and schema before generating a recipe. Source bindings and rendered output paths are passed as structured arguments, never shell fragments.
