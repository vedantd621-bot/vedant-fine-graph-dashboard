# Multi-Investigator Collaboration & Activity Feeds

## Overview
The Collaboration System (`backend/app/case_intelligence/service.py`) enables real-time team investigation workflows.

## Features
- **Collaborator Roles**: `OWNER` (full control), `COLLABORATOR` (create notes/evidence), `WATCHER` (read-only observer).
- **Auditable Comments**: Comments support creation, inline editing (with `is_edited=True`), and soft deletion preserving audit history.
- **Immutable Chronological Activity Feed**: Chronological log of case creations, assignments, status transitions, evidence additions, and comments with actor attribution and request correlation IDs.
