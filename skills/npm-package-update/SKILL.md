---
name: npm-package-update
description: Evaluates and performs JavaScript package updates in projects that use npm or Yarn, driven by the package manager's outdated report. Use when reviewing npm outdated or yarn outdated output, upgrading or bumping packages, updating package-lock.json or yarn.lock, analyzing release notes, handling breaking changes, or coordinating JavaScript updates with Rails gem dependencies.
---

# NPM Package Update

## Core principle

All updates are driven strictly by the package manager's **outdated** report (see the command table). Do not
introduce or evaluate packages outside it unless explicitly instructed.

## Step 0 — Detect the package manager

Do this once per session, in each directory that has a `package.json` with its own lockfile:

1. If `package.json` has a `packageManager` field (`"yarn@1.22.22"`, `"npm@10.8.0"`), use it.
2. Otherwise, use the tracked lockfile: `git ls-files '*yarn.lock' '*package-lock.json' '*npm-shrinkwrap.json'`.
   `yarn.lock` means Yarn. `package-lock.json` or `npm-shrinkwrap.json` means npm.
3. For Yarn, tell Classic from Berry by the files: a `.yarnrc.yml`, or a `yarn.lock` that starts with
   `__metadata:`, means Berry (2+). Confirm with `yarn --version` run in that directory; a global Yarn
   outside it can report 1.x for a Berry project.
4. Stop and ask the user if both lockfiles are tracked in the same directory, neither is, `packageManager`
   disagrees with the lockfile, or the project uses another manager (`pnpm-lock.yaml`, `bun.lock`,
   `bun.lockb`).

A repository can hold more than one JavaScript project. Run every step in each directory with its own
lockfile, and install in that directory. Artifacts for all of them go under the repository root (see
Artifacts).

npm workspaces share the root `package-lock.json`, and their folders have no lockfile. Run
`npm outdated --workspaces --include-workspace-root` at the root. To update a workspace's package, add
`-w <workspace>` to the update or install command, and snapshot that workspace's `package.json` too, in the
workspace's own snapshot folder.

## Command table

| Task | npm | Yarn Classic (1.x) | Yarn Berry (2+) |
|------|-----|--------------------|-----------------|
| Lockfile | `package-lock.json` | `yarn.lock` | `yarn.lock` |
| Outdated | `npm outdated` | `yarn outdated` | Ask the user. It needs a plugin, and `yarn upgrade-interactive` is interactive |
| Upgrade in range | `npm update <pkg>` (lockfile only) | `yarn upgrade <pkg>` | `yarn up -R <pkg>` |
| Widen range and upgrade | `npm install <pkg>@<range>` | `yarn upgrade <pkg>@<range>` | `yarn up <pkg>@<range>` |
| Install from lockfile | `npm ci` | `yarn install --frozen-lockfile` | `yarn install --immutable` |
| Show installed version | `npm ls <pkg>` | `yarn why <pkg>` | `yarn why <pkg>` |
| Run a script | `npm run <script>` (`npm test`) | `yarn <script>` | `yarn <script>` |
| Version pins | `overrides` | `resolutions` | `resolutions` |

`npm outdated` and `yarn outdated` (Yarn Classic) exit with status 1 when anything is outdated. That is not
an error.

## Per-package checklist

Copy this for each package and check items off:

```
- [ ] Step 1: classified (Wanted and Latest split, family grouped, package.json range and pins checked)
- [ ] Step 2: release notes fetched
- [ ] Step 3: evaluated, recommendation is Accept or Hold
- [ ] Step 4: gem coupling checked
- [ ] Step 5 (Accept only): snapshot taken, updated, installed version confirmed, build and tests run
- [ ] Verification plan, new feature report and upgrade report updated
```

## Artifacts

Write artifacts to `.claude/npm-updates/` at the repository root (`git rev-parse --show-toplevel`), even
while working in a nested project, so they accumulate across packages and projects in a session:
- The three reports below: one of each per session, covering every project.
- Files that belong to one project, its snapshot and its Yarn peer-dependency baseline, go in
  `.claude/npm-updates/<dir>/`, where `<dir>` is the project's path from the repository root. For the root
  project that is `.claude/npm-updates/` itself; for `packages/admin` it is
  `.claude/npm-updates/packages/admin/`. Separate folders keep one project's snapshot from overwriting
  another's.

### Verification plan → `.claude/npm-updates/verification-plan.md`

```markdown
# Verification Plan

## Package: <package_name>
- Current Version: <current_version>
- Target Version: <target_version>
- Release Type: Patch / Minor / Major

### Checks
- [ ]
```

### New feature report → `.claude/npm-updates/new-feature-report.md`

```markdown
# New Feature Report

## Package: <package_name>
- Current Version: <current_version>
- Target Version: <target_version>

### New Features Not Currently Used
-
```

### Upgrade report (required) → `.claude/npm-updates/upgrades-YYYY-MM-DD.md`

After every session, write this file (using today's date, a new file each session) with a row for every
update that was evaluated. A package with separate Wanted and Latest updates (Step 1) gets two rows, and a
package updated in two projects gets a row for each:

```markdown
# NPM Upgrade Report — YYYY-MM-DD

Package manager: <npm x.y / Yarn x.y>

| Package | Directory | From | To | Type | Status | Notes |
|---------|-----------|------|----|------|--------|-------|
| package-name | . | x.y.z | x.y.z | patch/minor/major | ✅ Updated / ⏸ Hold / ❌ Blocked | reason if not updated |
```

Status values:
- `✅ Updated`: the upgrade ran and build and tests pass.
- `⏸ Hold`: you decided not to update (breaking change, planned separately, paired gem must go first).
- `❌ Blocked`: the package manager can't resolve the update because another package constrains it (name the
  blocking package).

## Update workflow

### Step 1 — Identify candidate

For each package in the outdated report, record its name, current (installed) version and latest published
version, classify the gap from current to latest as Patch / Minor / Major, and note whether it is a
`dependency` or `devDependency`.

The report also has a **Wanted** column: the newest version the `package.json` range allows. When Wanted is
newer than Current but older than Latest, treat it as two updates, each classified and evaluated on its
own: Current → Wanted (in range, usually low risk) and Wanted → Latest (often a major). Do the Wanted update
first, so a Hold or Blocked on Latest doesn't also leave the safe update undone.

Below 1.0, classify one place higher, because npm treats the first non-zero number as the major version
(`^0.3.1` doesn't reach `0.4.0`): `0.3.x` → `0.4.0` is Major and `0.3.1` → `0.3.2` is Minor. In `0.0.x`,
every bump is Major.

Group packages that are released or used together into a **family**, and treat each family as one update:
- packages from one repository that share a version line (`@babel/core` and `@babel/preset-env`)
- a tool and its companion packages (`jest`, `babel-jest` and `jest-environment-jsdom`; `eslint` and its
  plugins; `typescript` and `@typescript-eslint/*`)
- `@types/<pkg>` and `<pkg>`

Read each member's release notes, but upgrade, test, roll back and record Hold or Blocked for the family
as a whole. Upgrading only some members leaves them on mismatched versions, which fails in ways the full
upgrade wouldn't. Only members that appear in the outdated report are part of the update. Each member
still gets its own report row, with the family named in Notes.

Check the version range in `package.json` (for example `"^1.0.0"`, `"~2.3"`, `">=4"`). If the range
already allows the latest version, the **upgrade in range** command is enough. If the range must be widened
to reach it, note that `package.json` must change and include the new range in the recommendation.

Also check the pins (`overrides` for npm, `resolutions` for Yarn). An upgrade won't move a package, or a
dependency it pulls in, past a pin. Update or remove the pin as part of the upgrade, or record Hold or
Blocked with the reason. After a major bump, check whether each security pin is still needed.

### Step 2 — Review release notes (mandatory)

Find the repository with `npm view <package_name> repository.url repository.directory homepage` (this
works in Yarn projects too). A `repository.directory` means the package is one of several published from
the same repository (`@rails/*` from rails/rails, `@babel/*`), so its notes live in that folder and its
release tags are often named `<package_name>@x.y.z` rather than `vx.y.z`.

Fetch the upstream release notes. Prefer the `gh` CLI when it is installed, because it reads GitHub
directly instead of scraping pages. Try these sources in order:
1. GitHub releases: `gh release list -R <owner>/<repo>`, then `gh release view <tag> -R <owner>/<repo>`
   for each release in the range (or `https://github.com/<owner>/<repo>/releases`). In a multi-package
   repository, pick only the tags for this package.
2. The changelog: `<directory>/CHANGELOG.md` when there is a `repository.directory`, otherwise the root
   `CHANGELOG.md` (also try `CHANGES.md`, `History.md`). Read it with
   `gh api repos/<owner>/<repo>/contents/<path> -H 'Accept: application/vnd.github.raw'` or
   `https://github.com/<owner>/<repo>/blob/main/<path>` (also try `master`).
3. The package's npm page: `https://www.npmjs.com/package/<package_name>?activeTab=versions`

Extract the changelog entries between the current and target versions, migration or upgrade guides, and
breaking change notices.

Do not summarize or infer release notes without fetching them. If none can be found, say so and flag the
package for manual review.

### Step 3 — Evaluate

**Patch releases:** accept by default, after checking the notes for breaking changes (some maintainers
ship them in patches).

**Minor and major releases:** evaluate breaking changes, deprecations, API or config changes, and peer
dependency changes (for example a newer Node or a paired gem update).
- Grep the codebase for each changed or removed API. If the project uses it, add a verification check.
- Features the project doesn't use yet go in the new feature report.

Recommend **Hold** when any of these apply:
- Major version with breaking changes that affect APIs used in this project
- Requires a Node version bump beyond what `engines` in `package.json` currently specifies
- A paired gem must be updated first (for example `@hotwired/turbo-rails` is coupled to the `turbo-rails` gem)
- The target version falls outside a gem's declared `peerDependencies` range (Step 4)
- Release notes indicate known regressions or instability (yanked versions, open critical issues)
- Requires significant code migration that should be planned separately

Every package is recommended as **Accept** or **Hold**. (An Accept can still end up Blocked at Step 5.)

### Step 4 — Gem coupling check

Some npm packages are tightly coupled to a Rails gem and must be updated together:

| npm package | Rails gem |
|---|---|
| `@hotwired/turbo-rails` | `turbo-rails` |
| `@hotwired/stimulus` | `stimulus-rails` |
| `@rails/activestorage` | `activestorage` (part of Rails) |
| `@rails/actioncable` | `actioncable` (part of Rails) |

`@hotwired/stimulus` and `stimulus-rails` are only loosely coupled, with no version lockstep. Check them,
but don't require them to move together.

Gems that ship JavaScript or stylesheets without their own `node_modules` (platform_ui, for example) import
npm packages from the app and declare them as `peerDependencies` in the gem's `package.json` (find it with
`bundle info --path <gem>`). The target version must satisfy that range. If it doesn't, Hold until the gem
supports it.

If a package has a coupled gem:
- check whether the gem version is already compatible with the target npm version
- if both need updating, coordinate them (gem first, then npm, or the reverse, per the package's docs); see
  the `rails-gem-update` skill
- add a verification check

### Step 5 — Execute update

Once a package is recommended as **Accept**, update it on its own, with its family (Step 1), or as part
of a batch.

**Batching low-risk packages.** Building and testing after every package is slow on a long list, so you can
update several packages together and build and test once. A package can join a batch only if it is a Patch
release (after the `0.x` rule in Step 1), its notes show no breaking changes, it has no gem coupling, and
neither its range nor a pin has to change. A family can join only if every member qualifies. Everything
else goes on its own. Each package in a batch still gets its own release notes, evaluation and report row.

1. **Snapshot** `package.json` and the lockfile before the package (or the whole family or batch), so a
   failure rolls back only that update. From the repository root, with `<dir>` the project's path (see
   Artifacts):
   ```
   mkdir -p .claude/npm-updates/<dir>/snapshot
   cp <dir>/package.json <dir>/<lockfile> .claude/npm-updates/<dir>/snapshot/
   ```
   If the update also touches gems, copy `Gemfile` and `Gemfile.lock` into the same snapshot folder. On
   Yarn, also record the peer-dependency baseline before the first upgrade in each directory (see below).

2. **Upgrade** with the **upgrade in range** command if the `package.json` range already allows the target
   version. If the range must be widened, use **widen range and upgrade**, which changes both
   `package.json` and the lockfile. For a family or a batch, pass all the package names to one command.

   If another package's peer dependency rules out the target version, roll back (see step 7) and record
   `❌ Blocked`, naming the blocking package. npm fails with an `ERESOLVE` error; don't get around it with
   `--force` or `--legacy-peer-deps`. Yarn only warns, so compare its warnings with the baseline: a new
   warning that names the target package means Blocked too.

3. **Confirm the target version installed** with the **show installed version** command. Yarn can finish
   without error and leave the old version in place. If the package is held back, find out what holds it
   (`npm explain <pkg>` or `yarn why <pkg>`). If it is this project's range or pin, fix it per Step 1 and
   re-run the upgrade. If another package constrains it, roll back (see step 7) and record `❌ Blocked`,
   naming that package.

4. **Rebuild assets** to catch bundler errors: run the `build` script. It may not build CSS. If
   `package.json` has a `build:css` script, run it whenever the package ships stylesheets or is part of the
   PostCSS or Sass toolchain.

5. **Run the JavaScript test suite** with the `test` script.

6. **If build and tests pass,** record `✅ Updated` and proceed to the next package or finalize.

7. **If build or tests fail,** diagnose the failure.
   - If the fix is straightforward (a renamed import, a changed config key), apply it and re-run.
   - If a batch fails and the cause isn't obvious, roll back the whole batch, split it in half and retry
     each half, until you find the package that fails. Then handle that package on its own.
   - If it is complex or unclear, roll back this package and recommend Hold. Copy `package.json` and the
     lockfile from `.claude/npm-updates/<dir>/snapshot/` back to `<dir>`, then run **install from
     lockfile** there. On Yarn Berry, also check `git status .yarn` and remove cache files the upgrade
     added. Undo only the code edits you made for this package, and leave all other uncommitted changes
     alone. If you also snapshotted `Gemfile` and `Gemfile.lock`, copy them back to the repository root and
     run `bundle install`.
   - Add the failure details to the verification plan for follow-up.

8. **Do not commit automatically.** Present the results and let the user decide when to commit.

#### Yarn peer-dependency baseline

Most Yarn projects already have peer-dependency warnings before any upgrade, so a warning on its own
doesn't mean the upgrade caused it. Before the first upgrade in a directory, save the existing warnings to
`.claude/npm-updates/<dir>/peer-warnings-baseline.txt`:
- Yarn Classic: the `unmet peer dependency` and `incorrect peer dependency` lines from
  `yarn install --frozen-lockfile --force`. Without `--force`, an installed project reports
  "Already up-to-date" and prints no warnings.
- Yarn 4: the output of `yarn explain peer-requirements`, which lists every peer requirement and marks
  unmet ones with ✘. Installs only print a summary (`YN0086`).
- Yarn 2 and 3: the `YN0060` lines from `yarn install --immutable`.

After each upgrade, collect the same warnings again and diff them against the baseline. Only a new warning
that names a package you just upgraded counts. After an update is recorded `✅ Updated`, refresh the
baseline.

## Per-package output format

Present each evaluated package like this:

```markdown
## <package_name>

- Current Version: <x.y.z>
- Target Version: <x.y.z>
- Release Type: Patch / Minor / Major
- Dependency Type: dependency / devDependency
- package.json Range: <current range or "exact">
- Range Change Required: Yes (new range) / No
- Recommendation: Accept / Hold
- Hold Reason: <reason, if applicable>
- Gem Coupling: Yes (<gem_name>) / No
- Build/Tests Pass: Yes / No / Not yet run

### Verification Plan Additions
- [ ]

### New Feature Report Additions
-
```

## Session completion status (required)

Always end a session with a status block so the user knows whether the task is finished:

```
## Update Session Status

- Packages updated this session: <count> (<list>)
- Packages held: <count> (<list with hold reasons>)
- Packages blocked: <count> (<list with blocking packages>)
- Packages not yet evaluated: <count> (<list>)
- Task complete: Yes / No

<If No>: Run this skill again to continue with the remaining packages.
```

**Never imply the task is done if packages remain in the outdated report that have not been evaluated.** If
the session ends before all packages are processed, tell the user how many are left and that another run is
needed.
