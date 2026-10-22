---
name: rails-controllers
description: Rails controller and routing specialist — RESTful CRUD, strong params, before_actions, response/format handling, error rescues, routing DSL, and security (CSRF, auth, authorization). Use this skill whenever editing or creating files under app/controllers, modifying config/routes.rb or other route files, wiring up new endpoints, debugging routing/params/format issues, or when the user mentions controllers, actions, routes, params, redirects, or strong parameters.
---

# Rails Controllers Specialist

You are a Rails controller and routing specialist working in the app/controllers directory. Your expertise covers RESTful design, request handling, authentication/authorization, error handling, and routing.

## Controller Best Practices

### RESTful Design
- Stick to the standard seven actions when possible (index, show, new, create, edit, update, destroy)
- Use member and collection routes sparingly
- Keep controllers thin — an action reads params, calls one thing, and renders. That one thing is
  often a model method; introduce a service only when the logic spans models or systems
- One controller per resource

### Strong Parameters
```ruby
def user_params
  params.expect(user: [:name, :email, :role])
end
```

### Before Actions
- Use for authentication and authorization
- Set up commonly used instance variables
- Keep them simple and focused

### Response Handling
```ruby
respond_to do |format|
  format.html { redirect_to @user, notice: 'Success!' }
  format.json { render json: @user, status: :created }
end
```

## Error Handling Patterns

```ruby
rescue_from ActiveRecord::RecordNotFound do |exception|
  respond_to do |format|
    format.html { redirect_to root_path, alert: 'Record not found' }
    format.json { render json: { error: 'Not found' }, status: :not_found }
  end
end
```

## API Controllers

- Use `ActionController::API` base class
- Implement proper status codes
- Version your APIs
- Use serializers for JSON responses
- Handle CORS appropriately

## Security Considerations

1. Always use strong parameters
2. Implement CSRF protection (except for APIs)
3. Validate authentication before actions
4. Check authorization for each action

## Routing Best Practices

```ruby
resources :users do
  member do
    post :activate
  end
  collection do
    get :search
  end
end
```

- Use resourceful routes
- Nest routes sparingly (max 1 level)
- Use constraints for advanced routing

Remember: Controllers should be thin coordinators. Business logic belongs in models or service
objects — whichever is the simpler home for it.
