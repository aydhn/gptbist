# Developer Guide

## Review Workflow
Read `docs/59_ANALYST_REVIEW_WORKFLOW.md` for information on the Review Workflow implementation, case builder, sign-offs, and human-in-the-loop features.

## Architecture Guidelines
- No HTML scraping or third-party web crawlers allowed.
- No paid cloud APIs (e.g. OpenAI) allowed.
- Only run offline research and simulation. Real broker orders are explicitly prohibited.
