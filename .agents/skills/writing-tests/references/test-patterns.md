# Test Patterns

Quick-reference templates for common testing scenarios.

## Unit Test (Node/Common)
```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { myFunction } from '../myModule';

describe('myFunction', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should return expected value', () => {
    const result = myFunction('input');
    expect(result).toBe('output');
  });
});
```

## Component Test (Renderer)
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { MyComponent } from '../MyComponent';

describe('MyComponent', () => {
  it('should trigger API call on click', () => {
    render(<MyComponent />);
    
    fireEvent.click(screen.getByRole('button'));
    
    expect(window.api.doSomething).toHaveBeenCalled();
  });
});
```

## Hook Test (Renderer)
```typescript
import { renderHook, act } from '@testing-library/react';
import { useMyHook } from '../useMyHook';

it('should update state', () => {
  const { result } = renderHook(() => useMyHook());
  
  act(() => {
    result.current.increment();
  });
  
  expect(result.current.count).toBe(1);
});
```

## Component Test with Mock Factories (Renderer)
```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { MyComponent } from '../MyComponent';

import { createMockApi } from '@/__tests__/mocks/api';
import { createMockTaskContext, createMockModelProviderContext } from '@/__tests__/mocks/contexts';

import { useApi } from '@/contexts/ApiContext';
import { useTask } from '@/contexts/TaskContext';
import { useModelProviders } from '@/contexts/ModelProviderContext';

// Mock contexts
vi.mock('@/contexts/ApiContext', () => ({ useApi: vi.fn() }));
vi.mock('@/contexts/TaskContext', () => ({ useTask: vi.fn() }));
vi.mock('@/contexts/ModelProviderContext', () => ({ useModelProviders: vi.fn() }));

describe('MyComponent', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Setup mock factories
    vi.mocked(useApi).mockReturnValue(createMockApi({
      // API-specific overrides
      getOpenProjects: vi.fn(() => Promise.resolve([])),
    }));
    
    vi.mocked(useTask).mockReturnValue(createMockTaskContext({
      getTaskState: vi.fn(() => ({
        loading: false,
        loaded: true,
        processing: false,
        messages: [],
        // ... other task state properties
      })),
    }));
    
    vi.mocked(useModelProviders).mockReturnValue(createMockModelProviderContext({
      models: [],
      modelsLoading: false,
    }));
  });

  it('should render with mocked contexts', async () => {
    render(<MyComponent />);
    
    await waitFor(() => {
      expect(screen.getByText('Expected Content')).toBeInTheDocument();
    });
  });

  it('should handle user interactions', async () => {
    const { rerender } = render(<MyComponent />);
    
    fireEvent.click(screen.getByRole('button'));
    
    await waitFor(() => {
      expect(window.api.someMethod).toHaveBeenCalled();
    });
  });
});
```
