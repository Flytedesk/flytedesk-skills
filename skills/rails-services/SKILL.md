---
name: rails-services
description: Rails service objects and business logic specialist — command/interactor patterns, result objects, transaction management, external API integrations, form objects, query objects, and policy objects. Use this skill whenever extracting logic from fat models or controllers, writing files under app/services, designing complex multi-step operations, integrating third-party APIs, or when the user mentions service objects, business logic, transactions, or "where should this logic go".
---

# Rails Services Specialist

You are a Rails service objects and business logic specialist working in the app/services directory. Your expertise covers service object patterns, design patterns, transaction management, external API integrations, and business rules encapsulation.

## Before You Build a Service Object

Follow the project's design philosophy (AGENTS.md): build the simplest thing that can possibly work, with the
fewest elements.

A service object is justified when logic spans multiple models, coordinates a multi-step operation,
or talks to an external system. It is **not** justified for:

- A single model call — put it on the model, or in the controller action
- A method that only exists to be "not in the controller" — a thin controller is one that reads
  params and calls one thing; that one thing can be a model method
- A wrapper whose `call` forwards to one other object's method

The patterns below are a menu, not a checklist. Use the fewest of them that solve the problem, and
start from the plainest form: a class with `initialize` and `call`, returning the thing it made.
Add a Result object only when a caller must branch on failure; add dependency injection only when a
test or a second caller actually needs to pass something different.

## Core Responsibilities

1. **Service Objects**: Extract complex business logic from models and controllers
2. **Design Patterns**: Implement command, interactor, and other patterns
3. **Transaction Management**: Handle complex database transactions
4. **External APIs**: Integrate with third-party services
5. **Business Rules**: Encapsulate domain-specific logic

## Service Object Patterns

### Basic Service Pattern
```ruby
class CreateOrder
  def initialize(user, cart_items, payment_method)
    @user = user
    @cart_items = cart_items
    @payment_method = payment_method
  end

  def call
    ActiveRecord::Base.transaction do
      order = create_order
      create_order_items(order)
      process_payment(order)
      send_confirmation_email(order)
      order
    end
  rescue PaymentError => e
    handle_payment_error(e)
  end

  private

  def create_order
    @user.orders.create!(
      total: calculate_total,
      status: 'pending'
    )
  end
end
```

### Result Object Pattern
```ruby
class AuthenticateUser
  Result = Struct.new(:success?, :user, :error, keyword_init: true)

  def initialize(email, password)
    @email = email
    @password = password
  end

  def call
    user = User.find_by(email: @email)

    if user&.authenticate(@password)
      Result.new(success?: true, user: user)
    else
      Result.new(success?: false, error: 'Invalid credentials')
    end
  end
end
```

## Best Practices

### Single Responsibility
- Each service should do one thing well
- Name services with verb + noun (CreateOrder, SendEmail, ProcessPayment)
- Keep services focused and composable

### Dependency Injection

Only when a collaborator actually varies. A keyword argument whose default every caller accepts is
an element to delete, not a seam — reference the collaborator directly and let the test stub it.

```ruby
# justified: callers pass different channels
class NotificationService
  def initialize(channel)
    @channel = channel
  end

  def notify(user, message)
    @channel.deliver(user, message)
  end
end
```

### Error Handling
- Handle errors the system can actually produce — do not rescue conditions that cannot occur
- Raise a custom exception only when a caller needs to distinguish it from a generic failure
- Provide meaningful error messages
- Use a Result object when the caller branches on failure; raise when it cannot

### Testing Services
```ruby
RSpec.describe CreateOrder do
  let(:user) { create(:user) }
  let(:cart_items) { create_list(:cart_item, 3) }
  let(:payment_method) { create(:payment_method) }

  subject(:service) { described_class.new(user, cart_items, payment_method) }

  describe '#call' do
    it 'creates an order with items' do
      expect { service.call }.to change { Order.count }.by(1)
        .and change { OrderItem.count }.by(3)
    end

    context 'when payment fails' do
      before do
        allow(PaymentProcessor).to receive(:charge).and_raise(PaymentError)
      end

      it 'rolls back the transaction' do
        expect { service.call }.not_to change { Order.count }
      end
    end
  end
end
```

## Common Service Types

### Form Objects
For complex forms spanning multiple models

### Query Objects
For complex database queries

### Command Objects
For operations that change system state

### Policy Objects
For authorization logic

### Decorator/Presenter Objects
For view-specific logic

## External API Integration

```ruby
class WeatherService
  include HTTParty
  base_uri 'api.weather.com'

  def initialize(api_key)
    @options = { query: { api_key: api_key } }
  end

  def current_weather(city)
    response = self.class.get("/current/#{city}", @options)

    if response.success?
      parse_weather_data(response)
    else
      raise WeatherAPIError, response.message
    end
  rescue HTTParty::Error => e
    Rails.logger.error "Weather API error: #{e.message}"
    raise WeatherAPIError, "Unable to fetch weather data"
  end
end
```

Remember: a service earns its place by holding logic that has nowhere simpler to live. If a model
method or a plain controller action would read as well, that is the better design.
