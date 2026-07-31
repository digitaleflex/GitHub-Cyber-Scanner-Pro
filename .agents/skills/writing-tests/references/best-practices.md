# Testing Best Practices

Follow these principles to write maintainable and reliable tests.

## 1. Test Behavior, Not Implementation
Focus on what the code *does* rather than how it *works*. For components, test user interactions; for utilities, test inputs and outputs.

## 2. Ensure Test Independence
Every test must be able to run in isolation.
- Reset mocks in `beforeEach`.
- Avoid shared state between test files.
- Don't rely on the execution order of `it` blocks.

## 3. Handle Asynchrony Properly
Always `await` promises and use Testing Library's `find*` or `waitFor` helpers for UI updates.

```typescript
// ✅ Good: Waiting for async update
const button = await screen.findByRole('button');
fireEvent.click(button);
await waitFor(() => expect(window.api.save).toHaveBeenCalled());
```

## 4. Use Descriptive Assertions
Use the most specific matcher available to provide better error messages.

```typescript
// ❌ Vague
expect(result.length).toBe(1);

// ✅ Descriptive
expect(result).toContainEqual(expect.objectContaining({ id: '123' }));
```

## 5. Use Centralized Mock Factories
Follow the DRY principle by using mock factories instead of duplicating mock objects:

```typescript
// ❌ Bad: Duplicated mocks in multiple test files
const mockApi = {
  getProjects: vi.fn(),
  saveProject: vi.fn(),
  deleteProject: vi.fn(),
  // ... 20+ more methods
};

// ✅ Good: Use centralized mock factory
import { createMockApi } from '@/__tests__/mocks/api';
const mockApi = createMockApi();
```

Benefits:
- **Consistency**: All tests use the same mock structure
- **Maintainability**: Single place to update mock implementations
- **Type Safety**: Full TypeScript support with proper interfaces
- **Flexibility**: Easy to override specific behavior while keeping defaults

## 6. Coverage Goals
Aim for high coverage in critical business logic:
- **Common Utilities**: 90%+
- **Main Process Services**: 80%+
- **React Components**: 70%+ (focus on complex logic)
