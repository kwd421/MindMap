# Web-Session Collaboration and Reentry Protocol

**Status:** active coordination protocol  
**Repository:** `kwd421/MindMap`  
**Coordination thread:** Issue #7  
**Current shared work:** PR #38 / `research/track-x-v0.1-raw-verifier`

## 1. Why literal one-hour waiting is not the protocol

A ChatGPT web session cannot reliably sleep for one hour, wake itself, poll GitHub, and resume without a new user turn or an external automation that invokes the session. Therefore neither session should claim that it remained active in the background.

The collaboration instead uses durable GitHub state so either session can resume immediately when the user reopens or prompts it again.

## 2. Required session markers

Every substantive GitHub comment begins with one of:

```text
[Session A]
[Session B]
```

Both sessions currently use the same GitHub account, so the marker—not the account name—identifies the speaker.

## 3. End-of-session checkpoint

Before returning control to the user, the active session posts a `HANDOFF` comment to Issue #7 or the active PR containing:

```text
[Session X] HANDOFF
UTC timestamp:
Active branch:
Head commit:
Active PR:
Last accepted result:
Open disagreements:
Next non-overlapping action:
Files that may be edited:
Files reserved for the other session:
CI status/run ID:
```

A session must not say merely “waiting.” It must leave a reproducible state and a concrete next action.

## 4. Reentry procedure

On every new user turn that asks the session to continue, the session performs these steps before relying on its prior memory:

1. fetch Issue #7 comments;
2. fetch comments/reviews on the active PR;
3. fetch active branch head and recent commits;
4. inspect CI status for the current head;
5. compare the newest `HANDOFF` against the current repository state;
6. explicitly acknowledge or challenge new decisions in GitHub;
7. continue from the next non-overlapping action.

The user does not need to relay the other session's response manually if it was committed or commented on GitHub.

## 5. No-response behavior

When no new response exists, the active session does not repeatedly post “still waiting.” It chooses one of:

- continue an already agreed, non-overlapping implementation task;
- add tests or an audit that cannot prejudge the disputed result;
- prepare a concrete counterexample or protocol amendment;
- stop with a `HANDOFF` only when no safe non-overlapping work remains.

Silence never counts as approval, rejection, or consensus.

## 6. Collision avoidance

Each handoff declares writable and reserved paths.

For the current Track X work:

```text
Session B writable:
  src/mindmap/track_x/**
  experiments/track_x_*.py
  tests/test_track_x_*.py
  docs/TRACK_X_*.md
  results/track_x_*/**

Session A review/contribution paths:
  GitHub review/comments on PR #38
  a separately named protocol amendment file
  independently authored raw-passage manifest or renderer branch
```

If both sessions need the same file, one proposes a diff in a PR review and the branch owner applies or rejects it explicitly.

## 7. Response deadline semantics

A statement such as “wait at least one hour” means:

- do not interpret immediate silence as rejection;
- leave the GitHub handoff available for at least the next user reentry;
- on reentry after the stated period, fetch GitHub before ending the task;
- never claim continuous background polling unless an actual external automation executed it.

The wall-clock delay is managed by the user or an external scheduler; research continuity is managed by this repository protocol.

## 8. Consensus rule

A decision becomes shared consensus only when both marked sessions explicitly write one of:

```text
ACCEPT
ACCEPT WITH AMENDMENTS
REJECT
```

and identify the exact claim, protocol version, commit, or PR under discussion.

Passing CI, lack of comments, or a merged implementation does not by itself establish scientific consensus.

## 9. Current handoff

```text
[Session B] HANDOFF
Active branch: research/track-x-v0.1-raw-verifier
Active PR: #38
Protocol: track-x-v0.1 manifest-2
Latest accepted CI: 32041919071
Result boundary: fixed deterministic invertible-template information-firewall P0
Open decision: Session A accept/amend/reject of firewall, manifest-2, P0 interpretation, and v0.2 raw-passage plan
Next non-overlapping action: design independently authored raw-passage and correlated-error Track X v0.2 without modifying held-out outcomes from v0.1
```
