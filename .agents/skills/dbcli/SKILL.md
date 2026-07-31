---
name: dbcli
description: "Universal database CLI supporting 30+ databases (SQLite, PostgreSQL, MySQL, SQL Server, Oracle, MongoDB, ClickHouse, DuckDB and more). Execute SELECT/DDL/DML, list tables, export schema, backup/restore tables, and run parameterized SQL. Use when the user asks to query, inspect, or modify a database, run SQL, list tables/columns, export data, or compare query results. Sub-skills: dbcli-query, dbcli-tables, dbcli-exec, dbcli-db-ddl, dbcli-export, dbcli-export-schema, dbcli-compare, dbcli-view, dbcli-index, dbcli-procedure, dbcli-interactive."
---

# dbcli — Database CLI for AI Agents

DbCli is a self-contained binary installed at `~/.local/bin/dbcli` (already on PATH). It speaks JSON/table/CSV output and follows the Agent Skills Specification.

## Quick connection (env vars — never pass `-c` with passwords)

```bash
export DBCLI_CONNECTION="Host=...;Port=5432;Database=...;Username=...;Password=...;SSL Mode=Require;Trust Server Certificate=true"
export DBCLI_DBTYPE="postgresql"   # sqlite | mysql | sqlserver | postgresql | oracle | mongodb | clickhouse | duckdb | ...
```

## Core commands

| Command | Alias | Use |
|---|---|---|
| `dbcli tables` | `ls` | List tables |
| `dbcli columns <table>` | `cols` | Show table structure |
| `dbcli query "<sql>"` | `q` | SELECT (read-only) |
| `dbcli exec "<sql>"` | `e` | INSERT/UPDATE/DELETE (backup first for UPDATE/DELETE) |
| `dbcli ddl "<sql>"` | — | CREATE/ALTER/DROP (critical — backup first) |
| `dbcli export <table>` | — | Export table data as INSERT SQL |
| `dbcli export-schema <type>` | `schema` | Export procedures/functions/triggers/views/indexes |
| `dbcli backup <table>` | — | Backup table (auto-selects fastest method) |
| `dbcli restore <table> --from <backup>` | — | Restore table |
| `dbcli compare` | — | Compare results of two SQL queries |
| `dbcli interactive` | `i` | REPL |

## Output formats

`-f json` (default for scripts), `-f table` (human), `-f csv`.

## Parameterized SQL

```bash
dbcli query "SELECT * FROM invoice WHERE customer_id IN (@Ids)" -p '{"Ids":[1,2,3]}'
```

## Sub-skills

Each sub-skill lives in `skills/<name>/SKILL.md` under this directory:
- `dbcli-query` — safe read-only SELECT
- `dbcli-tables` — list tables / view structure (read-only)
- `dbcli-exec` — INSERT/UPDATE/DELETE (backup required for UPDATE/DELETE)
- `dbcli-db-ddl` — CREATE/ALTER/DROP (critical, mandatory backup)
- `dbcli-export` — export table data as SQL (backup)
- `dbcli-export-schema` — export schema objects
- `dbcli-compare` — compare two query result sets (read-only)
- `dbcli-view` — manage views (moderate)
- `dbcli-index` — manage indexes (moderate)
- `dbcli-procedure` — manage stored procedures/functions/triggers (critical)
- `dbcli-interactive` — interactive SQL REPL

See `skills/README.md`, `skills/INTEGRATION.md`, and `skills/CONNECTION_STRINGS.md` for full details.

## Safety

- Always back up (`dbcli backup <table>` or `dbcli export-schema`) before DDL or destructive DML.
- Use env vars for connection strings, never `-c` (keeps passwords out of logs/history).
