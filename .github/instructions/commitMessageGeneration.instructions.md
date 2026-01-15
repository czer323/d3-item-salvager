# Git Commit Standards

Follow conventional commit format for consistency:

**Format:**

```text
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Examples:**

```text
feat(config): add environment variable loading
fix(exceptions): correct error code inheritance
docs(readme): update setup instructions
test(services): add integration test coverage
chore(deps): update development dependencies
```

**Rules:**

- Subject line ≤50 characters
- No capital letter at start of subject
- No period at end of subject
- Use imperative mood ("add" not "added")
- Body lines ≤72 characters
- Blank line between subject and body
