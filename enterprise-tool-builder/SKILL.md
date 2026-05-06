---
name: enterprise-tool-builder
description: Build or update enterprise API toolsets for LangChain and MCP-backed agent workflows. Use when Codex needs to turn a real SaaS API contract into safe, structured tools with clear schemas, auth guidance, stable outputs, and validation loops for services such as Jira, Confluence, Slack, GitHub, HubSpot, Salesforce, Zendesk, ServiceNow, Notion, or Google Workspace.
metadata:
  category: integration
  keywords: "enterprise API tools, LangChain, MCP, Jira, Confluence, Slack, GitHub, HubSpot, Salesforce, Zendesk, ServiceNow, Notion, Google Workspace"
---

# Enterprise Tool Builder

Build a small, coherent toolset around a real enterprise workflow. Prefer tight contracts, tenant-safe auth, and deterministic outputs over broad API passthroughs.

## Progress

- [ ] Reduce the request to the minimum useful operations
- [ ] Choose the source-of-truth endpoint file or create one
- [ ] Summarize the candidate endpoints before writing code
- [ ] Define input schema, output envelope, and auth strategy
- [ ] Scaffold or update the tool package
- [ ] Validate schemas, generated code, and response shaping
- [ ] Smoke-test realistic success and failure paths

## Default workflow

### 1. Reduce the request to concrete operations

Write down:

- target service and tenant/workspace scope
- read vs write actions
- exact API objects involved
- minimum inputs required for each tool
- expected confirmation or result shape
- preferred implementation SDK: `python`, `typescript`, or `javascript`

Prefer multiple focused tools over one large tool that mixes search, create, update, and admin operations.

Default SDK choice:

- prefer `python` when the user does not specify an SDK
- use `typescript` or `javascript` when the surrounding agent/app stack is Node-first
- for Python LangChain tools, use `@tool` plus Pydantic input schemas
- for TypeScript or JavaScript LangChain tools, use `tool(...)` from `langchain` plus `zod` schemas

### 2. Choose the source of truth

Use this order:

1. `assets/endpoints/*.json`
2. `references/REFERENCES.md` for missing base URL, auth, or official docs links
3. LangChain docs MCP for LangChain or MCP implementation details

Start by inspecting the closest bundled endpoint file:

```bash
python scripts/summarize_endpoints.py assets/endpoints/<service>_endpoints.json --format json
```

If the needed service or action is missing:

- extend the existing endpoint file instead of creating a parallel source
- only create a new endpoint file when the service is not already bundled
- keep endpoint files task-focused rather than dumping a full vendor spec

Use `references/REFERENCES.md` only when the endpoint JSON does not already answer the question.

### 3. Design the tool contract before implementation

For each tool, lock down:

- tool name and single responsibility
- required inputs, optional inputs, and constraints
- auth requirements and tenant/workspace identifiers
- stable output envelope
- whether the tool should be sync, async, or paginated

Default output envelope:

```json
{
  "success": true,
  "data": {},
  "error": null,
  "metadata": {}
}
```

Keep `data` small and human-readable. Return confirmation-shaped objects for write tools.

### 4. Pick the right implementation pattern

Use the bundled templates as defaults:

- `assets/templates/langchain_structured_tool.py` for most tools with strict schemas
- `assets/templates/langchain_tool_template.py` only for very simple cases
- `assets/templates/paginated_tool_template.py` for list endpoints
- `assets/templates/async_tool_template.py` for long-running or concurrent I/O
- `assets/templates/auth_header_template.py` for header construction patterns

Use Pydantic models for Python input validation. Keep descriptions and field constraints explicit.

### 5. Plan auth and tenant safety

Use the endpoint JSON plus vendor docs to decide whether the tool needs:

- bearer token
- basic auth
- OAuth 2.0
- service account or delegated credentials

Create `auth_flow.md` in the generated tool package when the user needs credential setup instructions.

Use the helpers in `scripts/auth/` when they fit, but validate that the flow matches the target service. Do not guess OAuth details.

### 6. Scaffold and implement

Scaffold package structure when starting a new service bundle:

```bash
python scripts/scaffold_tool_file.py <service> --sdk python
```

Use generators only as accelerators:

- `scripts/generate_tool.py` creates a first draft from one endpoint
- `scripts/generate_toolset.py` batch-generates drafts from one endpoint file

Examples:

```bash
python scripts/generate_tool.py assets/endpoints/github_api_endpoints.json --endpoint-id github_agent_tasks_create_task_in_repo --sdk python
python scripts/generate_tool.py assets/endpoints/github_api_endpoints.json --endpoint-id github_agent_tasks_create_task_in_repo --sdk typescript --dry-run
python scripts/generate_toolset.py --service github --sdk javascript --limit 5
```

Treat generated code as a draft. Replace placeholders with:

- real request construction
- auth wiring
- explicit validation
- deterministic output shaping
- service-specific error handling

### 7. Validate in a loop

Run validation after edits:

```bash
python scripts/validate_schema.py --format json
python scripts/lint_tools.py --tools-dir generated_tools --sdk python
python scripts/validate_toolset.py --tools-dir generated_tools --sdk python
```

If you generated or updated a specific tool, also run a focused smoke test:

```bash
python scripts/test_tool.py generated_tools/<tool_file>.py --tool-name <tool_symbol> --expect-key success --expect-key data
```

If validation fails:

1. Fix the schema or implementation.
2. Re-run the same validator.
3. Only proceed when it passes.

### 8. Use LangChain docs only for framework specifics

Use the LangChain docs MCP server or these docs pages for implementation guidance, not for the enterprise API contract itself:

- `https://docs.langchain.com/oss/python/langchain/mcp`
- `https://docs.langchain.com/oss/python/deepagents/cli/mcp-tools`
- `https://docs.langchain.com/oss/python/langchain/agents`
- `https://docs.langchain.com/oss/javascript/langchain/agents`

Use LangChain docs to confirm:

- MCP transport config
- header-based auth wiring
- when to use HTTP vs stdio transports
- tool exposure and filtering patterns
- Python tool patterns: `@tool` plus Pydantic schemas
- TypeScript and JavaScript tool patterns: `tool(...)` plus `zod` schemas

Do not replace vendor API docs with LangChain docs when you need endpoint semantics.

## Use bundled resources selectively

### Scripts

- `scripts/summarize_endpoints.py`: inspect an endpoint file before choosing operations, with `--offset` and JSON output for large bundles
- `scripts/fetch_endpoints.py`: convert a local or remote OpenAPI JSON source into the bundled endpoint-file shape
- `scripts/validate_schema.py`: validate endpoint JSON shape and optionally normalize leading slashes with `--fix-paths`
- `scripts/scaffold_tool_file.py`: create a package skeleton for `python`, `typescript`, or `javascript`
- `scripts/generate_tool.py`: generate one draft tool from one endpoint, targeting the preferred LangChain SDK
- `scripts/generate_toolset.py`: generate draft tools in bulk for one service or the whole bundle
- `scripts/lint_tools.py`: catch obvious structural issues in generated Python or JS/TS tools
- `scripts/validate_toolset.py`: run lint and SDK-specific validation against a generated tool directory
- `scripts/test_tool.py`: smoke-test a generated Python tool with explicit params and expected keys

### References

- `references/REFERENCES.md`: vendor docs index, base URLs, and auth starting points

### Assets

- `assets/endpoints/`: source-of-truth endpoint definitions
- `assets/templates/`: implementation templates for common tool patterns

## Gotchas

- Some bundled endpoint files are intentionally sparse or empty. Validate coverage before you start generating tools.
- `scripts/generate_tool.py` and `scripts/generate_toolset.py` produce drafts, not production-ready tools.
- The structured template file is `assets/templates/langchain_structured_tool.py`; do not guess a different filename.
- Keep read and write tools separate when permissions or failure modes differ.
- Do not expose unrestricted query languages such as raw JQL or SOQL without validation and narrowing.
- Validate tenant identifiers, workspace identifiers, and object IDs outside the LLM-facing tool call.
- Prefer confirmation-shaped outputs for write operations instead of returning the vendor's full payload.

## Deliverable checklist

Before finishing, make sure the skill user gets:

- updated or newly created endpoint JSON in `assets/endpoints/` when the API contract changed
- a generated or updated tool package with real auth and response shaping
- `auth_flow.md` when credential setup is non-trivial
- validation results from the bundled scripts
- a narrow set of tools that maps cleanly to the user workflow
