---
name: style-feedback
description: "Preserve timestamped owner feedback as reusable style rules when revising an edit or carrying style between sessions."
---

# style-feedback

Record each comment against the exact reviewed cut, project and timestamp. Distinguish a one-off correction from a reusable rule. Leave new suggestions pending. Mark accepted only from an actual owner decision; the user's current instruction can supply that decision. Read [contracts](../../references/contracts.md) for the portable ledger.

```sh
python3 scripts/video_suite.py style feedback.json > style.next.json
```

Run from the suite root. Compare the emitted rules with the current style and preserve the earlier version for review. The compiler includes only records that are both accepted and explicitly reusable; rejected and pending items remain in the input ledger. It never edits the input.

The resulting `idc.video-style/1` is an advisory, portable record, not the editor's runtime profile. To apply it to an editor profile, use the canonical editor's feedback acceptance interface and validate its profile. Never silently convert free text into executable renderer code. Current explicit instructions override an old rule.

Done when each applied rule links to accepted feedback and unresolved notes remain visible. Membership filtering is enforced by the compiler; visual implementation and acceptance authenticity remain advisory/manual review.
