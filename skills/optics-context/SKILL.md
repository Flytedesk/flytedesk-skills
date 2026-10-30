---
name: optics-context
description: Applies the Optics design system to CSS and view styling, covering components, design tokens (--op-* custom properties) and utility classes. Use when writing or reviewing CSS or SCSS, choosing classes in Slim or ERB views, picking tokens, or replacing hard-coded colors, spacing and shadows.
---

# Optics Design Framework

Apply the Optics design system for consistent, token-based styling in Rails applications. The bundled data
is for Optics 2.5.1. After an Optics upgrade, rebuild it from this skill's folder with
`python3 scripts/regenerate_data.py <app>/node_modules/@rolemodel/optics` and review the diff.

## Core principles

1. **Use tokens, not hard-coded values.** Tokens follow the theme, including dark mode (Optics colors are
   `light-dark()` pairs), so a literal value drifts the moment the theme changes.
2. **Follow BEM.** See the `bem-context` skill.
3. **Check existing components first.** Reuse before creating.

## Reading the data files

`assets/tokens.json` (24KB) and `assets/components.json` (13KB) are large. Search them instead of reading
them whole, from this skill's folder:

```bash
grep -n "space" assets/tokens.json            # tokens by name
grep -n -A25 '"card": {' assets/components.json   # one component's base, modifiers and elements
```

In `tokens.json`, `optics_design_tokens.meta` lists the categories (colors, typography, spacing, borders,
shadows, ...) and how many tokens each has. In `components.json`, each key under
`optics_component_classes` is a component, with its `base`, `modifiers` and `elements`.

Both files cover core Optics only. platform_ui's theme (`app/stylesheets/platform_ui/core/theme/` in the
gem, found with `bundle info --path platform_ui`) overrides Optics values and adds more `--op-*` tokens,
such as a `secondary` color scale and extra spacing steps (`--op-space-4x-small`, `--op-space-5x-large`
and up), plus the project's own `--fd-*` tokens. A token defined there is valid even though
`tokens.json` doesn't list it.

## Units

Optics sets the root font size to 62.5%, so **1rem = 10px**, not 16px. Spacing and font tokens are
multiples of that: `--op-space-medium` is 1.6rem (16px). Convert pixel values from a design at 10px per
rem, or the result comes out 1.6× too large.

## Finding Optics classes

Search in this order:

1. **Optics components**: `assets/components.json`. Find the component, its modifiers and its elements,
   and extend it with BEM if needed.
2. **Project styles**: the app's stylesheets and the platform_ui gem's `app/stylesheets`.
3. **A new component**: only if nothing exists (see "Creating components").

### Utility classes

Use utility classes (`flex`, `items-center`, `op-cluster`, `gap-md`, etc.) before writing custom
declarations. They aren't in the bundled data, so look them up rather than guessing a name:

- **Optics**: the app's `node_modules/@rolemodel/optics/dist/css/core/utilities.css`, which holds the
  flex, alignment, gap, margin and width utilities and the `op-*` layout classes. Read a layout class's
  rule before using it, since each one arranges its children differently.
- **platform_ui**: `app/stylesheets/platform_ui/utilities.scss` in the gem.

```bash
grep -oE '^\s*\.[a-z][a-z0-9-]*' node_modules/@rolemodel/optics/dist/css/core/utilities.css | sort -u
grep -oE '^\s*\.[a-z][a-z0-9-]*' "$(bundle info --path platform_ui)/app/stylesheets/platform_ui/utilities.scss" | sort -u
```

Keep utilities to **3 per element (hard max 4)**. Past that, the element's styling is scattered across
markup where it's hard to find, change or reuse, so move the declarations into a BEM block or element,
which gives them a name and one place to live.

## Using tokens

Always use CSS custom properties from `assets/tokens.json` (or platform_ui's theme):

- **Colors**: `var(--op-color-primary-base)`, `var(--op-color-background)` (see "Choosing colors")
- **Spacing**: `var(--op-space-small)`, `var(--op-space-medium)`, `var(--op-space-large)`
- **Typography**: `var(--op-font-medium)`, `var(--op-font-weight-semi-bold)`, `var(--op-line-height-base)`
- **Borders**: `var(--op-radius-small)`, `var(--op-border-width)`. The `--op-border-{all,top,bottom,x,y,...}`
  tokens are box-shadow offsets that draw a border without taking up layout space:
  `box-shadow: var(--op-border-all) var(--op-color-border)`.
- **Shadows**: `var(--op-shadow-small)`, `var(--op-shadow-medium)`
- **Stacking**: `var(--op-z-index-dropdown)`, `var(--op-z-index-dialog)`, `var(--op-z-index-tooltip)`.
  Never invent a number like `z-index: 9999`; pick the layer the element belongs to.
- **Opacity**: `var(--op-opacity-disabled)`, `var(--op-opacity-overlay)`, `var(--op-opacity-half)`
- **Transitions**: `var(--op-transition-input)`, `var(--op-transition-modal)`, `var(--op-transition-panel)`
- **Form controls**: `var(--op-input-height-medium)` and the `--op-input-focus-*` focus rings, so custom
  controls line up with Optics inputs

### Choosing colors

- **Scales**: `primary`, `neutral` and `alerts-{danger,warning,info,notice}` (red, yellow, blue, green),
  plus platform_ui's `secondary`. Each runs from `plus-max` (lightest) through `plus-eight` … `plus-one`,
  `base`, `minus-one` … `minus-eight` to `minus-max` (darkest). Match an alert scale to its meaning:
  `danger` for errors and destructive actions, `notice` for success.
- **Text on a filled background**: use the matching on-color. On `--op-color-primary-minus-two`, text is
  `--op-color-primary-on-minus-two`. The `-alt` variant is a softer, lower-emphasis version for secondary
  text on the same background. Pairing them this way keeps contrast right in both light and dark mode.
- **Page surfaces**: `--op-color-background` with `--op-color-on-background` (or `-alt` for muted text),
  and `--op-color-border` for dividers and outlines.
- Don't use the `-h`, `-s`, `-l` and `-original` tokens directly. They are inputs the theme uses to build
  the scales.

### Detecting violations

Never use hard-coded values:

- ❌ **Colors**: `#fff`, `#000`, `rgb(...)`, `rgba(...)`, `hsl(...)`, color names like `white`, `black`
- ❌ **Spacing**: bare `px`, `rem`, `em` values in padding, margin, gap
- ❌ **Shadows**: `box-shadow: 0 1px 3px rgba(...)`
- ❌ **Borders**: `border: 1px solid #ddd`
- ❌ **Gradients**: `linear-gradient(...)` with literal colors
- ❌ **Stacking**: literal `z-index` values

These are fine as they are, so don't flag or "fix" them:

- Keywords and resets: `0`, `auto`, `none`, `inherit`, `currentColor`, `transparent`, percentages
- Sizes with no token family, such as `width`, `max-width`, `height` and grid track sizes
- `@media` and `@container` queries. CSS custom properties don't work inside them, so write the pixel
  value and match an `--op-breakpoint-*` token (`small` is 768px, `medium` 1024px). Search
  `tokens.json` for the rest.

Common token mistakes:

- ❌ `var(--op_color_primary_base)`: underscore instead of hyphen
- ❌ `var(--color-primary-base)`: missing `--op-` prefix
- ❌ `var(--op-primary-color-base)`: wrong segment order

✅ `var(--op-color-primary-base)`

Fix violations by replacing them with tokens from `assets/tokens.json` or platform_ui's theme.

## Creating components

- Create the stylesheet beside the app's other stylesheets, named `{component-name}.scss`, and import it
  from the stylesheet that collects them (for example `app/assets/stylesheets/application.scss`).
- Define the base block with a semantic name, then nested elements, then modifiers. Use only tokens. One
  component per file unless tightly coupled.
- Optics ships `.card` and `.btn`, so use those rather than recreating them. platform_ui restyles both
  (`core/card.scss` and `core/buttons.css` in its stylesheets), so read those to see how they actually
  look before extending them.

An illustrative component built only from tokens:

```css
.callout {
  padding: var(--op-space-medium);
  border: var(--op-border-width) solid var(--op-color-border);
  border-radius: var(--op-radius-medium);
  background-color: var(--op-color-background);

  &.callout--elevated {
    box-shadow: var(--op-shadow-medium);
  }

  .callout__title {
    font-weight: var(--op-font-weight-medium);
  }
}
```

## Creating custom tokens

First make sure no existing token fits, including platform_ui's `--fd-*` tokens:

```bash
grep -rhoE -- '--fd-[a-z0-9-]+' "$(bundle info --path platform_ui)/app/stylesheets" app/assets/stylesheets | sort -u
```

When one is missing, create a project token rather than adding to core Optics:

- Use the `--fd-` prefix: `--fd-{category}-{name}`, for example `--fd-radius-dropdown` or
  `--fd-shadow-sheet-up`.
- Mirror the Optics categories: `--fd-color-*`, `--fd-space-*`, `--fd-font-*`, `--fd-radius-*`,
  `--fd-border-*`, `--fd-shadow-*`.
- Build the value from Optics tokens where you can (`--fd-focus-style` is made from `--op-border-all` and
  primary colors), so it still follows the theme.

## Before you finish

- [ ] Searched `components.json` and the project's stylesheets before creating anything
- [ ] Every color, spacing, border, shadow and z-index value is a token that exists in `tokens.json` or
      platform_ui's theme
- [ ] rem values were converted at 1rem = 10px
- [ ] Classes follow BEM (see `bem-context`), with at most 3 utilities per element, each one confirmed in
      the utility stylesheets
- [ ] New stylesheet is imported from the stylesheet that collects them
- [ ] Scanned the diff for hard-coded values
