# Flytedesk Skills

Reusable AI agent skills for Flytedesk projects. Each skill is a `SKILL.md` instruction set that teaches AI coding agents (Claude Code, GitHub Copilot) how to apply specific development patterns and workflows.

Skills follow the [Agent Skills](https://agentskills.io) open standard.

## Skills

| Skill | Description |
|-------|-------------|
| **[npm-package-update](skills/npm-package-update)** | Safely evaluate and perform npm/yarn package updates. Reviewing outdated output, analyzing release notes, handling breaking changes, coordinating with Rails gem dependencies. |
| **[rails-gem-update](skills/rails-gem-update)** | Safely evaluate and perform Ruby gem updates in a Rails modular monolith. Reviewing bundle outdated output, analyzing release notes, handling migrations, coordinating with frontend dependencies. |
| **[testing-patterns](skills/testing-patterns)** | Write automated tests using RSpec, Capybara, and FactoryBot for Rails applications. |

## Installation

### Copy individual skills

Copy the skill folders you need into your project's skills directory.

**For Claude Code:**

```bash
mkdir -p .claude/skills
cp -r path/to/flytedesk-skills/skills/testing-patterns .claude/skills/testing-patterns
```

Skills live in `.claude/skills/<skill-name>/SKILL.md` and are discovered automatically. Claude loads them when relevant to your conversation, or you can invoke them directly with `/<skill-name>`.

### Git submodule

Add this repo as a git submodule to keep skills synced across projects.

```bash
git submodule add <repo-url> .flytedesk-skills
git submodule update --init
```

Then point your agent at the skills directory. For Claude Code, add to `.claude/settings.json`:

```json
{
  "additionalDirectories": [".flytedesk-skills/skills"]
}
```

Or symlink individual skills for automatic discovery:

```bash
mkdir -p .claude/skills
ln -s ../../.flytedesk-skills/skills/testing-patterns .claude/skills/testing-patterns
```

To pull the latest updates:

```bash
git submodule update --remote .flytedesk-skills
```

## Structure

```
skills/
  {skill-name}/
    SKILL.md          # Skill definition with YAML frontmatter + markdown instructions
    references/       # Optional supporting documentation
    assets/           # Optional templates, data files
```

Each `SKILL.md` has YAML frontmatter:

```yaml
---
name: skill-name
description: What the skill does and when to use it.
---

Markdown instructions for the AI agent...
```

- **`name`** -- Identifier for the skill (becomes the `/slash-command` in Claude Code). Must match the directory name.
- **`description`** -- Tells the agent when to load this skill.
