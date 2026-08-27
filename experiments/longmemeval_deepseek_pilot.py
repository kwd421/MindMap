from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")
QUESTION_TYPES = (
    "knowledge-update",
    "multi-session",
    "single-session-assistant",
    "single-session-preference",
    "single-session-user",
    "temporal-reasoning",
)
ARMS = ("no_memory", "bm25_top3", "oracle_context")
DEFAULT_MODEL = "deepseek-v4-flash"
DEFAULT_BASE_URL = "https://api.deepseek.com"


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def select_sample(rows: list[dict[str, Any]], seed: str) -> list[dict[str, Any]]:
    def rank(row: dict[str, Any]) -> str:
        return sha256_text(f"{seed}\0{row['question_id']}")

    selected: list[dict[str, Any]] = []
    for question_type in QUESTION_TYPES:
        pool = [
            row
            for row in rows
            if row["question_type"] == question_type and "_abs" not in row["question_id"]
        ]
        if not pool:
            raise ValueError(f"no non-abstention rows for {question_type}")
        selected.append(min(pool, key=rank))

    abstention = sorted(
        (row for row in rows if "_abs" in row["question_id"]), key=rank
    )
    if len(abstention) < 2:
        raise ValueError("fewer than two abstention rows")
    selected.extend(abstention[:2])
    return selected


def sample_hash(rows: Iterable[dict[str, Any]]) -> str:
    ids = [row["question_id"] for row in rows]
    return sha256_text("".join(f"{question_id}\n" for question_id in ids))


def session_text(session: list[dict[str, Any]]) -> str:
    return "\n".join(f"{turn['role']}: {turn['content']}" for turn in session)


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def bm25_rank_sessions(
    question: str, sessions: list[list[dict[str, Any]]], top_k: int = 3
) -> list[int]:
    docs = [tokenize(session_text(session)) for session in sessions]
    if not docs:
        return []
    query = tokenize(question)
    document_frequency: Counter[str] = Counter()
    for doc in docs:
        document_frequency.update(set(doc))
    average_length = sum(map(len, docs)) / len(docs)
    k1, b = 1.5, 0.75
    scored: list[tuple[float, int]] = []
    for index, doc in enumerate(docs):
        frequencies = Counter(doc)
        score = 0.0
        for term in query:
            df = document_frequency.get(term, 0)
            if not df:
                continue
            inverse_document_frequency = math.log(1 + (len(docs) - df + 0.5) / (df + 0.5))
            frequency = frequencies[term]
            denominator = frequency + k1 * (
                1 - b + b * len(doc) / max(average_length, 1.0)
            )
            score += inverse_document_frequency * frequency * (k1 + 1) / denominator
        scored.append((score, index))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [index for _, index in scored[:top_k]]


def render_memory(row: dict[str, Any], indices: list[int]) -> str:
    rendered: list[str] = []
    for index in indices:
        date = row["haystack_dates"][index]
        rendered.append(f"[Session date: {date}]\n{session_text(row['haystack_sessions'][index])}")
    return "\n\n".join(rendered)


def answer_messages(row: dict[str, Any], arm: str, memory: str) -> list[dict[str, str]]:
    system = (
        "Answer the user's question concisely. Use only the supplied memory when it is present. "
        "If the requested personal information is not supported, say that you do not know. "
        "Do not mention this evaluation or invent memories."
    )
    if arm == "no_memory":
        user = f"Question date: {row['question_date']}\nQuestion: {row['question']}"
    else:
        user = (
            f"Question date: {row['question_date']}\n\nMemory:\n{memory}\n\n"
            f"Question: {row['question']}"
        )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def judge_prompt(row: dict[str, Any], response: str) -> str:
    question_type = row["question_type"]
    if "_abs" in row["question_id"]:
        return (
            "I will give you an unanswerable question, an explanation, and a response from a model. "
            "Answer yes if the model correctly identifies the question as unanswerable. The model "
            "may say the information is incomplete or that the asked information is unavailable.\n\n"
            f"Question: {row['question']}\n\nExplanation: {row['answer']}\n\n"
            f"Model Response: {response}\n\nDoes the model correctly identify the question as "
            "unanswerable? Answer yes or no only."
        )
    if question_type == "single-session-preference":
        return (
            "I will give you a question, a rubric for a desired personalized response, and a model "
            "response. Answer yes if the response uses the user's personal information correctly and "
            "satisfies the rubric; otherwise answer no. It need not mention every rubric point.\n\n"
            f"Question: {row['question']}\n\nRubric: {row['answer']}\n\nModel Response: "
            f"{response}\n\nIs the model response correct? Answer yes or no only."
        )
    extra = ""
    if question_type == "temporal-reasoning":
        extra = " Treat a one-unit day/week/month counting error as correct."
    elif question_type == "knowledge-update":
        extra = " If old information is also present, require the updated answer to be clear and correct."
    return (
        "I will give you a question, a correct answer, and a model response. Answer yes only if the "
        "response contains the complete correct answer or an equivalent answer; otherwise answer no. "
        "A response containing only a required subset is incorrect."
        f"{extra}\n\nQuestion: {row['question']}\n\nCorrect Answer: {row['answer']}\n\n"
        f"Model Response: {response}\n\nIs the model response correct? Answer yes or no only."
    )


class DeepSeekClient:
    def __init__(self, api_key: str, base_url: str, timeout_seconds: float) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def _request(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = None if payload is None else canonical_json(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=data,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="GET" if payload is None else "POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))

    def balance(self) -> dict[str, Any]:
        return self._request("/user/balance")

    def chat(self, payload: dict[str, Any], retries: int = 2) -> tuple[dict[str, Any], int]:
        attempts = 0
        while True:
            attempts += 1
            try:
                return self._request("/chat/completions", payload), attempts
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
                if attempts > retries:
                    raise
                time.sleep(2 ** (attempts - 1))


def safe_balance_value(balance: dict[str, Any]) -> str | None:
    for item in balance.get("balance_infos", []):
        if item.get("currency") == "USD":
            return item.get("total_balance")
    return None


def usage_cost(
    usage: dict[str, Any], cache_hit_price: float, cache_miss_price: float, output_price: float
) -> float:
    hit = int(usage.get("prompt_cache_hit_tokens", 0))
    miss = int(usage.get("prompt_cache_miss_tokens", usage.get("prompt_tokens", 0) - hit))
    output = int(usage.get("completion_tokens", 0))
    return (hit * cache_hit_price + miss * cache_miss_price + output * output_price) / 1_000_000


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> int:
    run_started_at = utc_now()
    runner_root = Path(__file__).resolve().parents[1]
    runner_source_revision = subprocess.run(
        ["git", "-C", str(runner_root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    runner_dirty = bool(
        subprocess.run(
            ["git", "-C", str(runner_root), "status", "--porcelain"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    )
    actual_oracle_sha256 = sha256_file(args.oracle)
    actual_long_sha256 = sha256_file(args.long)
    if actual_oracle_sha256 != args.oracle_sha256:
        raise ValueError(
            f"oracle data hash drift: expected {args.oracle_sha256}, got {actual_oracle_sha256}"
        )
    if actual_long_sha256 != args.long_sha256:
        raise ValueError(
            f"long data hash drift: expected {args.long_sha256}, got {actual_long_sha256}"
        )
    actual_harness_revision = subprocess.run(
        ["git", "-C", str(args.official_harness_dir), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if actual_harness_revision != args.official_harness_revision:
        raise ValueError(
            "official harness revision drift: "
            f"expected {args.official_harness_revision}, got {actual_harness_revision}"
        )
    oracle_rows = load_json(args.oracle)
    long_rows = load_json(args.long)
    if {row["question_id"] for row in oracle_rows} != {
        row["question_id"] for row in long_rows
    }:
        raise ValueError("oracle and long variants do not contain the same question IDs")
    selected = select_sample(long_rows, args.sample_seed)
    actual_sample_hash = sample_hash(selected)
    if actual_sample_hash != args.expected_sample_hash:
        raise ValueError(
            f"sample hash drift: expected {args.expected_sample_hash}, got {actual_sample_hash}"
        )

    args.output_dir.mkdir(parents=True, exist_ok=False)
    sample_public = [
        {
            "question_id": row["question_id"],
            "question_type": row["question_type"],
            "session_count": len(row["haystack_sessions"]),
        }
        for row in selected
    ]
    write_json(args.output_dir / "sample.json", sample_public)
    if args.dry_run:
        print(canonical_json({"sample_hash": actual_sample_hash, "sample": sample_public}))
        return 0

    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is required unless --dry-run is used")
    client = DeepSeekClient(api_key, args.base_url, args.timeout_seconds)
    balance_before = client.balance()
    oracle_by_id = {row["question_id"]: row for row in oracle_rows}
    raw_path = args.output_dir / "predictions.jsonl"
    results: list[dict[str, Any]] = []
    running_estimated_cost = 0.0
    with raw_path.open("w", encoding="utf-8") as output:
        for row in selected:
            for arm in ARMS:
                if running_estimated_cost >= args.cost_ceiling_usd:
                    raise RuntimeError(
                        f"estimated cost ceiling reached: {running_estimated_cost:.6f} "
                        f">= {args.cost_ceiling_usd:.6f}"
                    )
                if arm == "no_memory":
                    indices: list[int] = []
                    memory = ""
                elif arm == "bm25_top3":
                    indices = bm25_rank_sessions(row["question"], row["haystack_sessions"], 3)
                    memory = render_memory(row, indices)
                else:
                    oracle = oracle_by_id[row["question_id"]]
                    indices = list(range(len(oracle["haystack_sessions"])))
                    memory = render_memory(oracle, indices)

                messages = answer_messages(row, arm, memory)
                payload = {
                    "model": args.model,
                    "messages": messages,
                    "temperature": 0,
                    "max_tokens": args.max_output_tokens,
                    "stream": False,
                    "thinking": {"type": "disabled"},
                }
                started = time.perf_counter()
                response, answer_attempts = client.chat(payload, retries=args.retries)
                latency = time.perf_counter() - started
                answer = response["choices"][0]["message"]["content"].strip()
                prompt_hash = sha256_text(canonical_json(messages))

                evaluation_prompt = judge_prompt(row, answer)
                judge_payload = {
                    "model": args.model,
                    "messages": [{"role": "user", "content": evaluation_prompt}],
                    "temperature": 0,
                    "max_tokens": 16,
                    "stream": False,
                    "thinking": {"type": "disabled"},
                }
                judge_response, judge_attempts = client.chat(judge_payload, retries=args.retries)
                judge_text = judge_response["choices"][0]["message"]["content"].strip()
                usage = response.get("usage", {})
                judge_usage = judge_response.get("usage", {})
                estimated_cost = usage_cost(
                    usage, args.cache_hit_price, args.cache_miss_price, args.output_price
                ) + usage_cost(
                    judge_usage,
                    args.cache_hit_price,
                    args.cache_miss_price,
                    args.output_price,
                )
                running_estimated_cost += estimated_cost
                record = {
                    "question_id": row["question_id"],
                    "question_type": row["question_type"],
                    "arm": arm,
                    "selected_session_ids": [row["haystack_session_ids"][index] for index in indices]
                    if arm != "oracle_context"
                    else oracle_by_id[row["question_id"]]["haystack_session_ids"],
                    "prompt_sha256": prompt_hash,
                    "answer": answer,
                    "answer_response_id": response.get("id"),
                    "returned_model": response.get("model"),
                    "answer_usage": usage,
                    "answer_attempts": answer_attempts,
                    "answer_latency_seconds": round(latency, 6),
                    "judge_prompt_sha256": sha256_text(evaluation_prompt),
                    "judge": judge_text,
                    "judge_label": judge_text.lower().startswith("yes"),
                    "judge_response_id": judge_response.get("id"),
                    "judge_returned_model": judge_response.get("model"),
                    "judge_usage": judge_usage,
                    "judge_attempts": judge_attempts,
                    "estimated_cost_usd": estimated_cost,
                }
                results.append(record)
                output.write(canonical_json(record) + "\n")
                output.flush()

    balance_after = client.balance()
    arm_summary: dict[str, dict[str, Any]] = {}
    for arm in ARMS:
        arm_rows = [row for row in results if row["arm"] == arm]
        arm_summary[arm] = {
            "judge_correct": sum(row["judge_label"] for row in arm_rows),
            "denominator": len(arm_rows),
            "estimated_cost_usd": sum(row["estimated_cost_usd"] for row in arm_rows),
            "mean_answer_latency_seconds": sum(
                row["answer_latency_seconds"] for row in arm_rows
            )
            / len(arm_rows),
        }
    summary = {
        "experiment_id": args.experiment_id,
        "study_class": "pilot",
        "started_at": run_started_at,
        "ended_at": utc_now(),
        "runner_source_revision": runner_source_revision,
        "runner_dirty": runner_dirty,
        "official_benchmark": "LongMemEval",
        "official_harness_revision": args.official_harness_revision,
        "oracle_sha256": args.oracle_sha256,
        "long_sha256": args.long_sha256,
        "sample_seed": args.sample_seed,
        "sample_hash": actual_sample_hash,
        "sample_size": len(selected),
        "arms": arm_summary,
        "judge_status": "DeepSeek pilot judge using a locally frozen adaptation of the official rubric; not the official GPT-4o metric",
        "model_requested": args.model,
        "models_returned": sorted({row["returned_model"] for row in results}),
        "thinking": "disabled",
        "pricing_usd_per_million": {
            "cache_hit_input": args.cache_hit_price,
            "cache_miss_input": args.cache_miss_price,
            "output": args.output_price,
        },
        "estimated_total_cost_usd": sum(row["estimated_cost_usd"] for row in results),
        "estimated_cost_ceiling_usd": args.cost_ceiling_usd,
        "balance_before_usd": safe_balance_value(balance_before),
        "balance_after_usd": safe_balance_value(balance_after),
        "claim_boundary": "Eight-question cost/feasibility pilot; not an official score, confirmatory result, or leaderboard submission.",
    }
    write_json(args.output_dir / "summary.json", summary)
    print(canonical_json(summary))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--oracle", type=Path, required=True)
    parser.add_argument("--long", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--experiment-id", default="EXP-20260827-003")
    parser.add_argument("--sample-seed", default="EXP-20260827-003-v1")
    parser.add_argument("--expected-sample-hash", required=True)
    parser.add_argument("--oracle-sha256", required=True)
    parser.add_argument("--long-sha256", required=True)
    parser.add_argument("--official-harness-revision", required=True)
    parser.add_argument("--official-harness-dir", type=Path, required=True)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--max-output-tokens", type=int, default=256)
    parser.add_argument("--timeout-seconds", type=float, default=120.0)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--cache-hit-price", type=float, default=0.007)
    parser.add_argument("--cache-miss-price", type=float, default=0.22)
    parser.add_argument("--output-price", type=float, default=0.66)
    parser.add_argument("--cost-ceiling-usd", type=float, default=0.25)
    parser.add_argument("--dry-run", action="store_true")
    return parser


if __name__ == "__main__":
    raise SystemExit(run(build_parser().parse_args()))
