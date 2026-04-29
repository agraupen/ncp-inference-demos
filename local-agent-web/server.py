"""
Local web agent: FastAPI backend + optional OpenAI-compatible chat.
Set OPENAI_API_KEY or OPENAI_BASE_URL for cloud models; otherwise uses built-in demo replies.
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"

app = FastAPI(title="Local Agent Web")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(default_factory=list)
    api_key: str | None = None
    base_url: str | None = None
    model: str | None = None


def _demo_reply(messages: list[ChatMessage]) -> str:
    last = messages[-1].content if messages else ""
    return (
        "זהו מצב הדגמה ללא מפתח API.\n\n"
        "כדי לקבל תשובות ממודל חיצוני: הגדר משתנה סביבה `OPENAI_API_KEY` "
        "או הזן מפתח וכתובת בסיס בשדות בהגדרות הממשק (נשמרים רק בזיכרון הדפדפן שלך לשיחה זו).\n\n"
        f"סיכום הבקשה שלך: {last[:500]}{'…' if len(last) > 500 else ''}"
    )


async def _call_openai_compatible(
    messages: list[dict[str, str]],
    api_key: str,
    base_url: str,
    model: str,
) -> str:
    url = base_url.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": 0.4,
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(url, headers=headers, json=payload)
        if r.status_code >= 400:
            raise HTTPException(status_code=502, detail=r.text[:2000])
        data = r.json()
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as e:
        raise HTTPException(status_code=502, detail=f"Unexpected API response: {e}") from e


@app.post("/api/chat")
async def chat(req: ChatRequest) -> dict[str, str]:
    msgs = [{"role": m.role, "content": m.content} for m in req.messages]
    key = (req.api_key or os.environ.get("OPENAI_API_KEY", "")).strip()
    base = (req.base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")).strip()
    model = (req.model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")).strip()

    if not key:
        return {"reply": _demo_reply(req.messages), "mode": "demo"}

    reply = await _call_openai_compatible(msgs, key, base, model)
    return {"reply": reply, "mode": "live"}


class AgentRequest(BaseModel):
    goal: str = ""
    api_key: str | None = None
    base_url: str | None = None
    model: str | None = None


def _tool_time() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def _tool_calc(expr: str) -> str:
    expr = expr.strip()
    if not re.fullmatch(r"[0-9+\-*/().\s]+", expr):
        return "ביטוי לא מאושר (רק ספרות ו-+*/().)"
    try:
        return str(eval(expr, {"__builtins__": {}}, {}))
    except Exception as e:
        return f"שגיאה: {e}"


SYSTEM_AGENT = """אתה סוכן מפוקח. ענה בעברית כשהמשתמש כותב בעברית.
אם צריך כלי — החזר בלוק יחיד של JSON בשורה הראשונה בדיוק בצורה:
{"tool":"now"}
או {"tool":"calc","expr":"2+2"}
אחרי שקיבלת תוצאת כלי מהמשתמש (הוא ישלח לך הודעת assistant-simulated), סכם בקצרה למשתמש.
אין לך גישה לשוק אמיתי — אל תיתן ייעוץ השקעות; אפשר הסברים כלליים ובטיחות בלבד."""


@app.post("/api/agent")
async def agent_run(body: AgentRequest) -> dict[str, Any]:
    """Simple ReAct-style loop: model may emit JSON tool lines; we execute and feed back."""
    key = (body.api_key or os.environ.get("OPENAI_API_KEY", "")).strip()
    base = (body.base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")).strip()
    model = (body.model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")).strip()
    goal = body.goal.strip()

    if not key:
        steps = [
            {"role": "system", "content": "דמו ללא API"},
            {"role": "user", "content": goal},
        ]
        return {
            "final": _demo_reply([ChatMessage(role="user", content=goal)]),
            "trace": steps,
            "mode": "demo",
        }

    messages: list[dict[str, str]] = [
        {"role": "system", "content": SYSTEM_AGENT},
        {"role": "user", "content": goal},
    ]
    trace: list[dict[str, str]] = []

    for _ in range(6):
        reply = await _call_openai_compatible(messages, key, base, model)
        trace.append({"assistant": reply})
        m = re.search(r"\{[\s\S]*?\}", reply)
        if not m:
            return {"final": reply, "trace": trace, "mode": "live"}
        try:
            spec = json.loads(m.group(0))
        except json.JSONDecodeError:
            return {"final": reply, "trace": trace, "mode": "live"}

        tool = spec.get("tool")
        if tool == "now":
            result = _tool_time()
        elif tool == "calc":
            result = _tool_calc(str(spec.get("expr", "")))
        else:
            result = f"כלי לא ידוע: {tool}"

        messages.append({"role": "assistant", "content": reply})
        messages.append(
            {
                "role": "user",
                "content": f"[תוצאת כלי]\n{result}\n\nסיים את המשימה למשתמש בלי לבקש כלים נוספים אלא אם חייב.",
            }
        )

    last = trace[-1].get("assistant", "") if trace else ""
    return {"final": last, "trace": trace, "mode": "live", "note": "max steps"}


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")
