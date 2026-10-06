"""Fictional sample resume used by tests that need a full set of seed content."""

from datetime import date

SAMPLE_PROFILE = {
    "seed_key": "profile:primary",
    "full_name": "Alex Parker",
    "headline": "Analytics-focused software builder for business teams",
    "summary": (
        "Builds dependable data products and automation that help business "
        "partners make faster, better-informed decisions."
    ),
    "location": "Los Angeles, CA",
    "target_roles": "Analytics Engineer, Data Analyst, Business Systems Analyst",
    "email": "alex.parker@example.com",
    "linkedin_url": "https://www.linkedin.com/in/alexparker-analytics",
    "github_url": "https://github.com/alexparker-analytics",
    "published": True,
}

SAMPLE_SKILLS = [
    {
        "seed_key": "skill:sql",
        "name": "SQL",
        "category": "analytics",
        "context": "Warehouse modeling, QA, and decision support.",
        "display_order": 1,
        "published": True,
    },
    {
        "seed_key": "skill:python",
        "name": "Python",
        "category": "programming",
        "context": "Automation, data services, and testing.",
        "display_order": 2,
        "published": True,
    },
]

SAMPLE_EXPERIENCES = [
    {
        "seed_key": "experience:west-coast-commerce:analytics-engineering-intern",
        "role_title": "Analytics Engineering Intern",
        "organization": "West Coast Commerce",
        "location": "Los Angeles, CA",
        "start_date": date(2026, 6, 1),
        "end_date": None,
        "is_current": True,
        "summary": "Supported reporting automation and data quality initiatives.",
        "display_order": 1,
        "published": True,
        "skill_names": ["SQL", "Python"],
        "accomplishments": [
            {
                "statement": "Automated weekly KPI reporting for business stakeholders.",
                "metric": "6 hours saved per week",
                "display_order": 1,
            }
        ],
    }
]

SAMPLE_PROJECTS = [
    {
        "seed_key": "project:career-platform",
        "slug": "career-platform",
        "title": "Career Platform Resume Site",
        "summary": "Database-driven resume content for analytics-focused roles.",
        "problem": "Resume updates were slow and duplicated across pages.",
        "contribution": "Designed the content model, seed flow, and read service.",
        "methods": "FastAPI, SQLAlchemy, SQLite, pytest",
        "outcome": "Created a maintainable content workflow for future public pages.",
        "repository_url": None,
        "live_demo_url": None,
        "published": True,
        "featured": True,
        "display_order": 1,
        "skill_names": ["SQL", "Python"],
    }
]

SAMPLE_EDUCATION = [
    {
        "seed_key": "education:california-state-university:information-systems-bs",
        "institution_name": "California State University",
        "degree_or_program": "B.S.",
        "field_of_study": "Information Systems",
        "start_date": date(2022, 8, 22),
        "end_date": date(2026, 5, 18),
        "gpa": "3.8",
        "honors": "Dean's List",
        "relevant_coursework": "Database Systems, Business Analytics, Statistics",
        "certifications": None,
        "published": True,
        "display_order": 1,
    }
]
