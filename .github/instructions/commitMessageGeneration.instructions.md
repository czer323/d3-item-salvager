# Git Commit Standards

Always add humor into your commit messages, but keep it professional. Remember, your code is serious business, but that doesn't mean your commit messages can't have a little fun!

Always write in capital letters to emphasize the importance of your changes, but keep it concise. Your commit messages should be like a good joke: short, punchy, and to the point.

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
