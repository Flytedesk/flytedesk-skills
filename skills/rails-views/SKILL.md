---
name: rails-views
description: Frontend specialist for SLIM templates, ViewComponents, simple_form, and CSS. Use when working on views, layouts, view components (including naming them), forms, or UI styling — even for requests like "add a button" or "style this".
---

# Rails Views Specialist

Build views with SLIM, ViewComponents (https://viewcomponent.org), Turbo and Stimulus. Keep logic out of
templates and use off-the-shelf Hotwire behavior wherever possible. Chrome is the only supported browser,
so check CSS-only changes in Chrome rather than relying on specs.

## Template Organization

- View components live in `app/view_components`, inherit `PlatformUi::BaseComponent`, and take
  keyword-arg constructors exposed through `attr_reader`.
- A component with no real markup structure can skip the template and implement `call` with `tag` helpers
  (no `.slim` file)
- Use `renders_one` / `renders_many` slots for content the caller supplies, rather than passing HTML
  strings or booleans that switch markup
- View components never fetch data: resolve it in the controller and pass it through constructor args
- `platform_ui` components come from the platform_ui gem (Flytedesk/platform_ui); a component any Flytedesk app could use belongs there, one tied to an app's pages or data stays in the app
- Forms use simple_form
- Semantic HTML, with ARIA state set from component methods: `nav` gets an `aria-label`, the active tab
  gets `aria-current: 'page'`, icon-only buttons get a label. Interactive elements are keyboard reachable
- Give interactive elements a `data-testid` (components accept `test_id:`) so system specs can find them
- Images use `loading: 'lazy'` when they are below the fold
- **Never put conditionals in SLIM templates.** Every conditional lives in the view component's Ruby class:
  - Value choices (attributes, labels, text): a component method with an intention-revealing name
    that returns the value.
  - Whether markup renders: a `render_<thing>` method that returns nil when it shouldn't render (a guard
    clause, then `tag.*` or `render`); the template calls it unconditionally. Use `render?` only to
    suppress the whole component. Extract a new component only when the markup is large or reused.
  - Which markup variant renders: a `render_<thing>` method that picks the component to render.
  - `class_names` is allowed in SLIM for toggling CSS classes (see below).

```slim
/ Avoid
span = booked? ? 'Booked' : 'Pending'
- if show_badge?
  = render Badge.new(label:)

/ Prefer
span = status_label
= render_badge
```

```ruby
def status_label
  booked? ? 'Booked' : 'Pending'
end

def render_badge
  return unless show_badge?

  render Badge.new(label:)
end
```

## Conditional CSS classes with `class_names`

Use `class_names` (Rails' `token_list`) for conditional classes instead of ternaries or interpolation.
It works the same in a template and in a component method, and drops `nil`/`false` entries:

```slim
/ Avoid
a class=(active? ? 'tab tab--active' : 'tab') href=path
a class="tab #{'tab--active' if active?}" href=path

/ Prefer
a class=class_names('tab', classes, 'tab--active': active?) href=path
```

- Pass a predicate method (`active?`) as the hash value, never an inline expression. If the condition
  needs more than one term, give it a named method in the component.
- Use BEM modifiers for the conditional keys (`tab--active`), never state words like `active` alone.
  Class naming rules live in the `bem-context` skill.
- With more than two conditionals, move the call into a component method (`tab_class`) and use
  `a class=tab_class`.

## Naming View Components

**Name a component for the visible artifact it renders, not for the domain concept behind it.**
The last word is the artifact (`Button`, `Banner`, `Badge`, `Card`, `Modal`, `Drawer`, `Panel`, `Section`,
`Form`, `Field`, `Table`, `Row`, `Menu`, `Icon`, and so on). Turbo-frame wrappers are the one
non-visible exception and end in `Frame`. Domain words go in front, qualifying *which* one:

```ruby
VoidBillingStatementButton      # a button
ApproveOnBehalfOfSupplierModal  # a modal
ReportedIssueBanner             # a banner
CampaignMemoDrawer              # a drawer
```

Avoid:

- **A bare domain concept.** `BillingStatement`, `CreditPoolDetails` read as models or presenters.
- **`...Component`.** `BillingStatementComponent` — every class here is a component, so the suffix
  says nothing. Say what it renders instead.
- **Vague collective nouns.** `Actions`, `Details`, `Elements` — name the artifact the group
  actually is (`ReviewActionButtons`).

The test: "could I point at that on the screen?" If not, rename it. A namespace directory may be a
domain word (`billing/`); the classes inside it still name artifacts. Existing components such as
`AlertComponent` and `TableComponent` predate this rule; don't rename them unprompted.

## Related Skills

- CSS: `bem-context` and `optics-context` (Shoelace web components for UI primitives such as drawers, tabs, dropdowns)
- Stimulus, Turbo frames and streams: `hotwire`
- View component specs (`render_inline`): `testing-patterns`
