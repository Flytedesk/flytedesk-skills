---
name: rails-jobs
description: Writes and reviews ActiveJob background jobs that run on GoodJob, covering idempotency, retry and discard behavior, concurrency control, queues, progress reporting and recurring jobs. Use when editing files under app/jobs, calling perform_later, designing async workflows, or choosing retry behavior or a queue.
---

# Rails Background Jobs

A job should be idempotent and handle the errors it can actually hit. Batching, self-requeueing and custom
retry ladders answer a measured problem. Start with a plain `perform` and add them when the data volume
or failure rate demands it.

Inherit from the app's base job class, and read it first. What it rescues and reports decides how retries,
error reporting and specs behave, and the guidance below depends on it.

Pass record ids as keyword arguments, not records, and look the record up inside `perform`. That way the
job sees the record as it is when it runs, not as it was when it was enqueued. Keep `perform` thin: put
the logic it runs in a model or service (see the `rails-services` skill).

## Idempotency

Match the guard to the risk. A job that is safe to run twice needs none. A `return if already_done?` check
covers most of the rest. To de-duplicate work for the same record, use GoodJob concurrency control keyed
on the record, and pick the limit by what a dropped enqueue would cost:

- `total_limit: 1` drops a new enqueue while one is queued or running. Use it when a duplicate adds
  nothing. A change made while a run is in progress is lost.
- `enqueue_limit: 1` keeps one job waiting behind the running one, so a burst of enqueues collapses into
  one run that still sees the latest change. Add `perform_limit: 1` so runs never overlap. This suits jobs
  that recompute from current state.
- `perform_limit: 1` alone runs one at a time but keeps every enqueue.

```ruby
class UpdateMetricsJob < ApplicationJob
  include GoodJob::ActiveJobExtensions::Concurrency
  good_job_control_concurrency_with(
    enqueue_limit: 1,
    perform_limit: 1,
    key: -> { "#{self.class.name}_#{arguments.first.fetch(:ad_id)}" }
  )

  def perform(ad_id:)
    ad = Ad.find_by(id: ad_id)
    return if ad.nil? || ad.metrics_locked?

    ad.update!(metrics: MetricsCalculator.new(ad:).execute)
  end
end
```

Use `with_lock` instead when the guard belongs to the record rather than the job. Check the condition again
inside the block, because `with_lock` reloads the record.

A job that applies a delta (adjust stock by 5) is not safe to retry. Make it set a target state instead,
or record each change under a unique key so a repeat is rejected.

## Retries and discards

What follows assumes a base job that discards every unhandled exception and reports it to the error
tracker. If the base job doesn't, follow what it does instead.

With that base, a job retries **only** the errors it names in `retry_on`. A `retry_on` declared in the job
wins over the base class's discard. An error is reported once, on discard or when retries run out, not on
every attempt.

- Transient errors (timeouts, throttling, 5xx from a service): `retry_on` with a bounded `attempts:` and
  `wait: :polynomially_longer`. Report the error in the block, which runs when the attempts run out.
- Errors from one external service: put its `retry_on` lines in a concern (one per service or HTTP client)
  and include it in each job that calls that service. Check for an existing concern first.
- Expected business failures (a card expired): record the state in a `rescue`, or `return` early, and
  don't re-raise.
- A record deleted before the job runs: when that is expected, look it up with `find_by` and return on
  `nil`, or `discard_on ActiveRecord::RecordNotFound` without reporting. Otherwise `find` raises and an
  expected situation is reported as an error. Keep `find` when the record should always exist.
- A service that returns an unsaved model with errors doesn't raise. Check `persisted?` (or `errors`) and
  raise, or the job succeeds and nobody hears about the failure.

```ruby
module HandlesPaymentGatewayErrors
  extend ActiveSupport::Concern

  included do
    retry_on(PaymentGateway::Timeout, PaymentGateway::ServerError, wait: :polynomially_longer, attempts: 3) do |_job, error|
      Rails.error.report(error)
    end
  end
end
```

## Queues

Queues are sized by how jobs use resources, not by domain. Read the job server config to see which queues
exist and how many threads each gets. Typically:

- A queue for jobs that finish in a couple of seconds, so slow jobs can't block them.
- A queue for memory-heavy jobs (media processing, large files), limited to one thread per server.
- The default queue for everything else.

Workers usually pick up every queue through wildcard or exclusion rules, so a new queue runs on the general
threads until the job server config names it. Give it dedicated capacity or isolation there. Each worker
thread holds a database connection, so raise the pool size when you add threads.

## Progress and recurring jobs

- A long-running job that someone watches reports progress through activejob-status (`progress.total`,
  `progress.increment`, `status[:step]`). Put a final summary in `status[:results]`. To push progress to an
  open page, see the `hotwire` skill.
- Recurring jobs go in `config.good_job.cron`. Give the class as a string. Cron must be enabled in only one
  process (`config.good_job.enable_cron`), or each job runs once per process:

```ruby
nightly_cleanup: {
  cron: '0 2 * * * America/Chicago',
  class: 'NightlyCleanupJob',
  description: 'Remove expired drafts'
}
```

## Large datasets

Enqueue one job per item with `ActiveJob.perform_all_later`. It skips enqueue callbacks, so concurrency
keys don't de-duplicate at enqueue. Use `perform_later` in a loop when that matters. For a sweep too big for that, page by id with
`in_batches` or `find_each`, not `offset`, which is slow and can skip rows.

## Testing

Follow the `testing-patterns` skill for spec conventions. When the base job discards every error,
`perform_now` doesn't raise in a spec. Test a failure by checking the report (`allow(Rails.error).to
receive(:report)` in `# given`, `have_received(:report)` in `# then`), or a retry with
`have_enqueued_job(described_class)`.

```ruby
RSpec.describe ProcessOrderJob, type: :job do
  include ActiveJob::TestHelper

  it 'processes the order' do
    # given
    order = create(:order)

    # when
    described_class.perform_now(order_id: order.id)

    # then
    expect(order.reload.status).to eq('processed')
  end

  it 'enqueues email notification' do
    # given
    order = create(:order)

    # when / then
    expect {
      described_class.perform_now(order_id: order.id)
    }.to have_enqueued_job(ActionMailer::MailDeliveryJob)
  end

  it 'reports a failed charge' do
    # given
    order = create(:order)
    allow(PaymentGateway).to receive(:charge).and_raise(PaymentGateway::Error)
    allow(Rails.error).to receive(:report)

    # when
    described_class.perform_now(order_id: order.id)

    # then
    expect(Rails.error).to have_received(:report).with(instance_of(PaymentGateway::Error), any_args)
  end
end
```

## Before you finish

- [ ] Inherits the base job class (read first), takes ids as keyword arguments
- [ ] Safe to run twice, or guarded (early return, concurrency key, or lock)
- [ ] Concurrency limit fits the job: `enqueue_limit` when a change made mid-run must not be lost
- [ ] Each known transient error has a `retry_on` (from a shared concern where one exists). Nothing else retries.
- [ ] A record that can be deleted before the job runs is handled without reporting an error
- [ ] A returned model with errors raises
- [ ] On an existing queue that suits its runtime and memory use
- [ ] Spec covers success and one retry or failure path
