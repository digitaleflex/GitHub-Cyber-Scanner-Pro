# Test Checklist

Use this checklist before submitting code to ensure testing standards are met.

## 1. Coverage
- [ ] New logic has corresponding unit tests.
- [ ] New UI components have basic render and interaction tests.
- [ ] Edge cases (null, empty, error states) are covered.

## 2. Best Practices
- [ ] Tests use imperative voice in descriptions (e.g., "should return..." instead of "returns...").
- [ ] Mocks are cleared in `beforeEach`.
- [ ] Async operations use `await` and `waitFor` where appropriate.
- [ ] Assertions are specific and descriptive.

## 3. Organization
- [ ] Test files are placed in the correct `__tests__` directory.
- [ ] File naming follows the `[Name].test.ts[x]` convention.
- [ ] No large data blobs in test files (use `assets/` or local constants).

## 4. Execution
- [ ] `npm run typecheck` passes.
- [ ] `npm run test` passes locally.
- [ ] No `console.log` or `vi.fn().mockImplementation(() => console.log(...))` left in tests.
