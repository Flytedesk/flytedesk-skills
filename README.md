# Flytedesk Skills

Reusable AI agent skills for Flytedesk projects. Each skill is a `SKILL.md` instruction set that teaches AI coding agents (Claude Code, GitHub Copilot) how to apply specific development patterns and workflows.

Skills follow the [Agent Skills](https://agentskills.io) open standard.

## Skills

| Skill | Description |
|-------|-------------|
| **[bem](skills/bem)** | Name and structure CSS with BEM (Block Element Modifier) on top of Optics. |
| **[eli5](skills/eli5)** | Explain any topic, code, concept, or error tailored to a specific audience's level of understanding -- by age, education level, job role, or relationship. |
| **[hotwire](skills/hotwire)** | Stimulus controllers, Turbo Frames and Streams, and progressive enhancement. |
| **[npm-package-update](skills/npm-package-update)** | Safely evaluate and perform npm/yarn package updates. Reviewing outdated output, analyzing release notes, handling breaking changes, coordinating with Rails gem dependencies. |
| **[optics-context](skills/optics-context)** | Style with the Optics design framework: components, tokens and utility classes. |
| **[rails-api](skills/rails-api)** | REST APIs: JSON:API, OpenAPI, serialization, versioning, token auth and RSwag tests. |
| **[rails-controllers](skills/rails-controllers)** | Controllers and routing: RESTful actions, strong params, response handling and security. |
| **[rails-gem-update](skills/rails-gem-update)** | Safely evaluate and perform Ruby gem updates in a Rails modular monolith. Reviewing bundle outdated output, analyzing release notes, handling migrations, coordinating with frontend dependencies. |
| **[rails-jobs](skills/rails-jobs)** | Background jobs with ActiveJob and GoodJob: idempotency, retries, queues and scheduling. |
| **[rails-models](skills/rails-models)** | ActiveRecord models and migrations: validations, associations, scopes and query performance. |
| **[rails-services](skills/rails-services)** | Service objects: when one is justified, transactions, results and external integrations. |
| **[rails-views](skills/rails-views)** | Slim templates, ViewComponents (naming, slots, no template conditionals) and simple_form. |
| **[testing-patterns](skills/testing-patterns)** | Write automated tests using RSpec, Capybara, FactoryBot and shoulda-matchers for Rails applications. |

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
