# ✦ NOVA AI

### Neural-Oriented Virtual Assistant

NOVA AI is a **private, fully local AI assistant** built with Python, Streamlit, Ollama, and Llama 3.2 3B.

It provides a ChatGPT-style conversational interface while running the AI model locally through Ollama, without requiring paid cloud APIs.

---

## ✨ Features

### 💬 Local AI Chat
Interact with a locally running Llama 3.2 3B model through Ollama.

### 📖 PDF Analysis
Upload PDF documents and ask questions about their content.

### 📊 Data Analysis
Upload CSV or Excel files and interact with the uploaded dataset.

### 🧠 Context-Aware Responses
Uploaded documents and datasets are added to the model context so NOVA can answer questions based on the provided information.

### 💾 Chat History
Conversations are automatically stored locally and can be reopened from the sidebar.

### 📎 File Attachments
Attach PDF, CSV, XLSX, and XLS files directly through the chat interface.

### 🔒 Privacy-Focused
The application is designed to run locally using Ollama, so conversations and uploaded files remain on the local machine.

### 🎨 Interactive UI
Built with Streamlit with a clean chat interface, sidebar navigation, file status, and theme support.

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core application |
| Streamlit | Web interface |
| Ollama | Local LLM runtime |
| Llama 3.2 3B | Language model |
| Pandas | CSV/Excel processing |
| PyPDF | PDF text extraction |
| JSON | Chat persistence |

---

## 🏗️ Architecture

```text
                    ┌──────────────────┐
                    │     NOVA AI      │
                    │   Streamlit UI   │
                    └────────┬─────────┘
                             │
             ┌───────────────┼────────────────┐
             │               │                │
             ▼               ▼                ▼
        PDF Upload      CSV / Excel       Chat Input
             │               │                │
             ▼               ▼                │
           PyPDF           Pandas              │
             │               │                │
             └───────────────┼────────────────┘
                             ▼
                    Context Construction
                             │
                             ▼
                     Ollama Local Runtime
                             │
                             ▼
                      Llama 3.2 3B
                             │
                             ▼
                       NOVA Response
```

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/dnyaneshwari2309/NOVA-AI.git
cd NOVA-AI
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the environment

**Windows PowerShell:**

```powershell
venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Install Ollama

Install Ollama for your operating system and make sure it is running.

### 6. Download the model

```bash
ollama pull llama3.2:3b
```

### 7. Run NOVA AI

```bash
streamlit run app.py
```

The application will open in your browser.

---

## 📁 Project Structure

```text
NOVA-AI/
│
├── app.py
├── requirements.txt
├── README.md
│
└── nova_chats/
    └── saved conversations
```

---

## 🔒 Privacy

NOVA AI is designed around local processing.

The application does not require a paid OpenAI or other cloud API key. The LLM runs through Ollama on the local machine.

Uploaded files are processed by the application locally for the current session.

---

## 🎯 What I Learned

Building NOVA AI helped me gain practical experience with:

- Local LLM integration
- Ollama
- LLM prompt and context management
- Python application development
- Streamlit UI development
- PDF processing
- Structured data processing
- Pandas
- Session state management
- JSON-based persistence
- File handling
- Virtual environments
- Building and debugging an end-to-end AI application

---

## 🔮 Future Improvements

Planned improvements include:

- Multi-model support
- Improved document retrieval/RAG
- Conversation export
- More advanced data visualization
- Voice interaction
- Web search integration as an optional feature
- Improved document understanding
- Model configuration controls

---

## 👩‍💻 Author

**Dnyaneshwari Sonawane**

Interested in **AI/ML, Data Science, Python, LLMs and AI application development**.

---

⭐ If you find this project interesting, consider starring the repository!
