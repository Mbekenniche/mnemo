# Mnemo

A local-first personal assistant designed to be genuinely useful rather than cinematic.

Mnemo focuses on low latency, reliable context retrieval over local notes/documents, and seamless voice interaction without unnecessary complexity.

---

## Roadmap & Features

### v1 — Text & Contextual Memory (In progress)
- [ ] CLI / TUI conversational interface.
- [ ] Persistent short-term conversational history.
- [ ] Document indexing and local retrieval (RAG) over personal notes and files.

### v2 — Voice Interface
- [ ] Fast Speech-to-Text (STT) pipeline with near-instant transcription.
- [ ] Low-latency Text-to-Speech (TTS) response generation.
- [ ] Full hands-free vocal loop with acceptable response times.

---

## Prerequisites

- **Python 3.12**
- **[uv](https://github.com/astral-sh/uv)** (fast Python package manager)


---

## Installation

```bash
git clone https://github.com/Mbekenniche/mnemo.git
cd mnemo
uv sync
```

`uv sync` creates the virtual environment, installs the project in editable mode,
and pins every dependency to the versions recorded in `uv.lock`.

---

## Configuration

Mnemo reads its configuration from a TOML file, with environment variables
taking precedence over file values. Copy the example file to get started:

```bash
cp .env.example .env
```

### Settings

| TOML key | Environment variable | Type | Constraint |
|---|---|---|---|
| `model` | `MNEMO_MODEL` | string | — |
| `temperature` | `MNEMO_TEMPERATURE` | float | between 0.0 and 1.5 |
| `corpus_dir` | `MNEMO_CORPUS_DIR` | path | not checked for existence |
| `timeout_seconds` | `MNEMO_TIMEOUT_SECONDS` | float | strictly positive |
| `api_key` | `MNEMO_API_KEY` | string | never printed or logged |

All settings are required. There are no defaults: a missing key is an error,

### Precedence

Environment variables override TOML values, so that deployment settings can be
changed without editing files. An environment variable set to an empty string is
treated as unset and falls back to the TOML value.

Unknown keys in the TOML file are rejected, so that a typo fails.

---

## Development

Install the git hooks once per clone. They are stored in `.git/hooks/` and are
therefore not versioned — a fresh clone has no hooks until you run this:

```bash
uv run pre-commit install
```

Run the test suite:

```bash
uv run pytest
```

Run the same quality checks the CI enforces:

```bash
uv run ruff check
uv run ruff format --check
uv run mypy
```

Or all of them at once, across the entire repository:

```bash
uv run pre-commit run --all-files
```

---

## License

[MIT](LICENSE)
