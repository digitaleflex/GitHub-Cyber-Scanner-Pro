# Mocking Guide

AiderDesk provides pre-configured mocks for Electron and internal APIs.

## Global Mocks

Global mocks are defined in the `setup.ts` files and are automatically available.

### Main Process (`src/main/__tests__/setup.ts`)
The following modules are mocked by default:
- `electron` (app, ipcMain, dialog, etc.)
- `fs` (standard file system operations)
- `path` (cross-platform path handling)
- `winston` (logging)

### Renderer Process (`src/renderer/src/__tests__/setup.ts`)
The `window` object is extended with:
- `window.electron`: Dialog and basic Electron helpers
- `window.api`: The `ApplicationAPI` used by React components

## Custom Mocks

Use `vi.mock()` to mock internal modules or external dependencies.

### Mocking Internal Modules
```typescript
import { vi } from 'vitest';

vi.mock('@/main/services/ProjectManager', () => ({
  ProjectManager: vi.fn().mockImplementation(() => ({
    getProjects: vi.fn().mockResolvedValue([]),
  })),
}));
```

### Mocking the Renderer API
In renderer tests, you can override specific API functions:
```typescript
import { vi } from 'vitest';

// Mock specific API call
vi.mocked(window.api.getOpenProjects).mockResolvedValue([
  { id: '1', name: 'Test' }
]);
```

## Mock Factories

AiderDesk provides centralized mock factories for consistent testing across the codebase.

### Renderer API Mock Factory (`createMockApi`)

Location: `src/renderer/src/__tests__/mocks/api.ts`

Provides comprehensive mock for ApplicationAPI with sensible defaults:

```typescript
import { createMockApi } from '@/__tests__/mocks/api';

// Basic usage - complete API mock
const mockApi = createMockApi();

// Override specific methods
const mockApi = createMockApi({
  getOpenProjects: vi.fn(() => Promise.resolve(mockProjects)),
  setActiveProject: vi.fn(() => Promise.resolve()),
});
```

### Context Mock Factories (`contexts.ts`)

Location: `src/renderer/src/__tests__/mocks/contexts.ts`

Provides mocks for React contexts used throughout the application:

#### Task Context Mock

```typescript
import { createMockTaskContext } from '@/__tests__/mocks/contexts';

// Complete task context mock
const mockTaskContext = createMockTaskContext();

// Override specific methods
const mockTaskContext = createMockTaskContext({
  getTaskState: vi.fn(() => mockTaskState),
  clearSession: vi.fn(),
});
```

#### Model Provider Context Mock

```typescript
import { createMockModelProviderContext } from '@/__tests__/mocks/contexts';

const mockModelProviderContext = createMockModelProviderContext({
  models: [mockModel],
  modelsLoading: false,
});
```

#### Agents Context Mock

```typescript
import { createMockAgentsContext } from '@/__tests__/mocks/contexts';

const mockAgentsContext = createMockAgentsContext({
  profiles: [mockProfile],
  loading: true,
});
```

#### Responsive Hook Mock

```typescript
import { createMockResponsive } from '@/__tests__/mocks/contexts';

const mockResponsive = createMockResponsive({
  isMobile: true,
  isDesktop: false,
});
```

### Main Process Mock Factories

Location: `src/main/__tests__/mocks/`

Main process mocks are split into separate files per type with a barrel export (`index.ts`) for clean imports.

#### Task Mock Factory (`createMockTask`)

File: `src/main/__tests__/mocks/task.ts`

Provides a minimal mock for the Task class with only the properties needed for testing:

```typescript
import { createMockTask } from '@/__tests__/mocks';

// Basic usage - minimal task mock
const mockTask = createMockTask();

// Override specific properties
const mockTask = createMockTask({
  getProjectDir: vi.fn(() => '/custom/project'),
  task: { autoApprove: true } as TaskData,
});
```

**Key pattern**: Minimalist approach - only include properties/methods actually used in tests. This reduces maintenance burden when types change.

#### Settings Mock Factory (`createMockSettings`)

File: `src/main/__tests__/mocks/settings.ts`

Provides a minimal mock for SettingsData:

```typescript
import { createMockSettings } from '@/__tests__/mocks';

const mockSettings = createMockSettings({
  memory: { enabled: false },
});
```

#### Agent Profile Mock Factory (`createMockAgentProfile`)

File: `src/main/__tests__/mocks/agent-profile.ts`

Provides a minimal mock for AgentProfile:

```typescript
import { createMockAgentProfile } from '@/__tests__/mocks';

const mockProfile = createMockAgentProfile({
  useMemoryTools: false,
  useSkillsTools: false,
});
```

### Creating New Mock Factories

When creating a new mock factory for the main process:

1. **Create a dedicated file** for each type (e.g., `task.ts`, `settings.ts`, `agent-profile.ts`)
2. **Use minimalist approach** - only include properties/methods actually used in tests
3. **Add to barrel export** (`index.ts`) for clean imports
4. **Return type**: Use `Partial<ReturnType<typeof createMockFactory>>` for recursive type inference

```typescript
// Example: src/main/__tests__/mocks/my-type.ts
import { vi } from 'vitest';
import { MyType } from '@common/types';

export const createMockMyType = (overrides: Partial<ReturnType<typeof createMockMyType>> = {}) => {
  const defaultMock = {
    // Only include properties needed in tests
    property1: 'default',
    method1: vi.fn(() => 'result'),
  };

  return { ...defaultMock, ...overrides };
};

// Add to src/main/__tests__/mocks/index.ts
export { createMockMyType } from './my-type';
```

### Using Mock Factories in Tests

```typescript
import { createMockApi } from '@/__tests__/mocks/api';
import { createMockTaskContext, createMockModelProviderContext } from '@/__tests__/mocks/contexts';

// Mock contexts
vi.mock('@/contexts/ApiContext', () => ({ useApi: vi.fn() }));
vi.mock('@/contexts/TaskContext', () => ({ useTask: vi.fn() }));
vi.mock('@/contexts/ModelProviderContext', () => ({ useModelProviders: vi.fn() }));

describe('MyComponent', () => {
  beforeEach(() => {
    vi.mocked(useApi).mockReturnValue(createMockApi());
    vi.mocked(useTask).mockReturnValue(createMockTaskContext());
    vi.mocked(useModelProviders).mockReturnValue(createMockModelProviderContext());
  });
});
```

## Best Practices for Mocking
1. **Clear Mocks**: Use `vi.clearAllMocks()` in `beforeEach` to prevent test leakage.
2. **Partial Mocks**: Use `importOriginal` if you only need to mock specific functions of a module.
3. **Type Safety**: Use `vi.mocked()` to get type-safe mock methods.
4. **Use Factories**: Prefer centralized mock factories over inline mock objects for consistency.
5. **DRY Principle**: Extract reusable mock configurations to factory functions.
6. **Test-Specific Overrides**: Use override parameters in factories for test-specific behavior.
