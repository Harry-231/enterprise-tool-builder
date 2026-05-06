# Tool Creator Skill

A comprehensive guide and implementation framework for building high-quality custom LangChain tools over well-documented enterprise SaaS APIs such as Salesforce, HubSpot, Zendesk, Jira, Confluence, and Slack.

## Overview

This skill defines a step-by-step process for creating production-grade LangChain tools that integrate with external enterprise SaaS APIs. It covers research, API analysis, tool interface design, authentication-aware wrappers, validation, pagination, retries, and comprehensive testing strategies.

## Key Features

- Enterprise SaaS API integration patterns
- LangChain tool design best practices
- Authentication and authorization handling
- Structured input and output schema design
- Error handling and reliability patterns
- Validation and testing frameworks
- Context management for agentic systems
- Production deployment recommendations

## Supported Platforms

This skill is optimized for building tools for:

- Atlassian Jira
- Atlassian Confluence
- Salesforce
- HubSpot
- Zendesk
- Slack
- Other stable REST or OpenAPI-based SaaS platforms

## Prerequisites

- Python 3.13 or higher
- Network access to target enterprise SaaS APIs
- Valid credentials and API keys for the SaaS platform
- Understanding of REST API concepts
- Familiarity with LangChain framework

## Installation

1. Clone the repository
2. Navigate to the project directory:
   ```
   cd tool-creator-skill
   ```

3. Create and activate a Python virtual environment:
   ```
   python -m venv python
   ```

4. On Windows (PowerShell):
   ```
   (Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& .\python\Scripts\Activate.ps1)
   ```

5. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

Or using the project's pyproject.toml:
   ```
   pip install -e .
   ```

## Project Structure

```
tool-creator-skill/
├── README.md                 # Project documentation
├── SKILL.md                  # Detailed skill guide and workflow
├── main.py                   # Main entry point
├── pyproject.toml           # Project configuration and dependencies
├── python/                  # Virtual environment directory
├── assets/                  # Supporting assets and resources
├── scripts/                 # Utility scripts
└── references/              # Reference documentation and links
```

## Dependencies

Core dependencies managed in pyproject.toml:

- langchain >= 1.2.17: Core LangChain framework
- langchain-tools >= 0.1.34: Tool building utilities
- langgraph >= 1.1.10: Graph-based orchestration
- langsmith >= 0.8.0: Monitoring and debugging

## Getting Started


## Workflow Overview

### Phase 1: Deep Research and Planning

- Understand user requirements and use cases
- Research official API documentation
- Finalize API endpoints to integrate
- Define authentication strategy
- Create structured input/output schemas
- Establish naming conventions and discoverability patterns

### Phase 2: Tool Implementation

- Implement authentication wrappers
- Build API client integration layers
- Design tool interfaces with clear schemas
- Add validation and error handling
- Implement pagination and retry logic

### Phase 3: Testing and Validation

- Unit testing for individual components
- Integration testing with actual APIs
- Error scenario validation
- Performance and reliability testing

### Phase 4: Deployment and Monitoring

- Production deployment setup
- Observability and monitoring configuration
- Error handling and recovery patterns

## Authentication Setup

Each enterprise SaaS platform requires different authentication methods:

- Jira Cloud: Basic authentication with API token
- Salesforce: OAuth 2.0 token-based authentication
- HubSpot: API key or OAuth 2.0
- Confluence: API token authentication
- Slack: Bot tokens or OAuth 2.0

Refer to the SKILL.md document for detailed authentication setup instructions for each platform.

## Environment Variables

Create a .env file in the project root with necessary credentials:

```
API_KEY=your_api_key_here
API_TOKEN=your_token_here
API_ENDPOINT=https://api.example.com
```


## Use Cases

This skill is ideal for:

- Building autonomous agents that interact with enterprise systems
- Creating internal copilot assistants
- Developing workflow automation tools
- Integrating LLMs with SaaS platforms
- Building multi-step enterprise workflows

## Limitations


## Compatibility

- Requires network access to target enterprise SaaS APIs
- Best suited for APIs with stable, well-documented REST or OpenAPI interfaces
- Supports Python 3.13+
- Compatible with LangChain 1.2.17+

## Contributing

When extending this skill:

1. Follow the documented workflow and best practices
2. Add tests for new tool implementations
3. Update documentation with new patterns
4. Maintain consistent naming conventions
5. Include error handling and retry logic

## License

See LICENSE.txt for license information.

## Support

For issues, questions, or contributions, refer to the project's issue tracking system and documentation.

## Additional Resources

- API Documentation Resources: See references/REFERENCES.md
- LangChain Community: https://discord.gg/cU2qFTc9Vs
- Official Platform Developer Communities: Jira, Salesforce, HubSpot, Slack, etc.

## Version

Current version: 0.1.0

Last updated: May 2026
