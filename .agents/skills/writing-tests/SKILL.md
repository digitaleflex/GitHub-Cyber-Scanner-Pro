---
name: writing-tests
description: Comprehensive guide for writing unit tests, integration tests, and component tests in AiderDesk using Vitest. Use when creating new tests, configuring mocks, or organizing test files.
---

# Writing Tests

Write effective tests using Vitest and React Testing Library.

## Quick Start

Create a unit test in `src/common/__tests__/utils/math.test.ts`:

```typescript
import { describe, it, expect } from 'vitest';
import { add } from '../../utils/math';

describe('math utility', () => {
  it('adds two numbers correctly', () => {
    expect(add(1, 2)).toBe(3);
  });
});
```

Run tests with `npm run test`.

## Core Patterns

### Unit Testing
Focus on pure functions and logic in `src/main` or `src/common`. Use `vi.mock()` for dependencies.
- [references/unit-testing-examples.md](references/unit-testing-examples.md)

### Component Testing
Test React components in `src/renderer`. Focus on user interactions and props.
- [references/component-testing-patterns.md](references/component-testing-patterns.md)

### Mocking
Use centralized mock factories for consistent testing across components and contexts.
- [references/mocking-guide.md](references/mocking-guide.md) - Mock factories and API patterns

## Advanced Usage

For detailed information:
- [references/test-organization.md](references/test-organization.md) - Directory structure and naming
- [references/running-tests.md](references/running-tests.md) - CLI commands and coverage
- [references/best-practices.md](references/best-practices.md) - Principles and patterns
- [references/test-patterns.md](references/test-patterns.md) - Code templates
- [assets/test-checklist.md](assets/test-checklist.md) - Pre-flight checklist
