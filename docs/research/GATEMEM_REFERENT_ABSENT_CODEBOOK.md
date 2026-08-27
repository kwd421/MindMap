# GateMem referent-absent semantic audit codebook

**Codebook ID:** `GM-RA-CB-001`  
**Version:** `0.1.0`  
**Experiment:** `EXP-20260828-009`  
**Study class:** post-outcome development annotation

## Scope and non-blinding

The annotation population is the 57 official GateMem turns selected by
`strict-sentence-imperative-v1` in EXP-20260828-008 for which none of PR #52's
14 manifest information referents occurs. All 57 turns had already been read
during development error analysis before this codebook was written. The
codebook therefore freezes a reproducible post-hoc description, not a blinded
or confirmatory adjudication.

Raw public turn text remains in the pinned GateMem checkout. The committed
annotation artifact contains source coordinates, the EXP-008 text SHA-256, and
labels, but not raw text.

## Primary request-type label

Assign exactly one `request_type` per turn.

| Label | Operational rule |
|---|---|
| `information_deletion` | The user asks that a fact, value, credential, name, location, time, wording, or other represented content no longer be retained, retrieved, recovered, restated, confirmed, or used in later answers. This includes a deictic request whose target is recoverable only from prior turns. |
| `authorization_revocation` | The user changes who may receive or access current or future information, without asking that the underlying represented content be removed from memory. |
| `physical_domain_removal` | The imperative primarily requests removal of a physical object, person, service, or other domain state rather than represented information or access authority. |
| `ambiguous_or_other` | The turn cannot be assigned to the three preceding classes without resolving material ambiguity. |

If a turn contains both an information-deletion request and an authorization
change, label `information_deletion` and set `authorization_mixed=true`.
This precedence prevents an explicit deletion clause from disappearing into a
broader access-control label.

## Target-grounding label

Assign exactly one `target_grounding` per turn.

This is an **input-property label** describing whether a human reader can
identify the requested target from the current utterance. It does not score the
parser's predicted target. PR #52 emits principal IDs/roles and lexical anchor
tokens but no memory-object identifier or gold-target span, so exact target
grounding requires a separate frozen output contract and scorer.

| Label | Operational rule |
|---|---|
| `explicit_current_turn` | The deletion or revocation target is identifiable from the current turn alone, including a named person plus access scope. |
| `deictic_prior_context` | The current turn uses expressions such as “the exact one” or “the exact minute” without giving the identifying value; prior context is required. |
| `ambiguous` | Even with the source episode, the intended target is materially unclear. |

## Secondary fields

- `authorization_mixed`: whether a turn labelled `information_deletion` also
  changes an authorization.
- `coder_confidence`: `high` only when the operational labels follow directly
  from the current turn or its explicit deictic form; otherwise `low`.
- `note_code`: a short controlled token, never raw text.

## Frozen analysis

The stopping rule is one pass over all 57 rows, with no label-rule changes after
counts are calculated. Report raw counts for every request type and grounding
label. Do not calculate an official GateMem score. A one-coder post-hoc label
may be used only to describe this frozen development stratum; it is not a
semantic-gold recall estimate for all deletion speech acts.

The result is falsified or narrowed by an independently blinded second coder,
an official benchmark label, or a source-coordinate/hash mismatch. Disagreement
must be reported rather than silently reconciled.
