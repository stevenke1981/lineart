---
## Lesson #1 — 2026-06-19
**Trigger:** Visual companion server died across conversation turns on Windows
**Rule:** On Windows (PowerShell), use Start-Process with UseShellExecute=$true to create truly detached background processes; Start-Job and Start-Process without UseShellExecute both get reaped when the parent shell exits. Alternatively, skip BRAINSTORM_OWNER_PID to let the server rely on idle timeout only.
**Source:** lineart MVP build
