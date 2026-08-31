# Architecture Modernization

## Target boundaries

```text
UI / CLI
   |
Application services
   |
+----------------------+--------------------+-------------------+
| Scraping             | Extraction         | Scheduling        |
| HTTP + browser       | selectors/parsers  | durable jobs      |
+----------------------+--------------------+-------------------+
| Network policy       | Persistence        | Observability     |
| URL/SSRF/proxy       | projects/history   | logs/metrics      |
+----------------------+--------------------+-------------------+
                     Domain models
```

## Migration rules

1. Preserve the current public behavior unless a security issue requires a breaking change.
2. Add typed boundary modules before moving implementation behind them.
3. Keep network policy independent from scraping strategies.
4. Keep extraction pure where possible: input document + rule -> structured result.
5. Keep persistence behind interfaces so SQLite remains an implementation detail.
6. Make scheduler execution idempotent and observable.
7. Keep analytics/quant features isolated from the primary scraping pipeline.
8. Add regression tests before moving high-risk logic.

## Near-term sequence

- API request/auth/error boundary
- URL and redirect policy enforcement in HTTP and Playwright paths
- response/body/resource limits
- typed scrape job and extraction models
- persistent job execution records
- proxy health/circuit breaker
- integration fixtures for static and dynamic scraping
- end-to-end desktop smoke test
- reproducible release and artifact verification
