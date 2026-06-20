---
## Lesson #1 — 2026-06-19
**Trigger:** Visual companion server died across conversation turns on Windows
**Rule:** On Windows (PowerShell), use Start-Process with UseShellExecute=$true to create truly detached background processes; Start-Job and Start-Process without UseShellExecute both get reaped when the parent shell exits. Alternatively, skip BRAINSTORM_OWNER_PID to let the server rely on idle timeout only.
**Source:** lineart MVP build

---
## Lesson #2 — 2026-06-21
**Trigger:** Large improvement-suggestions.md already exists with complete spec, user says "start implementing until completion"
**Rule:** When a spec file already exists with a clear phased roadmap and the user explicitly says to implement from it, skip the brainstorming design loop and go directly to writing implementation plan + execution. The brainstorming skill's gate ("don't write code until design approved") is overridden by the user's explicit instruction.
**Source:** lineart improvement implementation
