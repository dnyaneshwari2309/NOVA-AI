import io
import json
import uuid
from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st
import ollama
from pypdf import PdfReader


# ============================================================
# NOVA AI - CONFIG
# ============================================================

APP_NAME = "NOVA AI"
MODEL = "llama3.2:3b"

BASE_DIR = Path(__file__).parent
CHAT_DIR = BASE_DIR / "nova_chats"
CHAT_DIR.mkdir(exist_ok=True)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title=APP_NAME,
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_id" not in st.session_state:
    st.session_state.chat_id = str(uuid.uuid4())

if "chat_title" not in st.session_state:
    st.session_state.chat_title = "New Chat"

if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

if "pdf_name" not in st.session_state:
    st.session_state.pdf_name = ""

if "dataset" not in st.session_state:
    st.session_state.dataset = None

if "dataset_name" not in st.session_state:
    st.session_state.dataset_name = ""


# ============================================================
# CSS - STYLING ONLY
# ============================================================

st.markdown(
    """
    <style>
        .stApp {
            background:
                radial-gradient(
                    circle at 10% 10%,
                    rgba(125, 90, 255, 0.08),
                    transparent 30%
                ),
                radial-gradient(
                    circle at 90% 90%,
                    rgba(70, 140, 255, 0.07),
                    transparent 30%
                );
        }

        section[data-testid="stSidebar"] {
        background-color: var(--secondary-background-color);
        border-right: 1px solid var(--border-color);
        }

        section[data-testid="stSidebar"] * {
            color: var(--text-color);
        }

        [data-testid="stSidebarCollapseButton"] button {
            border-radius: 10px;
        }

        [data-testid="stChatMessage"] {
            border-radius: 18px;
            border: 1px solid rgba(100, 80, 160, 0.08);
            padding: 0.8rem 1rem;
            margin-bottom: 0.65rem;
        }

        [data-testid="stChatInput"] {
            border-radius: 18px;
        }

        [data-testid="stChatInput"] textarea {
            border-radius: 18px !important;
        }

        [data-testid="stAlert"] {
            border-radius: 15px;
        }

        [data-testid="stExpander"] {
            border-radius: 14px;
        }

        .nova-brand-title {
            font-size: 27px;
            font-weight: 750;
            letter-spacing: 0.3px;
            text-align: center;
        }

        .nova-brand-subtitle {
            font-size: 12px;
            opacity: 0.62;
            text-align: center;
            margin-top: 4px;
            margin-bottom: 16px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# CHAT STORAGE
# ============================================================

def chat_file(chat_id):
    return CHAT_DIR / f"{chat_id}.json"


def save_chat():
    data = {
        "id": st.session_state.chat_id,
        "title": st.session_state.chat_title,
        "created": datetime.now().isoformat(),
        "messages": st.session_state.messages,
    }

    try:
        with open(
            chat_file(st.session_state.chat_id),
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2,
            )
    except Exception:
        pass


def load_saved_chats():
    chats = []

    for file in CHAT_DIR.glob("*.json"):
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
            chats.append(data)
        except Exception:
            continue

    chats.sort(
        key=lambda item: item.get("created", ""),
        reverse=True,
    )

    return chats


def load_chat(chat_id):
    file = chat_file(chat_id)

    if not file.exists():
        return False

    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        st.session_state.chat_id = data.get(
            "id",
            str(uuid.uuid4()),
        )

        st.session_state.chat_title = data.get(
            "title",
            "New Chat",
        )

        st.session_state.messages = data.get(
            "messages",
            [],
        )

        # Uploaded files are session-specific.
        st.session_state.pdf_text = ""
        st.session_state.pdf_name = ""
        st.session_state.dataset = None
        st.session_state.dataset_name = ""

        return True

    except Exception:
        return False


def delete_chat(chat_id):
    file = chat_file(chat_id)

    try:
        if file.exists():
            file.unlink()
    except Exception:
        pass


def new_chat():
    st.session_state.messages = []
    st.session_state.chat_id = str(uuid.uuid4())
    st.session_state.chat_title = "New Chat"

    st.session_state.pdf_text = ""
    st.session_state.pdf_name = ""

    st.session_state.dataset = None
    st.session_state.dataset_name = ""


# ============================================================
# OLLAMA
# ============================================================

def check_ollama():
    try:
        result = ollama.list()
        models = getattr(result, "models", [])

        for model in models:
            name = getattr(model, "model", "")

            if name == MODEL:
                return True

        return False

    except Exception:
        return False


ollama_online = check_ollama()


# ============================================================
# PDF FUNCTIONS
# ============================================================

def extract_pdf_text(pdf_bytes):
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        pages = []

        for page in reader.pages:
            text = page.extract_text()

            if text:
                pages.append(text)

        return "\n\n".join(pages).strip()

    except Exception:
        return ""


def clean_text(text):
    if not text:
        return ""

    return " ".join(
        text.replace("\x00", " ").split()
    )


def get_pdf_context(question, pdf_text, max_chars=14000):
    if not pdf_text:
        return ""

    pdf_text = clean_text(pdf_text)

    if len(pdf_text) <= max_chars:
        return pdf_text

    question_words = {
        word.lower()
        for word in question.split()
        if len(word) > 3
    }

    sentences = pdf_text.split(". ")
    scored = []

    for sentence in sentences:
        lower_sentence = sentence.lower()

        score = sum(
            1
            for word in question_words
            if word in lower_sentence
        )

        scored.append((score, sentence))

    scored.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    selected = []
    total = 0

    for _, sentence in scored:
        if total + len(sentence) > max_chars:
            continue

        selected.append(sentence)
        total += len(sentence)

        if total >= max_chars:
            break

    if not selected:
        return pdf_text[:max_chars]

    return ". ".join(selected)


# ============================================================
# DATASET FUNCTIONS
# ============================================================

def dataset_context(df):
    if df is None:
        return ""

    try:
        rows, columns = df.shape

        column_info = []

        for column in df.columns:
            column_info.append(
                f"- {column}: {df[column].dtype}"
            )

        sample = df.head(10).to_string(
            index=False
        )

        return f"""
Dataset dimensions:
{rows} rows × {columns} columns

Columns and data types:
{chr(10).join(column_info)}

First 10 rows:
{sample}
"""

    except Exception:
        return ""


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are NOVA AI.

NOVA stands for Neural-Oriented Virtual Assistant.

You are a private local AI assistant running through
Ollama using the Llama 3.2 3B model.

You can help with:
- General questions
- Python
- Programming
- SQL
- Data Science
- Machine Learning
- Artificial Intelligence
- LLM concepts
- Study
- Coding
- PDF analysis
- CSV analysis
- Excel analysis

Rules:
1. Give clear and useful answers.
2. Be accurate and honest.
3. Do not pretend to have internet access.
4. Do not invent information.
5. Use uploaded PDF content when relevant.
6. Use uploaded CSV/Excel data when relevant.
7. Clearly say when information is unavailable.
8. For coding questions, provide clean working code.
9. Use Markdown where helpful.
10. Keep normal responses reasonably concise.
11. Give numbered steps when the user asks for steps.
12. You are a local assistant and do not use paid online APIs.
"""


# ============================================================
# BUILD MODEL MESSAGES
# ============================================================

def build_messages(question):
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        }
    ]

    if st.session_state.pdf_text:
        context = get_pdf_context(
            question,
            st.session_state.pdf_text,
        )

        messages.append(
            {
                "role": "system",
                "content": f"""
The user uploaded this PDF:
{st.session_state.pdf_name}

Relevant PDF content:
{context}
""",
            }
        )

    if st.session_state.dataset is not None:
        context = dataset_context(
            st.session_state.dataset
        )

        messages.append(
            {
                "role": "system",
                "content": f"""
The user uploaded this dataset:
{st.session_state.dataset_name}

Dataset information:
{context}
""",
            }
        )

    for message in st.session_state.messages:
        messages.append(
            {
                "role": message["role"],
                "content": message["content"],
            }
        )

    messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    return messages


# ============================================================
# OLLAMA RESPONSE
# ============================================================

def generate_response(messages):
    try:
        stream = ollama.chat(
            model=MODEL,
            messages=messages,
            stream=True,
        )

        for chunk in stream:
            message = getattr(
                chunk,
                "message",
                None,
            )

            if message is not None:
                content = getattr(
                    message,
                    "content",
                    "",
                )

                if content:
                    yield content

                continue

            if isinstance(chunk, dict):
                message_data = chunk.get(
                    "message",
                    {},
                )

                content = message_data.get(
                    "content",
                    "",
                )

                if content:
                    yield content

    except Exception as error:
        yield (
            "🫧 I couldn't connect to Ollama.\n\n"
            f"Make sure Ollama is running and "
            f"`{MODEL}` is installed.\n\n"
            f"Error: `{error}`"
        )


# ============================================================
# SIDEBAR
# ============================================================
#
# IMPORTANT:
# We use Streamlit's REAL sidebar here.
# This means its native collapse/reopen button remains available.
# We do NOT create a fixed custom sidebar over the chat.
# ============================================================

with st.sidebar:

    # --------------------------------------------------------
    # BRAND
    # --------------------------------------------------------

    st.markdown(
        '<div class="nova-brand-title">✦ NOVA AI</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="nova-brand-subtitle">
            (<b>N</b>eural-<b>O</b>riented
            <b>V</b>irtual <b>A</b>ssistant)
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # NEW CHAT
    # --------------------------------------------------------

    if st.button(
        "＋  New Chat",
        use_container_width=True,
    ):
        new_chat()
        st.rerun()

    st.divider()

    # --------------------------------------------------------
    # OLLAMA STATUS
    # --------------------------------------------------------

    if ollama_online:
        st.success(
            f"🟢 Ollama Online\n\n{MODEL}",
            icon="✨",
        )
    else:
        st.error(
            "🔴 Ollama Offline",
            icon="🫧",
        )

        st.caption(
            "Start Ollama before chatting."
        )

    st.divider()

    # --------------------------------------------------------
    # PREVIOUS CHATS
    # --------------------------------------------------------

    st.subheader("💬 Previous Chats")

    saved_chats = load_saved_chats()

    if not saved_chats:
        st.caption(
            "🌷 Your conversations will appear here."
        )
    else:
        for chat in saved_chats[:15]:

            chat_id = chat.get("id")
            title = chat.get(
                "title",
                "New Chat",
            )

            if not title.strip():
                title = "New Chat"

            col1, col2 = st.columns(
                [5, 1],
                gap="small",
            )

            with col1:
                if st.button(
                    f"💭 {title[:26]}",
                    key=f"load_{chat_id}",
                    use_container_width=True,
                ):
                    if load_chat(chat_id):
                        st.rerun()

            with col2:
                if st.button(
                    "×",
                    key=f"delete_{chat_id}",
                ):
                    delete_chat(chat_id)
                    st.rerun()

    st.divider()

    # --------------------------------------------------------
    # CURRENT FILES
    # --------------------------------------------------------

    st.subheader("📎 Current Files")

    if st.session_state.pdf_name:
        st.info(
            f"📖 {st.session_state.pdf_name}",
            icon="✨",
        )

    if st.session_state.dataset_name:
        rows, columns = (
            st.session_state.dataset.shape
        )

        st.info(
            f"📊 {st.session_state.dataset_name}\n\n"
            f"{rows:,} rows × {columns} columns",
            icon="🫧",
        )

    if (
        not st.session_state.pdf_name
        and not st.session_state.dataset_name
    ):
        st.caption(
            "🌷 No files attached yet."
        )

    st.divider()

    # --------------------------------------------------------
    # PRIVACY
    # --------------------------------------------------------

    st.subheader("🔒 Privacy")

    st.caption(
        "Your conversations and uploaded files "
        "are processed locally through Ollama."
    )

    st.caption(
        "☁️ No paid API is required."
    )


# ============================================================
# MAIN HEADER
# ============================================================

st.title("✦ NOVA AI")

st.markdown(
    "(<b>N</b>eural-<b>O</b>riented <b>V</b>irtual <b>A</b>ssistant)",
    unsafe_allow_html=True,
)
# ------------------------------------------------------------
# Sidebar open/close information
# ------------------------------------------------------------
# Streamlit's native sidebar button is used.
# When closed, Streamlit automatically shows its reopen button.
# ------------------------------------------------------------

if not ollama_online:
    st.warning(
        "🌙 Ollama is not running. "
        "Start Ollama before chatting.",
        icon="⚠️",
    )

# ============================================================
# WELCOME
# ============================================================

if not st.session_state.messages:

    st.markdown("### 🫧 Hello! I'm NOVA.")

    st.write(
        "Your private local AI assistant. "

    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.info(
            "**🪄 Ask Anything**"
        )

    with col2:
        st.info(
            "**📖 Read PDFs**"
        )

    with col3:
        st.info(
            "**🐣 Analyse Data**"
        )


# ============================================================
# FILE STATUS
# ============================================================

if st.session_state.pdf_name:
    st.info(
        f"📖 **PDF attached:** {st.session_state.pdf_name}",
        icon="✨",
    )

if st.session_state.dataset_name:
    rows, columns = (
        st.session_state.dataset.shape
    )

    st.info(
        f"📊 **Dataset attached:** "
        f"{st.session_state.dataset_name} · "
        f"{rows:,} rows × {columns} columns",
        icon="🫧",
    )


# ============================================================
# CHAT HISTORY
# ============================================================

for message in st.session_state.messages:

    if message["role"] == "user":

        with st.chat_message("user"):
            st.markdown("🌷 **You**")
            st.markdown(message["content"])

    else:

        with st.chat_message("assistant"):
            st.markdown("🫧 **NOVA**")
            st.markdown(message["content"])


# ============================================================
# CHAT INPUT
# ============================================================

chat_input = st.chat_input(
    "Message NOVA...  📎 Attach PDF, CSV or Excel",
    accept_file=True,
    file_type=[
        "pdf",
        "csv",
        "xlsx",
        "xls",
    ],
    key="nova_chat",
)


# ============================================================
# HANDLE INPUT
# ============================================================

if chat_input is not None:

    user_text = ""
    uploaded_files = []

    # --------------------------------------------------------
    # Text
    # --------------------------------------------------------

    try:
        if hasattr(chat_input, "text"):
            user_text = chat_input.text or ""
        elif isinstance(chat_input, str):
            user_text = chat_input
    except Exception:
        user_text = ""

    # --------------------------------------------------------
    # Files
    # --------------------------------------------------------

    try:
        if hasattr(chat_input, "files"):
            uploaded_files = chat_input.files or []
    except Exception:
        uploaded_files = []

    processed_files = []

    # ========================================================
    # PROCESS FILES
    # ========================================================

    for uploaded_file in uploaded_files:

        filename = uploaded_file.name
        lower_name = filename.lower()

        try:
            file_bytes = uploaded_file.getvalue()

            # ------------------------------------------------
            # PDF
            # ------------------------------------------------

            if lower_name.endswith(".pdf"):

                extracted_text = extract_pdf_text(
                    file_bytes
                )

                if extracted_text:

                    st.session_state.pdf_text = (
                        extracted_text
                    )

                    st.session_state.pdf_name = (
                        filename
                    )

                    processed_files.append(
                        filename
                    )

                else:
                    st.warning(
                        f"📖 Could not extract text "
                        f"from **{filename}**. "
                        f"It may be a scanned PDF."
                    )

            # ------------------------------------------------
            # CSV
            # ------------------------------------------------

            elif lower_name.endswith(".csv"):

                df = pd.read_csv(
                    io.BytesIO(file_bytes)
                )

                st.session_state.dataset = df
                st.session_state.dataset_name = (
                    filename
                )

                processed_files.append(
                    filename
                )

            # ------------------------------------------------
            # Excel
            # ------------------------------------------------

            elif lower_name.endswith(
                (".xlsx", ".xls")
            ):

                df = pd.read_excel(
                    io.BytesIO(file_bytes)
                )

                st.session_state.dataset = df
                st.session_state.dataset_name = (
                    filename
                )

                processed_files.append(
                    filename
                )

        except Exception as error:
            st.error(
                f"🫧 Couldn't read "
                f"**{filename}**: {error}"
            )

    # ========================================================
    # BUILD QUESTION
    # ========================================================

    if processed_files:

        if user_text.strip():
            question = user_text.strip()
        else:
            file_names = ", ".join(
                processed_files
            )

            question = (
                f"I uploaded these files: "
                f"{file_names}. "
                f"Please analyse them and tell me "
                f"what they contain."
            )

    else:
        question = user_text.strip()

    if not question:
        st.stop()

    # ========================================================
    # CHAT TITLE
    # ========================================================

    if (
        not st.session_state.messages
        and st.session_state.chat_title == "New Chat"
    ):

        title = (
            question
            .replace("\n", " ")
            .strip()
        )

        if len(title) > 38:
            title = title[:38].rstrip() + "..."

        st.session_state.chat_title = (
            title or "New Chat"
        )

    # ========================================================
    # USER MESSAGE
    # ========================================================

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    with st.chat_message("user"):
        st.markdown("🌷 **You**")
        st.markdown(question)

    # ========================================================
    # NOVA RESPONSE
    # ========================================================

    with st.chat_message("assistant"):

        st.markdown("🫧 **NOVA**")

        response_placeholder = st.empty()
        full_response = ""

        model_messages = build_messages(
            question
        )

        for token in generate_response(
            model_messages
        ):

            full_response += token

            response_placeholder.markdown(
                full_response + "▌"
            )

        response_placeholder.markdown(
            full_response
        )

    # ========================================================
    # SAVE
    # ========================================================

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": full_response,
        }
    )

    save_chat()

    st.rerun()
