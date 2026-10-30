---
name: rails-api
description: Builds and modifies Flytedesk JSON:API endpoints served from ActionController::API, with jsonapi-serializer serializers and rswag specs that generate the OpenAPI document. Use when working in controllers that inherit from ActionController::API, adding or changing JSON:API endpoints, writing rswag specs or OpenAPI docs, designing serializers, or handling API errors, versioning, pagination, filtering or includes.
---

# Rails API

Flytedesk APIs follow [JSON:API](https://jsonapi.org). Find the API's base controller and a neighboring
endpoint, and build on their helpers rather than writing new ones.

If an endpoint you're touching doesn't conform, tell the user. Change its response shape only when that is in
scope, because existing clients may depend on it.

## Base controller

Each API has one base controller that inherits from `ActionController::API`. Its endpoints subclass it. It owns:

- **Authentication**: a `before_action` that checks an API key header and renders a 401 error on failure.
- **Error context**: a `before_action` that calls `Rails.error.set_context` with the user and request id.
- **Error rendering**: one `render_error(status:, title:, detail:, ...)` helper. Every error goes through it.
- **Content type**: responses use the JSON:API media type (`application/vnd.api+json`).
- **Param checks**: `before_action`s that validate version, filter, page and include params and render an
  error before any work runs.
- **Collection rendering**: one helper that serializes a collection and adds the pagination `meta` and `links`.

If the app has no API yet, build that base controller first, along with shared rswag examples for the
authentication, version and pagination errors, so the first endpoint starts from the same footing as later ones.

Endpoints stay small. They declare the checks they need and define the hooks the base controller calls:

```ruby
class AdsController < BaseController
  before_action -> { check_api_version('1.1.0') }
  before_action :check_filter_params
  before_action :check_page_params

  def index
    render_resources_with(AdSerializer)
  end

  private

  def resources
    @resources ||= AdQuery.new(**page_params.to_h, **filter_params.to_h).execute
  end

  def filter_params
    @filter_params ||= FilterParams.new(params:, config: { status: { klass: EnumFilterParam } })
  end

  def url_helper
    :api_ads_url
  end
end
```

The class names in this skill's examples (`AdQuery`, `FilterParams`, `EnumFilterParam`, `AdClient`) are
illustrative. Use the classes the project's API already has, and don't create one just because an example
names it.

When the query fails in an expected way (a model with errors, or a custom exception it raises), render it
as a 422 error.

## Errors

Every error is a JSON:API error object. `status` is a string. `source` names the query parameter or header
at fault:

```json
{ "errors": [{ "status": "422", "title": "Invalid Page Size", "detail": "...", "source": { "parameter": "page[size]" } }] }
```

## Serializers

Use `jsonapi-serializer`. Set the `type` explicitly and convert values whose JSON form would be ambiguous
(`BigDecimal` to a number). A relationship whose record isn't loaded gets a block that returns an id-only
stand-in, and an `if:` when its foreign key can be nil:

```ruby
class AdSerializer
  include JSONAPI::Serializer

  set_type :ads
  attributes :name, :start_date, :end_date, :status
  attribute(:price) { it.price.to_f }
  belongs_to(:client) { AdClient.new(id: it.client_id) }
  belongs_to :supplier, if: -> { it.supplier_id.present? } do
    Supplier.new(id: it.supplier_id)
  end
end
```

## Versioning, pagination, filtering and includes

- **Versioning**: clients send the version in a request header. If the header is missing, treat the request
  as the oldest version. Gate a breaking change behind a minimum version on that endpoint
  (`check_api_version`), which returns a 409 for older clients, and keep the old behavior for them.
- **Pagination**: use JSON:API's `page[...]` params with the strategy the API already uses, and a bounded
  page size with a default. Collections return pagination `links` (`self`, `first`, `last`, `prev`,
  `next`), and any counts go in `meta`. A link with no page to go to is `null`. Links keep the request's
  other params.
- **Filtering**: `filter[<name>]`, using the operator syntax the API already supports. Each filter type is
  a param object with ActiveModel validations, and the endpoint lists the filters it accepts in a config. An
  invalid or unknown filter is a 422 with `source.parameter: "filter"` and a `detail` that names the filter.
- **Includes**: `include=a,b` is checked against the endpoint's supported relationships, with a default. An
  unsupported value is a 400 with `source.parameter: "include"`. Pass the values to the serializer's
  `include:` option and keep them in the pagination links.

## rswag

[rswag](https://github.com/rswag/rswag) specs do two jobs: they validate API behavior and they generate
the OpenAPI document. Every endpoint gets one:

- [ ] Reuse the shared examples for the common error responses (authentication, version, pagination)
  instead of repeating those cases
- [ ] Each operation sets `operationId` and `produces 'application/vnd.api+json'`, and declares the version
  header with a `$ref` to the shared version schema
- [ ] Response bodies `$ref` the shared component schemas (the errors document and one document per resource).
  An enum attribute `$ref`s a schema that lists its values
- [ ] `filter` and `page` are declared as `style: :deepObject, explode: true` query params, reusing the
  existing parameter schemas
- [ ] Cover success, and each error the endpoint adds beyond the shared ones (400 or 422 for bad params)
- [ ] Assert the JSON:API content type, and follow `links.next` through to the last page. Do it again with a
  filter and an include set, and check both survive onto the next page
- [ ] An unknown path under the API returns a 404

## Adding an endpoint

1. Read the base controller and the closest existing endpoint: its route, controller, serializer and rswag spec.
2. Add the route, controller and serializer. Reuse the base controller's helpers.
3. Write the rswag spec.
4. Run the rswag specs and regenerate the OpenAPI document. Look for a project task that wraps rswag first
   (`rake -T docs`, `rake -T swagger`), because it may lint the document and move it to where it's committed,
   which calling `rswag:specs:swaggerize` directly skips. If the document is committed, check that its diff
   matches what you changed.

To change an existing endpoint, start at step 1 with that endpoint. If the change breaks existing clients,
gate it behind a new API version.
