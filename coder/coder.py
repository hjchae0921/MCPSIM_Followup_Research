"""Model calls and generated-code execution for the five-stage benchmarks."""
import os
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
from common.client import client as OPENAI_CLIENT, require_credentials
from openai import RateLimitError, APIConnectionError, APITimeoutError
from common.models import MODEL_PROFILES, completion_options

EXECUTION_TIMEOUT = 1200
WORK = Path(os.environ.get("RUN_DIR") or (ROOT / ".run"))

MAX_FIX = 5  # fix attempts per stage
PREFIX = ""  # earlier stages, prepended before running a stage's code
TRACE = None  # optional per-run request/response recorder

#   The coder model is separate from the embedding model, so the retrieval conditions
#   stay fixed while the coder is swapped. CODER_BASE_URL points at an OpenAI-compatible
#   gateway when the model is not served by OpenAI.
CODER_MODEL = os.environ.get("CODER_MODEL", "gpt-5.4-mini")
_gateway = (os.environ.get("CODER_BASE_URL") or "").strip()
if _gateway:
    from openai import OpenAI as _OpenAI

    CODER_CLIENT = _OpenAI(
        base_url=_gateway,
        api_key=os.environ.get("CODER_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or "not-configured",
    )
else:
    CODER_CLIENT = OPENAI_CLIENT



def ask(prompt, system, max_tokens=1200):
    """One completion, with retries.

    Reasoning models spend part of their budget before writing, so theirs is raised. A gateway
    can answer 200 with an error in the body; that is retried like a refused connection.
    """
    require_credentials(CODER_CLIENT)
    kw = {
        "model": CODER_MODEL,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
    }
    extra = {}
    if CODER_MODEL in [p['id'] for p in MODEL_PROFILES]:
        options=completion_options(CODER_MODEL,max_tokens=max(12000,max_tokens),reasoning=os.environ.get('CODER_REASONING') or None)
        extra=options.pop('extra_body',{})
        kw.update(options)
    elif CODER_MODEL.startswith("gpt-5"):
        kw["max_completion_tokens"] = max(12000, max_tokens)
        if os.environ.get("CODER_REASONING"):
            kw["reasoning_effort"] = os.environ["CODER_REASONING"]
    else:
        kw["temperature"] = 0
        kw["max_tokens"] = 6000 if ("/" in CODER_MODEL or "oss" in CODER_MODEL) else max_tokens
        if os.environ.get("CODER_REASONING") and _gateway:
            extra["reasoning"] = {"effort": os.environ["CODER_REASONING"]}

    last = ""
    if TRACE:
        TRACE(
            "model_request",
            model=CODER_MODEL,
            messages=kw["messages"],
            options={key: value for key, value in kw.items() if key not in {"messages", "model"}},
            extra_body=extra,
        )
    for attempt in range(6):
        try:
            r = CODER_CLIENT.chat.completions.create(**kw, extra_body=extra)
            if getattr(r, "choices", None):
                if TRACE:
                    TRACE(
                        "model_response",
                        model=CODER_MODEL,
                        content=r.choices[0].message.content,
                        usage=r.usage.model_dump() if r.usage else None,
                    )
                return (r.choices[0].message.content or "").strip()
            last = str(getattr(r, "error", None) or r)[:200]
        except (RateLimitError, APIConnectionError, APITimeoutError) as ex:
            last = f"{type(ex).__name__}: {str(ex)[:150]}"
        if attempt == 5:
            raise RuntimeError(f"no answer from {CODER_MODEL} — last: {last}")
        time.sleep(2**attempt)

def unfence(text):
    """The code out of a reply; the first fenced block wins."""
    m = re.search(r"```[a-zA-Z]*\n(.*?)```", text, re.S)
    if m:
        return m.group(1).strip()
    return re.sub(r"^\s*```[a-zA-Z]*\n|\n```\s*$", "", text.strip()).strip()

def clip_err(out, limit=8000):
    """The error, whole up to a limit, keeping the head where the first exception is."""
    out = out.replace(str(WORK / "cache"), "<cache>").replace(str(WORK), "<workdir>")
    if len(out) <= limit:
        return out
    head = limit * 2 // 3
    return (
        out[:head] + f"\n... ({len(out) - limit} characters omitted) ...\n" + out[-(limit - head) :]
    )

def run_code(code, tag, *, suffix="", output=None, result_dir=None):
    """Run one stage's code after the earlier stages. (passed?, error text)"""
    WORK.mkdir(parents=True, exist_ok=True)
    f = WORK / f"stage_{tag}.py"
    f.write_text((PREFIX or "") + code + suffix)
    command = [sys.executable, "-u", str(f)]
    env = {**os.environ, "XDG_CACHE_HOME": str(WORK / "cache")}
    if result_dir is not None:
        command = [sys.executable, "-u", "-m", "codegen.execute", "--script", str(f),
                   "--run-dir", str(result_dir)]
        env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    try:
        p = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=EXECUTION_TIMEOUT,
            cwd=WORK,
            env=env,
        )
    except subprocess.TimeoutExpired:
        return False, f"Generated stage execution exceeded {EXECUTION_TIMEOUT} seconds."
    if output:
        output(p.stdout, p.stderr)
    return p.returncode == 0, clip_err(p.stderr or p.stdout)
