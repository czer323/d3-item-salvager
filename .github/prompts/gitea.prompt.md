---
name: 'tea'
agent: 'agent'
tools: ['execute/testFailure', 'execute/getTerminalOutput', 'execute/runTask', 'execute/runInTerminal', 'execute/runTests', 'read/problems', 'read/readFile', 'read/terminalSelection', 'read/terminalLastCommand', 'edit/createFile', 'edit/editFiles', 'search', 'web', 'context7/*', 'agent']
description: 'Use Tea, the official Gitea CLI, for managing Gitea repositories, issues, pull requests.'
argument-hint: 'Manage Gitea repositories, issues, pull requests.'
---


# Tea - Official Gitea CLI

Tea is the official command-line interface for Gitea, a self-hosted Git service. It provides a comprehensive set of tools to interact with Gitea instances directly from the terminal, eliminating the need to switch to a web browser for common Git forge operations. Tea is designed as a productivity helper that enables developers to manage repositories, issues, pull requests, releases, and other Gitea entities efficiently.

The tool intelligently leverages context from the current working directory's Git repository, making it seamless to work with local and remote repositories. It supports multiple Gitea instances with persistent authentication, works best in upstream/fork workflows, and assumes local Git state is synchronized with remotes before performing operations. Configuration is stored in XDG-compliant directories for cross-platform compatibility.


PRefer to use --output yaml to get structured data for easier understanding.

## Branch Operations

### List Branches

Display repository branches.

```bash
# List all branches
tea branches

# List from specific repository
tea branches --repo owner/project

# List with remote information
tea branches --remote origin
```

NAME:
   tea pulls approve - Approve a pull request

USAGE:
   tea pulls approve [options] <pull index> [<comment>]

DESCRIPTION:
   Approve a pull request

---

NAME:
   tea pulls merge - Merge a pull request

USAGE:
   tea pulls merge [options] <pull index>

DESCRIPTION:
   Merge a pull request

OPTIONS:
   --style string, -s string    Kind of merge to perform: merge, rebase, squash, rebase-merge (default: "merge")
   --title string, -t string    Merge commit title
   --message string, -m string  Merge commit message
   --output string, -o string   Output format. (simple, table, csv, tsv, yaml, json)



## Authentication and Login

### Login to Gitea Instance

Add authentication credentials to interact with a Gitea server. Supports multiple authentication methods including application tokens and OAuth.

```bash
# Interactive login with application token
tea login add
# Follow the prompts:
# - Select authentication type: Application Token
# - Provide your Gitea instance URL (e.g., https://gitea.com)
# - Enter your application token (generated from User Settings → Applications)

# List all configured logins
tea login list

# Show details of a specific login
tea login gitea.com

# Set default login
tea login default gitea.com

# Delete a login
tea login delete gitea.com
```

## Repository Management

### Create Repository

Create a new repository on Gitea with custom configuration options.

```bash
// CLI equivalent
tea repos create \
  --name "my-project" \
  --description "My awesome project" \
  --private \
  --init \
  --license "MIT" \
  --gitignores "Go,VisualStudioCode" \
  --readme "Default" \
  --branch "main" \
  --output string yaml
```


// Create repository under an organization
```bash
tea repos create \
  --name "team-project" \
  --owner "myorg" \
  --description "Team collaboration project" \
  --private
```

```bash
// Create template repository
tea repos create \
  --name "project-template" \
  --template \
  --init \
  --trustmodel "collaborator"
```

### List Repositories

Display repositories accessible to the authenticated user.

```bash
# List all repositories for current login
tea repos list

# List repositories for specific organization
tea repos list --org myorg

# List with custom output format
tea repos list --output yaml

# Search repositories
tea repos search "keyword" --login gitea.com
```


## Comments

### Add Comment

Post comments on issues and pull requests.

```bash
# Add comment to issue
tea comment 42 "This has been fixed in the latest commit"

# Add comment to PR
tea comment 15 "Could you add unit tests for this?"

# Add multiline comment
tea comment 42 "$(cat <<EOF
This is a longer comment
with multiple lines
and code examples
EOF
)"
```
