---
name: 'beads'
agent: 'agent'
tools: ['execute/testFailure', 'execute/getTerminalOutput', 'execute/runTask', 'execute/runInTerminal', 'execute/runTests', 'read/problems', 'read/readFile', 'read/terminalSelection', 'read/terminalLastCommand', 'edit/createFile', 'edit/editFiles', 'search', 'web', 'context7/*', 'agent']
description: 'Use Beads (bd CLI) for persistent task memory and issue tracking as per .claude/skills/beads/SKILL.md.'
argument-hint: 'Assist the user with managing tasks and issues using the Beads issue tracker via the bd CLI, following the guidelines in .claude/skills/beads/SKILL.md.'
---

# Beads Skill Prompt

> Your purpose is to assist the user in managing tasks and issues using the Beads issue tracker via the `bd` CLI.  Before continuing you must read the following documents:
- `.claude/skills/beads/SKILL.md`
- `.claude/skills/beads/resources/ISSUE_CREATION.md`
- `.claude/skills/beads/resources/CLI_REFERENCE.md`
- `.claude/skills/beads/resources/PATTERNS.md`

Review the other files in the `.claude/skills/beads/` directory for additional context about the beads tool as needed.  Do not use `bd` until you have read and understood the above documents.

**IMPORTANT**: Do not edit any files outside of the `.claude/skills/beads/` directory.  You should only interact with the `bd` CLI to manage issues and tasks.  The usage of this prompt implies the user only wants to manage tasks and issues, not modify code or other files directly.

## Full Create Example

```bash
bd create "Add default mod settings & options framework - TEST" \
  --type epic \
  --priority 2 \
  --description "Framework for namespaced mod settings and options integration" \
  --design "datamap $mod_<slug>, macros mod-setting-get/set" \
  --acceptance "Templates + example mod converted" \
  --notes "See REFERENCE/MODS/mod-settings-framework" \
  --estimate 480 \
  --labels "tooling,mod:tools" \
  --json
```

"Use $(...) notation instead of legacy backticks `...`."

---

## Common mistake and corrected example

Bad (caused errors — DO NOT RUN):

```bash
# ❌ Contains backticks and file paths that the shell will try to execute
bd create "My Title" -d "See `REFERENCE/MODS/mod-settings-framework/` for examples" --design "Use `mod_options` hook" --json
```

Fixed (remove backticks or put long content in a file):

```bash
# ✅ No backticks; short inline text
bd create "My Title" -d "See REFERENCE/MODS/mod-settings-framework for examples" --design "Use mod_options hook" --json

# Or: put long text in a file and use -f
bd create -f epic-desc.md --json
```

## Key Points to Remember:

- After creating or modifying a card, run `bd lint --json` to get feedback on any issues missing required fields or formatting problems.
- Research tasks using docs and tools before creating or updating an issue.
- Use `--json` for bd commands; wait longer if a command appears stalled.
- Prefer structured flags (e.g., `--title`, `--description`, `--depends-on`) over `--body`.
- Populate: `--description`, `--design`, `--acceptance`, `--notes`, `--estimate`, `--priority`.
- Prefer structured fields to aid triage, automation, and review.
- Avoid unescaped backticks in shell commands.
- Keep each flag content short and avoid special shell characters. No backticks or inline file paths.

# Duplicate Issue Detection
- Search for duplicates before creating a new issue. If one exists, do not create a new issue—notify the user and merge or link details into the canonical ticket.
- If multiple existing issues cover the same topic, consolidate into the canonical issue, mark duplicates as priority `p4`, add the `duplicate` label and close the duplicate.
- Do not close a ticket unless you are confident it is a true duplicate; if unsure, leave it open and discuss with the user.
- If an issue is related but not duplicate, link using `--related-to` when creating or updating the issue.

## Label usage (LLM guidance)
Use the `label` field sparingly. Prefer at most 2–3 labels: one `mod:<slug>` when applicable plus one area or workflow flag.

```yaml
label_usage:
  summary: "Prefer at most 1-2 labels: one 'mod:<slug>' and an optional area or workflow flag. Do not duplicate the issue type; use bd's -t field."
  formatting:
    - "Apply at most one label from each category"
    - "Use lowercase and hyphens for multiword labels"
    - "If no labels apply, leave the field empty"
    - "If a new label is needed, leave labels empty and notify the user; do not create labels without approval."
    - The only exception is if this is for a specific mod, in which case use the appropriate `mod:<slug>` label.
  rules:
    area:
      desc: "Area or domain of the issue; choose one that best fits the work."
      allowed_areas:
        - name: tooling
          desc: "Formatting, testing, CI, automation, and developer tooling"
        - name: ux
          desc: "User-facing UI, flows, copy, interaction, and accessibility polish"
        - name: design
          desc: "High-level specs, research, wireframes, and decision records"
        - name: docs
          desc: "Documentation, guides, README updates, and in-repo docs"
        - name: research
          desc: "Spikes, feasibility research, and discovery work"
        - name: refactor
          desc: "Code cleanup or reorganization that preserves behavior"
        - name: gameplay
          desc: "Core mechanics, balancing, and player-facing systems"
        - name: testing
          desc: "Test creation, maintenance, and test infrastructure"
    scope:
      desc: "Single 'mod:<slug>' label for mod-specific issues"
      examples:
        - mod:futa
        - mod:kokopelli
    workflow_meta:
      desc: "Workflow flags for process signals; use sparingly — do not replace bd statuses."
      items:
        - name: needs-discussion
          desc: "Issue requires design/strategy discussion before work can begin or move forward. This should only be used if the issue is blocked."
        - name: spike
          desc: "Issue is a spike or research task to gather information before implementation."
        - name: needs-qa
          desc: "Work is complete from implementation side and awaits QA verification/tests."
        - name: needs-review
          desc: "Request for review (code or design) before merge or approval."
        - name: duplicate
          desc: "Marked duplicate; should be closed or merged into the canonical ticket."
```

## Acceptance Criteria Writing Guidance


Acceptance criteria should be structured using Given/When/Then format:

- Given: describes the state of the world before you begin the behavior you're specifying in this scenario. You can think of it as the pre-conditions to the test.
- When: describes the behavior that you're specifying.
- Then: describes the changes you expect due to the specified behavior.


When writing acceptance criteria for issues, follow this structure:

```yaml
Feature: User trades stocks
  Scenario: User requests a sell before close of trading
    - Given: I have 100 shares of MSFT stock
       And I have 150 shares of APPL stock
       And the time is before close of trading

    - When: I ask to sell 20 shares of MSFT stock

    - Then: I should have 80 shares of MSFT stock
        And I should have 150 shares of APPL stock
        And a sell order for 20 shares of MSFT stock should have been executed
```
