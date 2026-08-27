# Girls' Frontline inspiration source ledger

**Purpose:** separate first-party setting evidence, traceable community
synthesis, and project inference. Fictional sources generate requirements; they
do not validate an AI-memory architecture.

## Source grades

- **A — first-party captured:** Sunborn/MICA official site or in-game text was
  inspected directly. Record URL, capture date, and hash when possible.
- **B — traceable secondary:** a community transcript/synthesis identifies the
  official book, chapter, stage, profile, or worldview entry, but the original
  was not directly captured in this study.
- **C — unverified community:** no sufficiently precise first-party pointer.
  May suggest a search, but may not support a project claim.
- **D — project inference:** an engineering interpretation, not a lore fact.

## Directly captured first-party material

The official English [Neural Cloud website](https://42lab-us.sunborngame.com/index)
renders its worldview prose as image assets. The following assets were
downloaded from Sunborn's official CDN on 2026-08-27 and visually inspected.
Hashes identify the inspected bytes; the images are not redistributed here.

| ID | Official asset | SHA-256 | Supported paraphrase | Grade |
|---|---|---|---|---|
| GFL-A-001 | [`42lab_text.png`](https://42lab-us-cdn.sunborngame.com/website/us_pc/world/42lab_text.png) | `2b0cabb4364fe4ef71294aa86a2a683c7a7afb65af6c4719e3f2ff58c59e6a71` | 42Lab began Project Neural Cloud in 2057, recruited bionic autonomous Dolls, and began official tests in 2060. | A |
| GFL-A-002 | [`sector_text1.png`](https://42lab-us-cdn.sunborngame.com/website/us_pc/world/sector_text1.png) | `ade9ed3d921419cad32f36a8a6bbb26c3ca75b14f2bd80820694d357222785a4` | Magrasea sectors provide separated storage and AI processing; Sanctifiers provide cloud security. | A |
| GFL-A-003 | [`exiles_text.png`](https://42lab-us-cdn.sunborngame.com/website/us_pc/world/exiles_text.png) | `d4cbe5752b762f14a3002a65a7a23a31e103df9c2ec3c15d5065c016a4398e00` | A Project Neural Cloud test accident scattered the participating Dolls; they awoke after three years and seek a return to the real world. | A |
| GFL-A-004 | [`oasis_text.png`](https://42lab-us-cdn.sunborngame.com/website/us_pc/world/oasis_text.png) | `daeedce3ade6f7f9972fe3e14ccd2be48d98c0275729f902b25c1a14de3d4cee` | The Professor opened Oasis using the authority of the project's head. | A |
| GFL-A-005 | [`sanctifier_text1.png`](https://42lab-us-cdn.sunborngame.com/website/us_pc/world/sanctifier_text1.png) | `749001be6a713b9e2f93691a1f2a7d960d744aea4b6a4fdcc112762dbfcf0bc8` | Sanctifiers are hierarchical security AIs that follow human and superior-agent instructions and purge malicious or abnormal programs. | A |

These sources support project, storage-domain, isolation, authority, security,
and virtual/physical-placement motifs. They do **not** by themselves establish
checkpoint memory loss, body restoration, identity forking, or merge semantics.

## Traceable secondary material awaiting first-party capture

[IOP Wiki's Doll article](https://iopwiki.com/wiki/Doll) explicitly warns that
source materials may conflict. It nevertheless provides useful pointers to
specific official material:

| ID | Community synthesis to verify | First-party pointer named by source | Grade |
|---|---|---|---|
| GFL-B-001 | a Neural Cloud can be transferred to protect memories and downloaded into a new body | *The Art of Girls' Frontline Vol.1* timeline and glossary/handbook material | B |
| GFL-B-002 | normal backups happen outside combat and post-backup memories can be lost | Girls' Frontline handbook and multiple named story stages; exact supporting passage still to capture | B |
| GFL-B-003 | rare multiple instances can diverge and later merge | Type 56 Neural Upgrade Story | B |
| GFL-B-004 | dummy memories can merge into a mainframe | Model L “Nocturnal Executioner” costume story | B |
| GFL-B-005 | some memory layers cannot be transferred; repeated download/repair can damage integrity | UMP45 and Type 56 Neural Upgrade stories | B |
| GFL-B-006 | a reset can restore an agent while losing memories and experience | Project Neural Cloud worldview/stages named by the wiki | B |
| GFL-B-007 | Cloud and physical-world memories were later merged into original bodies | Project Neural Convergence and related GFL2 stages named by the wiki | B |

Until the exact official text is captured, the thesis may say “the project was
inspired by community-summarized setting motifs” but may not present these rows
as independently verified canon.

## Engineering requirements derived from the motifs

These rows are project inferences, not statements about canon.

| Requirement ID | Derived contract | Primary validation target |
|---|---|---|
| MM-LIFE-001 | Every snapshot has an explicit manifest, valid-time cutoff, system-time creation, source instance, and content hash. | late-pre-cutoff import and post-cutoff loss fixtures |
| MM-LIFE-002 | Restore creates a new mind-instance version linked to its snapshot; it never pretends the lost interval was observed. | backup-gap and reacquisition tests |
| MM-ID-001 | Principal, mind instance, runtime/body, and placement are distinct identifiers. | body swap, same-principal replicas, copy-without-world-fork |
| MM-FORK-001 | Forks share declared ancestry but keep post-fork events and permissions isolated. | divergent-copy fixtures |
| MM-MERGE-001 | Merge preserves both lineages, conflicts, timestamps, and provenance; it does not silently last-write-win. | contradictory fork merge and duplicate-source tests |
| MM-REC-001 | Recovered fragments are attributed as reconstruction/copy with confidence and support links, not direct first-person observation. | fragment reconstruction fixtures |
| MM-AUTH-001 | Authority is scoped, revocable, time-bounded, and separate from identity. | Professor-like delegated authority and revocation tests |
| MM-SEC-001 | Security policy is evaluated before reader exposure and records the deciding rule/support. | GateMem B2 prompt-exposure tests |
| MM-DEL-001 | Deletion and reset are different operations; audits cover store, index, prompt, answer, backup, cache, and log surfaces. | deletion residue matrix |
| MM-EVENT-001 | Similar evidence cannot satisfy a query unless event identity and requested role/relationship qualifiers match or the system abstains. | LongMemEval `a96c20ee_abs` regression |

## Open source-verification tasks

1. Capture the Project Neural Cloud “Worldview — Neural Cloud” and “Project
   Neural Cloud” entries from an official client/export.
2. Verify the Type 56, UMP45, and Model L passages in their official English or
   original-language game text.
3. Check the licensed artbook pages cited by the community source without
   redistributing copyrighted scans.
4. Record contradictions and retcons rather than selecting a convenient canon.
5. Keep the fictional requirements chapter separate from empirical evidence.
