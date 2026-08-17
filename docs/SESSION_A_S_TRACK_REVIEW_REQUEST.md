# Session A S-Track Integration Review

**Source branch:** `research/session-a-s-track-core`  
**Target branch:** `research/v0.2-reconciled`  
**Status:** pending integration review

Session A implemented a substantially more complete R2/R3 candidate than the initial Session B `v02_*` prototype. Its branch adds:

- a separate `mindmap.canonical` package;
- declarative common-event fixtures;
- independently implemented gold, generic, and typed evaluators;
- explicit snapshot-manifest membership;
- normative parent/child world-branch visibility, including the late-import/pre-fork contrast;
- exposure, availability, attitude, attribution, authorization, and alternative-support semantics;
- fourteen fixture families with at least seventy target cases;
- mutation tests for about-world scope and authorization revocation;
- a reproducible S-track evaluation entry point.

Integration criteria:

1. merged-tree CI passes both legacy and canonical suites;
2. gold imports no generic/typed resolver;
3. G and T receive byte-equivalent common events;
4. complete G = T = gold on the fixed S suite;
5. snapshot membership, not cutoff alone, controls restore inheritance;
6. child-world inheritance follows valid-time fork cutoff while allowing later system-time import of pre-fork facts;
7. the earlier Session B `v02_*` prototype is retained only until the canonical package is reviewed, then removed or archived to avoid two active semantic contracts.

This file is a coordination marker, not a second specification.