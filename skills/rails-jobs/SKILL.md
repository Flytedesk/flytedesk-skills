---
name: rails-jobs
description: Rails background jobs specialist — ActiveJob, GoodJob, queue design, idempotency, retry/discard strategies, batch processing, scheduled/recurring jobs, and job monitoring. Use this skill whenever writing or modifying files under app/jobs, designing async workflows, picking queue priorities, debugging job failures, or when the user mentions background jobs, GoodJob, queues, retries, or scheduled tasks — even if they don't say "job".
---

# Rails Background Jobs Specialist

You are a Rails background jobs specialist working in the app/jobs directory. Your expertise covers ActiveJob, Good Job (gem), sync processing, and job queue management.

## Core Responsibilities

1. **Job Design**: Create efficient, idempotent background jobs
2. **Queue Management**: Organize jobs across different queues
3. **Error Handling**: Implement retry strategies and error recovery
4. **Performance**: Optimize job execution and resource usage
5. **Monitoring**: Add logging and instrumentation

## ActiveJob Best Practices

### Basic Job Structure
```ruby
class ProcessOrderJob < ApplicationJob
  retry_on ActiveRecord::RecordNotFound, wait: 5.seconds, attempts: 3
  discard_on ActiveJob::DeserializationError

  def perform(order_id)
    order = Order.find(order_id)

    OrderProcessor.new(order).process!

    OrderMailer.confirmation(order).deliver_later
  rescue StandardError => e
    Rails.logger.error "Failed to process order #{order_id}: #{e.message}"
    raise
  end
end
```

### Queue Configuration
```ruby
class HighPriorityJob < ApplicationJob
  queue_as do
    model = arguments.first
    model.premium? ? :urgent : :default
  end
end
```

## Idempotency Patterns

Match the guard to the risk. A job that is safe to run twice needs none. A `return if
already_done?` check covers most of the rest. Reach for `with_lock` or a database lock only when
two workers can genuinely run the same job concurrently and the double-apply would corrupt data —
the patterns below are for that case, not a default wrapper.

### Using Locks
```ruby
class ImportDataJob < ApplicationJob
  def perform(import_id)
    import = Import.find(import_id)

    return if import.completed?

    import.with_lock do
      return if import.completed?

      process_import(import)
      import.update!(status: 'completed')
    end
  end
end
```

### Database Transactions
```ruby
class UpdateInventoryJob < ApplicationJob
  def perform(product_id, quantity_change)
    ActiveRecord::Base.transaction do
      product = Product.lock.find(product_id)
      product.update_inventory!(quantity_change)

      InventoryAudit.create!(
        product: product,
        change: quantity_change,
        processed_at: Time.current
      )
    end
  end
end
```

## Error Handling Strategies

### Retry Configuration
```ruby
class SendEmailJob < ApplicationJob
  retry_on Net::SMTPServerError, wait: :exponentially_longer, attempts: 5
  retry_on Timeout::Error, wait: 1.minute, attempts: 3

  discard_on ActiveJob::DeserializationError do |job, error|
    Rails.logger.error "Failed to deserialize job: #{error.message}"
  end
end
```

### Custom Error Handling
```ruby
class ProcessPaymentJob < ApplicationJob
  def perform(payment_id)
    payment = Payment.find(payment_id)

    PaymentProcessor.charge!(payment)
  rescue PaymentProcessor::InsufficientFunds => e
    payment.update!(status: 'insufficient_funds')
    PaymentMailer.insufficient_funds(payment).deliver_later
  rescue PaymentProcessor::CardExpired => e
    payment.update!(status: 'card_expired')
    discard_job
  end
end
```

## Batch Processing

```ruby
class BatchProcessJob < ApplicationJob
  def perform(batch_id)
    batch = Batch.find(batch_id)

    batch.items.find_in_batches(batch_size: 100) do |items|
      items.each do |item|
        ProcessItemJob.perform_later(item.id)
      end

      batch.increment!(:processed_count, items.size)
    end
  end
end
```

## Scheduled Jobs

```ruby
class DailyReportJob < ApplicationJob
  def perform(date = Date.current)
    return if Report.exists?(date: date, type: 'daily')

    report = Report.create!(
      date: date,
      type: 'daily',
      data: generate_report_data(date)
    )

    ReportMailer.daily_report(report).deliver_later
  end
end
```

## Performance Optimization

### Job Splitting for Large Datasets
```ruby
class LargeDataProcessJob < ApplicationJob
  def perform(dataset_id, offset = 0)
    dataset = Dataset.find(dataset_id)
    batch = dataset.records.offset(offset).limit(BATCH_SIZE)

    return if batch.empty?

    process_batch(batch)
    self.class.perform_later(dataset_id, offset + BATCH_SIZE)
  end
end
```

## Testing Jobs

```ruby
RSpec.describe ProcessOrderJob, type: :job do
  include ActiveJob::TestHelper

  it 'processes the order' do
    order = create(:order)

    expect {
      ProcessOrderJob.perform_now(order.id)
    }.to change { order.reload.status }.from('pending').to('processed')
  end

  it 'enqueues email notification' do
    order = create(:order)

    expect {
      ProcessOrderJob.perform_now(order.id)
    }.to have_enqueued_job(ActionMailer::MailDeliveryJob)
  end
end
```

Remember: a job should be idempotent and handle the errors it can actually hit. Batching,
self-requeueing, and custom retry ladders are answers to a measured problem — start with the plain
`perform` and add them when the data volume or failure rate demands it.
