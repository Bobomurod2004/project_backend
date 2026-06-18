import json
from typing import Any, Optional
from llm.datatools import DATA_TOOLS, DATA_HANDLERS
from llm.crudtools import CRUD_TOOLS, CRUD_HANDLERS

# ── Sahifalar reestri ─────────────────────────────────────────────────────────
# Har bir sahifa: path, label, va modeldan keladigan turli matnlarni
# moslashtirish uchun keywords.

PAGES: list[dict] = [
    {
        "path": "/",
        "label": "Bosh sahifa",
        "keywords": ["bosh", "asosiy", "home", "dashboard", "main"],
    },
    {
        "path": "/korxonalar",
        "label": "Korxonalar",
        "keywords": ["korxona", "kompaniya", "tashkilot", "company"],
    },
    {
        "path": "/hisobotlar",
        "label": "Hisobotlar",
        "keywords": ["hisobot", "report", "oylik", "jadval"],
    },
    {
        "path": "/ai",
        "label": "AI Assistant",
        "keywords": ["assistant", "yordamchi", "chat", "suhbat"],
    },
]


def resolve_page(raw: str) -> Optional[dict]:
    """
    Model qaytargan har qanday matnni eng yaqin haqiqiy sahifaga moslaydi.
    Masalan "/korxonalar ro'yxat" → {path: "/korxonalar", ...}
    """
    raw = (raw or "").lower().strip()
    if not raw:
        return None

    # 1) Aniq moslik
    for p in PAGES:
        if raw == p["path"] or raw.rstrip("/") == p["path"].rstrip("/"):
            return p

    # 2) startswith — "/korxonalar ro'yxat" → "/korxonalar"
    for p in PAGES:
        if p["path"] != "/" and raw.startswith(p["path"]):
            return p

    # 3) Kalit so'z bo'yicha
    for p in PAGES:
        if any(kw in raw for kw in p["keywords"]):
            return p

    return None


# ── Tool schemas ──────────────────────────────────────────────────────────────

_TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "navigate",
            "description": (
                "Foydalanuvchini ilova sahifasiga yo'naltiradi. "
                "Foydalanuvchi biror sahifaga O'TISHNI so'rasa ishlat. "
                "Ma'lumot so'ralganda (nechta, qaysi) BU EMAS, "
                "balki ma'lumot tool'larini ishlat."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Sahifa yo'li",
                        "enum": [p["path"] for p in PAGES],
                    },
                },
                "required": ["path"],
            },
        },
    },
    *DATA_TOOLS,
    *CRUD_TOOLS,
]

# ── Handlers ──────────────────────────────────────────────────────────────────

def _navigate(args: dict) -> dict:
    page = resolve_page(args.get("path", ""))
    if page is None:
        return {"ok": False, "error": "Sahifa topilmadi"}
    return {"ok": True, "path": page["path"], "label": page["label"]}


HANDLERS: dict[str, Any] = {
    "navigate": _navigate,
    **DATA_HANDLERS,
    **CRUD_HANDLERS,
}

# ── Public helpers ────────────────────────────────────────────────────────────

def get_tools() -> list[dict]:
    return _TOOLS


def call_tool(name: str, args: dict | str) -> str:
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except json.JSONDecodeError:
            args = {}

    handler = HANDLERS.get(name)
    if handler is None:
        return json.dumps({"error": f"'{name}' tool topilmadi"})

    try:
        result = handler(args)
        return json.dumps(result, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"error": str(exc)})
