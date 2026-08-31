# Security Policy

## Scope

WebScraper Pro is a desktop scraping and automation application. Security work prioritizes safe handling of user credentials, untrusted web content, filesystem paths, network destinations, browser processes, generated artifacts, and local API access.

## Security Boundaries

- Do not commit secrets, tokens, cookies, private keys, or local environment files.
- Treat scraped HTML, JSON, headers, filenames, URLs, and imported project files as untrusted input.
- Validate outbound URLs before HTTP or browser navigation, including redirects and user-controlled proxy settings.
- Local API endpoints must not be exposed beyond the intended interface without explicit authentication and access control.
- Generated files must stay inside approved output locations and must not allow path traversal.
- Browser automation must use bounded timeouts, bounded concurrency, and explicit resource limits.
- CAPTCHA or anti-bot detection is an operational signal, not a mechanism to bypass access controls.

## Reporting

Please report suspected security issues privately to the repository owner rather than opening a public issue with exploit details. Include affected component, reproduction steps, impact, and a suggested mitigation when available.

## Secret Rotation

If a credential is ever committed, remove it from active use and rotate it at the provider. Removing the file in a later commit does not make a previously committed secret safe.
