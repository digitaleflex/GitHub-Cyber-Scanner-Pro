# React Component Testing Patterns

This file provides comprehensive patterns for testing React components in AiderDesk.

## Component Testing Templates

### Basic Component Structure

```tsx
// src/renderer/src/components/Button/Button.tsx
import { clsx } from 'clsx';

type Props = {
  children: React.ReactNode;
  onClick: () => void;
  variant?: 'primary' | 'secondary';
  disabled?: boolean;
  loading?: boolean;
};

export const Button = ({
  children,
  onClick,
  variant = 'primary',
  disabled = false,
  loading = false,
}: Props) => {
  const handleClick = () => {
    if (!disabled && !loading) {
      onClick();
    }
  };

  return (
    <button
      onClick={handleClick}
      disabled={disabled || loading}
      className={clsx(
        'px-4 py-2 rounded font-medium transition-colors',
        {
          'bg-blue-600 text-white hover:bg-blue-700': variant === 'primary',
          'bg-gray-200 text-gray-900 hover:bg-gray-300': variant === 'secondary',
          'opacity-50 cursor-not-allowed': disabled || loading,
        }
      )}
    >
      {loading ? 'Loading...' : children}
    </button>
  );
};
```

```tsx
// src/renderer/src/__tests__/components/Button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from '../Button';

describe('Button Component', () => {
  const defaultProps = {
    children: 'Click me',
    onClick: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render children correctly', () => {
    render(<Button {...defaultProps} />);
    
    expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument();
  });

  it('should call onClick when clicked', () => {
    render(<Button {...defaultProps} />);
    
    fireEvent.click(screen.getByRole('button'));
    
    expect(defaultProps.onClick).toHaveBeenCalledTimes(1);
  });

  it('should apply primary variant by default', () => {
    render(<Button {...defaultProps} />);
    
    const button = screen.getByRole('button');
    expect(button).toHaveClass('bg-blue-600', 'text-white');
  });

  it('should apply secondary variant', () => {
    render(<Button {...defaultProps} variant="secondary" />);
    
    const button = screen.getByRole('button');
    expect(button).toHaveClass('bg-gray-200', 'text-gray-900');
  });

  it('should be disabled when disabled prop is true', () => {
    render(<Button {...defaultProps} disabled={true} />);
    
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
    expect(button).toHaveClass('opacity-50');
  });

  it('should show loading state', () => {
    render(<Button {...defaultProps} loading={true} />);
    
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('should not call onClick when disabled', () => {
    render(<Button {...defaultProps} disabled={true} />);
    
    fireEvent.click(screen.getByRole('button'));
    
    expect(defaultProps.onClick).not.toHaveBeenCalled();
  });

  it('should not call onClick when loading', () => {
    render(<Button {...defaultProps} loading={true} />);
    
    fireEvent.click(screen.getByRole('button'));
    
    expect(defaultProps.onClick).not.toHaveBeenCalled();
  });
});
```

## Complex Component Patterns

### Form Component Testing

```tsx
// src/renderer/src/components/ProjectForm/ProjectForm.tsx
type Props = {
  initialData?: ProjectData;
  onSubmit: (data: ProjectData) => void;
  onCancel: () => void;
};

export const ProjectForm = ({ initialData, onSubmit, onCancel }: Props) => {
  const [formData, setFormData] = useState<ProjectData>({
    name: initialData?.name || '',
    path: initialData?.path || '',
    description: initialData?.description || '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};
    
    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }
    if (!formData.path.trim()) {
      newErrors.path = 'Path is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (validateForm()) {
      onSubmit(formData);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium mb-1">Name</label>
        <input
          type="text"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          className="w-full px-3 py-2 border rounded"
          data-testid="name-input"
        />
        {errors.name && (
          <p className="text-red-500 text-sm mt-1">{errors.name}</p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Path</label>
        <input
          type="text"
          value={formData.path}
          onChange={(e) => setFormData({ ...formData, path: e.target.value })}
          className="w-full px-3 py-2 border rounded"
          data-testid="path-input"
        />
        {errors.path && (
          <p className="text-red-500 text-sm mt-1">{errors.path}</p>
        )}
      </div>

      <div className="flex gap-2">
        <button
          type="submit"
          className="px-4 py-2 bg-blue-600 text-white rounded"
        >
          Save
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 bg-gray-200 rounded"
        >
          Cancel
        </button>
      </div>
    </form>
  );
};
```

```tsx
// src/renderer/src/__tests__/components/ProjectForm.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ProjectForm } from '../ProjectForm';

describe('ProjectForm Component', () => {
  const mockOnSubmit = vi.fn();
  const mockOnCancel = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render form fields correctly', () => {
    render(
      <ProjectForm 
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.getByLabelText('Name')).toBeInTheDocument();
    expect(screen.getByLabelText('Path')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Save' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument();
  });

  it('should populate with initial data', () => {
    const initialData = {
      name: 'Test Project',
      path: '/test/path',
      description: 'Test Description'
    };

    render(
      <ProjectForm 
        initialData={initialData}
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.getByDisplayValue('Test Project')).toBeInTheDocument();
    expect(screen.getByDisplayValue('/test/path')).toBeInTheDocument();
  });

  it('should show validation errors for empty fields', async () => {
    render(
      <ProjectForm 
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    );

    await userEvent.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() => {
      expect(screen.getByText('Name is required')).toBeInTheDocument();
      expect(screen.getByText('Path is required')).toBeInTheDocument();
    });

    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it('should submit valid form data', async () => {
    render(
      <ProjectForm 
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    );

    await userEvent.type(screen.getByLabelText('Name'), 'Valid Project');
    await userEvent.type(screen.getByLabelText('Path'), '/valid/path');

    await userEvent.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        name: 'Valid Project',
        path: '/valid/path',
        description: '',
      });
    });

    expect(mockOnSubmit).toHaveBeenCalledTimes(1);
  });

  it('should call onCancel when cancel button clicked', async () => {
    render(
      <ProjectForm 
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    );

    await userEvent.click(screen.getByRole('button', { name: 'Cancel' }));

    expect(mockOnCancel).toHaveBeenCalledTimes(1);
  });

  it('should clear errors when user starts typing', async () => {
    render(
      <ProjectForm 
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    );

    // Trigger validation error
    await userEvent.click(screen.getByRole('button', { name: 'Save' }));
    await waitFor(() => {
      expect(screen.getByText('Name is required')).toBeInTheDocument();
    });

    // Start typing in name field
    await userEvent.type(screen.getByLabelText('Name'), 'a');

    await waitFor(() => {
      expect(screen.queryByText('Name is required')).not.toBeInTheDocument();
    });
  });
});
```

## Hooks Testing Patterns

### Custom Hook Testing

```tsx
// src/renderer/src/hooks/useDebounce.ts
import { useState, useEffect } from 'react';

export const useDebounce = <T>(value: T, delay: number): T => {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
};
```

```tsx
// src/renderer/src/__tests__/hooks/useDebounce.test.tsx
import { renderHook, act } from '@testing-library/react';
import { vi } from 'vitest';
import { useDebounce } from '../useDebounce';

describe('useDebounce', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should return initial value immediately', () => {
    const { result } = renderHook(() => useDebounce('test', 500));
    
    expect(result.current).toBe('test');
  });

  it('should not update value before delay', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 500),
      { initialProps: { value: 'initial' } }
    );

    rerender({ value: 'updated' });

    expect(result.current).toBe('initial');
  });

  it('should update value after delay', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 500),
      { initialProps: { value: 'initial' } }
    );

    rerender({ value: 'updated' });

    act(() => {
      vi.advanceTimersByTime(500);
    });

    expect(result.current).toBe('updated');
  });

  it('should cancel previous timeout on value change', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 500),
      { initialProps: { value: 'initial' } }
    );

    rerender({ value: 'first' });
    rerender({ value: 'second' });

    act(() => {
      vi.advanceTimersByTime(500);
    });

    expect(result.current).toBe('second');
  });
});
```

## Component Testing with Mock Factories

### Using Mock Factories for Consistency

Instead of creating inline mocks, use the centralized mock factories:

```tsx
// src/renderer/src/__tests__/components/ProjectList.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { ProjectList } from '../ProjectList';
import { createMockApi } from '@/__tests__/mocks/api';
import { useApi } from '@/contexts/ApiContext';

// Mock the context
vi.mock('@/contexts/ApiContext', () => ({ useApi: vi.fn() }));

describe('ProjectList with Mock Factories', () => {
  const mockProjects: Project[] = [
    { id: '1', name: 'Project 1', path: '/path/1', createdAt: new Date() },
    { id: '2', name: 'Project 2', path: '/path/2', createdAt: new Date() },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Use the mock factory
    vi.mocked(useApi).mockReturnValue(createMockApi());
  });

  it('should render projects after loading', async () => {
    // Override specific API behavior for this test
    vi.mocked(window.api.getOpenProjects).mockResolvedValue(mockProjects);
    
    render(<ProjectList />);

    await waitFor(() => {
      expect(screen.getByTestId('project-list')).toBeInTheDocument();
      expect(screen.getByText('Project 1')).toBeInTheDocument();
      expect(screen.getByText('Project 2')).toBeInTheDocument();
    });

    expect(window.api.getOpenProjects).toHaveBeenCalledTimes(1);
  });

  it('should handle API errors', async () => {
    const errorMessage = 'API Error';
    vi.mocked(window.api.getOpenProjects).mockRejectedValue(new Error(errorMessage));
    
    render(<ProjectList />);

    await waitFor(() => {
      expect(screen.getByTestId('error')).toBeInTheDocument();
      expect(screen.getByText(`Error: ${errorMessage}`)).toBeInTheDocument();
    });

    expect(window.api.getOpenProjects).toHaveBeenCalledTimes(1);
  });
});
```

### Complex Component with Multiple Contexts

```tsx
// src/renderer/src/__tests__/components/TaskView.test.tsx
import { createMockApi } from '@/__tests__/mocks/api';
import { createMockTaskContext, createMockModelProviderContext, createMockAgentsContext } from '@/__tests__/mocks/contexts';

import { useApi } from '@/contexts/ApiContext';
import { useTask } from '@/contexts/TaskContext';
import { useModelProviders } from '@/contexts/ModelProviderContext';
import { useAgents } from '@/contexts/AgentsContext';

// Mock all contexts
vi.mock('@/contexts/ApiContext', () => ({ useApi: vi.fn() }));
vi.mock('@/contexts/TaskContext', () => ({ useTask: vi.fn() }));
vi.mock('@/contexts/ModelProviderContext', () => ({ useModelProviders: vi.fn() }));
vi.mock('@/contexts/AgentsContext', () => ({ useAgents: vi.fn() }));

describe('TaskView with Multiple Contexts', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Setup all mocks using factories
    vi.mocked(useApi).mockReturnValue(createMockApi());
    vi.mocked(useTask).mockReturnValue(createMockTaskContext());
    vi.mocked(useModelProviders).mockReturnValue(createMockModelProviderContext());
    vi.mocked(useAgents).mockReturnValue(createMockAgentsContext());
  });

  it('should render with all contexts properly mocked', () => {
    render(<TaskView project={mockProject} task={mockTask} updateTask={vi.fn()} inputHistory={[]} />);
    
    expect(screen.getByTestId('task-bar')).toBeInTheDocument();
    expect(screen.getByTestId('messages')).toBeInTheDocument();
  });
});
```

## Integration Component Testing

### Component with API Integration

```tsx
// src/renderer/src/components/ProjectList/ProjectList.tsx
export const ProjectList = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadProjects = async () => {
      try {
        const data = await window.api.getOpenProjects();
        setProjects(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load projects');
      } finally {
        setLoading(false);
      }
    };

    loadProjects();
  }, []);

  const handleProjectSelect = (project: Project) => {
    window.api.setActiveProject(project.path);
  };

  if (loading) return <div data-testid="loading">Loading projects...</div>;
  if (error) return <div data-testid="error">Error: {error}</div>;

  return (
    <div data-testid="project-list">
      {projects.map((project) => (
        <div 
          key={project.id} 
          data-testid={`project-${project.id}`}
          onClick={() => handleProjectSelect(project)}
          className="p-4 border rounded mb-2 cursor-pointer hover:bg-gray-50"
        >
          <h3>{project.name}</h3>
          <p className="text-sm text-gray-600">{project.path}</p>
        </div>
      ))}
    </div>
  );
};
```

```tsx
// src/renderer/src/__tests__/components/ProjectList.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { ProjectList } from '../ProjectList';
import { Project } from '@common/types';

describe('ProjectList Integration', () => {
  const mockProjects: Project[] = [
    { id: '1', name: 'Project 1', path: '/path/1', createdAt: new Date() },
    { id: '2', name: 'Project 2', path: '/path/2', createdAt: new Date() },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should show loading state initially', () => {
    render(<ProjectList />);
    
    expect(screen.getByTestId('loading')).toBeInTheDocument();
    expect(screen.getByText('Loading projects...')).toBeInTheDocument();
  });

  it('should render projects after loading', async () => {
    vi.mocked(window.api.getOpenProjects).mockResolvedValue(mockProjects);
    
    render(<ProjectList />);

    await waitFor(() => {
      expect(screen.getByTestId('project-list')).toBeInTheDocument();
      expect(screen.getByText('Project 1')).toBeInTheDocument();
      expect(screen.getByText('Project 2')).toBeInTheDocument();
      expect(screen.getByText('/path/1')).toBeInTheDocument();
      expect(screen.getByText('/path/2')).toBeInTheDocument();
    });

    expect(window.api.getOpenProjects).toHaveBeenCalledTimes(1);
  });

  it('should handle API errors', async () => {
    const errorMessage = 'API Error';
    vi.mocked(window.api.getOpenProjects).mockRejectedValue(new Error(errorMessage));
    
    render(<ProjectList />);

    await waitFor(() => {
      expect(screen.getByTestId('error')).toBeInTheDocument();
      expect(screen.getByText(`Error: ${errorMessage}`)).toBeInTheDocument();
    });

    expect(window.api.getOpenProjects).toHaveBeenCalledTimes(1);
  });

  it('should handle project selection', async () => {
    vi.mocked(window.api.getOpenProjects).mockResolvedValue(mockProjects);
    
    render(<ProjectList />);

    await waitFor(() => {
      const project1 = screen.getByTestId('project-1');
      fireEvent.click(project1);
    });

    expect(window.api.setActiveProject).toHaveBeenCalledWith('/path/1');
  });

  it('should render empty state when no projects', async () => {
    vi.mocked(window.api.getOpenProjects).mockResolvedValue([]);
    
    render(<ProjectList />);

    await waitFor(() => {
      expect(screen.getByTestId('project-list')).toBeInTheDocument();
      expect(screen.queryByText(/Project/)).not.toBeInTheDocument();
    });
  });
});
```