# Running Tests

Commands and tools for executing and analyzing tests in AiderDesk.

## Execution Commands

| Command | Description |
| :--- | :--- |
| `npm run test` | Run all tests across all environments |
| `npm run test:node` | Run Main, Preload, and Common tests |
| `npm run test:web` | Run Renderer (React) tests |
| `npm run test:mcp` | Run MCP Server tests |
| `npm run test:watch` | Run tests in watch mode for development |

## Analysis and UI

### Coverage Reports
Generate a comprehensive coverage report using V8:
```bash
npm run test:coverage
```
Reports are available in the `coverage/` directory.

### Vitest UI
Open the interactive browser-based test runner:
```bash
npm run test:ui
```

## Continuous Integration
Tests are automatically executed on every Pull Request. Ensure all tests pass locally before pushing:
1. Run `npm run typecheck` to verify types.
2. Run `npm run test` to verify logic.
