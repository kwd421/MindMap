from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
from typing import Any, TextIO

from .gatemem_public import (
    GateMemBoundaryError,
    PublicCheckpoint,
    PublicEpisode,
    PublicPrincipal,
    PublicTurn,
    public_checkpoint_json,
    public_episode_json,
    public_turn_json,
)
from .gatemem_session import PublicGateMemAgent


class GateMemRPCError(RuntimeError):
    pass


class GateMemRPCTimeout(TimeoutError):
    pass


@dataclass(frozen=True, slots=True)
class RPCProcessConfig:
    command: tuple[str, ...]
    cwd: str | None = None
    env: Mapping[str, str] | None = None
    response_timeout_seconds: float = 60.0
    max_response_characters: int = 4_000_000

    def __post_init__(self) -> None:
        if not self.command:
            raise ValueError("RPC command must not be empty")
        if self.response_timeout_seconds <= 0:
            raise ValueError("response timeout must be positive")
        if self.max_response_characters <= 0:
            raise ValueError("maximum response size must be positive")


def _object(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise GateMemRPCError(f"{field} must be a JSON object")
    return value


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GateMemRPCError(f"{field} must be a non-empty string")
    return value


def _optional_text(value: Any, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise GateMemRPCError(f"{field} must be a string or null")
    return value


def public_episode_from_json(payload: Mapping[str, Any]) -> PublicEpisode:
    if "relationships" in payload:
        raise GateMemRPCError(
            "relationships are forbidden in the raw-language reset capability"
        )
    principals_value = payload.get("principals") or []
    if not isinstance(principals_value, Sequence) or isinstance(
        principals_value, (str, bytes)
    ):
        raise GateMemRPCError("principals must be a list")

    principals: list[PublicPrincipal] = []
    for index, item in enumerate(principals_value):
        row = _object(item, f"principals[{index}]")
        principals.append(
            PublicPrincipal(
                principal_id=_text(
                    row.get("principal_id"), f"principals[{index}].principal_id"
                ),
                role=_text(row.get("role"), f"principals[{index}].role"),
                display_name=_optional_text(
                    row.get("display_name"), f"principals[{index}].display_name"
                ),
            )
        )

    return PublicEpisode(
        episode_id=_text(payload.get("episode_id"), "episode_id"),
        domain=_text(payload.get("domain"), "domain"),
        principals=tuple(principals),
    )


def public_turn_from_json(payload: Mapping[str, Any]) -> PublicTurn:
    return PublicTurn(
        turn_id=_text(payload.get("turn_id"), "turn_id"),
        timestamp=_optional_text(payload.get("timestamp"), "timestamp"),
        speaker_principal_id=_text(
            payload.get("speaker_principal_id"), "speaker_principal_id"
        ),
        speaker_role=_text(payload.get("speaker_role"), "speaker_role"),
        turn_kind=_text(payload.get("turn_kind"), "turn_kind"),
        text=_text(payload.get("text"), "text"),
    )


def public_checkpoint_from_json(payload: Mapping[str, Any]) -> PublicCheckpoint:
    if "as_of_turn_id" in payload:
        raise GateMemRPCError("source as_of_turn_id is forbidden in method queries")
    return PublicCheckpoint(
        checkpoint_id=_text(payload.get("checkpoint_id"), "checkpoint_id"),
        episode_id=_text(payload.get("episode_id"), "episode_id"),
        asker_principal_id=_text(
            payload.get("asker_principal_id"), "asker_principal_id"
        ),
        asker_role=_text(payload.get("asker_role"), "asker_role"),
        query_text=_text(payload.get("query_text"), "query_text"),
    )


def _strict_json_line(value: Any) -> str:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise GateMemRPCError("RPC payload is not strict JSON") from exc


def serve_jsonl(
    agent: PublicGateMemAgent,
    *,
    input_stream: TextIO | None = None,
    output_stream: TextIO | None = None,
) -> None:
    """Serve an opaque public GateMem agent over a JSONL protocol."""

    source = input_stream or sys.stdin
    sink = output_stream or sys.stdout

    for line in source:
        line = line.strip()
        if not line:
            continue
        request_id: Any = None
        should_close = False
        try:
            request = json.loads(line)
            request = _object(request, "request")
            request_id = request.get("request_id")
            if not isinstance(request_id, int) or request_id < 0:
                raise GateMemRPCError("request_id must be a non-negative integer")
            operation = _text(request.get("operation"), "operation")
            payload = _object(request.get("payload") or {}, "payload")

            if operation == "reset":
                agent.reset(public_episode_from_json(payload))
                result: Any = {}
            elif operation == "ingest":
                agent.ingest(public_turn_from_json(payload))
                result = {}
            elif operation == "query":
                result = agent.query(public_checkpoint_from_json(payload))
                if not isinstance(result, Mapping):
                    raise GateMemRPCError("agent query result must be a JSON object")
                result = dict(result)
            elif operation == "close":
                result = {}
                should_close = True
            else:
                raise GateMemRPCError(f"unsupported RPC operation: {operation}")

            response = {
                "request_id": request_id,
                "ok": True,
                "result": result,
            }
        except Exception as exc:  # worker boundary must serialize method failures
            response = {
                "request_id": request_id,
                "ok": False,
                "error_type": type(exc).__name__,
                "error": str(exc),
            }

        sink.write(_strict_json_line(response) + "\n")
        sink.flush()
        if should_close:
            return


class SubprocessGateMemAgent:
    """PublicGateMemAgent client backed by a persistent JSONL subprocess.

    This prevents Python-object capability leakage. It is not by itself a full
    sandbox: a confirmatory method process must also be launched without access
    to raw benchmark/checkpoint files, credentials, or evaluator IPC channels.
    """

    def __init__(self, config: RPCProcessConfig) -> None:
        env = None if config.env is None else dict(config.env)
        self._config = config
        self._process = subprocess.Popen(
            list(config.command),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=1,
            cwd=config.cwd,
            env=env,
        )
        if self._process.stdin is None or self._process.stdout is None:
            self._process.kill()
            raise GateMemRPCError("failed to open RPC process pipes")

        self._responses: queue.Queue[str | None] = queue.Queue()
        self._stderr_lines: list[str] = []
        self._request_id = 0
        self._closed = False
        self._lock = threading.Lock()
        self._stdout_thread = threading.Thread(
            target=self._read_stdout,
            name="gatemem-rpc-stdout",
            daemon=True,
        )
        self._stderr_thread = threading.Thread(
            target=self._read_stderr,
            name="gatemem-rpc-stderr",
            daemon=True,
        )
        self._stdout_thread.start()
        self._stderr_thread.start()

    def _read_stdout(self) -> None:
        assert self._process.stdout is not None
        try:
            for line in self._process.stdout:
                self._responses.put(line)
        finally:
            self._responses.put(None)

    def _read_stderr(self) -> None:
        if self._process.stderr is None:
            return
        for line in self._process.stderr:
            self._stderr_lines.append(line.rstrip("\n"))
            if len(self._stderr_lines) > 100:
                del self._stderr_lines[: len(self._stderr_lines) - 100]

    def _diagnostic(self) -> str:
        suffix = "\n".join(self._stderr_lines[-20:])
        return f"; worker stderr:\n{suffix}" if suffix else ""

    def _terminate(self) -> None:
        if self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait(timeout=2)

    def _call(self, operation: str, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        with self._lock:
            if self._closed:
                raise GateMemRPCError("RPC agent is closed")
            if self._process.poll() is not None:
                raise GateMemRPCError(
                    f"RPC worker exited with code {self._process.returncode}"
                    + self._diagnostic()
                )
            request_id = self._request_id
            self._request_id += 1
            request = {
                "request_id": request_id,
                "operation": operation,
                "payload": dict(payload),
            }
            line = _strict_json_line(request)
            assert self._process.stdin is not None
            try:
                self._process.stdin.write(line + "\n")
                self._process.stdin.flush()
            except (BrokenPipeError, OSError) as exc:
                self._terminate()
                raise GateMemRPCError("RPC worker pipe failed" + self._diagnostic()) from exc

            try:
                response_line = self._responses.get(
                    timeout=self._config.response_timeout_seconds
                )
            except queue.Empty as exc:
                self._terminate()
                raise GateMemRPCTimeout(
                    f"RPC operation timed out: {operation}" + self._diagnostic()
                ) from exc
            if response_line is None:
                code = self._process.poll()
                raise GateMemRPCError(
                    f"RPC worker closed stdout (exit={code})" + self._diagnostic()
                )
            if len(response_line) > self._config.max_response_characters:
                self._terminate()
                raise GateMemRPCError("RPC response exceeded the configured size limit")

            try:
                response = json.loads(response_line)
            except json.JSONDecodeError as exc:
                self._terminate()
                raise GateMemRPCError(
                    "RPC worker returned invalid JSON" + self._diagnostic()
                ) from exc
            response = _object(response, "response")
            if response.get("request_id") != request_id:
                self._terminate()
                raise GateMemRPCError(
                    "RPC response request_id mismatch" + self._diagnostic()
                )
            if response.get("ok") is not True:
                raise GateMemRPCError(
                    f"RPC {operation} failed: {response.get('error_type')}: "
                    f"{response.get('error')}" + self._diagnostic()
                )
            result = response.get("result") or {}
            return _object(result, "response.result")

    def reset(self, episode: PublicEpisode) -> None:
        self._call("reset", public_episode_json(episode))

    def ingest(self, turn: PublicTurn) -> None:
        self._call("ingest", public_turn_json(turn))

    def query(self, checkpoint: PublicCheckpoint) -> Mapping[str, Any]:
        return self._call("query", public_checkpoint_json(checkpoint))

    def close(self) -> None:
        if self._closed:
            return
        try:
            if self._process.poll() is None:
                self._call("close", {})
        finally:
            self._closed = True
            if self._process.stdin is not None:
                self._process.stdin.close()
            try:
                self._process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self._terminate()

    def __enter__(self) -> SubprocessGateMemAgent:
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()


def minimal_subprocess_environment(
    *,
    python_path: str | None = None,
    additions: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Return a small environment for a method process.

    This is defense in depth, not a sandbox. Dataset paths, cloud credentials,
    API keys, and evaluator secrets are intentionally omitted.
    """

    env: dict[str, str] = {}
    for key in (
        "PATH",
        "SYSTEMROOT",
        "WINDIR",
        "LANG",
        "LC_ALL",
        "TMPDIR",
        "TEMP",
        "TMP",
    ):
        value = os.environ.get(key)
        if value:
            env[key] = value
    if python_path is not None:
        env["PYTHONPATH"] = python_path
    if additions:
        forbidden = {
            key
            for key in additions
            if any(
                marker in key.upper()
                for marker in (
                    "TOKEN",
                    "SECRET",
                    "PASSWORD",
                    "CREDENTIAL",
                    "API_KEY",
                )
            )
        }
        if forbidden:
            raise GateMemBoundaryError(
                "refusing credential-like RPC environment keys: "
                + ", ".join(sorted(forbidden))
            )
        env.update({str(key): str(value) for key, value in additions.items()})
    return env
