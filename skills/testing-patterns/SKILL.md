---
name: testing-patterns
description: Write automated tests using RSpec, Capybara, FactoryBot and shoulda-matchers for Rails applications — unit, view component, integration and system specs. Use when implementing features, fixing bugs, writing or reviewing spec files, or when the user mentions testing, specs, RSpec, Capybara, factories, TDD, or test data. Avoid using rails console or server for testing.
---

# Testing Patterns

## Overview
Write automated tests using RSpec and Capybara. Avoid using the Rails console or starting a Rails server for testing.

## Test Command
```bash
bundle exec rspec path/to/spec.rb
```

Run the specs you changed, never the whole suite without arguments. The project's AGENTS.md names its
parallel runner, if it has one.

## Tech Stack
- **RSpec** - Testing framework
- **Capybara** - System/integration testing
- **FactoryBot** - Test data generation
- **shoulda-matchers** - One-line validation and association matchers

## Best Practices

### General Guidelines
- Write the failing test first, and follow the project's TDD guidance (AGENTS.md)
- Avoid manual testing via console
- Use factories for test data creation
- Keep tests focused and readable

### RSpec Conventions
- Use descriptive context and describe blocks
- Use let for test data setup
- Prefer `let` over instance variables

### Given / When / Then
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

### Assertions per Example
- **Unit tests**: one logical assertion per example (it may take more than one `expect`). Prefer several
  small `it` blocks over one that checks many things.
- **System and integration tests**: several logical assertions per example are fine, including sanity
  checks in `# given`; they are expensive to run.
- The `it` description states the behavior the assertions check.

### Edge Cases
Test the cases that are reachable through the public interface and that a reader would doubt:

- Nil/empty values a caller can actually pass
- Boundary conditions
- Invalid inputs the system does not reject earlier
- Error scenarios the code handles deliberately
- Authorization failures

A test for a state the system cannot produce is an element to delete: it documents nothing and
locks in defensive code that should not exist.

### let vs let! (Lazy vs Eager Evaluation)

**Use `let` (lazy evaluation) when:**
- The variable is explicitly referenced in the test
- You want to avoid unnecessary database writes
- The record creation has side effects you want to control

**Use `let!` (eager evaluation) when:**
- Records must exist in the database before the test runs
- The variable is not directly referenced but its existence is required
- Testing queries that search for records (e.g., index pages, search functionality)
- Setting up background data that other records depend on

**Example - System Tests:**
```ruby
RSpec.describe 'Job Management', type: :system do
  # Use let! - these records must exist in DB for dropdowns and queries
  let!(:location) { create(:location, name: 'Downtown Site') }
  let!(:superintendent) { create(:user, :superintendent) }

  # Use let - only created when explicitly referenced in a test
  let(:job) { create(:job, name: 'Test Job', location:, superintendent:) }

  it 'shows location in dropdown' do
    visit new_job_path
    # location must exist in DB for dropdown to display it
    expect(page).to have_select('Location', with_options: [location.name])
  end

  it 'can delete a job' do
    visit job_path(job)  # job created here when first referenced
    click_button 'Delete'
  end
end
```

**Common Pitfall:**
```ruby
# ❌ WRONG - Test will fail because job2 doesn't exist in DB yet
let(:job1) { create(:job, name: 'Job 1') }
let(:job2) { create(:job, name: 'Job 2') }

it 'lists all jobs' do
  visit jobs_path
  expect(page).to have_content('Job 1')  # job1 created when referenced
  expect(page).to have_content('Job 2')  # FAIL - job2 never referenced, not in DB
end

# ✅ CORRECT - Both jobs exist before test runs
let!(:job1) { create(:job, name: 'Job 1') }
let!(:job2) { create(:job, name: 'Job 2') }

it 'lists all jobs' do
  visit jobs_path
  expect(page).to have_content('Job 1')  # Both jobs already in DB
  expect(page).to have_content('Job 2')  # Test passes
end
```

**Key Insight:**
If you expect to see data without explicitly interacting with the object variable (like viewing a list or selecting from a dropdown), use `let!` to ensure the record exists in the database.

### Validation Testing Pattern
Test validations explicitly using `build` with invalid data, then verify the model is invalid and check error messages:

```ruby
describe 'validations' do
  it 'must have a start date' do
    # given
    membership = build(:membership, start_date: nil)

    # when / then
    expect(membership).not_to be_valid
    expect(membership.errors.full_messages).to contain_exactly "Start date can't be blank"
  end

  it 'enforces end date must follow start date' do
    # given
    membership = build(:membership, start_date: 1.year.ago, end_date: 2.years.ago)

    # when / then
    expect(membership).not_to be_valid
    expect(membership.errors.full_messages).to contain_exactly 'End date must follow start date'
  end

  it 'permits empty end date' do
    # given
    membership = build(:membership, start_date: 1.year.ago, end_date: nil)

    # when / then
    expect(membership).to be_valid
  end
end
```

Key points:
- Use `build` instead of `create` to avoid database writes
- Test both invalid and valid scenarios
- Verify exact error messages with `full_messages`
- Use descriptive test names that explain the business rule
- Don't test associations or enums

### View Component Specs
Leave the top-level `describe` bare and split the examples into two second-level groups, each carrying
the metadata it needs:

- `context 'rendering', type: :component` renders the component in isolation with `render_inline` and
  checks `page` with Capybara matchers. Fast; no browser.
- `context 'behavior', :preview` drives the component's ViewComponent preview in a browser with
  `visit_preview`, for anything that needs JavaScript (Stimulus, Turbo, Shoelace).

A component with no JavaScript has only `rendering`.

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

**Setup:** `:preview` makes the group a JavaScript system spec, includes the preview helper and signs a
user in when previews need authentication:

```ruby
# spec/support/view_component_previews.rb
RSpec.configure do |config|
  config.define_derived_metadata(:preview) do |metadata|
    metadata[:type] = :system
    metadata[:js] = true
  end

  config.include PreviewHelper, :preview
end

# spec/support/helpers/preview_helper.rb
module PreviewHelper
  def visit_preview(preview_class, scenario = :default, **params)
    path = "/rails/view_components/#{preview_class.preview_name}/#{scenario}"
    visit(params.any? ? "#{path}?#{params.to_query}" : path)
  end
end
```

### Capybara System Tests
- Test user-facing functionality
- Use `data-testid` attributes with `dom_id` for reliable element selection
- Test happy paths and edge cases
- Ensure tests are deterministic
- Avoid sleep statements; use Capybara's waiting mechanisms such as native expectations of elements to appear
- Use `:js` (e.g. `it 'does something', :js do`) for specs that run javascript such as stimulus controllers

### Element Selection with data-testid
Use `data-testid` attributes with `dom_id` for stable, reliable element selection that's resistant to UI changes.
Find platform_ui's markup by its test ids too, never by its class names.

With `Capybara.test_id = 'data-testid'` configured, finders (`click_on`, `click_button`, `find`, `fill_in`, ...)
match a `data-testid` directly: pass the raw id (`click_on 'save_button'`). Use the `data_test(name)` helper
(returns `"[data-testid='name']"`) only where a CSS selector is needed, and never hand-write
`[data-testid='...']` in a spec.

**View:**
```slim
tbody
  - @entries.each do |entry|
    tr data-testid=dom_id(entry)
      td= entry.name
```

**Spec:**
```ruby
within(data_test(entry1)) do
  click_button 'Submit'
end
```

**Benefits:**
- Resilient to text changes (descriptions, labels, etc.)
- Works with dynamic content
- Self-documenting test intent
- Easier to refactor views

**Avoid:**
- Text-based lookups: `within('tr', text: 'Entry 1')`
- CSS class selectors that may change during styling
- Overly specific DOM traversal

### Named Capybara Matchers
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

### Scoping with within Blocks
When elements are ambiguous (multiple buttons/links with same text), use `within` blocks to scope interactions:

**Best Practice:**
Always use `within` blocks when:
1. Multiple elements share the same text/label
2. Interacting with modals, panels, or overlays
3. Working with repeating elements (table rows, cards)
4. Tests fail with "Ambiguous match" errors

### Turbo Confirm Dialogs
When testing actions that trigger Turbo confirm dialogs (e.g., delete buttons with `data: { turbo_confirm: 'message' }`), use the provided helper methods.

**Setup:**

Create the helper file:
```ruby
# spec/support/turbo_confirm_helper.rb
module TurboConfirmHelper
  def accept_turbo_confirm
    yield
    expect(page).to have_css '.confirm-dialog-wrapper--active', wait: 5
    sleep(0.5)
    within '.confirm-dialog-wrapper--active' do
      find('#confirm-accept').click
    end
    expect(page).to_not have_css '.confirm-dialog-wrapper--active', wait: 5
  end

  def deny_turbo_confirm
    yield
    expect(page).to have_css '.confirm-dialog-wrapper--active', wait: 5
    sleep(0.5)
    within '.confirm-dialog-wrapper--active' do
      find('#confirm-cancel').click
    end
    expect(page).to_not have_css '.confirm-dialog-wrapper--active', wait: 5
  end
end
```

Include in RSpec configuration:
```ruby
# spec/support/helpers.rb
RSpec.configure do |c|
  # ...existing code...
  c.include TurboConfirmHelper, type: :system
end
```

**Usage in Tests:**
```ruby
accept_turbo_confirm do
  click_button 'Delete'
end

deny_turbo_confirm do
  click_button 'Delete'
end
```

**Key Points:**
- Always use `:js` tag for tests involving Turbo confirm dialogs
- Pass the action that triggers the confirm as a block to the helper
- The helper automatically waits for the dialog to appear and disappear
- Use `accept_turbo_confirm` to click "Yes, I'm Sure"
- Use `deny_turbo_confirm` to click "Cancel"
- Helpers include proper wait times and scoping for reliability

### FactoryBot
- Use factories, never fixtures
- Define factories for all models
- Use traits for variations
- Keep factories minimal
- Override attributes in tests as needed
- Always use `build` or `create` instead of direct model instantiation
- Use `build` for validation tests to avoid database writes
- Use `create` when you need persisted records

### Speed
- Create only the data each example needs
- Stub external services (WebMock); never call them from specs
- Profile slow examples and fix them

## Future Topics
- Mocking and stubbing patterns
- Test organization strategies
- CI/CD integration
