---
name: testing-patterns
description: Writes and reviews Rails specs with RSpec, Capybara and FactoryBot, covering model, view component, integration and system specs, stubs and doubles, and time-dependent code. Use when implementing features, fixing bugs, writing, reviewing or fixing spec files, debugging a failing or flaky spec, or when the user mentions testing, specs, RSpec, Capybara, system specs, factories, mocks, stubs, WebMock, TDD or test data.
---

# Testing Patterns

Write automated specs. Don't use the Rails console or a running Rails server to test.

## Workflow

Write the failing spec first, and follow the project's TDD guidance (AGENTS.md).

1. Write the spec.
2. Run it and confirm it fails for the right reason.
3. Implement.
4. Re-run until it passes.

```bash
bundle exec rspec path/to/spec.rb
```

Run the specs you changed, never the whole suite without arguments. The project's AGENTS.md names its
parallel runner, if it has one.

## Given / When / Then

Separate setup, action and assertion in each `it` block with bare `# given`, `# when` and `# then`
comments. Put no prose after a marker: the "why" goes in the example's title or above the `it`.
Combine markers that share a line of code (`# when / then`).

```ruby
it 'returns the combined first and last name' do
  # given
  user = build(:user, first_name: 'John', last_name: 'Doe')

  # when / then
  expect(user.full_name).to eq('John Doe')
end
```

## Assertions per example

- **Unit specs**: one logical assertion per example (it may take more than one `expect`). Prefer several
  small `it` blocks over one that checks many things.
- **System and integration specs**: several logical assertions per example are fine, including sanity
  checks in `# given`, because they are expensive to run.
- The `it` description states the behavior the assertions check.

## Edge cases

Test the cases that are reachable through the public interface and that a reader would doubt:

- Nil/empty values a caller can actually pass
- Boundary conditions
- Invalid inputs the system does not reject earlier
- Error scenarios the code handles deliberately
- Authorization failures

A spec for a state the system cannot produce is an element to delete: it documents nothing and locks in
defensive code that should not exist.

## Test data

### FactoryBot

Use factories, never fixtures, and traits for variations. Use `build` for validation specs and `create`
only when you need a persisted record. Don't instantiate models directly.

Create only the data each example needs.

### `let` vs `let!`

Use `let` (lazy) when the variable is referenced in the example, or when you want to avoid unneeded
database writes.

Use `let!` (eager) when the record must exist before the example runs but the example never references
it: dropdown options, index pages, search results, or background data that other records depend on.

```ruby
RSpec.describe 'Job Management', type: :system do
  let!(:location) { create(:location, name: 'Downtown Site') } # must exist for the dropdown
  let(:job) { create(:job, name: 'Test Job', location:) }      # created when first referenced

  it 'shows location in dropdown' do
    # when
    visit new_job_path

    # then
    expect(page).to have_select('Location', with_options: [location.name])
  end

  it 'can delete a job' do
    # given
    visit job_path(job) # job is created here

    # when
    click_button 'Delete'

    # then
    expect(page).to have_no_content('Test Job')
  end
end
```

A lazy `let` that the example never references is never created:

```ruby
# ❌ Fails: neither job is referenced, so neither exists when the page loads
let(:job1) { create(:job, name: 'Job 1') }
let(:job2) { create(:job, name: 'Job 2') }

it 'lists all jobs' do
  visit jobs_path
  expect(page).to have_content('Job 1')
  expect(page).to have_content('Job 2')
end

# ✅ Both exist before the example runs
let!(:job1) { create(:job, name: 'Job 1') }
let!(:job2) { create(:job, name: 'Job 2') }
```

## Stubs, doubles and time

Stub only at the edge of the app: HTTP calls, third-party clients, and `Rails.error`. Don't stub the
object under test or the records it works with. Build real ones with factories, so the spec breaks when
their behavior changes.

- **HTTP**: stub with WebMock's `stub_request`. Real network calls are blocked in specs, so an unstubbed
  call fails rather than reaching the service.
- **Doubles**: use verifying doubles (`instance_double(Client)`, `class_double`) over plain `double`. They
  fail when the stubbed method doesn't exist or its arguments change, so a rename can't leave a passing
  spec behind.
- **Message assertions**: stub with `allow` in `# given` and check with `have_received` in `# then`,
  so the assertion sits with the others instead of before the action.
- **Time**: pin the clock with `travel_to` for code that reads the current date or time. A spec that depends on
  today's date passes now and fails at a month end, a weekend or a DST change. The setup is in
  [references/setup.md](references/setup.md).

```ruby
it 'reports a failed sync' do
  # given
  client = instance_double(Billing::Client)
  allow(client).to receive(:sync).and_raise(Billing::Client::Error)
  allow(Rails.error).to receive(:report)
  travel_to Time.zone.local(2026, 1, 31)

  # when
  SyncInvoices.new(client:).execute

  # then
  expect(Rails.error).to have_received(:report).with(instance_of(Billing::Client::Error), any_args)
end
```

## Validations

Use `build` to avoid database writes. Cover both an invalid and a valid case, check the exact messages
with `full_messages`, and name the example for the business rule. Don't test associations or enums.

```ruby
describe 'validations' do
  it 'must have a start date' do
    # given
    membership = build(:membership, start_date: nil)

    # when / then
    expect(membership).not_to be_valid
    expect(membership.errors.full_messages).to contain_exactly "Start date can't be blank"
  end

  it 'permits empty end date' do
    # given
    membership = build(:membership, start_date: 1.year.ago, end_date: nil)

    # when / then
    expect(membership).to be_valid
  end
end
```

## View component specs

Leave the top-level `describe` bare and split the examples into two second-level groups, each carrying
the metadata it needs:

- `context 'rendering', type: :component` renders the component in isolation with `render_inline` and
  checks `page` with Capybara matchers. Fast; no browser.
- `context 'behavior', :preview` drives the component's ViewComponent preview in a browser with
  `visit_preview`, for anything that needs JavaScript (Stimulus, Turbo, Shoelace).

A component with no JavaScript has only `rendering`. In `rendering`, `within` only scopes `page` when
the project has a component scoping helper; without one it silently skips the block. The `:component`
and `:preview` setup is in [references/setup.md](references/setup.md).

```ruby
RSpec.describe CreateAdUnitForm do
  let(:property) { create(:property) }

  context 'rendering', type: :component do
    it 'names the property' do
      # when
      render_inline(described_class.new(property:))

      # then
      expect(page).to have_content property.name
    end
  end

  context 'behavior', :preview do
    it 'shows the size inputs when a size-constrained sku is selected' do
      # given
      visit_preview(CreateAdUnitFormPreview, property_id: property.id)

      # when
      select 'Banner', from: 'SKU'

      # then
      expect(page).to have_field('Width')
    end
  end
end
```

## Capybara system specs

- Test user-facing functionality: happy paths and edge cases. Keep specs deterministic.
- No `sleep`. Use Capybara's waiting matchers and finders.
- Tag specs that run JavaScript (Stimulus controllers, Turbo) with `:js`: `it 'does something', :js do`.
- For an action that opens a confirm dialog (platform_ui's `ConfirmedDeleteButton`, or any
  `turbo_confirm`), click the trigger, then call `accept_confirmation` with the accept button's text
  (`'Yes, delete'` by default). Pass a block to assert on the dialog while it is open, and use
  `within_confirmation` to cancel it. Don't click the dialog's buttons directly: its accept button is
  swapped in after it opens, so a bare click can land on the previous confirmation's button. Both need
  `:js`. If the helper is missing, see [references/setup.md](references/setup.md).

```ruby
it 'deletes the comment', :js do
  # given
  visit ad_path(ad)

  # when
  click_on 'Delete'
  accept_confirmation do
    expect(page).to have_content('Are you sure you want to delete this comment?')
  end

  # then
  expect(page).to have_no_content(comment.body)
end
```

### Finding elements

Find elements the way a user does: by label, button or link text, or visible content. Text lookups read
like the user's steps and break only when what the user sees changes.

When text can't identify the element, fall back to a `data-testid`, built with `dom_id` for records:
rows or cards that share their button text, icon-only buttons, or a container to scope into.

Avoid CSS selectors (class names, ids, tag paths, `input[name=...]`). They tie the spec to markup and
styling that change without the behavior changing. This includes platform_ui's markup: find its
components by text or test id, never by class name.

With `Capybara.test_id = 'data-testid'` configured, finders (`click_on`, `click_button`, `fill_in`,
`find_field`, `find_button`, ...) match a test id as well as text: pass the raw id
(`click_on 'save_button'`). Use the `data_test(name)` helper (returns `"[data-testid='name']"`) only where
a selector is needed (`within`, `find`), and never hand-write `[data-testid='...']`. Existing specs often
hand-write it, so don't copy them on this point.

```slim
tbody
  - @entries.each do |entry|
    tr data-testid=dom_id(entry)
      td= entry.name
      td= button_tag 'Delete'
```

```ruby
# Text first
fill_in 'Amount', with: '100'
click_button 'Save'

# Every row has a Delete button, so scope into the row by test id
within(data_test(dom_id(entry))) do
  click_button 'Delete'
end
```

### Named Capybara matchers

Prefer named matchers (`have_field`, `have_button`, `have_link`, `have_select`, `have_checked_field`,
`have_table`) over `have_css`/`have_selector`: they state intent rather than markup.

```ruby
# preferred
expect(page).to have_field('Amount')

# avoid
expect(page).to have_selector('input[name="campaign_memo[amount]"]')
```

Reach for `have_css` only when no named matcher fits: a test id lookup (through `data_test`), the value
attribute of a `<select>` option, or a structural attribute with no semantic role.

### Scoping with `within`

Use `within` when several elements share the same text or label, when interacting with modals, panels or
overlays, with repeating elements (table rows, cards), or when a spec fails with "Ambiguous match".

## Reviewing a spec

```
- [ ] Each example has bare `# given` / `# when` / `# then` markers
- [ ] Unit examples check one behavior, and each title states it
- [ ] `let!` for records the example needs but never references; no unused `let`
- [ ] Factories and traits, no fixtures or `Model.new`; `build` where persistence isn't needed
- [ ] No specs for associations, enums, or states the system can't produce
- [ ] Edge cases a reader would doubt are covered
- [ ] Elements found by text first, then test id; no CSS selectors or hand-written `[data-testid=...]`
- [ ] Named matchers over `have_css`
- [ ] No `sleep`; `:js` on every example that needs JavaScript
- [ ] Confirm dialogs go through `accept_confirmation` / `within_confirmation`
- [ ] HTTP stubbed with WebMock; verifying doubles only; nothing stubbed on the object under test
- [ ] Code that reads the current time runs under `travel_to`
```
