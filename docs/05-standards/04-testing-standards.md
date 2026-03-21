# Testing Standards

Version: 1.0
Date: 2026-03-20

## Purpose

Define mandatory testing quality, layering, and release-readiness standards.

## Non-Negotiable Rules

1. Tests must assert business outcomes, not status-only behavior.
2. One test should validate one behavior unless explicitly defined as flow test.
3. Error-path tests must assert error codes/messages, not only status.
4. RBAC-sensitive write flows must test relevant role outcomes.
5. New behavior must ship with matching automated test coverage.

## Test Layer Standards

- API tests: transport contracts, auth gates, error shape.
- Service tests: business rules and side effects without HTTP layer coupling.
- Repository tests: query/filter/pagination correctness.
- Integration flow tests: multi-step business behavior across layers.
- Frontend tests: component/hook/store behavior, plus e2e journeys where needed.

## Quality Gate Standards

- A change is not complete without updated tests for changed behavior.
- Flaky tests must be fixed or quarantined with explicit follow-up ownership.
- Critical-path suites must pass before merge/release.
- Coverage trend should be monitored, but coverage alone is never release evidence.

## Test Data and Fixture Standards

- Repeated setup should be extracted into fixtures/helpers.
- Test data should be deterministic and readable.
- Avoid hidden coupling to execution order.
- Cleanup should be automatic through test infrastructure patterns.

## Reporting Standards

- Maintain concise test reports per sprint/release in `docs/04-testing/`.
- Report must include:
- build/commit tested
- pass/fail/skipped/flaky counts
- critical suite status
- blocking defects
- go/no-go recommendation

## Definition of Done (Testing)

- Required tests implemented and passing.
- Changed behavior has direct assertions for business outcomes.
- Critical regression risk areas covered.
- Test report evidence updated for release-bound work.
- Traceability references include test proof.
