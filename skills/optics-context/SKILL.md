---
name: optics-context
description: Use the Optics design framework for styling applications. Apply Optics classes for layout, spacing, typography, colors, and components. Use when working on CSS, styling views, or implementing design system guidelines.
metadata:
  triggers: "slim, css, frontend, design-system, optics"
---

# Optics Design Framework

Apply the Optics design system for consistent, token-based styling in Rails applications.

## Core Principles

1. **Use tokens, not hard-coded values** - All colors, spacing, typography from `assets/tokens.json`
2. **Follow BEM structure** - Block, Element, Modifier naming conventions
3. **Check existing components first** - Reuse before creating new
4. **Progressive enhancement** - Start with semantic HTML, layer styles

## Finding Optics Classes

Search for components in this order:

1. **Check Optics components** - `assets/components.json` (this skill's folder)
   - Find appropriate component, modifiers, and attributes
   - Modify using BEM if needed
2. **Search project styles** - Look in the app's stylesheets and the platform_ui gem's `app/stylesheets` (at `bundle info --path platform_ui`) for existing classes
3. **Create new component** - Only if nothing exists (see "Creating Components" below)

- Use Optics utility classes (`flex`, `items-center`, `op-cluster`, `gap-md`, `full-width`, etc.) before writing custom declarations, but keep them to **3 per element (hard max 4)**. When an element would need more, move the declarations into its BEM block or element instead of stacking utilities.

## Using Optics Tokens

**Always use CSS custom properties from `assets/tokens.json`:**

- **Colors**: `var(--op-color-primary-base)`, `var(--op-color-background)`
- **Spacing**: `var(--op-space-small)`, `var(--op-space-medium)`, `var(--op-space-large)`
- **Typography**: `var(--op-font-medium)`, `var(--op-line-height-base)`
- **Borders**: `var(--op-radius-small)`, `var(--op-border-width)`
- **Shadows**: `var(--op-shadow-small)`, `var(--op-shadow-medium)`

## Detecting Violations

**Never use hard-coded values:**

- ❌ **Colors**: `#fff`, `#000`, `rgb(...)`, `rgba(...)`, `hsl(...)`, color names like `white`, `black`
- ❌ **Spacing**: Bare `px`, `rem`, `em` values in padding, margin, gap
- ❌ **Shadows**: `box-shadow: 0 1px 3px rgba(...)`
- ❌ **Borders**: `border: 1px solid #ddd`
- ❌ **Gradients**: `linear-gradient(...)` with literal colors

**Common token mistakes:**

- ❌ `var(--op_color_primary_base)` - Wrong separator (underscore instead of hyphen)
- ❌ `var(--color-primary-base)` - Missing `--op-` prefix
- ❌ `var(--op-primary-color-base)` - Wrong segment order

✅ `var(--op-color-primary-base)` - Correct format

**Fix violations by replacing with tokens from `assets/tokens.json`**

## BEM Structure

**Block, Element, Modifier naming:**: Name classes with BEM — see the `bem-context` skill.

## Creating Components

**File organization:**

- Create the stylesheet beside the app's other stylesheets: `{component-name}.scss`
- Import it from the stylesheet that collects them (for example `app/assets/stylesheets/application.scss`)

**Component structure:**

1. Define base block with semantic name
2. Add nested elements (parts of component)
3. Add modifiers (variants)
4. Use only Optics tokens
5. One component per file unless tightly coupled

These examples are illustrative only — Optics already ships `.card` and `.btn`, so use those rather than recreating them.

**Example - Card component:**

```css
.card {
  position: relative;
  border-radius: var(--op-radius-medium);
  background-color: var(--op-color-background);
  box-shadow: var(--op-shadow-small);

  /* Modifiers */
  &.card--padded {
    padding: var(--op-space-medium);
  }

  &.card--elevated {
    box-shadow: var(--op-shadow-large);
  }

  /* Elements */
  .card__header {
    padding: var(--op-space-medium);
    border-bottom: var(--op-border-width) solid var(--op-color-border);
    border-start-start-radius: var(--op-radius-medium);
    border-start-end-radius: var(--op-radius-medium);
  }

  .card__body {
    padding: var(--op-space-medium);
  }

  .card__footer {
    padding: var(--op-space-medium);
    border-top: var(--op-border-width) solid var(--op-color-border);
    border-end-start-radius: var(--op-radius-medium);
    border-end-end-radius: var(--op-radius-medium);
  }
}
```

**Example - Button component:**

```css
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: var(--op-space-small) var(--op-space-medium);
  font-size: var(--op-font-medium);
  font-weight: var(--op-font-weight-medium);
  border-radius: var(--op-radius-small);
  border: var(--op-border-width) solid transparent;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    opacity: 0.9;
  }

  &.btn--large {
    padding: var(--op-space-medium) var(--op-space-large);
    font-size: var(--op-font-large);
  }

  &.btn--small {
    padding: var(--op-space-x-small) var(--op-space-small);
    font-size: var(--op-font-small);
  }

  &.btn--disabled,
  &:disabled {
    opacity: var(--op-opacity-disabled);
    cursor: not-allowed;
    pointer-events: none;
  }

  &.btn--primary {
    background-color: var(--op-color-primary-base);
    color: var(--op-color-primary-on-base);

    &:hover {
      background-color: var(--op-color-primary-plus-two);
      color: var(--op-color-primary-on-plus-two);
    }
  }

  &.btn--secondary {
    background-color: var(--op-color-neutral-base);
    color: var(--op-color-neutral-on-base);

    &:hover {
      background-color: var(--op-color-neutral-plus-two);
      color: var(--op-color-neutral-on-plus-two);
    }
  }

  &.btn--outline {
    background-color: transparent;
    border-color: var(--op-color-border);
    color: var(--op-color-neutral-on-plus-max);

    &:hover {
      border-color: var(--op-color-primary-base);
    }
  }
}
```

## Creating Custom Tokens

**First ensure there isn't an existing token that fits your need**

**When tokens are missing, create component-specific ones:**

**Project-specific tokens** (preferred for custom needs):

- Use namespace prefix: `--{project-prefix}-{category}-{name}`
- Example: `--ya-color-brand-accent` for "Your App" project
- Keeps project tokens separate from core Optics

**Token categories:**

- **Color**: `--op-color-{name}` or `--{prefix}-color-{name}`
- **Spacing**: `--op-space-{size}` or `--{prefix}-space-{size}`
- **Typography**: `--op-font-{property}-{value}`
- **Border**: `--op-radius-{size}`, `--op-border-{property}`
- **Shadow**: `--op-shadow-{size}`

## Quick Reference

**Discovery workflow:**

1. Check `assets/components.json` for existing component
2. Search the app's and platform_ui's stylesheets for project styles
3. Create new component with Optics tokens

**Token workflow:**

1. Check `assets/tokens.json` for appropriate token
2. Use token in CSS: `var(--op-category-name)`
3. Create custom token if needed (use project prefix)

**Component workflow:**

1. Create the file beside the app's other stylesheets
2. Define block with base styles
3. Add nested elements and modifiers
4. Use only Optics tokens (no hard-coded values)
5. Import it from the stylesheet that collects them

See `assets/components.json` for available Optics components and `assets/tokens.json` for all design tokens.
