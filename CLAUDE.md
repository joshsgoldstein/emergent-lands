# Emergent Lands — Rules

## Before You Code

**Do not write, edit, or modify any code without first explaining what you're about to do and getting confirmation.** This includes:
- New files
- Edits to existing files
- Config YAML changes
- Any file under `emergent/`, `config/`, `agents/`, or `tests/`

Exceptions (no need to ask):
- Running tests (`pytest`, etc.)
- Git operations (`git add`, `git commit`, `git push`)
- Reading files for understanding
- Searching/grepping

## Review Required

After each batch of changes, run `pytest tests/ -q --tb=short` and confirm all tests pass before pushing.
