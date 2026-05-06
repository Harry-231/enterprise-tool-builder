# Enterprise API References

Use this file only when `assets/endpoints/*.json` does not already cover the service or endpoint you need.

## How to use this file

1. Check whether the service already has a bundled endpoint file under `../assets/endpoints/`.
2. If it does, extend that file instead of creating a second source of truth.
3. If it does not, use the official docs links here to create a new endpoint JSON file with the same schema shape as the bundled files.
4. When auth is ambiguous, prefer the official authentication page over blog posts or community summaries.

## Bundled endpoint files

- `../assets/endpoints/confluence_cloud_endpoints.json`
- `../assets/endpoints/github_api_endpoints.json`
- `../assets/endpoints/google_workspace_api_endpoints.json`
- `../assets/endpoints/hubspot_api_endpoints.json`
- `../assets/endpoints/jira_service_management_endpoints.json`
- `../assets/endpoints/notion_api_endpoints.json`
- `../assets/endpoints/salesforce_api_endpoints.json`
- `../assets/endpoints/servicenow_api_endpoints.json`
- `../assets/endpoints/slack_api_endpoints.json`
- `../assets/endpoints/zendesk_api_endpoints.json`

No bundled file is currently shipped for Jira Cloud platform or Jira Server/Data Center. Create one if the task needs those APIs.

## Jira Cloud platform

- Bundled endpoint file: create `../assets/endpoints/jira_cloud_endpoints.json` if needed
- Docs home: `https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/`
- Issues: `https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/`
- Projects: `https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-projects/`
- Users: `https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-users/`
- JQL: `https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-jql/`
- OAuth scopes: `https://developer.atlassian.com/cloud/jira/platform/scopes-for-oauth-2-3lo-and-forge-apps/`
- OpenAPI: `https://developer.atlassian.com/cloud/jira/platform/swagger-v3.v3.json`
- Base URL: `https://{your-domain}.atlassian.net/rest/api/3`
- Common auth: Basic with email and API token, or OAuth 2.0

## Jira Server or Data Center

- Bundled endpoint file: create `../assets/endpoints/jira_server_dc_endpoints.json` if needed
- Docs home: `https://developer.atlassian.com/server/jira/platform/rest/v11002/intro/`
- Issue APIs: `https://developer.atlassian.com/server/jira/platform/rest/v11002/api-group-issue/`
- Search APIs: `https://developer.atlassian.com/server/jira/platform/rest/v11002/api-group-issue-search/`
- Base URL: `https://{your-jira-instance}/rest/api/2`
- Common auth: personal access token or basic auth

## Jira Service Management Cloud

- Bundled endpoint file: `../assets/endpoints/jira_service_management_endpoints.json`
- Docs home: `https://developer.atlassian.com/cloud/jira/service-desk/rest/intro/`
- Request APIs: `https://developer.atlassian.com/cloud/jira/service-desk/rest/api-group-request/`
- Customer APIs: `https://developer.atlassian.com/cloud/jira/service-desk/rest/api-group-customer/`
- Service desk APIs: `https://developer.atlassian.com/cloud/jira/service-desk/rest/api-group-servicedesk/`
- Base URL: `https://{your-domain}.atlassian.net`
- Common auth: same as Jira Cloud

## Confluence Cloud

- Bundled endpoint file: `../assets/endpoints/confluence_cloud_endpoints.json`
- Docs home: `https://developer.atlassian.com/cloud/confluence/rest/v2/intro/`
- v2 pages: `https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-page/`
- v2 spaces: `https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-space/`
- v2 comments: `https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-comment/`
- v1 content: `https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-content/`
- Base URL v2: `https://{your-domain}.atlassian.net/wiki/api/v2`
- Common auth: Basic with API token or OAuth 2.0

## Slack Web API

- Bundled endpoint file: `../assets/endpoints/slack_api_endpoints.json`
- Docs home: `https://docs.slack.dev/apis/web-api/`
- Method index: `https://api.slack.com/methods`
- OAuth guide: `https://api.slack.com/authentication/oauth-v2`
- Scopes: `https://api.slack.com/scopes`
- Base URL: `https://slack.com/api`
- Common auth: Bearer bot token

## HubSpot

- Bundled endpoint file: `../assets/endpoints/hubspot_api_endpoints.json`
- Docs home: `https://developers.hubspot.com/docs`
- API reference overview: `https://developers.hubspot.com/docs/api-reference/latest/overview`
- Auth overview: `https://developers.hubspot.com/docs/apps/developer-platform/build-apps/authentication/overview`
- CRM overview: `https://developers.hubspot.com/docs/guides/crm/understanding-the-crm`
- Base URL: `https://api.hubapi.com`
- Common auth: Bearer private app token or OAuth 2.0

## Notion

- Bundled endpoint file: `../assets/endpoints/notion_api_endpoints.json`
- Docs home: `https://developers.notion.com/reference/intro`
- Auth: `https://developers.notion.com/reference/authentication`
- Search: `https://developers.notion.com/reference/post-search`
- Pages: `https://developers.notion.com/reference/page`
- Databases: `https://developers.notion.com/reference/database`
- Base URL: `https://api.notion.com/v1`
- Common auth: Bearer integration token
- Required version header: `Notion-Version: 2022-06-28`

## GitHub REST API

- Bundled endpoint file: `../assets/endpoints/github_api_endpoints.json`
- Docs home: `https://docs.github.com/en/rest`
- Auth: `https://docs.github.com/rest/authentication/authenticating-to-the-rest-api`
- Repos: `https://docs.github.com/en/rest/repos`
- Issues: `https://docs.github.com/en/rest/issues`
- Pull requests: `https://docs.github.com/en/rest/pulls`
- Actions: `https://docs.github.com/en/rest/actions`
- Base URL: `https://api.github.com`
- Common auth: Bearer token
- Required version header: `X-GitHub-Api-Version: 2022-11-28`

## Salesforce REST API

- Bundled endpoint file: `../assets/endpoints/salesforce_api_endpoints.json`
- Docs home: `https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_rest.htm`
- OAuth and connected apps: `https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_oauth_and_connected_apps.htm`
- SObject APIs: `https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_sobject_basic_info.htm`
- SOQL query API: `https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_query.htm`
- Search API: `https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_search.htm`
- Base URL: `https://{instance}.salesforce.com/services/data/v{version}`
- Common auth: OAuth 2.0 bearer token

## Zendesk Support

- Bundled endpoint file: `../assets/endpoints/zendesk_api_endpoints.json`
- Docs home: `https://developer.zendesk.com/api-reference/`
- Auth overview: `https://developer.zendesk.com/api-reference/introduction/security-and-auth/`
- OAuth token guide: `https://developer.zendesk.com/documentation/api-basics/authentication/creating-and-using-oauth-tokens-with-the-api/`
- Tickets: `https://developer.zendesk.com/api-reference/ticketing/tickets/tickets/`
- Users: `https://developer.zendesk.com/api-reference/ticketing/users/users/`
- Search: `https://developer.zendesk.com/api-reference/ticketing/ticket-management/search/`
- Base URL: `https://{subdomain}.zendesk.com/api/v2`
- Common auth: basic auth with `email/token:api_token`, or OAuth 2.0

## ServiceNow Table API

- Bundled endpoint file: `../assets/endpoints/servicenow_api_endpoints.json`
- Docs home: `https://docs.servicenow.com/bundle/utah-application-development/page/integrate/inbound-rest/concept/c_TableAPI.html`
- Import set API: `https://docs.servicenow.com/bundle/utah-application-development/page/integrate/inbound-rest/concept/c_ImportSetAPI.html`
- Aggregate API: `https://docs.servicenow.com/bundle/utah-application-development/page/integrate/inbound-rest/concept/c_AggregateAPI.html`
- Attachment API: `https://docs.servicenow.com/bundle/utah-application-development/page/integrate/inbound-rest/concept/c_AttachmentAPI.html`
- Base URL: `https://{instance}.service-now.com/api/now/table/{tableName}`
- Common auth: basic auth or bearer token

## Google Workspace

- Bundled endpoint file: `../assets/endpoints/google_workspace_api_endpoints.json`
- Workspace hub: `https://developers.google.com/workspace`
- OAuth 2.0: `https://developers.google.com/identity/protocols/oauth2`
- Service accounts: `https://developers.google.com/workspace/guides/create-credentials#service-account`
- Gmail REST reference: `https://developers.google.com/gmail/api/reference/rest`
- Drive REST reference: `https://developers.google.com/drive/api/reference/rest/v3`
- Calendar REST reference: `https://developers.google.com/calendar/api/v3/reference`
- Sheets REST reference: `https://developers.google.com/sheets/api/reference/rest`
- Common auth: OAuth 2.0 bearer token or service account with domain-wide delegation

## Endpoint JSON reminders

Keep endpoint files small and task-focused. Every endpoint entry should include at least:

- `id`
- `method`
- `path`
- `description`

Add pagination, parameter, or body-shape details only when they materially help the generated tool.
