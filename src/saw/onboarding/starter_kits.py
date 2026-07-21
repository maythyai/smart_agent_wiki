"""Starter kits for onboarding new users.

Each kit contains a set of interlinked demo pages that showcase
different entity types and wiki features.
"""
from __future__ import annotations

from typing import Any

STARTER_KITS: dict[str, dict[str, Any]] = {
    "personal_pkm": {
        "name": "Personal Knowledge Base",
        "description": "Organize your thoughts, bookmarks, and learning",
        "icon": "🧠",
        "pages": [
            {
                "slug": "welcome-to-your-wiki",
                "title": "Welcome to Your Wiki",
                "entity_type": "note",
                "content": """# Welcome to Smart Agent Wiki! 🎉

This is your personal knowledge base. Here are some tips to get started:

## Quick Actions
- Press `Cmd/Ctrl+K` to search
- Press `Cmd/Ctrl+Shift+N` to quick capture
- Create [[wiki-links]] by typing `[[page-name]]`

## Your Starter Pages
- [[reading-list]] — Track books and articles
- [[learning-goals]] — Your current projects

## Next Steps
1. Explore the **Graph** view to see how pages connect
2. Try **Quick Capture** to add a new note
3. Import your existing notes from Obsidian or Markdown

Happy learning! 🚀
""",
                "tags": ["welcome", "getting-started"],
            },
            {
                "slug": "reading-list",
                "title": "Reading List",
                "entity_type": "bookmark",
                "properties": {
                    "url": "https://example.com",
                    "saved_date": "2024-01-15",
                },
                "content": """# Reading List 📚

## Currently Reading
- **Deep Work** by Cal Newport
  - Status: 50% complete
  - Key insight: Focus is the new IQ

## To Read
- [[atomic-habits]] — James Clear
- [[thinking-fast-and-slow]] — Daniel Kahneman

## Completed
- ✅ The Pragmatic Programmer
- ✅ Clean Code

---
Related: [[learning-goals]]
""",
                "tags": ["reading", "books", "learning"],
            },
            {
                "slug": "learning-goals",
                "title": "Learning Goals",
                "entity_type": "project",
                "properties": {
                    "status": "active",
                    "start_date": "2024-01-01",
                    "team": ["self"],
                },
                "content": """# Learning Goals 🎯

## Q1 2024
- [ ] Master Python async programming
- [ ] Build a personal project with FastAPI
- [x] Read 5 books from [[reading-list]]

## Resources
- [[welcome-to-your-wiki]] — Getting started guide
- Online courses and tutorials

## Progress Tracking
Update this page weekly to track your learning journey.
""",
                "tags": ["goals", "learning", "planning"],
            },
        ],
    },
    "team_wiki": {
        "name": "Team Wiki",
        "description": "Collaborate with your team on projects and documentation",
        "icon": "👥",
        "pages": [
            {
                "slug": "team-directory",
                "title": "Team Directory",
                "entity_type": "note",
                "content": """# Team Directory 👥

Welcome to the team wiki! Here you'll find information about our team members and how we work together.

## Team Members
- [[alice-chen]] — Product Lead
- [[bob-smith]] — Engineering Lead
- [[carol-jones]] — Design Lead

## Quick Links
- [[current-projects]] — Active projects
- [[meeting-notes]] — Recent meetings
- [[team-processes]] — How we work
""",
                "tags": ["team", "directory"],
            },
            {
                "slug": "alice-chen",
                "title": "Alice Chen",
                "entity_type": "person",
                "properties": {
                    "email": "alice@example.com",
                    "role": "Product Lead",
                    "organization": "Product Team",
                },
                "content": """# Alice Chen 👤

**Role:** Product Lead
**Email:** alice@example.com
**Team:** Product Team

## Responsibilities
- Product roadmap and strategy
- Stakeholder management
- [[current-projects]] oversight

## Recent Contributions
- Led Q4 planning session
- Defined product vision 2024

## Connect
- Schedule a 1:1 via calendar
- Slack: @alice
""",
                "tags": ["team", "product"],
            },
            {
                "slug": "bob-smith",
                "title": "Bob Smith",
                "entity_type": "person",
                "properties": {
                    "email": "bob@example.com",
                    "role": "Engineering Lead",
                    "organization": "Engineering Team",
                },
                "content": """# Bob Smith 👤

**Role:** Engineering Lead
**Email:** bob@example.com
**Team:** Engineering Team

## Responsibilities
- Technical architecture
- Code reviews and mentoring
- [[current-projects]] technical direction

## Expertise
- Distributed systems
- Performance optimization
- DevOps and infrastructure

## Connect
- Slack: @bob
- GitHub: @bobsmith
""",
                "tags": ["team", "engineering"],
            },
            {
                "slug": "carol-jones",
                "title": "Carol Jones",
                "entity_type": "person",
                "properties": {
                    "email": "carol@example.com",
                    "role": "Design Lead",
                    "organization": "Design Team",
                },
                "content": """# Carol Jones 👤

**Role:** Design Lead
**Email:** carol@example.com
**Team:** Design Team

## Responsibilities
- User experience and interface design
- Design system maintenance
- User research

## Recent Work
- Redesigned onboarding flow
- Created component library
- Conducted usability studies

## Connect
- Figma: @carol
- Slack: @carol
""",
                "tags": ["team", "design"],
            },
            {
                "slug": "current-projects",
                "title": "Current Projects",
                "entity_type": "project",
                "properties": {
                    "status": "active",
                    "start_date": "2024-01-01",
                    "team": ["alice-chen", "bob-smith", "carol-jones"],
                },
                "content": """# Current Projects 🚀

## Active Projects

### Project Alpha
**Status:** In Progress
**Lead:** [[alice-chen]]
**Team:** [[bob-smith]], [[carol-jones]]
**Goal:** Launch new feature by Q2 2024

**Progress:**
- [x] Requirements gathering
- [x] Design mockups
- [ ] Implementation
- [ ] Testing

### Project Beta
**Status:** Planning
**Lead:** [[bob-smith]]
**Goal:** Infrastructure upgrade

---
See also: [[meeting-notes]] for project discussions
""",
                "tags": ["projects", "active"],
            },
            {
                "slug": "meeting-notes",
                "title": "Meeting Notes",
                "entity_type": "meeting",
                "properties": {
                    "date": "2024-01-15",
                    "attendees": ["alice-chen", "bob-smith", "carol-jones"],
                    "decisions": "Approved Project Alpha timeline",
                },
                "content": """# Meeting Notes 📅

## Weekly Sync — Jan 15, 2024

**Attendees:** [[alice-chen]], [[bob-smith]], [[carol-jones]]

### Agenda
1. [[current-projects]] status update
2. Q1 planning review
3. Open discussion

### Decisions
- Approved Project Alpha timeline
- Scheduled design review for next week

### Action Items
- [ ] Alice: Finalize roadmap document
- [ ] Bob: Set up dev environment
- [ ] Carol: Complete design specs

### Notes
Great progress on all fronts. Team alignment is strong.

---
Previous: [[team-directory]]
""",
                "tags": ["meetings", "notes"],
            },
            {
                "slug": "team-processes",
                "title": "Team Processes",
                "entity_type": "note",
                "content": """# Team Processes 📋

## How We Work

### Communication
- Daily standup: 9:30 AM
- Weekly sync: Monday 2 PM
- Slack for async communication

### Project Management
- Use [[current-projects]] page to track work
- Update status weekly
- Document decisions in [[meeting-notes]]

### Code Reviews
- All PRs require 2 approvals
- [[bob-smith]] leads technical reviews
- Focus on quality and maintainability

### Design Reviews
- [[carol-jones]] leads design reviews
- Figma for collaboration
- User testing before launch

---
See also: [[team-directory]]
""",
                "tags": ["processes", "team"],
            },
        ],
    },
    "research_notebook": {
        "name": "Research Notebook",
        "description": "Track research topics, literature, and findings",
        "icon": "🔬",
        "pages": [
            {
                "slug": "research-overview",
                "title": "Research Overview",
                "entity_type": "note",
                "content": """# Research Overview 🔬

Welcome to your research notebook! Track your research journey here.

## Current Research
- [[research-topic-ai]] — Artificial Intelligence Trends
- [[literature-review]] — Key papers and books

## Methodology
Document your research approach in [[research-methods]]

## Findings
Track insights in [[research-findings]]

---
Use tags to organize by theme, date, or source type.
""",
                "tags": ["research", "overview"],
            },
            {
                "slug": "research-topic-ai",
                "title": "AI Research Topic",
                "entity_type": "concept",
                "properties": {
                    "domain": "Artificial Intelligence",
                    "related_concepts": ["machine-learning", "deep-learning", "nlp"],
                },
                "content": """# AI Research Topic 💡

**Domain:** Artificial Intelligence
**Status:** Active investigation

## Research Questions
1. What are the latest trends in LLMs?
2. How are organizations adopting AI?
3. What are the ethical considerations?

## Key Concepts
- Large Language Models (LLMs)
- Transformer architectures
- Prompt engineering
- AI alignment

## Related
- [[literature-review]] — Supporting research
- [[research-findings]] — Emerging insights

## Notes
Add observations and connections as you explore.
""",
                "tags": ["ai", "research", "technology"],
            },
            {
                "slug": "literature-review",
                "title": "Literature Review",
                "entity_type": "reference",
                "properties": {
                    "authors": "Various",
                    "published_date": "2024-01-01",
                },
                "content": """# Literature Review 📚

## Key Papers

### Attention Is All You Need (2017)
**Authors:** Vaswani et al.
**Key Contribution:** Transformer architecture
**Relevance:** Foundation for modern LLMs

### GPT-3 Paper (2020)
**Authors:** OpenAI
**Key Contribution:** Few-shot learning at scale
**Relevance:** [[research-topic-ai]]

## Books
- **Deep Learning** by Goodfellow et al.
- **AI Superpowers** by Kai-Fu Lee

## Synthesis
The field is moving rapidly toward larger models with emergent capabilities.

---
See also: [[research-findings]]
""",
                "tags": ["literature", "papers", "books"],
            },
            {
                "slug": "research-methods",
                "title": "Research Methods",
                "entity_type": "note",
                "content": """# Research Methods 📋

## Approach
1. **Literature Search** — Systematic review of papers
2. **Data Collection** — Gather relevant sources
3. **Analysis** — Identify patterns and themes
4. **Synthesis** — Connect findings to [[research-topic-ai]]

## Tools
- Academic databases (Google Scholar, arXiv)
- Reference management (Zotero)
- Note-taking (this wiki!)

## Quality Criteria
- Peer-reviewed sources preferred
- Recent publications (last 5 years)
- High citation count
- Relevant to research questions

---
Document your process for reproducibility.
""",
                "tags": ["methods", "process"],
            },
            {
                "slug": "research-findings",
                "title": "Research Findings",
                "entity_type": "note",
                "content": """# Research Findings 💡

## Key Insights

### Finding 1: Scale Matters
Larger models show emergent capabilities not present in smaller models.
- Evidence: [[literature-review]] papers
- Implications: Compute requirements will continue to grow

### Finding 2: Prompt Engineering is Critical
How you ask questions significantly impacts AI responses.
- Related: [[research-topic-ai]]
- Future work: Develop best practices guide

### Finding 3: Ethical Considerations
AI systems require careful consideration of bias and safety.
- Needs further investigation
- Connect with ethics literature

## Next Steps
- [ ] Deep dive into alignment research
- [ ] Interview practitioners
- [ ] Write synthesis paper

---
Update this page as new findings emerge.
""",
                "tags": ["findings", "insights"],
            },
        ],
    },
    "project_tracker": {
        "name": "Project Tracker",
        "description": "Track projects, tasks, and progress",
        "icon": "📊",
        "pages": [
            {
                "slug": "projects-dashboard",
                "title": "Projects Dashboard",
                "entity_type": "note",
                "content": """# Projects Dashboard 📊

Welcome to your project tracker! Monitor all your active projects here.

## Active Projects
- [[project-alpha]] — Q1 Product Launch
- [[project-beta]] — Infrastructure Upgrade

## Completed
- ✅ Website Redesign (Dec 2023)

## Templates
- Use the project entity type for new projects
- Link team members as [[person]] entities
- Track meetings with [[meeting]] entity type

---
Update weekly to keep progress visible.
""",
                "tags": ["projects", "dashboard"],
            },
            {
                "slug": "project-alpha",
                "title": "Project Alpha",
                "entity_type": "project",
                "properties": {
                    "status": "active",
                    "start_date": "2024-01-01",
                    "end_date": "2024-03-31",
                    "team": ["product-lead", "dev-lead"],
                },
                "content": """# Project Alpha 🚀

**Status:** Active
**Timeline:** Jan 1 - Mar 31, 2024
**Goal:** Launch new feature to increase user engagement

## Objectives
- [x] Define requirements
- [x] Design mockups
- [ ] Implement MVP
- [ ] User testing
- [ ] Launch

## Team
- Product Lead
- Development Lead
- Designer

## Milestones
1. **Jan 15:** Requirements complete ✅
2. **Feb 1:** Design approved ✅
3. **Mar 1:** MVP ready
4. **Mar 31:** Launch

## Notes
- On track for Q1 launch
- Need to schedule user testing
- Budget approved

---
Related: [[projects-dashboard]], [[project-beta]]
""",
                "tags": ["project", "q1-2024"],
            },
            {
                "slug": "project-beta",
                "title": "Project Beta",
                "entity_type": "project",
                "properties": {
                    "status": "on-hold",
                    "start_date": "2024-02-01",
                    "end_date": "2024-06-30",
                    "team": ["dev-lead", "ops"],
                },
                "content": """# Project Beta ⚙️

**Status:** On Hold
**Timeline:** Feb 1 - Jun 30, 2024
**Goal:** Upgrade infrastructure for scalability

## Objectives
- [ ] Audit current infrastructure
- [ ] Design new architecture
- [ ] Migration plan
- [ ] Implementation
- [ ] Testing and rollout

## Dependencies
- [[project-alpha]] must complete first
- Budget approval pending

## Risks
- Technical complexity
- Potential downtime during migration
- Team capacity constraints

## Notes
Paused until Project Alpha launches.
Will resume in Q2.

---
Related: [[projects-dashboard]], [[project-alpha]]
""",
                "tags": ["project", "infrastructure", "q2-2024"],
            },
            {
                "slug": "weekly-review-template",
                "title": "Weekly Review Template",
                "entity_type": "meeting",
                "properties": {
                    "date": "2024-01-15",
                    "attendees": ["team"],
                    "decisions": "Weekly progress review",
                },
                "content": """# Weekly Review Template 📅

Use this template for weekly project reviews.

## Date: [Week of]

### Progress
**[[project-alpha]]:**
- Completed: [list]
- In progress: [list]
- Blocked: [list]

**[[project-beta]]:**
- Completed: [list]
- In progress: [list]
- Blocked: [list]

### Key Metrics
- Tasks completed: X
- Tasks in progress: Y
- Blockers: Z

### Decisions Made
- [list decisions]

### Action Items
- [ ] [Action] — Owner — Due date
- [ ] [Action] — Owner — Due date

### Next Week Focus
- [priority 1]
- [priority 2]

---
Link to [[projects-dashboard]] for overview.
""",
                "tags": ["template", "weekly-review"],
            },
        ],
    },
}


def get_starter_kit(kit_id: str) -> dict[str, Any] | None:
    """Get a starter kit by ID.

    Args:
        kit_id: Starter kit identifier.

    Returns:
        Starter kit definition or None if not found.
    """
    return STARTER_KITS.get(kit_id)


def list_starter_kits() -> list[dict[str, Any]]:
    """List all available starter kits.

    Returns:
        List of starter kit metadata (without full page content).
    """
    return [
        {
            "id": kit_id,
            "name": kit["name"],
            "description": kit["description"],
            "icon": kit["icon"],
            "page_count": len(kit["pages"]),
        }
        for kit_id, kit in STARTER_KITS.items()
    ]
