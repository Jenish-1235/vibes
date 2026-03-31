# vibes

Personal monorepo of side projects, tools, and utilities — built fast, built for me, shipped when it feels right.

These are not production SaaS products. They are sharp tools that solve real friction in daily life. If they're useful to others, great. If not, they still exist because they were useful to me.

---

## Philosophy

- **Solve real friction first.** Every project in here started because something annoyed me enough to fix it.
- **No overengineering.** The right tool for the job. If it's a 200-line script, it stays a 200-line script.
- **Finish the core loop.** A working v0 beats a perfect v0.1 that never ships.
- **Personal use is a valid reason to build something.**

---

## Repository Structure

```
vibes/
├── README.md               ← you are here
├── ledge/                  ← Native Android app, friend money tracker
├── <project-slug>/         ← one directory per project
└── ...
```

Each project lives in its own top-level directory. There is no shared library, no shared build system, and no shared runtime between projects unless explicitly noted inside a project. Projects are intentionally isolated — pulling one out into its own repo should require zero refactoring.

---

## Project Index

| Project | Platform | Status | One-liner |
|---------|----------|--------|-----------|
| `ledge` | Android (Kotlin) | 🚧 In progress | Minimal friend money ledger with home screen widget |

Status legend: 🚧 In progress · ✅ Usable · 🧊 Frozen · 🗑️ Abandoned

---

## Project Structure Convention

Every project directory follows this layout:

```
<project-slug>/
├── README.md       ← what it is, how to run it, known limitations
├── PRD.md          ← product requirements (what and why)
├── TRD.md          ← technical requirements (how)
└── <source>/       ← actual code, platform-specific structure inside
```

`PRD.md` and `TRD.md` are first-class citizens, not afterthoughts. They exist so that any agent or collaborator picking up a project mid-flight has full context on intent, constraints, and decisions made — without needing to reverse-engineer them from code.

---

## For Agents Working in This Repo

If you are an AI agent operating inside this repository, read this section carefully.

**Before touching any project:**
1. Read `<project-slug>/README.md` for current state and known issues.
2. Read `<project-slug>/PRD.md` to understand what the project is supposed to do and what is explicitly out of scope.
3. Read `<project-slug>/TRD.md` to understand the tech stack, architecture decisions, and data model.

**Do not:**
- Add dependencies not already in the TRD without flagging it explicitly.
- Add abstractions, layers, or patterns beyond what the TRD specifies — these are intentionally lean projects.
- Introduce shared libraries across projects — isolation is intentional.
- Change the data model without re-reading the TRD rationale first (e.g. money is stored in paise as `Long`, not `Float` — this is deliberate).
- Rename or restructure directories without confirming against this README.

**Do:**
- Keep changes minimal and scoped to the task.
- Respect the explicit non-goals listed in each PRD — they are guardrails, not oversights.
- Add a brief entry to the project's README if you add a new file, dependency, or architectural piece.
- Prefer deleting code over adding code when fixing bugs.

---

## Starting a New Project

When adding a new project to this monorepo:
0. Create a new branch with this naming strategy project/<project-name>, this helps keeping all projects as separate branches until ready to be merged into main
1. Create a top-level directory with a short, lowercase, hyphenated slug.
2. Write `PRD.md` before writing any code. If you can't write a one-paragraph problem statement, the idea isn't ready.
3. Write `TRD.md` before writing any code. Commit to the stack and data model upfront.
4. Add a row to the Project Index table above.
5. Build the core loop first. Everything else is optional.

---

## What This Is Not

- Not a portfolio repo — code quality varies intentionally based on project stakes.
- Not a framework or library — nothing here is designed to be imported by other things.
- Not a startup codebase — no CI/CD, no staging environments, no SLAs.
