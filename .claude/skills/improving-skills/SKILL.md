---
name: improving-skills
description: >
  Tracks skill feedback and drives continuous improvement. Use when a skill
  produced wrong output, missed a case, gave outdated commands, or could be
  clearer. Records the issue, the fix, and the lesson so the same gap doesn't
  recur. Also use to request a new skill when a recurring task has no skill yet.
allowed-tools: Read Edit Write Bash(git *)
---

# Improving Skills — Feedback Loop

## When to invoke this skill

- A skill gave wrong commands or outdated information
- A skill was missing a common case (e.g., a failure mode not in the table)
- A skill was too verbose or too sparse for the task
- A recurring task has no skill — you've done it manually three times
- A CI failure isn't in the `checking-ci-status` common-failures table

## Feedback format

File a feedback entry in `SKILL_FEEDBACK.md` at the repo root (create if absent):

```markdown
## YYYY-MM-DD — <skill-name>

**Issue:** [What was wrong or missing]
**Context:** [What you were trying to do when you hit it]
**Fix applied:** [What the correct command/approach was]
**Skill change needed:** [Specific line or section to update]
```

Then immediately apply the fix to the skill file on a branch, open a PR.
Don't let feedback sit in `SKILL_FEEDBACK.md` without a corresponding PR.

## Making a skill update

```bash
git checkout main && git pull
git checkout -b fix/<skill-name>-<short-description>
# Edit the relevant SKILL.md
git add .claude/skills/<skill-name>/
git commit -m "Fix(<skill-name>): <what changed and why>"
git push --set-upstream origin fix/<skill-name>-<short-description>
gh pr create --title "Fix(<skill-name>): <what changed>" --body "..."
```

## Requesting a new skill

When you've manually performed the same multi-step task three or more times,
it belongs in a skill. Open an issue or add to `SKILL_FEEDBACK.md`:

```markdown
## New skill request: <proposed-name>

**Frequency:** [How often this task comes up]
**What it does:** [One-sentence description]
**Commands involved:** [Key commands or steps]
**Related skills:** [Which existing skills it depends on or overlaps with]
**Catalog reference:** [Skill name from the 27-skill catalog, if applicable]
```

## Catalog alignment

Before writing a new skill, check against the 27-skill catalog in memory
(`reference-skills-catalog`). Names, parallelism, and dependency relationships
are already decided. If a skill you need is in the catalog, use its catalog name.

## What makes a good skill update

- **Specific**: points to the exact command that was wrong, not "the skill was confusing"
- **Reproducible**: explains the context so the reviewer can verify the fix
- **Minimal**: changes only what's wrong — don't refactor the whole skill for one fix
- **Tested**: the corrected command was actually run and worked before committing
