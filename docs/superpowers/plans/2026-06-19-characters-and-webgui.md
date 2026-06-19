# Characters + Web GUI Implementation Plan

> **Goal:** Add 2 new characters and a Flask web GUI to the lineart prompt generator.

**Architecture:** New YAML character files in `characters/`; Flask web app (`app.py`) living alongside existing `cli.py`, reusing `engine.py`.

**Tech Stack:** Flask (Python), existing pyyaml+jinja2

---

### Task 1: Add New Characters

**Files:**
- Create: `characters/sword_maiden.yaml` — 仙俠劍姬
- Create: `characters/meiji_schoolgirl.yaml` — 明治女學生

- [ ] Create `sword_maiden.yaml` with distinct components (fantasy xianxia, cold expression, flowing robes)
- [ ] Create `meiji_schoolgirl.yaml` with distinct components (Meiji era, Japanese school uniform)
- [ ] Test: run `python cli.py list` to verify both appear
- [ ] Test: `python cli.py generate sword_maiden three_view --model sd --lang zh`
- [ ] Commit

### Task 2: Build Flask Web GUI

**Files:**
- Create: `app.py` — Flask web application
- Modify: `requirements.txt` — add flask

- [ ] Create `app.py` with routes: `/` (form), `/generate` (POST → result)
- [ ] Create `templates/index.html` — Jinja2 form with dropdowns
- [ ] Create `static/style.css` — clean styling
- [ ] Add JS for copy-to-clipboard
- [ ] Test: run `flask run` → verify form loads and generation works
- [ ] Commit
