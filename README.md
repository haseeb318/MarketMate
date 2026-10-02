# Marketing Agent

Phase 0 project scaffold. It includes dependency and environment setup plus a minimal CrewAI/Gemini smoke test. Marketing agents, database storage, and the Streamlit application are intentionally not implemented yet.

## Requirements

- Python 3.12
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)

## Setup on Windows

From the project directory, create and activate a virtual environment, then install the pinned dependencies:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Copy the environment template and add your key to `.env`:

```powershell
Copy-Item .env.example .env
```

Set `GEMINI_API_KEY` in `.env`. `GOOGLE_API_KEY` is also accepted if that is the name you use. The default model is `gemini/gemini-2.5-flash`; set `MODEL` in `.env` to override it.

## Run the CrewAI smoke test

```powershell
python crew.py
```

The script creates one CrewAI agent, assigns it a simple hello task, and prints the model response. A valid API key and network access are required.

## Project structure

- `data/`: reserved for future project data; no database is created in Phase 0.
- `tools/`: reserved for future CrewAI tools.
- `agents.py` and `tasks.py`: placeholders for later marketing workflow phases.
- `crew.py`: executable CrewAI hello-task smoke test.
- `app.py`: reserved for a later Streamlit implementation.
