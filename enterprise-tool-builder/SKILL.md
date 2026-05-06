---
name: enterprise-tool-builder
description: Use when building or updating custom LangChain tools for enterprise SaaS APIs such as Jira, Confluence, Slack, HubSpot, Salesforce, Zendesk, ServiceNow, Notion, GitHub, or Google Workspace. Follow this skill for schema-driven endpoint selection, auth-aware wrappers, deterministic outputs, and validation with the bundled endpoint JSON files, templates, and scripts. Do not use for MCP server packaging or generic web scraping.
metadata:
  category: integration
  keywords: "enterprise SaaS, LangChain tools, API wrappers, Jira, Confluence, HubSpot, Salesforce, Zendesk, Slack"
---

# Enterprise Tool Builder

Build a coherent set of LangChain tools around a real enterprise API workflow. Keep `SKILL.md` procedural and lean. Load heavier references only when the bundled endpoint files do not already answer the question.

## Default workflow

Progress:
- [ ] Define the user-visible tool contract
- [ ] Choose or author the endpoint schema
- [ ] Generate or scaffold code
- [ ] Replace placeholders with real auth and response shaping
- [ ] Validate schemas and generated code
- [ ] Test with realistic inputs and failure cases

### 1. Define the tool contract first

Write down the minimum set of operations before touching code:

- tool names, using `service_action_object` style such as `jira_get_issue`
- required inputs, optional filters, pagination controls, and auth requirements
- exact output fields the agent should see
- whether the tool is read-only, write-capable, or destructive

Prefer a small set of focused tools over one broad tool that hides many behaviors.

### 2. Choose the source of truth for endpoints

Start with `assets/endpoints/*.json`.

- If the service already has a bundled endpoint file, trim or extend that JSON to the endpoints you need.
- If the service is bundled but the specific endpoint is missing, read `references/REFERENCES.md` for the official docs, then add the missing endpoint definition to the matching JSON file.
- If the service is not bundled at all, read `references/REFERENCES.md`, create a new `assets/endpoints/<service>_endpoints.json`, and keep the schema format consistent with the existing files.

Only browse external docs after checking the bundled JSON and references.

### 3. Validate the schema before generating code

Run:

```bash
python scripts/validate_schema.py
```

Do this every time you edit `assets/endpoints/*.json`. Fix schema problems before generating tools.

### 4. Generate or scaffold code

Use the bundled scripts as starting points, not as final production output.

Available scripts:

- `scripts/validate_schema.py` - validates endpoint JSON files
- `scripts/generate_tool.py` - generates a single draft tool from an endpoint definition
- `scripts/generate_toolset.py` - batch-generates draft tools for all endpoints in a service file
- `scripts/scaffold_tool_file.py` - creates a service package layout under `generated_tools/`
- `scripts/lint_tools.py` - checks generated tool files for basic quality issues
- `scripts/test_tool.py` - runs basic functional, error, and rate-limit style tests
- `scripts/fetch_endpoints.py` - saves small starter endpoint files; use only as seed data

Use the templates in `assets/templates/` when the generators are too shallow for the request:

- `langchain_tool_template.py` for a plain `@tool`
- `langchain_structured_tool.py` when you need Pydantic-backed input validation
- `paginated_tool_template.py` when the API pages results
- `async_tool_template.py` when async calls matter
- `auth_header_template.py` for auth header patterns

### 5. Replace generator placeholders immediately

The bundled generators are intentionally incomplete. After generation:

- replace placeholder parameters such as `query: str = 'default'`
- replace TODO comments with real request construction
- wire in auth from `scripts/auth/`
- shape the response into a small, deterministic object
- add pagination inputs only when the endpoint supports them

Do not ship raw generated files without this pass.

### 6. Implement with enterprise-safe defaults

Defaults:

- use strong input schemas with descriptions and constraints
- return a stable envelope with `success`, `data`, and optional `error` or `metadata`
- keep outputs small and human-readable
- split read and write tools when permissions differ
- validate auth, workspace, and object identifiers outside the LLM

Avoid:

- raw API passthroughs
- giant response blobs
- shared auth tokens between users or tenants
- unrestricted query languages such as SOQL or JQL without validation
- one tool that mixes search, create, update, and admin actions

### 7. Validate in a loop

Run this loop until the generated tool is clean:

```bash
python scripts/validate_schema.py
python scripts/lint_tools.py
python scripts/test_tool.py
```

If a command fails:

1. Fix the schema or implementation.
2. Re-run the same command.
3. Only proceed once it passes.

### 8. Use the reference file selectively

Read `references/REFERENCES.md` only when:

- the endpoint JSON does not already cover the service
- you need the correct auth flow or base URL
- you need an official docs link for a new endpoint
- you need to confirm whether the API uses cursor, offset, or token pagination

Do not load the full reference file by default for simple edits to an existing endpoint JSON file.

## Gotchas

- The bundled endpoint directory is `assets/endpoints`, not `assets/api_schemas`.
- `scripts/generate_tool.py` and `scripts/generate_toolset.py` create drafts, not production-ready tools.
- Some services in `references/REFERENCES.md` do not yet have a bundled endpoint JSON file. Add one before relying on batch generation.
- `scripts/test_tool.py` is a lightweight harness. It does not replace service-specific contract tests.
- If a tool writes data, define a narrow input schema and a small confirmation-shaped output instead of returning the full API payload.

## Deliverable checklist

Before finishing, make sure the skill user gets:

- updated endpoint JSON in `assets/endpoints/` when the API contract changed
- generated or scaffolded code under `generated_tools/` when code generation was requested
- auth wiring that matches the target service
- deterministic output shaping
- validation results from the bundled scripts
