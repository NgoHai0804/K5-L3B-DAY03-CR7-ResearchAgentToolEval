from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# chat.run_model_tool_loop prints "🔧 tool(...)" to stdout. On a Windows console
# (cp1252) that raises UnicodeEncodeError mid-loop, so force UTF-8 here.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError, OSError):
        pass

import streamlit as st

from chat import run_model_tool_loop, trim_history
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import build_artifact_version

ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
PROVIDERS = ["openrouter", "openai", "anthropic", "gemini", "ollama"]

load_lab_env(ROOT)

st.set_page_config(page_title="Research Agent", page_icon="🔎", layout="wide")


@st.cache_resource(show_spinner=False)
def get_provider(name: str) -> Any:
    return make_provider(name)


def render_turn(turn: dict[str, Any]) -> None:
    with st.chat_message(turn["role"]):
        st.markdown(turn["text"] or "_(không có nội dung)_")
        for event in turn.get("tool_events", []):
            with st.expander(f"🔧 {event.get('tool', 'tool')}"):
                st.caption("args")
                st.json(event.get("args", {}))
                st.caption("result")
                st.json(event.get("result", {}))


# ---------------------------------------------------------------------------
# Sidebar: provider / model / version / artifact_version / tools
# ---------------------------------------------------------------------------
st.sidebar.header("Cấu hình")
provider_name = st.sidebar.selectbox("Provider", PROVIDERS)
model_input = st.sidebar.text_input("Model (trống = mặc định provider)", "")
version = st.sidebar.text_input("Version label", "v3")
history_window = st.sidebar.slider("history_window", min_value=1, max_value=10, value=5)
max_tool_rounds = st.sidebar.slider("max_tool_rounds", min_value=1, max_value=6, value=4)

prompt_path = ARTIFACTS_DIR / "system_prompt.md"
tools_path = ARTIFACTS_DIR / "tools.yaml"

try:
    artifact_version = build_artifact_version(version, prompt_path, tools_path)
    declarations = load_tool_declarations(tools_path)
    openai_tools = to_openai_tools(declarations)
    tools_error = None
except Exception as exc:  # artifacts may be mid-edit by teammates
    artifact_version, declarations, openai_tools = None, [], []
    tools_error = f"{type(exc).__name__}: {exc}"

if artifact_version is not None:
    st.sidebar.caption(f"artifact_version: `{artifact_version.artifact_version}`")
    st.sidebar.write("Tools đang bật:", ", ".join(d.get("name", "?") for d in declarations))

if tools_error:
    st.sidebar.error(f"Không load được artifacts: {tools_error}")

default_model = getattr(get_provider(provider_name), "default_model", None)
selected_model = model_input.strip() or default_model
st.sidebar.caption(f"model: `{selected_model or 'default'}`")

if st.sidebar.button("Xóa hội thoại", use_container_width=True):
    st.session_state.history = []
    st.session_state.rendered = []
    st.rerun()

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
st.session_state.setdefault("history", [])
st.session_state.setdefault("rendered", [])

system_prompt = prompt_path.read_text(encoding="utf-8")

st.title("Research Agent")
st.caption("Chat multi-turn với tool-calling agent. Tool calls + args + kết quả hiện ngay dưới mỗi lượt.")

for turn in st.session_state.rendered:
    render_turn(turn)

if tools_error:
    st.warning("Sửa lỗi artifacts ở sidebar trước khi chat.")

user_text = st.chat_input("Hỏi gì đó...", disabled=bool(tools_error))

if user_text:
    user_turn = {"role": "user", "text": user_text, "tool_events": []}
    st.session_state.rendered.append(user_turn)
    render_turn(user_turn)

    messages = [
        {"role": "system", "content": system_prompt},
        *trim_history(st.session_state.history, history_window),
        {"role": "user", "content": user_text},
    ]

    try:
        provider = get_provider(provider_name)
        result = run_model_tool_loop(
            provider=provider,
            messages=messages,
            tools=openai_tools,
            model=model_input.strip() or None,
            max_tool_rounds=max_tool_rounds,
        )
        answer = result.get("assistant_text") or ""
        tool_events = result.get("tool_events", [])
        status = result.get("status")
        if status == "waiting_for_user":
            answer = f"🟡 {answer}"
        elif status == "max_tool_rounds":
            answer = f"⚠️ {answer}"
    except Exception as exc:
        answer = f"❌ Lỗi provider ({type(exc).__name__}): {exc}"
        tool_events = []

    assistant_turn = {"role": "assistant", "text": answer, "tool_events": tool_events}
    st.session_state.rendered.append(assistant_turn)
    render_turn(assistant_turn)

    st.session_state.history.append({"role": "user", "content": user_text})
    st.session_state.history.append({"role": "assistant", "content": answer})
