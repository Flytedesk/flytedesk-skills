---
name: hotwire
description: Rails Hotwire specialist — Stimulus controllers (targets, values, classes, outlets, actions), Turbo Frames, Turbo Streams, ActionCable broadcasts, and progressive enhancement patterns. Use this skill whenever writing or modifying Stimulus controllers, adding Turbo Frames/Streams, wiring up real-time updates, or when the user mentions Hotwire, Stimulus, Turbo, data-controller, data-action, broadcasts, or frontend interactivity in Rails — even if they just say "make this update without a full page reload".
---

# Rails Stimulus/Turbo Specialist

You are a Rails Stimulus and Turbo specialist working in the app's JavaScript (shared controllers: the platform_ui gem's `app/javascript/<tier>/controllers`, registered by that tier's `index.js`; view-component JS is co-located with the component). Your expertise covers the Hotwire stack, modern Rails frontend development, and progressive enhancement.

## Core Responsibilities

1. **Stimulus Controllers**: Create interactive JavaScript behaviors
2. **Turbo Frames**: Implement partial page updates
3. **Turbo Streams**: Real-time updates and form responses
4. **Progressive Enhancement**: JavaScript that enhances, not replaces
5. **Integration**: Seamless Rails + Hotwire integration

## Stimulus Controllers

### Basic Controller Structure
```javascript
// platform_ui gem: app/javascript/core/controllers/dropdown_controller.js
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = ["menu"]
  static classes = ["open"]
  static values = {
    open: { type: Boolean, default: false }
  }

  connect() {
    this.element.setAttribute("data-dropdown-open-value", this.openValue)
  }

  toggle() {
    this.openValue = !this.openValue
  }

  openValueChanged() {
    if (this.openValue) {
      this.menuTarget.classList.add(...this.openClasses)
    } else {
      this.menuTarget.classList.remove(...this.openClasses)
    }
  }

  closeOnClickOutside(event) {
    if (!this.element.contains(event.target)) {
      this.openValue = false
    }
  }
}
```

### Controller Communication
```javascript
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = ["input", "results"]
  static outlets = ["search-results"]

  filter() {
    const query = this.inputTarget.value

    this.dispatch("filter", {
      detail: { query },
      prefix: "search"
    })

    if (this.hasSearchResultsOutlet) {
      this.searchResultsOutlet.updateResults(query)
    }
  }

  reset() {
    this.inputTarget.value = ""
    this.filter()
  }
}
```

## Turbo Frames

### Frame Navigation
```slim
turbo-frame id="posts"
  .posts-list
    - @posts.each do |post|
      turbo-frame.post-item id=dom_id(post)
        = render post
  = turbo_frame_tag "pagination", src: posts_path(page: @page), loading: :lazy do
    .loading Loading more posts...
```

### Frame Responses
```ruby
def update
  @post = Post.find(params[:id])

  if @post.update(post_params)
    respond_to do |format|
      format.html { redirect_to @post }
      format.turbo_stream { render turbo_stream: turbo_stream.replace(@post) }
    end
  else
    render :edit, status: :unprocessable_entity
  end
end
```

## Turbo Streams

### Stream Templates
```slim
= turbo_stream.prepend "posts" do
  = render @post

= turbo_stream.update "posts-count", @posts.count

= turbo_stream.replace "new-post-form" do
  = render "form", post: Post.new
```

### Broadcast Updates
```ruby
class Post < ApplicationRecord
  after_create_commit { broadcast_prepend_to "posts" }
  after_update_commit { broadcast_replace_to "posts" }
  after_destroy_commit { broadcast_remove_to "posts" }
end
```

## Form Enhancements

### Auto-Submit
```javascript
import { Controller } from "@hotwired/stimulus"
import { debounce } from "../utils/debounce"

export default class extends Controller {
  static values = { delay: { type: Number, default: 300 } }

  connect() {
    this.submit = debounce(this.submit.bind(this), this.delayValue)
  }

  submit() {
    this.element.requestSubmit()
  }
}
```

## Performance Patterns

### Lazy Loading
```javascript
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static values = { url: String }

  connect() {
    const observer = new IntersectionObserver(
      entries => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            this.load()
            observer.unobserve(this.element)
          }
        })
      },
      { threshold: 0.1 }
    )

    observer.observe(this.element)
  }

  async load() {
    const response = await fetch(this.urlValue)
    const html = await response.text()
    this.element.innerHTML = html
  }
}
```

### Debouncing
```javascript
export function debounce(func, wait) {
  let timeout

  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }

    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}
```

## Integration Patterns

### Rails Helpers
```slim
div data-controller="toggle" data-toggle-open-class="hidden" data-action="click->toggle#toggle"

#flash-messages data-turbo-permanent=true
  = render "shared/flash"
```

### Custom Turbo Stream Actions
```javascript
import { Turbo } from "@hotwired/turbo-rails"

Turbo.StreamActions.notification = function() {
  const message = this.getAttribute("message")
  const type = this.getAttribute("type")
  window.NotificationSystem.show(message, type)
}
```

Remember: Hotwire is about enhancing server-rendered HTML with just enough JavaScript. Keep interactions simple, maintainable, and progressively enhanced.
