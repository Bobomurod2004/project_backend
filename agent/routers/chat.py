import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from llm.client import chat as llm_chat
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
