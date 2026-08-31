# Security Policy

## Scope

WebScraper Pro is a desktop scraping and analysis application. It can make outbound HTTP requests, launch a browser through Playwright, persist local project/history data, manage proxies, and expose a local HTTP API.

## Security principles

- Never commit credentials, cookies, session tokens, API keys, or private certificates.
- Keep the local API bound to loopback unless an explicit deployment configuration requires otherwise.
- Do not treat scraped HTML, JSON, headers, or downloaded files as trusted input.
- Validate URLs, file paths, selectors, expressions, export destinations, and scheduler inputs at trust boundaries.
- Apply request timeouts, response-size limits, redirect limits, and per-domain rate limits.
- Avoid executing downloaded content or shell commands derived from scraped data.
- Redact secrets and sensitive payloads from logs and persisted history.
- Use least-privilege permissions in CI and release workflows.

## Reporting a vulnerability

Please do not open a public issue for an undisclosed security vulnerability. Use GitHub's private vulnerability reporting mechanism for this repository when available. Include a concise description, affected component/version, reproduction steps, impact assessment, and a suggested mitigation if known.

If private reporting is unavailable, contact the repository owner privately through GitHub before public disclosure.

## Credential rotation

If a credential is ever committed accidentally, remove it from the working tree **and rotate/revoke the credential immediately**. Removing the file from the latest commit does not invalidate a credential that was already exposed in repository history.
