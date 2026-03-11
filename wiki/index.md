# Sophikon — Product Overview

## What Is It?

Sophikon is an **AI-powered project management platform** modeled after Microsoft Project and Monday.com. It provides Gantt charts, WBS task hierarchies, dependency scheduling, resource management, and AI-assisted features — all in a modern web application.

The name comes from "sophia" (wisdom) + "ikon" (image), reflecting the goal of making project intelligence visible.

## Who Is It For?

| Audience            | Use Case                                                         |
| ------------------- | ---------------------------------------------------------------- |
| Project Managers    | Gantt scheduling, critical path, resource utilization, WBS       |
| Team Members        | Task tracking, time logging, collaboration, notifications        |
| University Showcase | Full-stack portfolio piece demonstrating production architecture |

The V1.0 is a university MVP scheduled for **April 2026**, with community and enterprise releases planned through 2027.

## Current Status

| Component        | Status         | Notes                                              |
| ---------------- | -------------- | -------------------------------------------------- |
| Authentication   | ✅ Built        | JWT + refresh tokens, email verification, RBAC     |
| Organizations    | ✅ Built        | Multi-tenancy, org CRUD, membership, roles         |
| Project CRUD     | ✅ Built        | Org-scoped projects with settings and members      |
| Task Management  | ✅ Built        | Hierarchy, WBS, drag-drop reorder, bulk ops        |
| Gantt Chart      | ✅ Built        | Custom canvas, dependency arrows, timeline zoom    |
| Scheduling Engine| ✅ Built        | Forward scheduling, critical path, constraints     |
| Resources        | ✅ Built        | CRUD, assignments, utilization, over-allocation    |
| AI Service       | ✅ Built        | Chat (SSE), estimation, suggestions (mock mode)    |
| Calendars        | ✅ Built        | Work calendars, exceptions, inheritance            |
| Comments         | ✅ Built        | Polymorphic comments on any entity                 |
| Notifications    | ✅ Built        | In-app + WebSocket real-time notifications         |
| Project Members  | ✅ Built        | Invite via email, RBAC roles, accept flow          |
| WebSockets       | ✅ Built        | Real-time project updates and user notifications   |
| Import/Export    | 🔲 Planned      | MS Project XML, CSV — V1.0 Phase 4                 |
| Baselines        | 🔲 Planned      | Save/compare schedule snapshots — V1.0 Phase 4     |
| Time Tracking    | 🔲 Schema-only  | Model exists, no endpoints — V1.1+                 |
| Advanced AI      | 🔲 Planned      | AI Planner, Risk Detector, Optimizer — V1.2        |
| OAuth (Google)   | 🔲 Planned      | V1.0                                               |
| Landing Page     | ✅ Built        | Static HTML, separate from React SPA               |
| Deployment       | ✅ Documented   | AWS EC2 + S3 + CloudFront, Docker Compose, SSL     |
| CI/CD            | ✅ Built        | GitHub Actions, pre-commit hooks                   |

## Tech Stack Summary

| Layer          | Technology                                                           |
| -------------- | -------------------------------------------------------------------- |
| Backend        | Python 3.13, FastAPI, SQLAlchemy 2.0 (async), Alembic, Celery       |
| Database       | PostgreSQL 18, Redis 7                                               |
| Frontend       | React 19, TypeScript 5.9, Vite, Tailwind CSS 4.1, shadcn/ui         |
| State          | Zustand (per-feature stores), TanStack Query (server state)          |
| AI Service     | Standalone FastAPI microservice (mock + live LLM modes)              |
| Infrastructure | Docker Compose, Nginx, GitHub Actions, AWS (EC2 + S3 + CloudFront)  |

---

*Evidence: [`README.md`](../README.md), [`CLAUDE.md`](../CLAUDE.md), [`docs/03-implementation/project-plan.md`](../docs/03-implementation/project-plan.md)*
