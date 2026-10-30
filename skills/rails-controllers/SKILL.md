---
name: rails-controllers
description: Writes and reviews Rails controllers and routes, covering RESTful actions, strong params, authentication and ActionPolicy authorization, and routing. Use when editing files under app/controllers or config/routes.rb (and other route files), adding endpoints, or debugging routing, params, format or redirect issues.
---

# Rails Controllers

## RESTful design

- Stick to the standard seven actions (index, show, new, create, edit, update, destroy) where possible.
- One controller per resource. Use member and collection routes sparingly.
- Keep controllers thin: an action reads params, calls one thing, and renders. That one thing is often a
  model method. Introduce a service only when the logic spans models or systems.

## Strong parameters

Use `params.expect` (Rails 8):

```ruby
def user_params
  params.expect(user: [:name, :email, :role])
end
```

## Authentication and authorization

The app's base controllers handle authentication and authorization. Names vary by app; in the examples below
they are `AuthenticatedController` and `authorize_user!`.

- **Inherit from the nearest base controller** in the area you're working in. It may add scoping and a
  layout on top of the top-level authenticated controller, which runs `authenticate_user!`. Don't add
  authentication `before_action`s to individual controllers.
- **Authorization rules live in ActionPolicy policies**, not in controllers. A concern included in the base
  controller provides an authorize method that raises a not-authorized error, and handles that error once
  with `rescue_from`. Turbo Frame and Stream requests get an inline 403 alert, and other requests a 403 page.
  Don't rescue the error or add Turbo guards in individual actions.
- **Authorize every action** with an explicit rule. Authorize the class for collection actions (`index`,
  `new`, `create`) and the record for member actions. The policy is found from the controller's namespace,
  so pass one only when it differs.
- **For conditional UI** (showing a button or link), use the concern's non-raising check.

```ruby
class PostsController < AuthenticatedController
  def index
    authorize_user!(Post, :index?)
    @posts = Post.all
  end

  def update
    @post = Post.find(params[:id])
    authorize_user!(@post, :update?)
    # ...
  end
end
```

Don't call `skip_forgery_protection` in a controller that serves browsers. JSON-only endpoints belong in
`ActionController::API` controllers, which have no CSRF protection.

## Responding

Turbo acts on the status code, so set it explicitly:

- **A failed form submission** re-renders with `status: :unprocessable_content`. Turbo ignores a 200
  response to a form submission, so the errors would never appear.
- **A redirect after a submission** passes `status: :see_other`. After a PATCH or DELETE, a 302 makes the
  browser repeat that method against the new URL.

Base controllers include `PlatformUi::ControllerHelpers`. Use it rather than writing your own:

- **Flash**: the alert container renders only `notice`, `info`, `warning` and `danger`. A Rails `alert:`
  flash never appears, so report failures with `danger:`.
- **`send_danger_alert(message, path_helper:)`** reports a failure to either kind of request: a danger alert
  stream for Turbo, or a 303 redirect with a danger flash for HTML.
- **`render_top_level_component(modal: ...)`** (or `drawer:`) makes a modal or drawer route work both from a
  link that targets its frame and as a direct URL.

```ruby
def destroy
  @post = Post.find(params[:id])
  authorize_user!(@post, :destroy?)

  if @post.destroy
    redirect_to posts_path, status: :see_other, notice: 'Post deleted.'
  else
    send_danger_alert(@post.errors.full_messages.to_sentence, path_helper: :posts_path)
  end
end
```

## Routing

- Use `resources`. Nest at most one level.
- Reach for constraints only when `resources` can't express the route.
- Each area of the app keeps its routes in its own file under `config/routes/`, loaded with `draw(:name)`
  and wrapped in a `namespace`. Add a route to its area's file, not to the main `config/routes.rb`.

## Adding an endpoint

1. Add the route, then run `bin/rails routes -g <name>` to confirm it.
2. Add the action, using strong params, and authorize it.
3. Write a request spec under `spec/requests`, signing in the way the app's other request specs do. Cover
   the authorized path, an unauthorized user, and invalid params for actions that write.

For API endpoints, see the `rails-api` skill.

## Reviewing a controller

```
- [ ] Inherits from the nearest base controller; no authentication before_actions or authorization rescues
- [ ] Every action authorizes: the class for collection actions, the record for member actions
- [ ] Failed submissions render with `:unprocessable_content`; redirects after a submission use `:see_other`
- [ ] Flash uses `notice`, `info`, `warning` or `danger`, never `alert`
- [ ] A request spec covers an unauthorized user
```
