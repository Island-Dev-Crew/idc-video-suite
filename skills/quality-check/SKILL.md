---
name: quality-check
description: "Inspect actual rendered exports and delivery copies when a preview, final render or external-drive package is ready."
---

# quality-check

Read the spec and actual export list. Run the bounded container check from the suite root:

```sh
python3 scripts/video_suite.py quality /absolute/path/video.mp4 --expected-ms 10000 > quality.json
```

Set expected duration from the compiled timeline plus deliberate intro/outro, not a guessed round number. The command requires installed ffprobe, rejects missing or empty exports and missing video streams, measures duration/dimensions/codecs and hashes the actual bytes. It fails if expected duration differs by over 100 ms. Its report explicitly lists unchecked properties.

Then inspect decoded frames, typography and caption timing at representative points and source transitions. Review voice sync at multiple anchors and known capture hiccups. Check audible music absence by listening or comparison with the intended clean track. A silent stream, a matching container duration or a structural pass alone proves none of these judgments. Report partial checks honestly.

For delivery pair each export with the chosen cover and captions, compare source/destination checksums, and record the mounted destination path. Export success is distinct from upload or platform acceptance.

Done when every promised file exists, copied bytes match where copying was requested, and the receipt separates measured checks from unverified visual/audio/platform properties. This tool probes containers, not full decode or editorial quality.
