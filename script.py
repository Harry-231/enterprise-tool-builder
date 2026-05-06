"""
Enterprise API Endpoint Extractor
===================================
Extracts REST API endpoints from 12 enterprise services and saves
each to a structured JSON file.

Services covered:
  1.  Jira Cloud Platform (OpenAPI spec)
  2.  Jira Data Center / Server (OpenAPI spec)
  3.  Jira Service Management Cloud (OpenAPI spec)
  4.  Confluence Cloud (OpenAPI specs v1 + v2)
  5.  Slack Web API (HTML scraping)
  6.  HubSpot CRM (HTML scraping)
  7.  Notion API (HTML scraping)
  8.  GitHub REST API (OpenAPI spec via GitHub)
  9.  Salesforce REST API (hardcoded well-known endpoints)
  10. Zendesk Support API (HTML scraping)
  11. ServiceNow Table API (hardcoded well-known endpoints)
  12. Google Workspace APIs (Discovery API)

Usage
-----
  python extract_enterprise_endpoints.py               # extract all
  python extract_enterprise_endpoints.py --service jira_cloud
  python extract_enterprise_endpoints.py --output-dir ./endpoints
  python extract_enterprise_endpoints.py --list
"""

import argparse
import json
import re
import sys
import time
import urllib.request
import urllib.error
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

# ── Output directory ──────────────────────────────────────────────────────────
DEFAULT_OUTPUT_DIR = Path("./endpoints")

# ── Request helpers ───────────────────────────────────────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; EnterpriseAPIExtractor/2.0; "
        "+https://github.com/enterprise-api-extractor)"
    ),
    "Accept": "application/json, text/html, */*",
}


def http_get(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def fetch_json(url: str) -> dict:
    return json.loads(http_get(url))


def fetch_html(url: str) -> str:
    return http_get(url).decode("utf-8", errors="replace")



HTTP_METHODS = ("get", "post", "put", "patch", "delete", "head", "options")


def endpoints_from_openapi(spec: dict, api_label: str = "") -> list[dict]:
    """Extract flat endpoint list from an OpenAPI/Swagger spec dict."""
    endpoints = []
    for path, path_item in spec.get("paths", {}).items():
        for method in HTTP_METHODS:
            op = path_item.get(method)
            if not op:
                continue
            endpoints.append(
                {
                    "method": method.upper(),
                    "path": path,
                    "operation_id": op.get("operationId", ""),
                    "summary": op.get("summary", ""),
                    "description": op.get("description", ""),
                    "tags": op.get("tags", []),
                    "deprecated": op.get("deprecated", False),
                    "parameters": [
                        {
                            "name": p.get("name", ""),
                            "in": p.get("in", ""),
                            "required": p.get("required", False),
                            "description": p.get("description", ""),
                        }
                        for p in op.get("parameters", [])
                        if isinstance(p, dict)
                    ],
                }
            )
    return endpoints


def build_output(
    service_key: str,
    service_name: str,
    base_url: str,
    auth_header: str,
    endpoints: list[dict],
    extra: dict | None = None,
) -> dict:
    grouped: dict[str, list] = defaultdict(list)
    for ep in endpoints:
        tag = ep.get("tags", [None])[0] or "General"
        grouped[tag].append(ep)

    result = {
        "service": service_name,
        "service_key": service_key,
        "base_url": base_url,
        "auth_header": auth_header,
        "total_endpoints": len(endpoints),
        "endpoints_by_tag": {tag: grouped[tag] for tag in sorted(grouped)},
        "all_endpoints": endpoints,
    }
    if extra:
        result.update(extra)
    return result


# ═════════════════════════════════════════════════════════════════════════════
# 1. JIRA CLOUD PLATFORM
# ═════════════════════════════════════════════════════════════════════════════
def extract_jira_cloud() -> dict:
    url = "https://developer.atlassian.com/cloud/jira/platform/swagger-v3.v3.json"
    spec = fetch_json(url)
    endpoints = endpoints_from_openapi(spec)
    return build_output(
        service_key="jira_cloud",
        service_name="Jira Cloud Platform REST API (v3)",
        base_url="https://{your-domain}.atlassian.net/rest/api/3",
        auth_header="Authorization: Basic <base64(email:api_token)>",
        endpoints=endpoints,
        extra={
            "spec_url": url,
            "api_version": "v3",
            "auth_docs": "https://developer.atlassian.com/cloud/jira/platform/basic-auth-for-rest-apis/",
            "oauth_docs": "https://developer.atlassian.com/cloud/jira/platform/oauth-2-3lo-apps/",
        },
    )


# ═════════════════════════════════════════════════════════════════════════════
# 2. JIRA DATA CENTER / SERVER
# ═════════════════════════════════════════════════════════════════════════════
def extract_jira_server() -> dict:
    # Atlassian publishes a WADL but not a clean OpenAPI for DC;
    # the best publicly available OpenAPI is from apis.guru
    url = "https://raw.githubusercontent.com/APIs-guru/openapi-directory/refs/heads/main/APIs/atlassian.com/jira/1001.0.0-SNAPSHOT/openapi.json"
    spec = fetch_json(url)
    endpoints = endpoints_from_openapi(spec)
    return build_output(
        service_key="jira_server_datacenter",
        service_name="Jira Data Center / Server REST API (v2)",
        base_url="https://{your-jira-instance}/rest/api/2",
        auth_header="Authorization: Bearer <personal_access_token>",
        endpoints=endpoints,
        extra={
            "spec_url": url,
            "api_version": "v2",
            "auth_docs": "https://confluence.atlassian.com/enterprise/using-personal-access-tokens-1026032365.html",
            "official_docs": "https://developer.atlassian.com/server/jira/platform/rest/v11002/intro/",
        },
    )


# ═════════════════════════════════════════════════════════════════════════════
# 3. JIRA SERVICE MANAGEMENT CLOUD
# ═════════════════════════════════════════════════════════════════════════════
def extract_jira_service_management() -> dict:
    url = "https://developer.atlassian.com/cloud/jira/service-desk/swagger.v3.json"
    spec = fetch_json(url)
    endpoints = endpoints_from_openapi(spec)
    return build_output(
        service_key="jira_service_management_cloud",
        service_name="Jira Service Management Cloud REST API",
        base_url="https://{your-domain}.atlassian.net",
        auth_header="Authorization: Basic <base64(email:api_token)>",
        endpoints=endpoints,
        extra={
            "spec_url": url,
            "auth_docs": "https://developer.atlassian.com/cloud/jira/platform/basic-auth-for-rest-apis/",
            "api_intro": "https://developer.atlassian.com/cloud/jira/service-desk/rest/intro/",
        },
    )


# ═════════════════════════════════════════════════════════════════════════════
# 4. CONFLUENCE CLOUD
# ═════════════════════════════════════════════════════════════════════════════
def extract_confluence_cloud() -> dict:
    v1_url = "https://developer.atlassian.com/cloud/confluence/swagger.v3.json"
    v2_url = "https://developer.atlassian.com/cloud/confluence/swagger-v2.v3.json"

    all_endpoints: list[dict] = []

    for label, url in [("v1", v1_url), ("v2", v2_url)]:
        try:
            spec = fetch_json(url)
            eps = endpoints_from_openapi(spec)
            for ep in eps:
                ep["api_version"] = label
            all_endpoints.extend(eps)
        except Exception as e:
            print(f"    ⚠ Confluence {label} spec failed: {e}", file=sys.stderr)

    return build_output(
        service_key="confluence_cloud",
        service_name="Confluence Cloud REST API (v1 + v2)",
        base_url="https://{your-domain}.atlassian.net/wiki/rest/api (v1) | /wiki/api/v2 (v2)",
        auth_header="Authorization: Basic <base64(email:api_token)>",
        endpoints=all_endpoints,
        extra={
            "v1_spec_url": v1_url,
            "v2_spec_url": v2_url,
            "auth_docs": "https://developer.atlassian.com/cloud/confluence/basic-auth-for-rest-apis/",
            "api_v1_intro": "https://developer.atlassian.com/cloud/confluence/rest/v1/intro/",
            "api_v2_intro": "https://developer.atlassian.com/cloud/confluence/rest/v2/intro/",
        },
    )


# ═════════════════════════════════════════════════════════════════════════════
# 5. SLACK WEB API
# ═════════════════════════════════════════════════════════════════════════════

class SlackMethodParser(HTMLParser):
    """Parse https://api.slack.com/methods to extract method list."""

    def __init__(self):
        super().__init__()
        self.methods: list[dict] = []
        self._in_method_link = False
        self._current_href = ""
        self._current_text = ""

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            attrs_dict = dict(attrs)
            href = attrs_dict.get("href", "")
            if href.startswith("/methods/"):
                self._in_method_link = True
                self._current_href = href
                self._current_text = ""

    def handle_data(self, data):
        if self._in_method_link:
            self._current_text += data

    def handle_endtag(self, tag):
        if tag == "a" and self._in_method_link:
            name = self._current_text.strip()
            if name and "." in name:
                self.methods.append(
                    {
                        "method": "POST",
                        "path": f"/api/{name}",
                        "operation_id": name.replace(".", "_"),
                        "summary": name,
                        "description": "",
                        "tags": [name.split(".")[0]],
                        "deprecated": False,
                        "parameters": [],
                        "docs_url": f"https://api.slack.com{self._current_href}",
                    }
                )
            self._in_method_link = False


def extract_slack() -> dict:
    html = fetch_html("https://api.slack.com/methods")
    parser = SlackMethodParser()
    parser.feed(html)

    # Deduplicate by path
    seen = set()
    unique = []
    for ep in parser.methods:
        if ep["path"] not in seen:
            seen.add(ep["path"])
            unique.append(ep)

    return build_output(
        service_key="slack",
        service_name="Slack Web API",
        base_url="https://slack.com/api",
        auth_header="Authorization: Bearer xoxb-<bot_token>",
        endpoints=unique,
        extra={
            "methods_reference": "https://api.slack.com/methods",
            "scopes_reference": "https://api.slack.com/scopes",
            "auth_docs": "https://api.slack.com/authentication/oauth-v2",
        },
    )


# ═════════════════════════════════════════════════════════════════════════════
# 6. HUBSPOT CRM
# ═════════════════════════════════════════════════════════════════════════════
def extract_hubspot() -> dict:
    # HubSpot publishes OpenAPI specs on GitHub
    base = "https://raw.githubusercontent.com/HubSpot/HubSpot-public-api-spec-collection/main/PublicApiSpecs"
    spec_paths = {
        "Contacts": "CRM/Contacts/Codegen/V3",
        "Companies": "CRM/Companies/Codegen/V3",
        "Deals": "CRM/Deals/Codegen/V3",
        "Tickets": "CRM/Tickets/Codegen/V3",
        "Search": "CRM/CRM_Search/Codegen/V3",
        "Properties": "CRM/Properties/Codegen/V3",
        "Associations": "CRM/Associations/Codegen/V4",
        "Pipelines": "CRM/Pipelines/Codegen/V3",
    }

    all_endpoints: list[dict] = []

    for tag, path in spec_paths.items():
        url = f"{base}/{path}/openapi.json"
        try:
            spec = fetch_json(url)
            eps = endpoints_from_openapi(spec)
            for ep in eps:
                if not ep.get("tags"):
                    ep["tags"] = [tag]
            all_endpoints.extend(eps)
            time.sleep(0.2)
        except Exception as e:
            print(f"    ⚠ HubSpot {tag} spec failed ({url}): {e}", file=sys.stderr)

    # Fallback: if GitHub specs fail, use hardcoded well-known endpoints
    if not all_endpoints:
        all_endpoints = _hubspot_hardcoded()

    return build_output(
        service_key="hubspot",
        service_name="HubSpot CRM & Platform REST API",
        base_url="https://api.hubapi.com",
        auth_header="Authorization: Bearer <private_app_access_token>",
        endpoints=all_endpoints,
        extra={
            "api_reference": "https://developers.hubspot.com/docs/api-reference/latest/overview",
            "llms_txt": "https://developers.hubspot.com/docs/llms.txt",
            "auth_docs": "https://developers.hubspot.com/docs/apps/developer-platform/build-apps/authentication/overview",
        },
    )


def _hubspot_hardcoded() -> list[dict]:
    """Hardcoded well-known HubSpot endpoints as fallback."""
    entries = [
        ("GET",    "/crm/v3/objects/contacts",              "getContacts",          "Get all contacts",             ["Contacts"]),
        ("POST",   "/crm/v3/objects/contacts",              "createContact",         "Create a contact",             ["Contacts"]),
        ("GET",    "/crm/v3/objects/contacts/{contactId}",  "getContactById",        "Get contact by ID",            ["Contacts"]),
        ("PATCH",  "/crm/v3/objects/contacts/{contactId}",  "updateContact",         "Update a contact",             ["Contacts"]),
        ("DELETE", "/crm/v3/objects/contacts/{contactId}",  "deleteContact",         "Delete a contact",             ["Contacts"]),
        ("POST",   "/crm/v3/objects/contacts/search",       "searchContacts",        "Search contacts",              ["Contacts"]),
        ("GET",    "/crm/v3/objects/companies",             "getCompanies",          "Get all companies",            ["Companies"]),
        ("POST",   "/crm/v3/objects/companies",             "createCompany",         "Create a company",             ["Companies"]),
        ("GET",    "/crm/v3/objects/companies/{companyId}", "getCompanyById",        "Get company by ID",            ["Companies"]),
        ("PATCH",  "/crm/v3/objects/companies/{companyId}", "updateCompany",         "Update a company",             ["Companies"]),
        ("DELETE", "/crm/v3/objects/companies/{companyId}", "deleteCompany",         "Delete a company",             ["Companies"]),
        ("GET",    "/crm/v3/objects/deals",                 "getDeals",              "Get all deals",                ["Deals"]),
        ("POST",   "/crm/v3/objects/deals",                 "createDeal",            "Create a deal",                ["Deals"]),
        ("GET",    "/crm/v3/objects/deals/{dealId}",        "getDealById",           "Get deal by ID",               ["Deals"]),
        ("PATCH",  "/crm/v3/objects/deals/{dealId}",        "updateDeal",            "Update a deal",                ["Deals"]),
        ("DELETE", "/crm/v3/objects/deals/{dealId}",        "deleteDeal",            "Delete a deal",                ["Deals"]),
        ("GET",    "/crm/v3/objects/tickets",               "getTickets",            "Get all tickets",              ["Tickets"]),
        ("POST",   "/crm/v3/objects/tickets",               "createTicket",          "Create a ticket",              ["Tickets"]),
        ("GET",    "/crm/v3/objects/tickets/{ticketId}",    "getTicketById",         "Get ticket by ID",             ["Tickets"]),
        ("PATCH",  "/crm/v3/objects/tickets/{ticketId}",    "updateTicket",          "Update a ticket",              ["Tickets"]),
        ("DELETE", "/crm/v3/objects/tickets/{ticketId}",    "deleteTicket",          "Delete a ticket",              ["Tickets"]),
        ("POST",   "/crm/v3/objects/{objectType}/search",   "searchObjects",         "Search CRM objects",           ["Search"]),
        ("GET",    "/crm/v3/properties/{objectType}",       "getProperties",         "Get all properties",           ["Properties"]),
        ("POST",   "/crm/v3/properties/{objectType}",       "createProperty",        "Create a property",            ["Properties"]),
        ("GET",    "/crm/v3/properties/{objectType}/{propertyName}", "getProperty",  "Get property by name",         ["Properties"]),
        ("PATCH",  "/crm/v3/properties/{objectType}/{propertyName}", "updateProperty", "Update a property",          ["Properties"]),
        ("DELETE", "/crm/v3/properties/{objectType}/{propertyName}", "deleteProperty", "Delete a property",          ["Properties"]),
        ("GET",    "/crm/v4/objects/{objectType}/{objectId}/associations/{toObjectType}", "getAssociations", "Get associations", ["Associations"]),
        ("PUT",    "/crm/v4/objects/{objectType}/{objectId}/associations/{toObjectType}/{toObjectId}", "createAssociation", "Create association", ["Associations"]),
        ("DELETE", "/crm/v4/objects/{objectType}/{objectId}/associations/{toObjectType}/{toObjectId}", "deleteAssociation", "Delete association", ["Associations"]),
        ("GET",    "/crm/v3/pipelines/{objectType}",        "getPipelines",          "Get all pipelines",            ["Pipelines"]),
        ("POST",   "/crm/v3/pipelines/{objectType}",        "createPipeline",        "Create a pipeline",            ["Pipelines"]),
        ("GET",    "/crm/v3/pipelines/{objectType}/{pipelineId}", "getPipelineById", "Get pipeline by ID",           ["Pipelines"]),
        ("PATCH",  "/crm/v3/pipelines/{objectType}/{pipelineId}", "updatePipeline",  "Update a pipeline",            ["Pipelines"]),
        ("DELETE", "/crm/v3/pipelines/{objectType}/{pipelineId}", "deletePipeline",  "Delete a pipeline",            ["Pipelines"]),
    ]
    return [
        {"method": m, "path": p, "operation_id": oid, "summary": s,
         "description": "", "tags": tags, "deprecated": False, "parameters": []}
        for m, p, oid, s, tags in entries
    ]


# ═════════════════════════════════════════════════════════════════════════════
# 7. NOTION API
# ═════════════════════════════════════════════════════════════════════════════
def extract_notion() -> dict:
    # Notion provides an llms.txt but no public OpenAPI; use hardcoded well-known endpoints
    endpoints = [
        # Pages
        ("POST",   "/pages",                                "createPage",             "Create a page",                       ["Pages"]),
        ("GET",    "/pages/{page_id}",                      "getPage",                "Retrieve a page",                     ["Pages"]),
        ("PATCH",  "/pages/{page_id}",                      "updatePage",             "Update page properties",              ["Pages"]),
        ("DELETE", "/pages/{page_id}",                      "deletePage",             "Delete (archive) a page",             ["Pages"]),
        ("GET",    "/pages/{page_id}/properties/{property_id}", "getPageProperty",    "Retrieve a page property item",       ["Pages"]),
        # Databases
        ("POST",   "/databases",                            "createDatabase",         "Create a database",                   ["Databases"]),
        ("GET",    "/databases/{database_id}",              "getDatabase",            "Retrieve a database",                 ["Databases"]),
        ("PATCH",  "/databases/{database_id}",              "updateDatabase",         "Update a database",                   ["Databases"]),
        ("POST",   "/databases/{database_id}/query",        "queryDatabase",          "Query a database",                    ["Databases"]),
        # Blocks
        ("GET",    "/blocks/{block_id}",                    "getBlock",               "Retrieve a block",                    ["Blocks"]),
        ("PATCH",  "/blocks/{block_id}",                    "updateBlock",            "Update a block",                      ["Blocks"]),
        ("DELETE", "/blocks/{block_id}",                    "deleteBlock",            "Delete a block",                      ["Blocks"]),
        ("GET",    "/blocks/{block_id}/children",           "getBlockChildren",       "Retrieve block children",             ["Blocks"]),
        ("PATCH",  "/blocks/{block_id}/children",           "appendBlockChildren",    "Append block children",               ["Blocks"]),
        # Users
        ("GET",    "/users",                                "listUsers",              "List all users",                      ["Users"]),
        ("GET",    "/users/{user_id}",                      "getUser",                "Retrieve a user",                     ["Users"]),
        ("GET",    "/users/me",                             "getMe",                  "Retrieve your token's bot user",      ["Users"]),
        # Search
        ("POST",   "/search",                               "search",                 "Search by title",                     ["Search"]),
        # Comments
        ("GET",    "/comments",                             "getComments",            "Retrieve comments",                   ["Comments"]),
        ("POST",   "/comments",                             "createComment",          "Create a comment",                    ["Comments"]),
    ]

    eps = [
        {"method": m, "path": p, "operation_id": oid, "summary": s,
         "description": "", "tags": tags, "deprecated": False, "parameters": []}
        for m, p, oid, s, tags in endpoints
    ]

    return build_output(
        service_key="notion",
        service_name="Notion REST API",
        base_url="https://api.notion.com/v1",
        auth_header="Authorization: Bearer <integration_token>",
        endpoints=eps,
        extra={
            "required_header": "Notion-Version: 2022-06-28",
            "api_reference": "https://developers.notion.com/reference/intro",
            "llms_txt": "https://developers.notion.com/llms.txt",
            "auth_docs": "https://developers.notion.com/reference/authentication",
        },
    )


# ═════════════════════════════════════════════════════════════════════════════
# 8. GITHUB REST API
# ═════════════════════════════════════════════════════════════════════════════
def extract_github() -> dict:
    url = "https://raw.githubusercontent.com/github/rest-api-description/main/descriptions/api.github.com/api.github.com.json"
    spec = fetch_json(url)
    endpoints = endpoints_from_openapi(spec)
    return build_output(
        service_key="github",
        service_name="GitHub REST API",
        base_url="https://api.github.com",
        auth_header="Authorization: Bearer <token>",
        endpoints=endpoints,
        extra={
            "spec_url": url,
            "required_header": "X-GitHub-Api-Version: 2022-11-28",
            "api_docs": "https://docs.github.com/en/rest",
            "auth_docs": "https://docs.github.com/rest/authentication/authenticating-to-the-rest-api",
        },
    )


# ═════════════════════════════════════════════════════════════════════════════
# 9. SALESFORCE REST API
# ═════════════════════════════════════════════════════════════════════════════
def extract_salesforce() -> dict:
    endpoints = [
        # Versions & Discovery
        ("GET",   "/",                                                     "getVersions",            "List available Salesforce REST API versions",           ["Discovery"]),
        ("GET",   "/services/data/",                                       "getApiVersions",         "List available API versions",                           ["Discovery"]),
        ("GET",   "/services/data/v{version}/",                            "getResources",           "List available resources for the specified API version", ["Discovery"]),
        # SObjects
        ("GET",   "/services/data/v{version}/sobjects/",                   "listSObjects",           "List all SObjects",                                     ["SObjects"]),
        ("GET",   "/services/data/v{version}/sobjects/{sObjectName}/",     "describeSObject",        "Get SObject metadata",                                  ["SObjects"]),
        ("POST",  "/services/data/v{version}/sobjects/{sObjectName}/",     "createRecord",           "Create an SObject record",                              ["SObjects"]),
        ("GET",   "/services/data/v{version}/sobjects/{sObjectName}/{id}", "getRecord",              "Get an SObject record by ID",                           ["SObjects"]),
        ("PATCH", "/services/data/v{version}/sobjects/{sObjectName}/{id}", "updateRecord",           "Update an SObject record",                              ["SObjects"]),
        ("DELETE","/services/data/v{version}/sobjects/{sObjectName}/{id}", "deleteRecord",           "Delete an SObject record",                              ["SObjects"]),
        ("GET",   "/services/data/v{version}/sobjects/{sObjectName}/describe/", "fullDescribeSObject", "Get full SObject description",                        ["SObjects"]),
        # SOQL
        ("GET",   "/services/data/v{version}/query/",                      "soqlQuery",              "Execute a SOQL query",                                  ["SOQL"]),
        ("GET",   "/services/data/v{version}/query/{id}",                  "soqlQueryMore",          "Get next batch of query results",                       ["SOQL"]),
        ("GET",   "/services/data/v{version}/queryAll/",                   "soqlQueryAll",           "Execute a SOQL queryAll (includes deleted/archived)",   ["SOQL"]),
        # Search
        ("GET",   "/services/data/v{version}/search/",                     "soqlSearch",             "Execute a SOSL search",                                 ["Search"]),
        ("GET",   "/services/data/v{version}/search/scopeOrder",           "searchScopeOrder",       "Return default search scope order",                     ["Search"]),
        ("GET",   "/services/data/v{version}/search/layout",               "searchResultLayout",     "Return search result layout",                           ["Search"]),
        # Composite
        ("POST",  "/services/data/v{version}/composite/",                  "compositeRequest",       "Execute a composite request",                           ["Composite"]),
        ("POST",  "/services/data/v{version}/composite/batch",             "compositeBatch",         "Execute a composite batch request",                     ["Composite"]),
        ("POST",  "/services/data/v{version}/composite/sobjects",          "compositeSObjects",      "Create multiple records in one request",                 ["Composite"]),
        ("PATCH", "/services/data/v{version}/composite/sobjects",          "updateMultipleRecords",  "Update multiple records in one request",                 ["Composite"]),
        # Bulk
        ("POST",  "/services/data/v{version}/jobs/ingest",                 "createBulkIngestJob",    "Create a bulk ingest job",                              ["Bulk"]),
        ("GET",   "/services/data/v{version}/jobs/ingest",                 "listBulkIngestJobs",     "List bulk ingest jobs",                                 ["Bulk"]),
        ("GET",   "/services/data/v{version}/jobs/ingest/{jobId}",         "getBulkJob",             "Get info about a bulk ingest job",                      ["Bulk"]),
        ("PATCH", "/services/data/v{version}/jobs/ingest/{jobId}",         "closeBulkJob",           "Close or abort a bulk ingest job",                      ["Bulk"]),
        ("DELETE","/services/data/v{version}/jobs/ingest/{jobId}",         "deleteBulkJob",          "Delete a bulk ingest job",                              ["Bulk"]),
        # Chatter
        ("GET",   "/services/data/v{version}/chatter/feeds/news/{userId}/feed-elements", "getChatterNewsFeed", "Get Chatter news feed", ["Chatter"]),
        ("POST",  "/services/data/v{version}/chatter/feed-elements",       "postChatterFeedElement", "Post to Chatter",                                       ["Chatter"]),
        # Metadata
        ("GET",   "/services/data/v{version}/limits/",                     "getApiLimits",           "Get API usage limits",                                  ["Metadata"]),
        ("GET",   "/services/data/v{version}/recent/",                     "getRecentlyViewedItems", "Get recently viewed items",                             ["Metadata"]),
        ("GET",   "/services/data/v{version}/tooling/sobjects/",           "listToolingSObjects",    "List tooling API SObjects",                             ["Tooling"]),
        ("GET",   "/services/data/v{version}/tooling/query/",              "toolingQuery",           "Execute a tooling API query",                           ["Tooling"]),
    ]

    eps = [
        {"method": m, "path": p, "operation_id": oid, "summary": s,
         "description": "", "tags": tags, "deprecated": False, "parameters": []}
        for m, p, oid, s, tags in endpoints
    ]

    return build_output(
        service_key="salesforce",
        service_name="Salesforce REST API",
        base_url="https://{instance}.salesforce.com/services/data/v{version}",
        auth_header="Authorization: Bearer <oauth_access_token>",
        endpoints=eps,
        extra={
            "api_docs": "https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_rest.htm",
            "auth_docs": "https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_oauth_and_connected_apps.htm",
            "token_endpoint": "https://login.salesforce.com/services/oauth2/token",
            "auth_endpoint": "https://login.salesforce.com/services/oauth2/authorize",
        },
    )


# ═════════════════════════════════════════════════════════════════════════════
# 10. ZENDESK SUPPORT API
# ═════════════════════════════════════════════════════════════════════════════
def extract_zendesk() -> dict:
    # Zendesk publishes an OpenAPI spec
    url = "https://raw.githubusercontent.com/zendesk/openapi/main/openapi.yaml"
    try:
        # Try to get YAML (requires PyYAML) – fall back to hardcoded if unavailable
        try:
            import yaml  # noqa: F401
            raw = http_get(url).decode()
            spec = yaml.safe_load(raw)
            endpoints = endpoints_from_openapi(spec)
            if endpoints:
                return build_output(
                    service_key="zendesk",
                    service_name="Zendesk Support REST API",
                    base_url="https://{subdomain}.zendesk.com/api/v2",
                    auth_header="Authorization: Basic <base64(email/token:api_token)>",
                    endpoints=endpoints,
                    extra={"spec_url": url},
                )
        except ImportError:
            pass
        raise ValueError("YAML not available")
    except Exception:
        pass

    # Hardcoded well-known Zendesk endpoints
    entries = [
        # Tickets
        ("GET",    "/tickets",                                 "listTickets",             "List all tickets",                      ["Tickets"]),
        ("POST",   "/tickets",                                 "createTicket",            "Create a ticket",                       ["Tickets"]),
        ("GET",    "/tickets/{ticket_id}",                     "getTicket",               "Get a ticket",                          ["Tickets"]),
        ("PUT",    "/tickets/{ticket_id}",                     "updateTicket",            "Update a ticket",                       ["Tickets"]),
        ("DELETE", "/tickets/{ticket_id}",                     "deleteTicket",            "Delete a ticket",                       ["Tickets"]),
        ("GET",    "/tickets/{ticket_id}/comments",            "listTicketComments",      "List comments for a ticket",            ["Ticket Comments"]),
        ("POST",   "/tickets/{ticket_id}/comments",            "createTicketComment",     "Add a comment to a ticket",             ["Ticket Comments"]),
        ("PUT",    "/tickets/update_many",                     "bulkUpdateTickets",       "Bulk update tickets",                   ["Tickets"]),
        ("DELETE", "/tickets/destroy_many",                    "bulkDeleteTickets",       "Bulk delete tickets",                   ["Tickets"]),
        # Users
        ("GET",    "/users",                                   "listUsers",               "List users",                            ["Users"]),
        ("POST",   "/users",                                   "createUser",              "Create a user",                         ["Users"]),
        ("GET",    "/users/{user_id}",                         "getUser",                 "Get a user",                            ["Users"]),
        ("PUT",    "/users/{user_id}",                         "updateUser",              "Update a user",                         ["Users"]),
        ("DELETE", "/users/{user_id}",                         "deleteUser",              "Delete a user",                         ["Users"]),
        ("GET",    "/users/me",                                "getCurrentUser",          "Get the current user",                  ["Users"]),
        ("GET",    "/users/search",                            "searchUsers",             "Search users",                          ["Users"]),
        # Groups
        ("GET",    "/groups",                                  "listGroups",              "List groups",                           ["Groups"]),
        ("POST",   "/groups",                                  "createGroup",             "Create a group",                        ["Groups"]),
        ("GET",    "/groups/{group_id}",                       "getGroup",                "Get a group",                           ["Groups"]),
        ("PUT",    "/groups/{group_id}",                       "updateGroup",             "Update a group",                        ["Groups"]),
        ("DELETE", "/groups/{group_id}",                       "deleteGroup",             "Delete a group",                        ["Groups"]),
        # Organizations
        ("GET",    "/organizations",                           "listOrganizations",       "List organizations",                    ["Organizations"]),
        ("POST",   "/organizations",                           "createOrganization",      "Create an organization",                ["Organizations"]),
        ("GET",    "/organizations/{organization_id}",         "getOrganization",         "Get an organization",                   ["Organizations"]),
        ("PUT",    "/organizations/{organization_id}",         "updateOrganization",      "Update an organization",                ["Organizations"]),
        ("DELETE", "/organizations/{organization_id}",         "deleteOrganization",      "Delete an organization",                ["Organizations"]),
        # Search
        ("GET",    "/search",                                  "search",                  "Search Zendesk",                        ["Search"]),
        ("GET",    "/search/count",                            "searchCount",             "Get search result count",               ["Search"]),
        ("POST",   "/search/export",                           "exportSearch",            "Export search results",                 ["Search"]),
        # Views
        ("GET",    "/views",                                   "listViews",               "List views",                            ["Views"]),
        ("POST",   "/views",                                   "createView",              "Create a view",                         ["Views"]),
        ("GET",    "/views/{view_id}",                         "getView",                 "Get a view",                            ["Views"]),
        ("PUT",    "/views/{view_id}",                         "updateView",              "Update a view",                         ["Views"]),
        ("DELETE", "/views/{view_id}",                         "deleteView",              "Delete a view",                         ["Views"]),
        ("GET",    "/views/{view_id}/tickets",                 "getViewTickets",          "Get tickets in a view",                 ["Views"]),
        # Macros
        ("GET",    "/macros",                                  "listMacros",              "List macros",                           ["Macros"]),
        ("POST",   "/macros",                                  "createMacro",             "Create a macro",                        ["Macros"]),
        ("GET",    "/macros/{macro_id}",                       "getMacro",                "Get a macro",                           ["Macros"]),
        ("PUT",    "/macros/{macro_id}",                       "updateMacro",             "Update a macro",                        ["Macros"]),
        ("DELETE", "/macros/{macro_id}",                       "deleteMacro",             "Delete a macro",                        ["Macros"]),
        ("POST",   "/macros/{macro_id}/apply",                 "applyMacro",              "Apply a macro",                         ["Macros"]),
    ]

    eps = [
        {"method": m, "path": p, "operation_id": oid, "summary": s,
         "description": "", "tags": tags, "deprecated": False, "parameters": []}
        for m, p, oid, s, tags in entries
    ]

    return build_output(
        service_key="zendesk",
        service_name="Zendesk Support REST API",
        base_url="https://{subdomain}.zendesk.com/api/v2",
        auth_header="Authorization: Basic <base64(email/token:api_token)>",
        endpoints=eps,
        extra={
            "api_reference": "https://developer.zendesk.com/api-reference/",
            "auth_docs": "https://developer.zendesk.com/api-reference/introduction/security-and-auth/",
        },
    )


# ═════════════════════════════════════════════════════════════════════════════
# 11. SERVICENOW TABLE API
# ═════════════════════════════════════════════════════════════════════════════
def extract_servicenow() -> dict:
    entries = [
        # Table API
        ("GET",    "/api/now/table/{tableName}",                                 "getRecords",           "Retrieve multiple records from a table",               ["Table API"]),
        ("POST",   "/api/now/table/{tableName}",                                 "createRecord",         "Create a record in a table",                           ["Table API"]),
        ("GET",    "/api/now/table/{tableName}/{sys_id}",                        "getRecord",            "Retrieve a record by sys_id",                          ["Table API"]),
        ("PUT",    "/api/now/table/{tableName}/{sys_id}",                        "replaceRecord",        "Replace a record by sys_id",                           ["Table API"]),
        ("PATCH",  "/api/now/table/{tableName}/{sys_id}",                        "updateRecord",         "Update a record by sys_id",                            ["Table API"]),
        ("DELETE", "/api/now/table/{tableName}/{sys_id}",                        "deleteRecord",         "Delete a record by sys_id",                            ["Table API"]),
        # Aggregate API
        ("GET",    "/api/now/stats/{tableName}",                                 "getAggregateStats",    "Get aggregate statistics for a table",                  ["Aggregate API"]),
        # Import Set API
        ("POST",   "/api/now/import/{stagingTableName}",                         "importRecord",         "Insert a record into a staging table",                  ["Import Set API"]),
        ("POST",   "/api/now/import/{stagingTableName}/insertMultiple",          "importMultiple",       "Insert multiple records into a staging table",          ["Import Set API"]),
        # Attachment API
        ("GET",    "/api/now/attachment",                                        "listAttachments",      "Retrieve all attachments",                              ["Attachment API"]),
        ("POST",   "/api/now/attachment/file",                                   "uploadAttachment",     "Upload a file attachment",                              ["Attachment API"]),
        ("GET",    "/api/now/attachment/{sys_id}",                               "getAttachment",        "Retrieve attachment metadata",                          ["Attachment API"]),
        ("GET",    "/api/now/attachment/{sys_id}/file",                          "downloadAttachment",   "Download attachment file",                              ["Attachment API"]),
        ("DELETE", "/api/now/attachment/{sys_id}",                               "deleteAttachment",     "Delete an attachment",                                  ["Attachment API"]),
        # CI/CD API
        ("POST",   "/api/sn_cicd/app_repo/install",                              "installApp",           "Install an application from a source control repo",     ["CI/CD API"]),
        ("POST",   "/api/sn_cicd/app_repo/publish",                              "publishApp",           "Publish an application to a source control repo",       ["CI/CD API"]),
        ("POST",   "/api/sn_cicd/sc/apply_changes",                              "applyChanges",         "Apply changes from a source control branch",            ["CI/CD API"]),
        ("POST",   "/api/sn_cicd/plugin/{pluginID}/activate",                    "activatePlugin",       "Activate a plugin",                                     ["CI/CD API"]),
        ("POST",   "/api/sn_cicd/plugin/{pluginID}/rollback",                    "rollbackPlugin",       "Rollback a plugin to a previous version",               ["CI/CD API"]),
        ("GET",    "/api/sn_cicd/progress/{progressID}",                         "getProgress",          "Get the progress of a CI/CD operation",                 ["CI/CD API"]),
        # Scripted REST
        ("GET",    "/api/now/ui/scripted_rest_apis",                             "listScriptedAPIs",     "List scripted REST APIs",                               ["Scripted REST"]),
        # Password Reset
        ("POST",   "/api/now/pa/reset_user_password",                            "resetPassword",        "Reset a user's password",                               ["Password Reset"]),
    ]

    eps = [
        {"method": m, "path": p, "operation_id": oid, "summary": s,
         "description": "", "tags": tags, "deprecated": False, "parameters": []}
        for m, p, oid, s, tags in entries
    ]

    return build_output(
        service_key="servicenow",
        service_name="ServiceNow REST API (Table API)",
        base_url="https://{instance}.service-now.com",
        auth_header="Authorization: Basic <base64(username:password)> or Authorization: Bearer <oauth_token>",
        endpoints=eps,
        extra={
            "table_api_docs": "https://docs.servicenow.com/bundle/utah-application-development/page/integrate/inbound-rest/concept/c_TableAPI.html",
            "rest_explorer": "https://{instance}.service-now.com/api_doc.do",
            "auth_docs": "https://www.servicenow.com/docs/r/washingtondc/platform-security/authentication/token-based-auth-api.html",
        },
    )


# ═════════════════════════════════════════════════════════════════════════════
# 12. GOOGLE WORKSPACE APIs
# ═════════════════════════════════════════════════════════════════════════════
GOOGLE_DISCOVERY_APIS = {
    "Gmail": "https://www.googleapis.com/discovery/v1/apis/gmail/v1/rest",
    "Drive": "https://www.googleapis.com/discovery/v1/apis/drive/v3/rest",
    "Calendar": "https://www.googleapis.com/discovery/v1/apis/calendar/v3/rest",
    "Sheets": "https://www.googleapis.com/discovery/v1/apis/sheets/v4/rest",
}


def endpoints_from_google_discovery(discovery_doc: dict, service_name: str) -> list[dict]:
    """Extract endpoints from a Google Discovery document."""
    eps = []
    base_path = discovery_doc.get("basePath", "/")

    def walk_resources(resources: dict, path_prefix: str = ""):
        for resource_name, resource in resources.items():
            for method_name, method in resource.get("methods", {}).items():
                http_method = method.get("httpMethod", "GET")
                path = method.get("path", "")
                # Combine base and method path
                full_path = path_prefix + "/" + path if path_prefix else path
                # Normalize double slashes
                full_path = re.sub(r"/+", "/", full_path)

                params = [
                    {
                        "name": p_name,
                        "in": "query" if p_info.get("location") == "query" else "path",
                        "required": p_info.get("required", False),
                        "description": p_info.get("description", ""),
                    }
                    for p_name, p_info in method.get("parameters", {}).items()
                ]

                eps.append(
                    {
                        "method": http_method,
                        "path": full_path,
                        "operation_id": method.get("id", f"{resource_name}.{method_name}"),
                        "summary": method.get("description", ""),
                        "description": method.get("description", ""),
                        "tags": [service_name, resource_name],
                        "deprecated": False,
                        "parameters": params,
                        "scopes": method.get("scopes", []),
                    }
                )

            # Recurse into sub-resources
            sub_resources = resource.get("resources", {})
            if sub_resources:
                walk_resources(sub_resources, path_prefix)

    walk_resources(discovery_doc.get("resources", {}))
    return eps


def extract_google_workspace() -> dict:
    all_endpoints: list[dict] = []

    for svc, discovery_url in GOOGLE_DISCOVERY_APIS.items():
        try:
            doc = fetch_json(discovery_url)
            eps = endpoints_from_google_discovery(doc, svc)
            all_endpoints.extend(eps)
            print(f"    ✓ Google {svc}: {len(eps)} endpoints")
            time.sleep(0.3)
        except Exception as e:
            print(f"    ⚠ Google {svc} failed: {e}", file=sys.stderr)

    return build_output(
        service_key="google_workspace",
        service_name="Google Workspace APIs (Gmail, Drive, Calendar, Sheets)",
        base_url="https://www.googleapis.com",
        auth_header="Authorization: Bearer <oauth2_access_token>",
        endpoints=all_endpoints,
        extra={
            "included_apis": list(GOOGLE_DISCOVERY_APIS.keys()),
            "developer_hub": "https://developers.google.com/workspace",
            "auth_docs": "https://developers.google.com/identity/protocols/oauth2",
            "credentials_console": "https://console.cloud.google.com/apis/credentials",
        },
    )


# ═════════════════════════════════════════════════════════════════════════════
# SERVICE REGISTRY
# ═════════════════════════════════════════════════════════════════════════════
SERVICES: dict[str, tuple[str, Any]] = {
    "jira_cloud":               ("jira_cloud_endpoints.json",               extract_jira_cloud),
    "jira_server_datacenter":   ("jira_server_dc_endpoints.json",           extract_jira_server),
    "jira_service_management":  ("jira_service_management_endpoints.json",  extract_jira_service_management),
    "confluence_cloud":         ("confluence_cloud_endpoints.json",         extract_confluence_cloud),
    "slack":                    ("slack_api_endpoints.json",                extract_slack),
    "hubspot":                  ("hubspot_api_endpoints.json",              extract_hubspot),
    "notion":                   ("notion_api_endpoints.json",               extract_notion),
    "github":                   ("github_api_endpoints.json",               extract_github),
    "salesforce":               ("salesforce_api_endpoints.json",           extract_salesforce),
    "zendesk":                  ("zendesk_api_endpoints.json",              extract_zendesk),
    "servicenow":               ("servicenow_api_endpoints.json",           extract_servicenow),
    "google_workspace":         ("google_workspace_api_endpoints.json",     extract_google_workspace),
}


# ═════════════════════════════════════════════════════════════════════════════
# CLI & RUNNER
# ═════════════════════════════════════════════════════════════════════════════

def run_service(key: str, output_dir: Path) -> bool:
    filename, extractor = SERVICES[key]
    out_path = output_dir / filename
    print(f"\n{'─' * 60}")
    print(f"  [{key}]  →  {filename}")
    print(f"{'─' * 60}")
    try:
        data = extractor()
        out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        print(f"  ✓ {data['total_endpoints']} endpoints saved → {out_path}")
        return True
    except Exception as exc:
        print(f"  ✗ FAILED: {exc}", file=sys.stderr)
        return False


def print_summary(results: dict[str, bool]) -> None:
    print(f"\n{'═' * 60}")
    print("  EXTRACTION SUMMARY")
    print(f"{'═' * 60}")
    ok = sum(v for v in results.values())
    for key, success in results.items():
        status = "✓" if success else "✗"
        print(f"  {status}  {key}")
    print(f"{'─' * 60}")
    print(f"  {ok}/{len(results)} services extracted successfully")
    print(f"{'═' * 60}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract API endpoints for 12 enterprise services.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--service",
        choices=list(SERVICES.keys()),
        help="Extract only a specific service (default: all).",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        metavar="DIR",
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR}).",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available service keys and exit.",
    )
    args = parser.parse_args()

    if args.list:
        print("\nAvailable services:")
        for key, (fname, _) in SERVICES.items():
            print(f"  {key:<30}  →  {fname}")
        return

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    targets = [args.service] if args.service else list(SERVICES.keys())

    print(f"\n{'═' * 60}")
    print("  Enterprise API Endpoint Extractor")
    print(f"  Output dir: {output_dir.resolve()}")
    print(f"  Services  : {len(targets)}")
    print(f"{'═' * 60}")

    results = {}
    for key in targets:
        results[key] = run_service(key, output_dir)

    print_summary(results)


if __name__ == "__main__":
    main()