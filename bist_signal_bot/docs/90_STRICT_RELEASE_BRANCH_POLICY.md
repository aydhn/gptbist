# Strict Release Branch Policy

## Overview
This document outlines the strict release branch policy for the BIST Signal Bot.

## Branch Kinds
- `main`: Protected, production-ready codebase.
- `develop`: Main integration branch.
- `release/*`: Preparation for a new release.
- `hotfix/*`: Critical bug fixes for `main`.
- `feature/*`: New features or enhancements.
- `experimental/*`: R&D, not for release.
- `archive/*`: Preserved code.

## Required Artifacts
- **Changelog**: Required for all releases.
- **Migration Notes**: Required for breaking changes, schema updates, etc.
- **Deprecation Notices**: When retiring old features.

## Compatibility Gate
All releases must pass compatibility checks (Schema, Config, CLI, Data Contract).

## Disclaimer
> *Branch policy is local software release governance metadata only. It is not investment advice, deployment approval, or permission to trade. No real order was sent.*
