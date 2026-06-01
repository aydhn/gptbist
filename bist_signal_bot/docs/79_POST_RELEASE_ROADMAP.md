# Phase 100: Post-Release Roadmap

This document outlines potential future enhancements for the BIST Signal Bot following the Final MVP Handoff.

**Disclaimer:** This roadmap outlines software capabilities only and does not represent a promise of financial performance or trading capability.

## Phase 101: Performance Optimization & Profiling
- **Priority**: HIGH
- **Target Area**: core
- **Description**: Profile and optimize critical paths in the scanner and backtesting engines using line_profiler and cProfile. Implement efficient numpy/pandas vectorization where loops still exist.

## Phase 102: Richer Local Data Import Adapters
- **Priority**: MEDIUM
- **Target Area**: data
- **Description**: Add support for more offline data formats (e.g., direct SQLite reading, Parquet arrays) for faster sequential reads.

## Phase 103: Advanced Report Templates
- **Priority**: LOW
- **Target Area**: reports
- **Description**: Expose Jinja2 templating natively to allow operators to construct deeply customized markdown and HTML-rendered PDF reports entirely offline.

## Phase 105: Optional Local UI/TUI Investigation
- **Priority**: MEDIUM
- **Target Area**: ux
- **Description**: Investigate safe, offline local Text UI (TUI) options like Textual to browse scanner results without breaking the core CLI contract constraints or exposing a web server.

## Phase 109: Plugin Architecture
- **Priority**: MEDIUM
- **Target Area**: architecture
- **Description**: Decouple modules into isolated plugins with defined interfaces, allowing third-party local models or signals to be dropped in without altering core files.

## Phase 110: Strict Release Branch Policy
- **Priority**: HIGH
- **Target Area**: governance
- **Description**: Implement semantic release and branching governance utilizing the local Git history and hook directly into the QA/Release Gates.
