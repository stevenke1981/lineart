## Goal Runner Policy

When the user invokes `/goal` or asks for a complete task, use the goal-runner workflow.

Default behavior:
- Do not ask repeated clarification questions.
- Inspect repository files before editing.
- Make reasonable assumptions from existing code, docs, tests, and conventions.
- Implement directly.
- Run relevant tests or checks.
- Fix failures before reporting completion.
- Report in zh-TW.

Ask only when:
- the task is destructive
- credentials are required
- the goal is impossible with available files
- two interpretations would produce incompatible results
- the requested change would break existing public API without evidence

Verification preference:
- Rust: `cargo fmt`, `cargo check`, `cargo test`, `cargo clippy` when relevant.
- Node: `npm/pnpm/bun test`, `build`, `lint` when relevant.
- UI tasks: run build plus inspect affected components/styles.

Final report format:

### 完成內容
- ...

### 驗證結果
- ...

### 注意事項
- ...
