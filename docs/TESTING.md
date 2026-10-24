# Testing Strategy

Backend tests currently cover GST rounding and AY 2026-27 salary-estimate examples. Expand coverage to authentication, permission denial, tenant isolation, encrypted document access, audit-log immutability, database constraints, filing review separation, and GST reconciliation edge cases before production sign-off. Tax fixtures are assessment-year-specific and require qualified CA approval.

Before production promotion, set up CI for linting, unit/API tests, migration checks, dependency/security scanning, and frontend component tests. Promotion requires integration sandbox tests, successful restore drills, security review and sign-off for changed tax rules.
