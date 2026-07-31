# Test Organization

Detailed directory structure and naming conventions for AiderDesk.

## Directory Structure

AiderDesk uses a **colocated** test structure for components and local logic, and a **mirrored** structure for global services or shared utilities.

### Colocated (Preferred for Components/Hooks)
Place tests in a `__tests__` folder immediately adjacent to the file(s) being tested. This keeps tests close to the implementation and simplifies refactoring.

```
src/renderer/src/components/
└── MyComponent/
    ├── MyComponent.tsx
    ├── MyComponent.scss
    └── __tests__/
        └── MyComponent.test.tsx
```

### Mirrored (For Global/Shared Logic)
For global services, shared utilities, or integration tests that span multiple modules, use a mirrored structure.

```
src/
├── main/
│   └── __tests__/
│       ├── integration/    # Multi-module interaction tests
│       └── setup.ts        # Main process test configuration
├── common/
│   └── __tests__/          # Shared utility and type tests
```

## Naming Conventions

Follow these patterns to ensure tests are automatically discovered:

- **Components**: `[ComponentName].test.tsx`
- **Hooks**: `[hookName].test.ts`
- **Utilities/Services**: `[FileName].test.ts`
- **Integration**: `[feature-name].integration.test.ts`

## Environments

| Environment | Purpose | Configuration |
| :--- | :--- | :--- |
| **Node** | Main process, preload, common | `vitest.config.node.ts` |
| **Web** | Renderer process (React, JSDOM) | `vitest.config.web.ts` |
| **MCP** | MCP Server components | `vitest.config.mcp.ts` |
