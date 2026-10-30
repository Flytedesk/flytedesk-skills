---
name: rails-models
description: Writes and reviews ActiveRecord models and migrations, covering validations, associations, scopes, callbacks, indexing and query performance. Use when editing files under app/models or db/migrate, designing schema, adding a column or a validation, relating models, or fixing N+1 queries.
---

# Rails Models

Read the app's `ApplicationRecord` and its model concerns before adding a model or a helper. They decide
what shared behavior already exists (enum helpers, search defaults, soft deletion), and new code should use
it rather than add a second way to do the same thing. Keep a model to its own data and rules. Work that
spans several models or calls another system belongs in a service (see the `rails-services` skill).

## Validations and constraints

A validation runs only when a record is saved through ActiveRecord. Concurrent writes, `update_column`,
`insert_all` and raw SQL get past it, so back each validation the data depends on with a database
constraint, added in the same migration:

- `presence` → `null: false` on the column
- `belongs_to` (required by default) → `null: false` and `foreign_key: true` on the reference
- `uniqueness` → a unique index over the column and its `scope:` columns. Without it, two concurrent writes
  both pass. For `case_sensitive: false`, index `lower(column)`.

Decide what deleting the parent does to its children, and make the association's `:dependent` and the
foreign key's `on_delete` say the same thing:

- `dependent: :destroy` or `:delete_all` with a plain foreign key. Rails removes the children first.
- `dependent: :nullify` with `on_delete: :nullify`.
- `dependent: :restrict_with_error` with a plain foreign key.
- `on_delete: :cascade` only when the children have no callbacks that must run, since the database deletes
  them without loading them.

An association with no `:dependent` over a plain foreign key makes destroying the parent raise
`ActiveRecord::InvalidForeignKey`.

## Associations

- Choose `:dependent` deliberately. Don't leave it to default.
- Prefer `has_many :through` over `has_and_belongs_to_many`.
- Add `:inverse_of` only when Rails can't infer the inverse (a scope, `:through`, `:foreign_key`, or a
  non-conventional inverse name).

## Callbacks

Use them sparingly and keep them to the model's own concerns. Extract to a service object when an
operation spans models or calls another system, not merely because the method is long.

## Scopes and queries

Put reusable queries in named scopes. Prevent N+1 queries with `includes` (or `preload` / `eager_load`).

## Performance

Indexing foreign keys and WHERE columns is a default. The rest are earned. Reach for them in response to
a measured problem, not in anticipation of one:

- Counter caches for association counts
- Database views for complex queries
- Bulk operations in place of per-record writes
- Arel in place of readable ActiveRecord

Each adds a moving part that must stay correct. Write the plain query first.

## Migrations

Migrations run during deploy, while the old code is still serving requests, so a migration must not
break the code that is running.

Copy this checklist and check items off:

```
- [ ] If the app keeps migrations in more than one directory, it's in the one for the code that owns the table
- [ ] Reversible: use `change`, or write both `up` and `down`
- [ ] `ActiveRecord::Migration[x.y]` matches the Rails version in the Gemfile, not an older migration's
- [ ] Index every foreign key and frequently queried column with a plain `add_index`. On a table large
      enough that locking it would block traffic, use `algorithm: :concurrently` with
      `disable_ddl_transaction!`, in a migration that does nothing else.
- [ ] Safe for the running code. To remove a column, add it to `self.ignored_columns` and deploy, then drop
      it in a later migration. To rename one, add the new column, write to both, backfill, switch reads, then
      remove the old one. A plain `rename_column` breaks the running code.
- [ ] No backfill of real data in a migration: write a one-off script run with `rails runner` (or a job), so
      deploys don't wait on it. A migration may set a constant value before adding a NOT NULL constraint.
- [ ] Run `db:migrate`, `db:rollback`, then `db:migrate` again
- [ ] Confirm `db/schema.rb` (or `structure.sql`) changed as expected
```

## Testing

Follow the `testing-patterns` skill for spec conventions; its Validations section covers model specs. Spec
each validation, scope and callback the model adds. Don't spec associations or enums.

## Before you finish

- [ ] Uses what `ApplicationRecord` and existing concerns already provide
- [ ] Each validation the data depends on has a matching constraint (`null: false`, foreign key, unique index)
- [ ] `:dependent` on each `has_many` / `has_one` agrees with its foreign key's `on_delete`
- [ ] Callbacks stay within the model; cross-model or external work is in a service
- [ ] Queries that load associations in a loop use `includes`, `preload` or `eager_load`
- [ ] Spec covers each new validation, scope and callback
