---
name: bem-context
description: Names and structures CSS with BEM (Block Element Modifier) on top of the Optics design system. Use when naming CSS classes, writing, reviewing or refactoring stylesheets, fixing BEM structure, or adding classes in Slim templates.
---

# BEM

Write CSS with BEM so stylesheets stay maintainable and reusable. Use BEM alongside Optics, the RoleModel
design system, and don't recreate what Optics already provides. Before creating a new block, use the
`optics-context` skill to check for an existing component.

Prioritize clarity, predictability and minimal unintended side effects. If project constraints stop you
following these rules, say why in the chat output.

## Syntax

| Pattern | Syntax | Example |
|---------|--------|---------|
| **Block** | `.block` | `.card` |
| **Element** | `.block__element` | `.card__title` |
| **Block modifier** | `.block--modifier` | `.card--elevated` |
| **Element modifier** | `.block__element--modifier` | `.card__title--large` |
| **Multi-word names** | kebab-case | `.user-profile` |

## Rules

### Naming

- Class names are fully explicit BEM and flat: `block__element`, never `block__element__subelement`.
- Block, element and modifier names use lowercase letters, digits and dashes, modifiers included
  (`block--size-big`, not `block--size_big`). Don't use element syntax for a block (`.dropdown__menu` is
  an element, not a block).
- `__` separates block from element. `--` separates a block or element from its modifier.
- Names say what something is for, not how it looks. Modifiers are the exception (`small`, `large`,
  `padded`). Aim for the shared type of workflow (`form`, `table`, `card`, `button`) and avoid
  abbreviations that aren't universally understood.

### Selectors and nesting

- Classes only: no IDs, no tag selectors, no styling by DOM hierarchy beyond nesting an element under its
  block. The exception is third-party web components such as Shoelace, which can only be styled through
  their tag and parts (`sl-drawer::part(panel)`). Scope those inside a block where you can.
- In the stylesheet, nest elements and modifiers inside their block. Nesting is for organization, and the
  DOM structure doesn't need to match it.
- Use `&` only as a reference to the full selector: modifiers (`&.block--modifier`), pseudo-classes
  (`&:hover`, `&:focus-visible`, `&:disabled`) and attributes (`&[aria-expanded="true"]`). Never use it to
  build a class name (`&--modifier`, `&__element`).
- An element never exists outside its block. Blocks may contain other blocks. Give each block one
  conceptual responsibility.

### Modifiers and state

- A modifier is always used with its base class: `class="card card--elevated"`.
- Prefer a modifier over a new element for a simple state or appearance change that adds no new content.
  Put the default styles on the base class and let the modifier override them. Don't create two
  modifiers for a default and its variant.
- When the markup already carries the state, style that instead of adding a modifier: `&:disabled`,
  `&[aria-expanded="true"]`, `&[aria-current="page"]`. Use a modifier for states with no native or ARIA
  equivalent.

## Good and bad

✅ GOOD

```css
.block {
  .block__element {
    &.block__element--modifier { }
    &:hover { }
  }

  &.block--modifier { }
  &[aria-expanded="true"] { }
}
```

```html
<div class="block block--modifier">
  <div class="block__element">...</div>
  <div class="block__element block__element--modifier">...</div>
</div>
```

```slim
form.form.form--simple
  input.form__input type="text"
  input.form__submit.form__submit--disabled type="submit"
```

🚫 BAD

```css
.block {
  .block--modifier { }          /* use `&` before every modifier */
  &--featured { }               /* never build a class name with `&` */
  .block__element__sub { }      /* no element of an element */
}

.block_element { }              /* use `__`, and nest the element in its block */
.block__element-modifier { }    /* use `--` before the modifier */
```

```html
<div class="block__element">...</div>              <!-- element without its block -->
<div class="block__element--modifier">...</div>    <!-- modifier without its element -->
<div class="block--modifier">...</div>             <!-- modifier without its base class -->
```

## Modifier instead of a second element

Don't create an exclusive element for a variant. Add the default to the base element and override it
with a modifier:

```css
.product-card {
  .product-card__image {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;

    &.product-card__image--placeholder {
      object-fit: unset;
      display: flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, var(--op-color-neutral-plus-six) 0%, var(--op-color-neutral-plus-seven) 100%);
    }
  }
}
```

## Reviewing or refactoring CSS

- [ ] Before renaming a class, search `app/`, `spec/` and `app/javascript/` for every use of it, and
      update them all. Capybara selectors in system specs, Stimulus controllers and ViewComponent
      templates break silently when a class disappears.
- [ ] Check Optics first (`optics-context`) for an existing component
- [ ] Every class is explicit, flat BEM, in kebab-case
- [ ] Every modifier appears with its base class in the markup
- [ ] Variants use a modifier on the base class, not a separate element
- [ ] Names describe purpose, not appearance (modifiers excepted)
- [ ] Elements and modifiers are nested in their block, with `&` only as a reference to the full selector
- [ ] No IDs, tag selectors or DOM-hierarchy selectors, except for third-party web components
- [ ] Any deviation from these rules is explained in the chat output
