# Sophikon V1.0 - User Stories

**Version:** 1.0
**Date:** 2026-02-06
**Status:** Aligned with database-schema.md v3.0

---

## Document References

| Document                   | Relationship                         |
| -------------------------- | ------------------------------------ |
| functional-requirements.md | User stories → Functional reqs       |
| database-schema.md         | Data entities referenced in stories  |
| api-specification.md       | API endpoints implementing stories   |
| ai-features.md             | AI-specific stories (Epic 5)         |

---

## User Personas

### 1. Project Manager (PM) - "Sarah"

- Manages 3-5 projects simultaneously
- Needs visibility into timelines and resources
- Reports to stakeholders weekly
- Primary user of planning and tracking features

### 2. Team Lead (TL) - "Marcus"

- Manages a team of 5-8 people
- Assigns and monitors team tasks
- Needs resource utilization view
- Updates task progress regularly

### 3. Team Member (TM) - "Alex"

- Works on assigned tasks
- Updates own task progress
- Needs simple, focused view
- May work on multiple projects

### 4. Stakeholder (SH) - "Diana"

- Executive/client who needs project visibility
- View-only access
- Interested in milestones and high-level status
- Receives reports

---

## Epic 1: Project Setup & Management

### US-1.1: Create New Project

**As a** Project Manager
**I want to** create a new project with basic information
**So that** I can start planning my project

**Acceptance Criteria:**

- [ ] Can enter project name (required)
- [ ] Can enter description (optional)
- [ ] Can set start date (defaults to today)
- [ ] Can select scheduling mode (forward/backward)
- [ ] Can select default calendar
- [ ] Project is created and opens in Gantt view

---

### US-1.2: Create Project with AI

**As a** Project Manager
**I want to** describe my project to AI and get a generated plan
**So that** I can quickly bootstrap a project with reasonable estimates

**Acceptance Criteria:**

- [ ] Can enter free-text project description
- [ ] Can specify team size/composition
- [ ] Can specify timeline constraints
- [ ] AI generates task hierarchy (WBS)
- [ ] AI suggests dependencies
- [ ] AI provides duration estimates
- [ ] Can review and modify before accepting
- [ ] Can regenerate with different parameters

---

### US-1.3: Import Existing Project

**As a** Project Manager
**I want to** import a project from MS Project XML file
**So that** I can migrate existing projects to this system

**Acceptance Criteria:**

- [ ] Can upload .xml file (MS Project format)
- [ ] Tasks are imported with hierarchy intact
- [ ] Dependencies are preserved
- [ ] Resources are imported
- [ ] Assignments are preserved
- [ ] Calendars are imported
- [ ] Shows import summary with any warnings

---

### US-1.4: Project Dashboard

**As a** Project Manager
**I want to** see a dashboard overview of my project
**So that** I can quickly assess project health

**Acceptance Criteria:**

- [ ] Shows overall % complete
- [ ] Shows tasks by status (not started, in progress, complete, overdue)
- [ ] Shows upcoming milestones
- [ ] Shows critical path summary
- [ ] Shows resource utilization summary
- [ ] Shows AI-detected risks (if any)
- [ ] Can click through to details

---

## Epic 2: Task Management

### US-2.1: Add Task

**As a** Project Manager
**I want to** add a new task to my project
**So that** I can define work that needs to be done

**Acceptance Criteria:**

- [ ] Can add task via button or keyboard shortcut
- [ ] Can enter task name (required)
- [ ] Task is added at current selection or end of list
- [ ] New task row is immediately editable
- [ ] Can tab through fields to enter details

---

### US-2.2: Edit Task Properties

**As a** Project Manager
**I want to** edit all properties of a task
**So that** I can fully define task details

**Acceptance Criteria:**

- [ ] Can double-click task to open detail panel
- [ ] Can edit: name, duration, start/finish, notes
- [ ] Can set constraint type and date
- [ ] Can set scheduling type
- [ ] Can set priority
- [ ] Can mark as milestone
- [ ] Changes auto-save or have explicit save

---

### US-2.3: Create Task Hierarchy (WBS)

**As a** Project Manager
**I want to** organize tasks in a hierarchy
**So that** I can create a Work Breakdown Structure

**Acceptance Criteria:**

- [ ] Can indent task (make child of above task)
- [ ] Can outdent task (move up in hierarchy)
- [ ] Parent tasks automatically become summary tasks
- [ ] Summary tasks show rolled-up duration
- [ ] Summary tasks show rolled-up progress
- [ ] Can collapse/expand summary tasks
- [ ] WBS codes auto-generate (e.g., 1.1, 1.1.1)

---

### US-2.4: Create Dependencies

**As a** Project Manager
**I want to** link tasks with dependencies
**So that** the schedule respects task relationships

**Acceptance Criteria:**

- [ ] Can create FS dependency (default)
- [ ] Can create FF, SS, SF dependencies
- [ ] Can add lag time (positive or negative)
- [ ] Can create by dragging in Gantt
- [ ] Can create via task properties
- [ ] Can create by selecting multiple tasks and linking
- [ ] Circular dependencies are prevented with error message

---

### US-2.5: AI Task Estimation

**As a** Project Manager
**I want** AI to suggest task duration estimates
**So that** I get realistic estimates faster

**Acceptance Criteria:**

- [ ] Can click "Estimate with AI" on task
- [ ] AI analyzes task name and description
- [ ] AI provides optimistic/likely/pessimistic estimates
- [ ] AI shows reasoning for estimate
- [ ] AI shows similar historical tasks (if available)
- [ ] Can accept, modify, or reject estimate
- [ ] Can bulk-estimate multiple tasks

---

### US-2.6: Update Task Progress

**As a** Team Member
**I want to** update my task progress
**So that** the project reflects actual status

**Acceptance Criteria:**

- [ ] Can set % complete (0-100)
- [ ] Can set actual start date
- [ ] Can set actual finish date (marks 100%)
- [ ] Can add progress notes/comments
- [ ] Gantt bar shows progress visually
- [ ] Summary tasks auto-calculate progress

---

## Epic 3: Resource Management

### US-3.1: Add Resource

**As a** Project Manager
**I want to** add team members as resources
**So that** I can assign them to tasks

**Acceptance Criteria:**

- [ ] Can add work resource (person)
- [ ] Can specify name and email
- [ ] Can set max units (availability %)
- [ ] Can set hourly rates
- [ ] Can assign calendar
- [ ] Resource appears in resource sheet

---

### US-3.2: Assign Resource to Task

**As a** Project Manager
**I want to** assign resources to tasks
**So that** work is allocated to team members

**Acceptance Criteria:**

- [ ] Can assign from task properties
- [ ] Can assign from resource dropdown in Gantt
- [ ] Can assign multiple resources to one task
- [ ] Can set allocation % per assignment
- [ ] Can see assigned resources on Gantt bars
- [ ] Resource workload updates automatically

---

### US-3.3: View Resource Utilization

**As a** Project Manager
**I want to** see resource workload over time
**So that** I can identify over/under allocation

**Acceptance Criteria:**

- [ ] Resource usage view shows time-phased allocation
- [ ] Over-allocation highlighted in red
- [ ] Can see which tasks contribute to workload
- [ ] Can filter by date range
- [ ] Can filter by resource
- [ ] Shows utilization percentage

---

### US-3.4: AI Resource Optimization

**As a** Project Manager
**I want** AI to suggest resource reallocation
**So that** I can resolve over-allocation efficiently

**Acceptance Criteria:**

- [ ] AI identifies over-allocated resources
- [ ] AI suggests alternative assignments
- [ ] AI considers skills/roles if defined
- [ ] Shows impact of suggested changes
- [ ] Can accept/reject suggestions
- [ ] Can apply suggestions in bulk

---

## Epic 4: Gantt Chart

### US-4.1: View Gantt Chart

**As a** Project Manager
**I want to** see tasks displayed on a Gantt chart
**So that** I can visualize the project timeline

**Acceptance Criteria:**

- [ ] Tasks shown as horizontal bars
- [ ] Bar position reflects start/finish dates
- [ ] Bar length reflects duration
- [ ] Milestones shown as diamonds
- [ ] Summary tasks shown as brackets
- [ ] Dependencies shown as arrows
- [ ] Today line visible
- [ ] Timeline header shows dates

---

### US-4.2: Zoom & Navigate Gantt

**As a** Project Manager
**I want to** zoom and navigate the Gantt timeline
**So that** I can see different time ranges

**Acceptance Criteria:**

- [ ] Can zoom in/out (day/week/month/quarter/year)
- [ ] Can scroll horizontally through timeline
- [ ] Can scroll vertically through tasks
- [ ] Can "Go to today"
- [ ] Can "Go to date"
- [ ] Can fit project to view
- [ ] Mouse wheel zooms

---

### US-4.3: Interactive Gantt Editing

**As a** Project Manager
**I want to** edit tasks directly in the Gantt chart
**So that** I can quickly adjust the schedule visually

**Acceptance Criteria:**

- [ ] Can drag task bar to change dates
- [ ] Can drag bar edges to change duration
- [ ] Can drag to create dependencies
- [ ] Can double-click to open task details
- [ ] Can right-click for context menu
- [ ] Changes reflect immediately
- [ ] Undo available for accidental changes

---

### US-4.4: Critical Path Highlighting

**As a** Project Manager
**I want to** see the critical path highlighted
**So that** I can focus on tasks that affect the finish date

**Acceptance Criteria:**

- [ ] Critical path tasks highlighted (different color)
- [ ] Can toggle critical path display on/off
- [ ] Critical path dependencies also highlighted
- [ ] Slack/float shown for non-critical tasks

---

## Epic 5: AI Assistant

### US-5.1: Chat with Project

**As a** Team Member
**I want to** ask questions about the project in natural language
**So that** I can get information without navigating the UI

**Acceptance Criteria:**

- [ ] Chat panel accessible from any view
- [ ] Can ask about task status, dates, assignments
- [ ] Can ask about resource workload
- [ ] Can ask about project progress
- [ ] Responses are contextual to current project
- [ ] Can click entities in responses to navigate

---

### US-5.2: AI Actions via Chat

**As a** Project Manager
**I want to** make changes via chat commands
**So that** I can quickly update the project

**Acceptance Criteria:**

- [ ] Can add tasks: "Add task 'Review docs' for 2 days"
- [ ] Can assign: "Assign Sarah to API task"
- [ ] Can update: "Mark login task as 50% complete"
- [ ] Can move: "Move testing to start March 1"
- [ ] Shows preview before applying changes
- [ ] Requires confirmation for bulk changes

---

### US-5.3: AI Risk Alerts

**As a** Project Manager
**I want** AI to proactively alert me to risks
**So that** I can address issues before they impact the project

**Acceptance Criteria:**

- [ ] AI analyzes project continuously (or on-demand)
- [ ] Risks shown in dashboard widget
- [ ] Risks categorized by severity
- [ ] Each risk has explanation and recommendation
- [ ] Can dismiss or acknowledge risks
- [ ] Can click through to affected tasks

---

### US-5.4: AI Weekly Report

**As a** Project Manager
**I want** AI to generate a status report
**So that** I can quickly communicate project status to stakeholders

**Acceptance Criteria:**

- [ ] Can request report from AI
- [ ] Report includes summary, accomplishments, upcoming, risks
- [ ] Report is in professional format
- [ ] Can edit report before sending
- [ ] Can export as PDF or email
- [ ] Can schedule automatic weekly reports

---

## Epic 6: Collaboration

### US-6.1: Invite Team Members

**As a** Project Manager
**I want to** invite others to my project
**So that** we can collaborate

**Acceptance Criteria:**

- [ ] Can invite by email
- [ ] Can set role (Editor, Viewer)
- [ ] Invitee receives email notification
- [ ] Invitee can accept and access project
- [ ] Can manage team members list
- [ ] Can remove access

---

### US-6.2: Real-time Updates

**As a** Team Member
**I want to** see changes made by others in real-time
**So that** I'm always looking at current data

**Acceptance Criteria:**

- [ ] Changes sync within seconds
- [ ] Visual indicator when others are editing
- [ ] No data loss on concurrent edits
- [ ] Can see who made recent changes
- [ ] Works across views (Gantt, table, etc.)

---

### US-6.3: Task Comments

**As a** Team Member
**I want to** add comments on tasks
**So that** I can communicate about specific work items

**Acceptance Criteria:**

- [ ] Can add comment from task detail panel
- [ ] Comments show author and timestamp
- [ ] Can @mention team members
- [ ] Mentioned users get notified
- [ ] Can edit/delete own comments
- [ ] Comment count shown on task row

---

## Epic 7: Baseline & Tracking

### US-7.1: Save Baseline

**As a** Project Manager
**I want to** save a baseline snapshot
**So that** I can compare actual vs planned

**Acceptance Criteria:**

- [ ] Can save baseline (captures all task dates/work)
- [ ] Can name the baseline
- [ ] Can save multiple baselines (up to 10)
- [ ] Baseline date recorded
- [ ] Confirmation shown

---

### US-7.2: Compare to Baseline

**As a** Project Manager
**I want to** compare current schedule to baseline
**So that** I can see schedule variance

**Acceptance Criteria:**

- [ ] Gantt shows baseline bars (different color)
- [ ] Can select which baseline to compare
- [ ] Variance calculated (days early/late)
- [ ] Variance shown in table columns
- [ ] Summary shows overall variance

---

## Epic 8: Import/Export

### US-8.1: Export to MS Project XML

**As a** Project Manager
**I want to** export my project to MS Project format
**So that** I can share with others using MS Project

**Acceptance Criteria:**

- [ ] Can export to .xml (MSPDI format)
- [ ] All tasks, dependencies, resources exported
- [ ] Can open in MS Project without errors
- [ ] Download initiated in browser

---

### US-8.2: Export to PDF

**As a** Project Manager
**I want to** export the Gantt chart to PDF
**So that** I can share or print the schedule

**Acceptance Criteria:**

- [ ] Can export current Gantt view
- [ ] Respects current zoom/filter
- [ ] Can select page size and orientation
- [ ] Tasks are readable
- [ ] Timeline is included
- [ ] Company logo/title option

---

---

## Story Map Summary

| Epic            | Must Have                              | Should Have            | Could Have |
| --------------- | -------------------------------------- | ---------------------- | ---------- |
| Project Setup   | US-1.1, US-1.3, US-1.4                 | US-1.2                 |            |
| Task Management | US-2.1, US-2.2, US-2.3, US-2.4, US-2.6 | US-2.5                 |            |
| Resources       | US-3.1, US-3.2, US-3.3                 | US-3.4                 |            |
| Gantt Chart     | US-4.1, US-4.2                         | US-4.3, US-4.4         |            |
| AI Assistant    | US-5.1                                 | US-5.2, US-5.3, US-5.4 |            |
| Collaboration   | US-6.1                                 | US-6.2, US-6.3         |            |
| Baseline        | US-7.1, US-7.2                         |                        |            |
| Import/Export   | US-8.1                                 | US-8.2                 |            |

---

## Document History

| Version | Date       | Author    | Changes                                     |
| ------- | ---------- | --------- | ------------------------------------------- |
| 1.0     | 2026-02-05 | Ermir | Initial draft                               |
| 2.0     | 2026-02-06 | Ermir | Aligned with schema v3.0, added doc refs    |

