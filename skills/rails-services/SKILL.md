---
name: rails-services
description: Decides whether logic belongs in a service object and writes minimal ones under app/services, including transactions, error handling and external API calls. Use when extracting logic from fat models or controllers, editing files under app/services, designing multi-step operations, integrating third-party APIs, or asking where logic should go.
---

# Rails Services

Build the simplest thing that can possibly work, with the fewest elements.

## Before you build a service object

A service object is justified when logic spans multiple models, coordinates a multi-step operation, or
talks to an external system. It is **not** justified for:

- A single model call. Put it on the model, or in the controller action.
- A method that only exists to be "not in the controller". A thin controller reads params and calls one
  thing, and that one thing can be a model method.
- A wrapper whose `execute` forwards to one other object's method.

Decide in this order:

1. One model call: a model method.
2. Several models, several steps or an external system: a service with `initialize` and `execute`.
3. Validation failure: return the model unsaved, with its errors (`save`, not `save!`). If earlier steps
   already wrote rows, raise `ActiveRecord::Rollback` so they are undone too, and copy the failing record's
   errors onto the model you return so the caller can show them. A failure the caller must tell apart (a
   declined payment): raise a custom exception for the caller to rescue. Anything else unexpected: raise.
4. A collaborator that a test or a second caller really needs to swap: inject it. Otherwise reference it
   directly and stub it in the test.

The patterns below are a menu. Use the fewest that solve the problem, starting from a class with
`initialize` and `execute` that returns the thing it made.

## Basic service

Name services verb + noun (`CreateTeam`). Take keyword arguments in `initialize`, and put the work in an
instance method named `execute`, not `call` or a class-level `.call`, which is the common Rails convention
but not this codebase's. Every existing service uses `execute`, so a caller never has to check which one
a given service uses.

Keep the transaction to database writes. Side effects that leave the system, like email or an HTTP call,
go after the transaction commits: a network call inside it holds the transaction open, and if the commit
then fails, the call has already happened. (If a caller wraps the service in its own transaction, the email
is still enqueued before that outer commit.)

```ruby
class CreateTeam
  def initialize(owner:, name:, member_ids:)
    @owner = owner
    @name = name
    @member_ids = member_ids
  end

  def execute
    team = Team.new(owner: @owner, name: @name)

    ActiveRecord::Base.transaction(requires_new: true) do
      raise ActiveRecord::Rollback unless team.save && add_members(team)
    end

    TeamMailer.created(team).deliver_later if team.persisted?
    team
  end

  private

  def add_members(team)
    @member_ids.each do |user_id|
      membership = team.memberships.create(user_id:)
      next if membership.persisted?

      team.errors.merge!(membership.errors)
      return false
    end
    true
  end
end
```

`ActiveRecord::Rollback` undoes the team and any memberships already saved, and Rails marks `team` as not
persisted again, so the caller gets an unsaved team carrying the error. `requires_new: true` matters when a
caller has already opened a transaction: without it, the nested block joins the outer transaction, Rails
swallows the `Rollback` silently, and nothing is undone.

## Dependency injection

Only when a collaborator actually varies. A keyword argument whose default every caller accepts is an
element to delete, not a seam.

```ruby
# justified: callers pass different channels (email, SMS)
class RemindOverdueCustomers
  def initialize(channel:)
    @channel = channel
  end

  def execute
    Invoice.overdue.includes(:customer).find_each do |invoice|
      @channel.deliver(invoice.customer, "Invoice #{invoice.number} is overdue")
    end
  end
end
```

## Error handling

- Handle errors the system can actually produce. Don't rescue conditions that cannot occur.
- Raise a custom exception only when a caller needs to tell it apart from a generic failure.
- When wrapping an external service, rescue its network errors (timeouts and connection failures, not
  only its API errors) and raise one service-specific error.

## Testing

```ruby
RSpec.describe CreateTeam do
  it 'creates the team with its members' do
    # given
    owner = create(:user)
    member_ids = create_list(:user, 2).map(&:id)

    # when
    team = described_class.new(owner:, name: 'Design', member_ids:).execute

    # then
    expect(team).to be_persisted
    expect(team.memberships.count).to eq(2)
  end

  context 'when a membership is invalid' do
    it 'rolls back the team and returns its errors' do
      # given
      owner = create(:user)

      # when
      team = described_class.new(owner:, name: 'Design', member_ids: [nil]).execute

      # then
      expect(team).not_to be_persisted
      expect(team.errors).to be_present
      expect(Team.count).to eq(0)
    end
  end
end
```

See the `testing-patterns` skill for spec conventions.
