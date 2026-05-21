# Analyst Review Workflow

This document explains the Analyst Review Inbox, a human-in-the-loop mechanism introduced in Phase 62.

## Core Concepts

The Analyst Review Inbox is a completely **offline, local-first** system. It presents automated research candidates (signals, consensus outcomes, portfolio targets) to a human analyst for manual review.

### Research-Only
All actions inside the review system are **research-only**.
- An `APPROVED_RESEARCH` decision is **not** an order execution instruction.
- A `REJECTED_RESEARCH` decision is **not** a sell order.
- No real orders are sent to any broker API.
- There is no automated connection between an approval and a live trade.

### The Review Process
1. **Inbox Triage**: Items land in the inbox from the scanner or signal lifecycle.
2. **Evidence Collection**: The system aggregates fundamental, technical, stress, and drift context.
3. **Checklist Validation**: A predefined checklist is filled out. Missing required checklist items prevent normal approval.
4. **Thesis Building**: The analyst must write a main thesis, and ideally a counter-thesis with invalidation points. The thesis text is sanitized of unsafe claims (like "100% guarantee").
5. **Decision & Journal**: The analyst makes a decision (e.g., WATCH_ONLY, APPROVE_RESEARCH). This is appended to the Decision Journal for future outcome-tracking.
6. **Follow-ups**: Setting a follow-up date puts the item back in front of the analyst at the specified time. This is a local metadata tag, not an external calendar invite.

## Governance & Security
All thesis texts, decision reasons, and manual notes are passed through the Governance Gates. If unsafe financial claims ("kesin kazanç", "garanti") are detected, they are flagged or sanitized.

Data is stored locally in append-only JSONL files. Deleting an item (Archiving) requires explicit confirmation.
