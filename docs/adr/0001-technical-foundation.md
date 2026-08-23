# ADR 0001: Technical Foundation

**Date:** 2026-08-23
**Status:** Accepted

## Context
The project is developed by a single developer on two distinct environments (Windows and macOS) for an estimated duration of ten months. The code is intended to be read, audited, and potentially reused by third parties. These constraints require a strict, cross-platform, reproducible toolchain free of hidden magic to guarantee the project's longevity without relying on the developer's memory.

## Decisions

*   **Python 3.12**
    *   *Choice:* Use Python 3.12.
    *   *Alternative discarded:* Python 3.13 and 3.14.
    *   *Justification:* In practice, this avoids compatibility breaks with C extensions in the AI ecosystem; the risk would specifically hit in Phase 7 with audio libraries (sounddevice, VAD, TTS), which are often maintained by one or two people and lag 12 to 18 months behind major Python versions.
*   **uv**
    *   *Choice:* Use `uv` for dependency and environment management.
    *   *Alternative discarded:* Poetry or pip.
    *   *Justification:* `uv` unifies Python version and package management with Rust-based speed, reducing CI installation time. The default `uv_build` backend is kept without arbitration: it is suitable for a pure Python package but must be re-evaluated if native extensions appear.
*   **Ruff**
    *   *Choice:* Use Ruff as the sole linter and formatter.
    *   *Alternative discarded:* The classic toolchain (Flake8, Black, isort, pyupgrade).
    *   *Justification:* Ruff replaces four disparate tools with a single ultra-fast executable. Additional rules (like `B` for Bugbear and `I` for import sorting) are enabled, but `ANN` (flake8-annotations) is discarded because `mypy --strict` already requires annotations; maintaining two distinct tools to verify the same thing inevitably leads to divergences.
*   **Mypy (strict mode)**
    *   *Choice:* Enable `mypy --strict`.
    *   *Alternative discarded:* Optional or disabled typing.
    *   *Justification:* Strict mode forces a rigor that catches static errors, but it has two limitations: it performs no runtime verification, and a misplaced `Any` type silently neutralizes it locally. Consequently, `Any` types are banned outside of boundaries, and strict data validation at the application's entry points remains indispensable.
*   **`src/` Layout**
    *   *Choice:* Place the application code in a `src/mnemo/` subdirectory.
    *   *Alternative discarded:* The flat layout (code at the root next to tests).
    *   *Justification:* The source tree is not importable by accident, so tests import the installed package
*   **MIT License**
    *   *Choice:* Apply the MIT license.
    *   *Alternative discarded:* GPL (strict copyleft) or Apache 2.0 (patent clauses).
    *   *Justification:* The MIT license allows maximum and frictionless reuse of the code by third parties (including in closed-source projects), which aligns with the goal of a showcase project.
*   **tomllib**
    *   *Choice:* Write a custom loader based on `tomllib` (standard library).
    *   *Alternative discarded:* `pydantic-settings` or `dynaconf`.
    *   *Justification:* Choice imposed by a pedagogical constraint to understand and master precedence, type casting, and error validation. Switching to `pydantic-settings` will only happen if the project later requires deeply nested configurations or complex schema validation.

## Consequences
These decisions incur a high initial cost: the tooling (`mypy strict`, `ruff`) and the manual writing of the loader slow down the first days of development by forcing the immediate resolution of errors (types, imports, conventions) that could have otherwise been ignored. Furthermore, rejecting libraries like `pydantic` forces the maintenance of custom casting logic that must be meticulously tested (and updated) with every new configuration field added over the next ten months.
