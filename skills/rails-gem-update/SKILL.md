---
name: rails-gem-update
description: Evaluates and performs Ruby gem updates in a Rails modular monolith, driven by bundle outdated. Use when reviewing bundle outdated output, upgrading or bumping gems, updating Gemfile.lock, analyzing release notes, handling gem-related migrations, or coordinating gem updates with npm dependencies.
---

# Rails Gem Update (Modular Monolith)

## Core principle

All updates are driven strictly by:

    bundle outdated

Do not introduce or evaluate gems outside this output unless explicitly instructed.

Gems sourced from git and pinned by `tag:` or `ref:` don't appear in `bundle outdated`. List them in the
session status as not checked. Update one only when the user asks: change the tag in the Gemfile, read that
repository's release notes or tags, then run `bundle update <gem_name>`.

## Per-gem checklist

Copy this for each gem and check items off:

```
- [ ] Step 1: classified (Gemfile constraint checked)
- [ ] Step 2: release notes fetched
- [ ] Step 3: evaluated, recommendation is Accept or Hold
- [ ] Steps 4-5: migrations and npm coupling checked
- [ ] Step 6: snapshot taken, updated, tests run
- [ ] Verification plan, new feature report and upgrade report updated
```

## Artifacts

Write artifacts to `.claude/gem-updates/` so they accumulate across gems in a session.

### Verification plan → `.claude/gem-updates/verification-plan.md`

```markdown
# Verification Plan

## Gem: <gem_name>
- Current Version: <current_version>
- Target Version: <target_version>
- Release Type: Patch / Minor / Major

### Checks
- [ ]
```

### New feature report → `.claude/gem-updates/new-feature-report.md`

```markdown
# New Feature Report

## Gem: <gem_name>
- Current Version: <current_version>
- Target Version: <target_version>

### New Features Not Currently Used
-
```

### Upgrade report (required) → `.claude/gem-updates/upgrades-YYYY-MM-DD.md`

After every session, write this file (using today's date, a new file each session) with a row for every gem
that was evaluated:

```markdown
# Gem Upgrade Report — YYYY-MM-DD

| Gem | From | To | Type | Status | Hold Reason / Notes |
|-----|------|----|------|--------|---------------------|
| gem_name | x.y.z | x.y.z | patch/minor/major | ✅ Updated / ⏸ Hold / ❌ Blocked | reason if not updated |
```

Status values:
- `✅ Updated`: `bundle update` ran and tests pass.
- `⏸ Hold`: you decided not to update (breaking change, planned separately).
- `❌ Blocked`: bundler can't resolve the update because another gem constrains it (name the blocking gem).

## Update workflow

### Step 1 — Identify candidate

For each gem in `bundle outdated`, record its name, current version and target version, and classify the
update as Patch / Minor / Major.

Check whether the gem is pinned in the Gemfile (for example `gem "foo", "~> 1.0"`). If the constraint
prevents reaching the target version, note that the Gemfile must change first and include the new
constraint in the recommendation.

### Step 2 — Review release notes (mandatory)

Fetch the upstream release notes. Try these sources in order:
1. `https://github.com/<owner>/<repo>/releases`
2. `https://github.com/<owner>/<repo>/blob/main/CHANGELOG.md` (also try `master`, `CHANGES.md`, `History.md`)
3. The gem's homepage URL from `bundle info <gem_name>`

Extract the changelog entries between the current and target versions, upgrade guides, and breaking change
notices.

Do not summarize or infer release notes without fetching them. If none can be found, say so and flag the
gem for manual review.

### Step 3 — Evaluate

**Patch releases:** accept by default, after checking the notes for migrations or breaking changes.

**Minor and major releases:** evaluate breaking changes, deprecations, migrations and config changes.
- Grep the codebase for each changed or removed API. If the project uses it, add a verification check.
- Features the project doesn't use yet go in the new feature report.

Recommend **Hold** when any of these apply:
- Major version with breaking changes that affect features used in this project
- Requires a Rails version bump beyond what is currently pinned
- Depends on another gem that must be updated first (coordinated upgrade)
- Release notes indicate known regressions or instability (yanked prior versions, open critical issues)
- Requires significant code migration that should be planned separately

Every gem is recommended as **Accept** or **Hold**. (An Accept can still end up Blocked at Step 6.)

### Step 4 — Database migrations

Look in the release notes for new migrations (`install:migrations`, a generator, or a documented
migration). If the gem needs migrations, put them where its earlier migrations live: the module that owns
the gem's tables, such as the module that wraps the gem or a shared infrastructure module for a
cross-cutting gem like the job backend. Generators and `install:migrations` write to the root `db/migrate`,
so move the files if the project keeps migrations elsewhere. Check that `ActiveRecord::Migration[x.y]`
matches the Rails version in the Gemfile, and add a verification check.

### Step 5 — NPM coupling

Check whether the gem ships a JavaScript package that must move with it (for example `turbo-rails` and
`@hotwired/turbo-rails`). If so, update the npm package too and verify frontend behavior; see the
`npm-package-update` skill.

### Step 6 — Execute update

Once a gem is recommended as **Accept**:

1. **Snapshot** the files the update can change, so a failure rolls back only this gem:
   ```
   mkdir -p .claude/gem-updates/snapshot
   cp Gemfile Gemfile.lock .claude/gem-updates/snapshot/
   ```
   If the update also touches npm packages, snapshot `package.json` and `yarn.lock` too.

2. **If the Gemfile constraint needs changing** (Step 1), edit the Gemfile first.

3. **Update the gem conservatively**, which avoids pulling in unrelated dependency changes:
   ```
   bundle update <gem_name> --conservative
   ```

4. **Confirm the target version installed.** `bundle update --conservative` succeeds even when another
   gem holds the version back, so check with `bundle info <gem_name>`. If bundler held it back, restore
   the snapshot (see step 7), record `❌ Blocked` and name the gem that constrains it.

5. **Run the specs for the code that uses the gem** with the project's test command (check `bin/` and the
   project's agent instructions; it may take paths and run in parallel). Then run the full suite, and the
   other checks the agent instructions require, such as linting the changed files.

6. **If tests pass,** record `✅ Updated` and proceed to the next gem or finalize.

7. **If tests fail,** diagnose the failure.
   - If the fix is straightforward (a renamed method, a changed config key), apply it and re-run.
   - If it is complex or unclear, roll back this gem and recommend Hold. Restore the snapshot, undo only
     the code edits you made for this gem, and leave all other uncommitted changes alone:
     ```
     cp .claude/gem-updates/snapshot/Gemfile .claude/gem-updates/snapshot/Gemfile.lock .
     bundle install
     ```
     If you also snapshotted `package.json` and `yarn.lock`, restore them and run `yarn install`.
   - Add the failure details to the verification plan for follow-up.

8. **Do not commit automatically.** Present the results and let the user decide when to commit.

## Per-gem output format

Present each evaluated gem like this:

```markdown
## <gem_name>

- Current Version: <x.y.z>
- Target Version: <x.y.z>
- Release Type: Patch / Minor / Major
- Gemfile Constraint: <current constraint or "unpinned">
- Constraint Change Required: Yes (new constraint) / No
- Recommendation: Accept / Hold
- Hold Reason: <reason, if applicable>
- Migrations Required: Yes / No / Unclear
- Requires NPM Update: Yes / No / Unclear
- Tests Pass: Yes / No / Not yet run

### Verification Plan Additions
- [ ]

### New Feature Report Additions
-
```

## Session completion status (required)

Always end a session with a status block so the user knows whether the task is finished:

```
## Update Session Status

- Gems updated this session: <count> (<list>)
- Gems held: <count> (<list with hold reasons>)
- Gems not yet evaluated: <count> (<list>)
- Task complete: Yes / No

<If No>: Run this skill again to continue with the remaining gems.
```

**Never imply the task is done if gems remain in `bundle outdated` that have not been evaluated.** If the
session ends before all gems are processed, tell the user how many are left and that another run is needed.
