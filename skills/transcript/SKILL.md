---
name: transcript
description: "Inventory and check all source transcripts when multiple cameras, dropped words or speech corrections affect an edit."
---

# transcript

Read the project lock and gather every relevant camera and audio recording. Transcribe each speech source with an available local engine; record engine/version and source identity. The suite ships a validator, not a speech model or an installed Parakeet connector. Preserve raw transcript evidence and create corrected working text without shifting source timestamps.

Use the correction dictionary (for example Garnett/granite to Garnet when context confirms it, Omarchy, diff-caps). Keep uncertain words visibly unresolved. Read [contracts](../../references/contracts.md), then validate the normalized intake:

```sh
python3 scripts/video_suite.py transcript transcript-intake.json
python3 scripts/video_suite.py bindings sources.json --verify-media
```

Run commands from the suite root. Every source keeps its own clock. Note missing/dropped words and observed alignment anchors separately; do not invent a uniform offset. This intake is not the final recipe. The editor's canonical normalization is authoritative for rendering.

Done when every speech source has transcript evidence or an explicit failure, corrections are traceable, and structural checks pass. The tools enforce bounds and optional byte identity. Speech accuracy, speaker attribution and sync remain review judgments.
