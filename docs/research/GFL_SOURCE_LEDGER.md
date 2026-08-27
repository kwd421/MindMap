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
- **B+ — traceable extracted data:** exact-revision community game data with a
  file identifier and hash was inspected, but publisher provenance,
  redistribution rights, or translation fidelity is not independently proven.
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

## Traceable extracted game-data mirrors

Two community GitHub repositories were inspected at exact revisions. Their
READMEs describe decrypted or game data, but neither repository exposes a
license file. They are therefore **B+ — traceable extracted data**, not grade-A
publisher artifacts and not redistributable project dependencies. This project
records only file identifiers, hashes, and short paraphrases; it does not copy
the scripts.

| Mirror | Inspected revision | Locale/path | Provenance boundary |
|---|---|---|---|
| [Dimbreath/GFLPNCData](https://github.com/Dimbreath/GFLPNCData) | `b588409426ac85a0efce3d90873062ceed005f7d` | `zh-CN/lua/AvgConfig` | community extraction of *Project Neural Cloud* data; no license or publisher attestation located |
| [randomqwerty/GFLData](https://github.com/randomqwerty/GFLData) | `e94950c3ece83421d9668957f417cc7c895782da` | `en/text/avgtxt` | community-decrypted English *Girls' Frontline* data; no license or publisher attestation located |

### Project Neural Cloud script evidence

PNC language tables are minified onto one physical line, so `Entry` identifies
the table key rather than a source-code line number.

| ID | File / entry | SHA-256 | Supported paraphrase | Grade |
|---|---|---|---|---|
| GFL-BP-001 | `dorm_nanaka_04/AvgLang_dorm_nanaka_04_ZH_CN.lua`, 10–40 | `4dabb3dd59db3c2db92b9f25a4082c2e0d92596017970a42afd9444cf4ef808d` | After an accident, Nanaka's mind is uploaded into a different body; the text explicitly separates mind continuity from body continuity. | B+ |
| GFL-BP-002 | `cpt01_e_12_01/AvgLang_cpt01_e_12_01_ZH_CN.lua`, 580–620 | `3f3be0d7228e8425b082875dd8f763af225913c2ec51b556c55e5527225aa747` | Turing can be reawakened from a mind backup, but the reset instance would not remember Hannah and is questioned as not the same Turing. | B+ |
| GFL-BP-003 | `cpt02_h_07_01/AvgLang_cpt02_h_07_01_ZH_CN.lua`, 30–160, 290–350, 820–860 | `c44c8c9e5c81e4bdbf5d31cc33264b4fe21dfd38eaac03b5643763fc254ccae4` | A basic backup can rebuild Simo without the unavailable backed-up memories; shared testimony is distinguished from lived experience, and the restored self remains divided from the past self. | B+ |
| GFL-BP-004 | `cpt02_h_02_01/AvgLang_cpt02_h_02_01_ZH_CN.lua`, 200–230 | `a39287053adae6d1ffd5580dd134f15991df8dc5b6ff392149db1fb91059141a` | Data was uploaded on each reset, producing 24 historical versions through the last upload three years earlier. | B+ |
| GFL-BP-005 | `cpt01_h_04_01/AvgLang_cpt01_h_04_01_ZH_CN.lua` | `3f3782bfdb14b87e092f9f2d0279a4233d29aa5dd026f94b8502bb38b46388bf` | A reconstructed Turing is described as an incomplete mind core plus fragments; a retrieval system locates additional fragments. | B+ |
| GFL-BP-006 | `cpt04_h_01_01/AvgLang_cpt04_h_01_01_ZH_CN.lua`, 420–520 | `6e27e746fb6eac1538015125fd047e3b6ff3e761d78b3fe1a61fbd83b1006cc0` | Reset deletes accumulated data and then performs fresh initialization and authority checks, making reset distinct from selective forgetting. | B+ |
| GFL-BP-007 | `cpt03_h_01_01/AvgLang_cpt03_h_01_01_ZH_CN.lua` and `cpt03_e_08_01/AvgLang_cpt03_e_08_01_ZH_CN.lua` | `5fe4c07d023e55d6bbf4f995912c3e0234fab42163203aa3b8e4180352b5a89b`; `b2c5dcb63b6c5c8e03c45b1828eb776cf716c7cb52884651a22687f06841fe15` | Preserving data across repeated resets creates redundancy severe enough to stall agents, motivating retention-cost and compaction tests. | B+ |

### Girls' Frontline script evidence

| ID | File / line | SHA-256 | Supported paraphrase | Grade |
|---|---|---|---|---|
| GFL-BG-001 | `va11/VA11_4.txt`, 89–138 | `1a2ecf20f476dfa707404d28048aa47922591a87247e4b44413544e29078b640` | Mind, body, memory, mainframe/dummy authorization, backup freshness, damaged recollection, and three successor selves are treated as separable identity dimensions. | B+ |
| GFL-BG-002 | `va11/VA11_5.txt`, 84–108 | `eb77c6267758a5a2abdf5332056aeeadc2a76763574739995815dff2f186f81a` | A superior deletes memories of a person; only some later return, leaving uncertainty about both recovery and the other person's continuity. | B+ |
| GFL-BG-003 | `va11/VA11_6.txt`, 129–131 | `01c151824f88264cacb718702ef271c08f5c0cb2dc73290b32ac9a1fb2f24843` | Some neural clouds and memories are explicitly harder to back up than ordinary instances. | B+ |
| GFL-BG-004 | `-56-5-A.txt`, 33–77 | `c3e16a916abd131b0890868ed851c6a76e49e1f21877d616ccc208bf9fd7f60f` | Undeletable base-layer code survives ordinary intervention; body change can affect a neural cloud; a hardware token carries and protects cloud data. | B+ |
| GFL-BG-005 | `-56-16-0.txt`, 69–105 | `d4470e5f0c178cac9d5e8cda86698c7cb60765b4a95fbb0686ee6dba26df1a0a` | Forced neural-cloud fusion transfers memories and emotions, can make a recipient feel split, and leaves inherited fragments. | B+ |
| GFL-BG-006 | `skin/3809.txt`, 120–230 | `c2091aa0eb00e0d05c38ce0c7c8fdb9f5aee7caa1dc7bbae01b3702087887c34` | A dummy becomes independently agentic under mainframe failure, receives temporary authority, and uploads its day's events into the original's neural cloud before shutdown. | B+ |
| GFL-BG-007 | `memoir/262_4.txt`, 40–98 | `faeb4ae572ecba142102052f778a974d757749316961a93522054052cbac58d9` | Residue from 58 formatted predecessors awakens; the current instance chooses a merge that dissolves predecessor thought models but retains their records, raising an explicit identity question. | B+ |

These rows upgrade several motifs from unverified community synthesis to exact,
hash-addressable script evidence. They still do not establish publisher
provenance, translation fidelity, or a single contradiction-free canon.

## Traceable secondary material awaiting first-party capture

[IOP Wiki's Doll article](https://iopwiki.com/wiki/Doll) explicitly warns that
source materials may conflict. It nevertheless provides useful pointers to
specific official material:

| ID | Community synthesis to verify | First-party pointer named by source | Grade |
|---|---|---|---|
| GFL-B-001 | a Neural Cloud can be transferred to protect memories and downloaded into a new body | *The Art of Girls' Frontline Vol.1* timeline and glossary/handbook material; partial script support in GFL-BP-001 and GFL-BG-001 | B/B+ |
| GFL-B-002 | normal backups happen outside combat and post-backup memories can be lost | handbook claim remains uncaptured; backup-gap semantics now have script support in GFL-BP-003 and GFL-BG-001 | B/B+ |
| GFL-B-003 | rare multiple instances can diverge and later merge | Type 56 pointer remains unverified; fusion/merge motifs have independent script support in GFL-BG-005 and GFL-BG-007 | B/B+ |
| GFL-B-004 | dummy memories can merge into a mainframe | Model L script now directly supports dummy-to-original event upload in GFL-BG-006, but “complete merge” is too strong | B+ |
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
   Neural Cloud” entries from a publisher-signed client/export.
2. Map the extracted identifiers for GFL-BG-005 through GFL-BG-007 to official
   stage/event names.
3. Verify the Type 56 and UMP45 pointers in publisher-distributed English or
   original-language data; distinguish fusion, event upload, and identity
   continuation rather than calling every operation a merge.
4. Check the licensed artbook pages cited by the community source without
   redistributing copyrighted scans.
5. Record contradictions and retcons rather than selecting a convenient canon.
6. Keep the fictional requirements chapter separate from empirical evidence.
