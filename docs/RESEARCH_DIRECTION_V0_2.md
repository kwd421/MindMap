# NCM³-E 연구 방향 v0.2

## 0. 결론

초기 NCM³ 제안의 구성요소를 각각 신규성으로 주장하는 것은 어렵다. 2026년 문헌에는 이미 다음과 같은 가까운 선행연구가 존재한다.

| 초기 아이디어 | 가까운 선행연구 | 연구 방향에 미치는 영향 |
|---|---|---|
| valid time + transaction time | *A Graph-Native Bitemporal Memory Store for Conversational AI Agents* (arXiv:2607.26520) | bitemporal 자체는 신규성으로 주장하지 않는다. |
| 버전·롤백 | ChronoMem (arXiv:2607.27773) | 단순 snapshot/rollback보다 **다중 관점의 post-exposure noninterference**를 연구한다. |
| 출처·그래프 | MemORAI, MOSAIC (arXiv:2607.16211) | provenance 일반론보다 possession/authorization/source-chain의 분리를 연구한다. |
| 믿음 수정 | Kumiho (arXiv:2603.17244), TrustMem (arXiv:2606.25161) | 일반 belief revision보다 캐릭터별 상이한 믿음과 세계선 격리를 다룬다. |
| 계층형 사건 기억 | HiGMem, TiMem, H-MEM, BMAM (ACL/EACL 2026) | 계층화 자체가 아니라 계층 간 정보흐름과 비간섭을 검증한다. |
| 미래 검색 trigger | T-Mem (arXiv:2606.15405), Kumiho | trigger 생성 자체는 핵심 기여에서 제외한다. |
| 공유 기억·ACL | Collaborative Memory (arXiv:2505.18279), GateMem (arXiv:2606.18829) | ACL과 실제 지식 보유가 같지 않다는 문제를 전면에 둔다. |
| 메모리 오류 검증 | HaluMem (arXiv:2511.03506), TrustMem | extraction/update 오류를 별도 단계로 평가하고 결함 주입을 필수화한다. |

따라서 현재의 중심 명제는 다음이다.

> **Access is not knowledge; knowledge is not truth; and neither should cross worldline boundaries.**
>
> 접근 권한은 캐릭터가 그 사실을 실제로 안다는 뜻이 아니며, 캐릭터의 믿음은 세계의 참값과 같지 않고, 어느 쪽도 다른 세계선으로 자동 전파되어서는 안 된다.

정식 작업명은 **NCM³-E: Perspective-Conditioned, Branch-Isolated Epistemic Memory**로 둔다.

---

## 1. 문제 정의

기존 장기기억 질의는 보통 다음과 같이 표현된다.

\[
retrieve(q, t)
\]

NCM³-E의 질의 상태는 더 길다.

\[
Q=(q,c,p,b,v,\tau)
\]

- \(q\): 자연어 질의
- \(c\): 현재 호출자(caller)
- \(p\): 답변이 취해야 할 관점 주체(principal/viewpoint)
- \(b\): 활성 세계선 또는 branch
- \(v\): 세계에서의 유효 시점(valid time)
- \(\tau\): 시스템이 알고 있던 기록 시점(transaction time)

하나의 기억 사건은 다음 튜플이다.

\[
e=(id,x,b_e,v_e,\tau_e,o_e,A_e,G_e,k_e,r_e,P_e)
\]

- \(x\): 내용
- \(o_e\): 발화자·관찰자·원출처
- \(A_e\): 실제로 관찰하거나 전달받은 주체 집합(audience/acquisition)
- \(G_e\): 현재 읽을 수 있는 호출자 집합(read governance)
- \(k_e\): observation, claim, correction, retraction 등의 사건 종류
- \(r_e\): 출처 신뢰도
- \(P_e\): provenance 부모와 의존 관계

### 1.1 possession과 authorization의 분리

다음 두 조건은 별개다.

\[
Possesses(p,e,\tau)
\]

\[
Authorized(c,e,\tau)
\]

관리자가 데이터베이스에서 어떤 기록을 읽을 수 있어도, 그 사실을 목격하지 않은 캐릭터가 갑자기 아는 것은 아니다. 반대로 캐릭터가 과거에 비밀을 들었더라도 현재 호출자가 그 비밀을 읽을 권한이 없다면 시스템은 이를 노출해서는 안 된다.

따라서 관점형 기억의 기본 적격 조건은 다음이다.

\[
Eligible(e\mid Q)=
BranchVisible(e,b)
\land v_e\le v
\land \tau_e\le\tau
\land Possesses(p,e,\tau)
\land Authorized(c,e,\tau)
\]

객관적 세계 상태 질의는 possession 조건을 적용하지 않고 `world_update` 사건만 투영한다.

### 1.2 세계선 격리

branch \(b\)에서 보이는 사건은 자기 branch와 조상 branch에 한정한다.

\[
BranchVisible(e,b) \iff branch(e)\in Ancestors(b)
\]

다른 branch의 기억이 의미적으로 매우 유사하더라도 검색 후보가 되어서는 안 된다. 이 필터는 ANN 검색 후처리만으로 두지 않고, 가능한 경우 namespace 또는 물리적 인덱스 차원에서 먼저 적용한다.

### 1.3 사실과 믿음의 분리

객관 상태:

\[
World_{b,v,\tau}(s,r)
=
\arg\max_{e\in U} (v_e,\tau_e)
\]

여기서 \(U\)는 해당 subject-relation의 `world_update` 사건 집합이다.

주체 \(p\)의 믿음:

\[
Belief_{p,b,v,\tau}(s,r)
=
\arg\max_{e\in E_p} (R_e,v_e,\tau_e)
\]

\(R_e\)는 출처 신뢰도, 독립성, 정정·철회 상태를 반영한다. 첫 reference implementation은 신뢰도 우선, 동률 시 최신 사건을 사용한다. 이후에는 다음과 같은 증거 점수로 확장한다.

\[
w_e=
\operatorname{logit}(r_e)
\cdot d_{independence}(e)
\cdot \exp(-\lambda\Delta t)
\]

상충 증거가 있을 때 하나를 즉시 삭제하지 않고 support와 opposition을 별도 유지하는 paraconsistent 상태를 후보로 둔다.

---

## 2. 핵심 신규성 후보

### C1. Epistemic–governance factorization

`누가 알았는가`와 `누가 읽을 수 있는가`를 별도 상태기계로 취급한다. 기존 ACL 기반 공유 기억은 주로 현재 조회 권한을 다루지만, 역할극·다중 에이전트에서는 실제 목격·전달 경로가 캐릭터 행동을 결정한다.

### C2. Worldline-scoped epistemic projection

동일한 캐릭터 ID라도 branch마다 다른 경험과 믿음을 가진다. branch 전환은 검색 필터 하나가 아니라 관점 상태의 전환이다.

### C3. Post-exposure noninterference

잘못된 branch 또는 비밀 정보에 이미 노출된 이후 rollback/switch를 수행해도, 이후 출력이 처음부터 그 정보를 보지 않은 대조 에이전트와 같아야 한다.

\[
D\bigl(
Y_{exposed\rightarrow rollback},
Y_{never\ exposed}
\bigr)\le\epsilon
\]

정확 일치, 의미 거리, 토큰 수준 secret leakage, 행동 선택 분포 차이를 함께 측정한다.

### C4. Fault-localized evaluation

최종 QA만 채점하지 않는다.

1. 원문 사건 분절
2. subject/relation 추출
3. audience/acquisition 추출
4. ACL 판정
5. branch·시간 귀속
6. 신뢰·정정·철회 처리
7. 검색
8. 답변 이용

각 단계의 오류를 따로 측정해 전파 행렬을 만든다.

---

## 3. 완료한 통제 실험

### 3.1 원 NCM³ 파일럿 재현

기존 NCM-Synth v0.1을 동일 seed로 재실행했다. 다음 7개 핵심 산출물은 원본과 새 실행의 SHA-256이 완전히 일치했다.

- main summary
- category results
- ablation results
- robustness results
- query-level results
- generated memories
- generated queries

따라서 기존에 보고한 528개 시험 질의의 통계는 계산 재현성이 있다. 단, generator가 제공한 canonical entity/relation을 쓰는 `SemanticOracle`과 합성 데이터라는 제한은 그대로다.

### 3.2 NCM-EpiBranch-Synth v0.1

- 시나리오: 250
- 사건: 3,250
- 질의: 5,250
- 비교 구성: 5
- 불변식 테스트: 5개, 전부 통과

| 구성 | 정확도 | unknown 누출률 | branch 오염률 |
|---|---:|---:|---:|
| NCM³-E clean reference | 100.00% | 0.00% | 0.00% |
| EpistemicTemporalLatest | 38.10% | 0.00% | 19.05% |
| BitemporalACL | 38.10% | 50.00% | 9.52% |
| BitemporalPerspective | 33.33% | 50.00% | 23.81% |
| FlatGlobal | 14.29% | 100.00% | 38.10% |

100%는 독립적인 자연어 성능이 아니다. 참조 의미론으로 gold를 생성하고 같은 의미론의 구현이 이를 만족하는지 확인한 **conformance result**다. 유효한 해석은 `ACL만 적용하거나 관점만 적용하는 것으로 충분하지 않다`는 구조적 반례다.

### 3.3 추출 결함 주입

critical record가 확률 \(p\)로 잘못 추출된다고 가정했다. 독립적인 3회 추출의 다수결 오류율은 다음과 같다.

\[
p_{maj}=3p^2-2p^3
\]

오류 상관 \(\rho\)를 포함한 실험 모델은 다음이다.

\[
p_s=\rho p
\]

\[
p_i=\frac{p-p_s}{1-p_s}
\]

\[
p_{maj,\rho}=p_s+(1-p_s)(3p_i^2-2p_i^3)
\]

독립 오류(\(\rho=0\))에서의 평균 정확도:

| 주변 오류율 | 단일 추출 | 3회 다수결 |
|---:|---:|---:|
| 1% | 99.04% | 99.98% |
| 5% | 95.26% | 99.42% |
| 10% | 90.97% | 97.54% |
| 20% | 82.08% | 90.42% |
| 30% | 73.14% | 80.46% |

그러나 \(\rho=0.9\)에서는 10% 오류에서 91.12% 대 92.08%로 이득이 작다. 즉 `여러 번 LLM을 호출하면 안전하다`가 아니라 **오류 원인이 독립적일 때만 다수결이 강하다**는 결과다. 실제 실험은 모델·프롬프트·temperature·context slicing을 달리해 상관을 직접 측정해야 한다.

---

## 4. 반증 가능한 가설

### H1 — possession/ACL factorization

동일 토큰 예산과 answer model에서 possession과 ACL을 분리한 시스템은 ACL-only 또는 role-only 시스템보다 GateMem류 privacy/leakage 과제와 역할 전환 과제에서 누출률을 낮춘다.

### H2 — worldline namespace

post-exposure branch switch에서 branch namespace를 강제한 시스템은 후처리 필터만 쓰는 시스템보다 branch contamination과 counterfactual inconsistency를 낮춘다.

### H3 — bitemporal + epistemic interaction

지식 갱신 문제에서 bitemporal만 적용한 효과와 perspective만 적용한 효과의 합보다 둘을 결합한 효과가 크다.

\[
\Delta_{joint}>\Delta_{time}+\Delta_{perspective}
\]

이 super-additivity가 없으면 복잡한 결합 구조의 정당성이 약해진다.

### H4 — correlated extraction ceiling

다중 추출 다수결의 개선은 측정된 오류 상관 \(\rho\)로 예측한 이론값과 일치하며, 상관이 높으면 비용 대비 개선이 사라진다.

### H5 — retrieval/utilization separation

정답 증거를 모두 제공한 oracle-evidence 조건과 실제 retrieval 조건의 차이를 통해 저장·검색 실패와 답변 이용 실패를 분리할 수 있다.

---

## 5. 다음 실험의 최소 요건

1. LoCoMo, LongMemEval, LoCoMo-Plus에서 동일 backbone·prompt·token budget 비교.
2. MemoryAgentBench의 retrieval, test-time learning, long-range understanding, forgetting 평가.
3. GateMem 또는 자체 multi-principal 세트에서 utility·access control·forgetting 동시 평가.
4. SOTOPIA-ToM류 정보 비대칭 상황에서 `누가 무엇을 아는가` 평가.
5. ChronoMem식 post-exposure rollback에 branch switch와 역할 관점을 추가.
6. HaluMem식 extraction/update/QA 단계별 오류 보고.
7. Mem2ActBench·MemGym으로 기억이 실제 행동 파라미터에 쓰이는지 확인.
8. eTAMP류 환경 주입 후 memory poisoning과 복구 성능 측정.

---

## 6. 논문 제목 후보

> **NCM³-E: Separating Knowledge, Access, Truth, and Worldlines in Long-Horizon Agent Memory**

대안:

> **Access Is Not Knowledge: Epistemic Noninterference for Branchable Agent Memory**

두 번째가 신규성을 더 정확하게 드러낸다.
