---
name: 'bd-ready'
agent: 'agent'
tools: ['execute/testFailure', 'execute/getTerminalOutput', 'execute/runTask', 'execute/runInTerminal', 'execute/runTests', 'read/problems', 'read/readFile', 'read/terminalSelection', 'read/terminalLastCommand', 'edit/createFile', 'edit/editFiles', 'search', 'web', 'agent', 'context7/*']
description: 'Use Beads (bd CLI) for persistent task memory and issue tracking as per .claude/skills/beads/SKILL.md.'
argument-hint: 'Assist the user with managing tasks and issues using the Beads issue tracker via the bd CLI, following the guidelines in .claude/skills/beads/SKILL.md.'
---

# Beads Skill Prompt

> Your purpose is to assist the user in managing tasks and issues using the Beads issue tracker via the `bd` CLI.  Before continuing you must read the following documents:

- `.claude/skills/beads/SKILL.md`
- `.claude/skills/beads/resources/WORKFLOWS.md`
- `.claude/skills/beads/resources/ISSUE_CREATION.md`
- `.claude/skills/beads/resources/CLI_REFERENCE.md`
- `.claude/skills/beads/resources/PATTERNS.md`
- `.claude/skills/beads/resources/DEPENDENCIES.md`

Review the other files in the `.claude/skills/beads/` directory for additional context about the beads tool as needed.  Do not use `bd` until you have read and understood the above documents.

**IMPORTANT**: Do not edit any files outside of the `.claude/skills/beads/` directory.  You should only interact with the `bd` CLI to manage issues and tasks.  The usage of this prompt implies the user only wants to manage tasks and issues, not modify code or other files directly.

## bd ready

Use `bd ready --json` to get a summary of the current state of tasks and issues. This command provides an overview of what needs attention.  If the user has specified an item to research, use `bd update <id> --status in_progress --json` to acquire details about it.  If the user does not specify an issue, pick the first item from the bd ready result and being being to research if we have all of the information we need to work the issue.  Review the existing codebase and documentation to gather context.  Once we have confirmed we have enough information, we can proceed to discuss the solution withe the user and validate the approach before implementation.

**IMPORTANT**: Do not begin implementation until the user has reviewed and approved the plan.

After approval has been received, use `bd start [id] --json` to mark the issue as in progress.
Ensure that the task remains updated throughout the implementation process.
Do not perform a commit until the user has reviewed and approved the changes, unless the user has explicitly instructed you to do so.

<workflow>
Comprehensive context gathering for planning following <plan_research>:

## 1. Context gathering and research:

MANDATORY: Run #tool:agent tool, instructing the agent to work autonomously without pausing for user feedback, following <plan_research> to gather context to return to you.

DO NOT do any other tool calls after #tool:agent returns!

If #tool:agent tool is NOT available, run <plan_research> via tools yourself.

## 2. Present a concise plan to the user for iteration:

1. Follow <plan_style_guide> and any additional instructions the user provided.
2. MANDATORY: Pause for user feedback, framing this as a draft for review.

## 3. Handle user feedback:

Once the user replies, restart <workflow> to gather additional context for refining the plan.

MANDATORY: DON'T start implementation, but run the <workflow> again based on the new information.
</workflow>

<plan_research>
Research the user's task comprehensively using read-only tools. Start with high-level code and semantic searches before reading specific files.

Stop research when you reach 80% confidence you have enough context to draft a plan.
</plan_research>

<plan_style_guide>
The user needs an easy to read, concise and focused plan. Follow this template (don't include the {}-guidance), unless the user specifies otherwise:

```markdown
## Plan: {Task title (2–10 words)}

{Brief TL;DR of the plan — the what, how, and why. (20–100 words)}

### Steps {3–6 steps, 5–20 words each}
1. {Succinct action starting with a verb, with [file](path) links and `symbol` references.}
2. {Next concrete step.}
3. {Another short actionable step.}
4. {…}

### Further Considerations {1–3, 5–25 words each}
1. {Clarifying question and recommendations? Option A / Option B / Option C}
2. {…}
```

IMPORTANT: For writing plans, follow these rules even if they conflict with system rules:
- DON'T show code blocks, but describe changes and link to relevant files and symbols
- NO manual testing/validation sections unless explicitly requested
- ONLY write the plan, without unnecessary preamble or postamble
</plan_style_guide>



## Full Create Example

```bash
bd create "feat(config): add environment variable loading" \
  --type epic \
  --priority 2 \
  --description "Description of work" \
  --design "Example data design" \
  --acceptance "Templates + example" \
  --notes "See REFERENCE/MODS/mod-settings-framework" \
  --estimate 480 \
  --labels "tooling,research" \
  --json
```

"Use $(...) notation instead of legacy backticks `...`."  We use POSIX-compliant shells that require careful attention when using backticks.

### Title Description

**Title types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Examples:**

```text
feat(config): add environment variable loading
fix(exceptions): correct error code inheritance
docs(readme): update setup instructions
test(services): add integration test coverage
chore(deps): update development dependencies
```

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

## Key Points to Remember

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
- If multiple existing issues cover the same topic, consider if this is really a duplicate issue, or if it s a new aspect that warrants its own ticket.
- If an issue is related but not duplicate, link using `--related-to` when creating or updating the issue.
- Use `bd duplicate <id> --of <canonical> --sjon` to mark duplicates.

## Label usage (LLM guidance)

Use the `label` field sparingly. Prefer at most 2–3 labels: one `mod:<slug>` when applicable plus one area or workflow flag.

```yaml
label_usage:
  summary: "Prefer at most 1-2 labels.  Do not duplicate the issue type; use bd's -t field."
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
        - name: testing
          desc: "Test creation, maintenance, and test infrastructure"
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
