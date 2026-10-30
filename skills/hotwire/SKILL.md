---
name: hotwire
description: Writes Stimulus controllers, Turbo Frames and Streams, and ActionCable broadcasts, favoring progressive enhancement of server-rendered HTML. Use when writing or modifying Stimulus controllers, adding Turbo Frames or Streams, wiring up real-time or live updates, opening content in a modal or drawer, adding a confirmation dialog, or lazy-loading part of a page, or when the user mentions Hotwire, Stimulus, Turbo, data-controller, data-action, broadcasts, or making a page update without a full reload.
---

# Hotwire

Hotwire enhances server-rendered HTML with just enough JavaScript.

Shared Stimulus controllers live in the platform_ui gem at `app/javascript/platform_ui/<tier>/controllers`
(find the gem with `bundle info --path platform_ui`) and are registered in that tier's `index.js`.
JavaScript for a view component is co-located with the component.

## Choosing the mechanism

Take the first one that works:

1. Plain server-rendered HTML and links or forms.
2. A Turbo Frame, to update one region of the page.
3. A Turbo Stream, to change several regions or respond to a form submission. Broadcast it for real-time
   updates.
4. Something that already exists: a platform_ui view component, a Shoelace element (dropdowns, drawers,
   dialogs, tabs) or a controller already registered from a Stimulus library. Check each tier's
   `index.js` for what is registered, and use the identifier passed to `application.register`, which may
   not match the file name.
5. A new Stimulus controller, for behavior that has no server round trip and nothing above covers.

## Adding a Stimulus controller

Copy this checklist and check items off:

```
- [ ] File is in the right place (platform_ui tier controllers, or next to its view component)
- [ ] Registered: a shared controller in its tier's `index.js`, an app controller where the app registers its others
- [ ] data-controller, targets, values and actions wired in the Slim template
- [ ] Spec: a `:js` system spec, or a `behavior` preview spec for a component (see testing-patterns)
```

```javascript
// app/view_components/character_count/character_count.js
import { Controller } from '@hotwired/stimulus'

export default class extends Controller {
  static targets = ['input', 'count']
  static classes = ['over']
  static values = { max: Number }

  connect() {
    this.update()
  }

  update() {
    const remaining = this.maxValue - this.inputTarget.value.length
    this.countTarget.textContent = remaining
    this.countTarget.classList.toggle(this.overClass, remaining < 0)
  }
}
```

```slim
.character-count data-controller="character-count" data-character-count-max-value="280" data-character-count-over-class="character-count__count--over"
  textarea.character-count__input data-character-count-target="input" data-action="input->character-count#update"
  span.character-count__count data-character-count-target="count"
```

## Turbo Frames

```slim
= turbo_frame_tag "posts" do
  - @posts.each do |post|
    = turbo_frame_tag dom_id(post) do
      = render post
= render PlatformUi::TurboFrame.new(id: 'pagination', src: posts_path(page: @page + 1))
```

`PlatformUi::TurboFrame` lazy-loads `src` behind a loading spinner and marks the frame
`data-turbo-temporary`, so a stale copy isn't restored from Turbo's cache. Given a block, it renders that
content instead. Turbo keeps only the matching frame from the response, so the next page must render its
posts, and the following `pagination` frame, inside a frame with the id `pagination`.

### Modals and drawers

Link with `modal_link_to` or `drawer_link_to` (same arguments as `link_to`). They target the page's
`remote_modal` and `remote_drawer` frames. The response renders `PlatformUi::TurboModal` or
`PlatformUi::TurboDrawer`, which wraps itself in that frame. Its controller opens it on connect and empties
the frame when it closes:

```slim
= modal_link_to 'Edit', edit_post_path(post)
```

```slim
/ edit.html.slim
= render PlatformUi::TurboModal.new(label: 'Edit post', body: render(PostForm.new(post: @post)), footer: nil)
```

Close it from the server, not with custom JS: return
`turbo_stream.hide_shoelace_component(PlatformUi::TurboModal::DOM_ID)` (or `TurboDrawer::DOM_ID`) from a
stream response, or call `PlatformUi::TurboModal.broadcast_hide_to(stream_id)` from a broadcast. To stop
Esc or an overlay click from closing a modal, pass `data: { turbo_modal_explicit_close_value: true }`.

## Turbo Stream responses

Render streams from view components. A component that includes `PlatformUi::TurboStreamable` and defines
`dom_id` builds its own stream with `replace`, `update`, `append` or `remove`, each taking `view_context`.
Report success and failure with `PlatformUi::AlertComponent`, which streams into the page's alert container:

```ruby
def update
  @post = Post.find(params[:id])

  if @post.update(post_params)
    render turbo_stream: [
      PostRow.new(post: @post).replace(view_context),
      PlatformUi::AlertComponent.notice('Post updated.').append(view_context),
      turbo_stream.hide_shoelace_component(PlatformUi::TurboModal::DOM_ID)
    ]
  else
    render turbo_stream: PlatformUi::AlertComponent.danger(@post.errors.full_messages.to_sentence)
                                                   .append(view_context),
           status: :unprocessable_content
  end
end
```

```ruby
class PostRow < PlatformUi::BaseComponent
  include PlatformUi::TurboStreamable

  attr_reader :post

  def initialize(post:)
    super()
    @post = post
  end

  def dom_id
    "post_#{post.id}"
  end
end
```

platform_ui's core tier adds custom stream actions (`Turbo.StreamActions`), such as
`hide_shoelace_component` and `show_shoelace_component`. Check there before writing JS that runs after a
stream.

## Confirmations

Use platform_ui's confirm dialog through data attributes, not `window.confirm` or a new controller. For a
delete, render `PlatformUi::ConfirmedDeleteButton.new(delete_path:, delete_message:, resource_name:)`.
Otherwise set `turbo_confirm` plus any of `confirm_title`, `confirm_message`, `confirm_accept` (HTML for
the accept button) and `confirm_deny` (the cancel label):

```slim
= link_to 'Archive', archive_post_path(post),
  data: { turbo_method: :patch, turbo_confirm: true, confirm_title: 'Archive post?',
          confirm_message: "#{post.title} will be hidden from readers.",
          confirm_accept: tag.button('Archive', class: 'btn btn--small btn--primary') }
```

## Broadcasts

A broadcast reaches only pages that subscribe, so pair the model callbacks with `turbo_stream_from` in the
view. Prefer the `_later` variants, which broadcast from a job. `broadcast_remove_to` has no `_later`
variant, and doesn't need one:

```ruby
class Post < ApplicationRecord
  after_create_commit { broadcast_prepend_later_to "posts" }
  after_update_commit { broadcast_replace_later_to "posts" }
  after_destroy_commit { broadcast_remove_to "posts" }
end
```

```slim
= turbo_stream_from "posts"
```

To broadcast a view component, include `PlatformUi::TurboBroadcastable` and call
`component.broadcast_replace_to(stream_id)` (or `broadcast_append_to`, `broadcast_update_to`,
`broadcast_remove_to`), which targets the component's `dom_id`.
