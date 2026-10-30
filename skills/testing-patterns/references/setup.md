# One-time spec support setup

Support code that the `testing-patterns` skill assumes exists. Add each file only if the project lacks it.

## Contents

- Test ids
- View component specs
- ViewComponent preview specs
- Confirm dialogs
- Time helpers

## Test ids

Let Capybara's finders match `data-testid`, and add the `data_test` helper for the places that need a
selector:

```ruby
# spec/support/capybara_testid.rb
Capybara.configure do |config|
  config.test_id = 'data-testid'
end

# spec/support/helpers/test_element_helper.rb
module TestElementHelper
  def data_test(name)
    "[data-testid='#{name}']"
  end
end
```

```ruby
# spec/support/helpers.rb
RSpec.configure do |c|
  c.include TestElementHelper, type: :component
  c.include TestElementHelper, type: :system
end
```

## View component specs

`type: :component` groups need ViewComponent's helpers and Capybara's matchers:

```ruby
# spec/rails_helper.rb, inside RSpec.configure
config.include ViewComponent::TestHelpers, type: :component
config.include ViewComponent::SystemTestHelpers, type: :component
config.include Capybara::RSpecMatchers, type: :component
config.include ComponentScopingHelper, type: :component
```

In a component spec `page` is a `Capybara::Node::Simple` built from the rendered HTML, not a session, so
there is no session-level `within`. A bare `within` resolves to RSpec's `within` (an alias of
`be_within`), which discards the block, so every assertion inside it silently never runs. This helper
gives component specs a real `within`:

```ruby
# spec/support/helpers/component_scoping_helper.rb
module ComponentScopingHelper
  def within(locator, **opts)
    previous = @page
    @page = (previous || page).find(locator, **opts)
    yield
  ensure
    @page = previous
  end
end
```

## ViewComponent preview specs

`:preview` makes the group a JavaScript system spec and includes the preview helper:

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

If previews need authentication, sign a user in for `:preview` groups.

## Confirm dialogs

platform_ui renders one shared confirm dialog (`PlatformUi::ConfirmedDeleteButton` renders
`platform_ui/shared/_confirm`), and `@rolemodel/turbo-confirm` swaps each confirmation's accept button
into `#confirm--accept-btn` before showing it. Two details make an unscoped `click_on 'Yes, delete'`
unreliable:

1. The `dialog--active` class is added only after the accept button has been swapped in and its listener
   bound. Scoping to it guarantees the click hits the confirmation just opened, not the previous one.
2. 300ms after a confirmation resolves, the dialog's content is restored, which rewrites its HTML. A
   confirmation opened in that window is overwritten: the click is swallowed or raises
   `StaleElementReferenceError`. Waiting for the restored `Confirm` button proves the restore has run.

The helper targets the dialog's own markup because it is platform_ui's internals, not the app's. Specs
call the helper instead of repeating these selectors.

```ruby
# spec/support/helpers/confirmation_helper.rb
module ConfirmationHelper
  def accept_confirmation(button_text = 'Yes, delete')
    # Find the dialog and click in one synchronize block: accepting often triggers a Turbo Stream that
    # re-renders the dialog, so a scope resolved before that would leave the button stale.
    page.document.synchronize do
      dialog = page.document.find('.dialog--confirm.dialog--active')
      yield if block_given?
      dialog.find_button(button_text).click
    end
    await_restored_confirm_dialog
  end

  # For examples that assert on the dialog, or cancel it, without accepting.
  def within_confirmation(&)
    within('.dialog--confirm.dialog--active', &)
  end

  def await_restored_confirm_dialog
    expect(page).to have_css('#confirm--accept-btn', text: 'Confirm', visible: :all)
  end
end
```

```ruby
# spec/support/helpers.rb
RSpec.configure do |c|
  c.include ConfirmationHelper, type: :system
end
```

Usage, with the `:js` tag:

```ruby
click_on 'Delete'
accept_confirmation

click_on 'Deactivate'
accept_confirmation('Yes, deactivate user') do
  expect(page).to have_content('Are you sure you want to deactivate Jane Doe?')
end

click_on 'Delete'
within_confirmation { click_on 'Cancel' }
```

## Time helpers

`travel_to` and `freeze_time` come from ActiveSupport. Rails resets the clock after each example.

```ruby
# spec/rails_helper.rb, inside RSpec.configure
config.include ActiveSupport::Testing::TimeHelpers
```
