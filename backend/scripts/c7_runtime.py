"""C7-only runtime controls; production defaults and prompts are unchanged."""
from __future__ import annotations

import hashlib
import json
import os
from functools import lru_cache
from pathlib import Path
from urllib.request import Request, urlopen

CONTEXT = 32768
MAX_OUTPUT = 4096
SEED = 20261012
MODEL = "qwen25-7b-c7"
BASE_MODEL = "qwen2.5:7b-instruct-q4_K_M"


def endpoint() -> str:
    url = os.environ.get("OPENAI_BASE_URL", "http://127.0.0.1:11434/v1").rstrip("/")
    if url not in ("http://127.0.0.1:11434/v1", "http://localhost:11434/v1"):
        raise ValueError("C7 is pinned to the localhost Ollama endpoint")
    return url.removesuffix("/v1")


def request(path: str, payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode()
    req = Request(endpoint() + path, data=data, headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=1800) as response:
        return json.load(response)


def canonical(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha(value) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


@lru_cache(maxsize=1)
def tokenizer():
    from tokenizers import Tokenizer
    path = Path(os.environ.get("C7_TOKENIZER", ".venv/c7/tokenizer.json"))
    return Tokenizer.from_file(str(path))


def render(messages: list[dict]) -> str:
    # Text-only Qwen ChatML, checked against Ollama's prompt_eval_count at G2.
    return "".join(f"<|im_start|>{role}\n{content}<|im_end|>\n"
                   for role, content in ((m["role"], m["content"]) for m in messages)
                   ) + "<|im_start|>assistant\n"


def token_count(messages: list[dict]) -> int:
    return len(tokenizer().encode(render(messages), add_special_tokens=False).ids)


def provenance() -> dict:
    tags = request("/api/tags")["models"]
    model = next(m for m in tags if m["name"].split(":")[0] == MODEL)
    show = request("/api/show", {"model": MODEL})
    result = {"model": MODEL, "base_model": BASE_MODEL, "digest": model["digest"],
            "ollama_version": request("/api/version")["version"],
            "details": model["details"], "parameters": show["parameters"],
            "template": show["template"], "context": CONTEXT, "max_output": MAX_OUTPUT,
            "seed": SEED, "temperature": 0.0,
            "tokenizer_sha256": hashlib.sha256(Path(os.environ.get(
                "C7_TOKENIZER", ".venv/c7/tokenizer.json")).read_bytes()).hexdigest()}
    installation = Path(".venv/c7/runtime.json")
    if installation.exists():
        metadata = json.loads(installation.read_text(encoding="utf-8-sig"))
        result["executable_sha256"] = metadata["executable_sha256"]
        result["server_settings"] = metadata["server_settings"]
    return result


def verify_runtime(gates: dict) -> None:
    if os.environ.get("OPENAI_API_KEY") != "ollama-local":
        raise ValueError("Set OPENAI_API_KEY=ollama-local explicitly for C7")
    if os.environ.get("OPENAI_MODEL") != MODEL or os.environ.get("OPENAI_FALLBACK_MODEL") != MODEL:
        raise ValueError("C7 primary and fallback must both be the pinned local model")
    if os.environ.get("LLM_DISABLE_FALLBACK") != "1":
        raise ValueError("C7 fallback must be disabled")
    if provenance() != gates["runtime"]:
        raise ValueError("The model/runtime differs from the passed C7 gates")


def configure_agent(agent) -> None:
    """Guard every request, including schema correction; retain raw-output hashes."""
    agent._c7_calls = []

    def create(model: str, messages: list[dict]):
        count = token_count(messages)
        # A conservative 64-token framing margin also guards correction prompts.
        if count + 64 + MAX_OUTPUT > CONTEXT:
            agent._c7_calls.append({"status": "context_overflow", "prompt_tokens_local": count})
            raise ValueError(f"C7 context_overflow: {count}+64+{MAX_OUTPUT}>{CONTEXT}")
        response = agent._client.chat.completions.create(
            model=model, messages=messages, temperature=0.0, seed=SEED,
            max_tokens=MAX_OUTPUT, response_format={"type": "json_object"})
        raw = response.choices[0].message.content or ""
        prompt_tokens = response.usage.prompt_tokens
        agent._c7_calls.append({
            "status": "ok", "prompt_sha256": sha(messages),
            "raw_sha256": hashlib.sha256(raw.encode()).hexdigest(),
            "raw_output": raw, "prompt_tokens_local": count,
            "prompt_tokens_server": prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "finish_reason": response.choices[0].finish_reason})
        if prompt_tokens < count - 64:
            raise ValueError(f"C7 suspected prompt truncation: local={count}, server={prompt_tokens}")
        return response

    agent._create = create
