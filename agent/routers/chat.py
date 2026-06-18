import json
import re
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from llm.client import chat as llm_chat
from llm.datatools import (
    hisobotlar_royxati,
    korxonalar_royxati,
    platforma_statistikasi,
)
from llm.tools import resolve_page
from llm.navparse import extract_navigation, detect_user_navigation

router = APIRouter()


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]
    system: Optional[str] = None


class NavigationAction(BaseModel):
    path: str
    label: str


class PendingAction(BaseModel):
    type: str                        # korxona_create | _update | _delete
    label: str
    data: dict
    target_id: Optional[int] = None
    current: Optional[dict] = None


Nav = Optional[NavigationAction]
Act = Optional[PendingAction]


class ChatResponse(BaseModel):
    reply: str
    history: list[dict]
    navigate: Nav = None
    action: Act = None


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    try:
        # 0) TEZKOR YO'L — foydalanuvchi xabari aniq navigatsiya buyrug'i
        # bo'lsa, modelni kutmasdan darhol javob beramiz. Bu ishonchli
        # (model kayfiyatiga bog'liq emas) va tez.
        user_msgs = [m for m in req.messages if m.role == "user"]
        if user_msgs:
            last = user_msgs[-1].content
            data_reply = _direct_data_reply(req.messages)
            if data_reply:
                return ChatResponse(reply=data_reply, history=[], navigate=None)

            page = detect_user_navigation(last)
            # qisqa buyruq bo'lsa (qo'shimcha savol yo'q) — to'g'ridan javob
            if page and len(last.split()) <= 6:
                return ChatResponse(
                    reply=f"{page['label']} sahifasiga o'tdim.",
                    history=[],
                    navigate=NavigationAction(
                        path=page["path"],
                        label=page["label"],
                    ),
                )

        reply, history, tool_calls = llm_chat(
            messages=[
                {"role": m.role, "content": m.content}
                for m in req.messages
            ],
            system=req.system,
        )

        # 1) Haqiqiy tool_call orqali navigate chaqirilganmi?
        nav_action = None
        for tc in tool_calls:
            if tc["name"] == "navigate":
                args = tc.get("args", {})
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except Exception:
                        args = {}
                # Model path'ni noto'g'ri qaytarishi mumkin —
                # resolve_page eng yaqin haqiqiy route'ga moslaydi
                page = resolve_page(args.get("path", ""))
                if page:
                    nav_action = NavigationAction(
                        path=page["path"],
                        label=page["label"],
                    )
                break

        # 2) Tool_call bo'lmasa — model matn ichida yozgan bo'lishi
        # mumkin (navigate('/...') yoki <navigate url="...">). Topib,
        # matndan tozalaymiz.
        if nav_action is None:
            reply, page = extract_navigation(reply)
            if page:
                nav_action = NavigationAction(
                    path=page["path"],
                    label=page["label"],
                )

        # 3) Hali ham yo'q — foydalanuvchi niyatini oxirgi fallback
        # sifatida tekshiramiz (uzun xabarlar uchun).
        if nav_action is None and user_msgs:
            page = detect_user_navigation(user_msgs[-1].content)
            if page:
                nav_action = NavigationAction(
                    path=page["path"],
                    label=page["label"],
                )

        # 4) CRUD taklifi (proposal) — tool natijasidan ajratamiz.
        pending = _extract_proposal(tool_calls)

        return ChatResponse(
            reply=reply,
            history=history,
            navigate=nav_action,
            action=pending,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


def _extract_proposal(tool_calls: list[dict]) -> Optional[PendingAction]:
    """CRUD taklif tool'larining natijasidan proposal'ni ajratadi."""
    for tc in tool_calls:
        result = tc.get("result")
        if not result:
            continue
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except Exception:
                continue
        proposal = result.get("proposal") if isinstance(result, dict) else None
        if proposal:
            return PendingAction(
                type=proposal["type"],
                label=proposal["label"],
                data=proposal.get("data", {}),
                target_id=proposal.get("target_id"),
                current=proposal.get("current"),
            )
    return None


_DATA_INTENT_RE = re.compile(
    r"(nechta|soni|qancha|sanab|hisobla|ro['‘’]?yxat|mavjud|\bbor\b)",
    re.IGNORECASE,
)


def _direct_data_reply(messages: list[Message]) -> Optional[str]:
    """Aniq ma'lumot savollarini LLMga yubormasdan javoblaydi."""
    if not messages:
        return None

    text = messages[-1].content or ""
    if not _DATA_INTENT_RE.search(text):
        return None

    subject = _infer_data_subject(messages)
    if subject is None:
        return None

    try:
        if subject == "korxonalar":
            data = korxonalar_royxati({})
            names = [k.get("nomi") for k in data.get("korxonalar", []) if k.get("nomi")]
            extra = f"\n\nKorxonalar: {', '.join(names)}" if names else ""
            return f"Tizimda {data['soni']} ta korxona bor.{extra}"

        if subject == "hisobotlar":
            data = hisobotlar_royxati({})
            return f"Tizimda {data['soni']} ta hisobot bor."

        data = platforma_statistikasi({})
        return (
            f"Umumiy statistika:\n"
            f"- Korxonalar: {data['korxonalar_soni']} ta\n"
            f"- Hisobotlar: {data['hisobotlar_soni']} ta"
        )
    except Exception as exc:
        return (
            "Django API'dan ma'lumot olishda xatolik bo'ldi: "
            f"{exc}. Serverda DJANGO_API va ALLOWED_HOSTS sozlamalarini tekshiring."
        )


def _infer_data_subject(messages: list[Message]) -> Optional[str]:
    current = (messages[-1].content or "").lower()
    if "korxona" in current:
        return "korxonalar"
    if "hisob" in current or "report" in current:
        return "hisobotlar"
    if "statistika" in current or "umumiy" in current:
        return "platforma"

    # "yo'q, menga soni bergin" kabi xabarlarda mavzuni yaqin tarixdan olamiz.
    for msg in reversed(messages[:-1][-6:]):
        content = (msg.content or "").lower()
        if "korxona" in content:
            return "korxonalar"
        if "hisob" in content or "report" in content:
            return "hisobotlar"
    return None


@router.get("/models")
def list_models():
    import ollama
    from config import OLLAMA_HOST, OLLAMA_API_KEY
    try:
        headers = {}
        if OLLAMA_API_KEY:
            headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"
        client = ollama.Client(host=OLLAMA_HOST, headers=headers)
        models = client.list()
        return {"models": [m.model for m in models.models]}
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Ollama ulanmadi: {exc}",
        )
