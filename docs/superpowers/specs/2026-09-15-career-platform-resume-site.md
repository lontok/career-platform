# Database-Driven Personal Resume Site Specification

**Status:** Awaiting user approval  
**Date:** 2026-09-15  
**Audience:** Senior business analytics and information student learning application development and cloud networking

## 1. Purpose

Build a public, recruiter-focused personal resume website for Los Angeles analytics and technical opportunities. The website must communicate the candidate's ability to understand business needs and deliver measurable value, not simply list technical tools.

This is the first stage of a future career platform. The initial release is deliberately a single-profile public site, but its database structure must allow future features to be added without redesigning the core resume data.

## 2. Goals

1. Give recruiters a clear professional introduction and contact path.
2. Present work, education, skills, and projects as evidence of business impact.
3. Store all displayed resume data in a relational database.
4. Allow a developer to update the database through seed data or database scripts.
5. Keep the essential professional profile visible when the database is temporarily unavailable.
6. Keep the application simple enough to learn from and deploy to the cloud.

## 3. Non-Goals for the First Release

The following are explicitly out of scope:

- User registration, sign-in, and multiple public profiles.
- A browser-based admin dashboard or content-management system.
- Job application tracking, networking, messaging, and social-feed features.
- Resume import from LinkedIn or a document file.
- Blog posts, testimonials, awards beyond education records, and a downloadable PDF resume.
- An external contact-form delivery service.
- Advanced analytics, personalization, or recruiter accounts.

These may be considered later, after the public resume site is working and its content is validated.

## 4. Users and Primary Scenario

### Primary user: recruiter or hiring manager

A recruiter searching for analytics or technical talent in or open to the Los Angeles area visits the site. Within one page, they should be able to understand:

- The candidate's target direction: analytics and technical roles.
- The candidate's location: Los Angeles area.
- The candidate's value proposition: using technical and analytics skills to solve business problems with measurable results.
- Evidence supporting that claim: experience, projects, skills, and education.
- How to contact or verify the candidate through professional links.

### Content owner: candidate/developer

The candidate updates resume information through version-controlled seed data or a database script. An update is deployed with the application in the same way as an application code change.

## 5. Public Site Structure

### 5.1 Homepage

The homepage is the primary recruiter experience. It contains, in this order:

1. **Professional introduction:** Name, Los Angeles-area location, target role description, and a short value proposition.
2. **Impact summary:** A small set of highlighted outcomes or metrics pulled from selected experience or project records.
3. **Selected experience:** A concise preview of the most relevant roles, with a link to all experience.
4. **Selected projects:** A concise preview of selected projects, with a link to all projects.
5. **Skills preview:** A grouped snapshot of capabilities.
6. **Education preview:** Most relevant education and certifications.
7. **Contact links:** Professional links, including LinkedIn and GitHub, plus an email link.

### 5.2 Detail and listing pages

The site contains these public routes:

| Route | Purpose |
| --- | --- |
| `/` | Value-led homepage |
| `/experience` | Full chronological work-experience list |
| `/projects` | All selected projects/case studies |
| `/projects/:slug` | Individual project detail page |
| `/skills` | Skills grouped by category |
| `/education` | Education and certifications |

Each page has consistent navigation, a clear page title, and a link back to the homepage.

## 6. Content Requirements

### 6.1 Professional profile

The single profile record stores:

- Full name.
- Short professional headline.
- Professional summary.
- Los Angeles-area location text.
- Target roles or role categories.
- Public email address.
- Optional LinkedIn URL.
- Optional GitHub URL.

The headline and summary must emphasize business understanding and measurable outcomes alongside analytics and technical ability.

### 6.2 Experience

Each experience record stores:

- Role title and organization.
- Location text.
- Start date and optional end date.
- Current-role indicator.
- Short role summary.
- Ordered accomplishment statements.
- Optional quantified metric per accomplishment, such as percentage improvement, dollars saved, time reduced, customers served, or records analyzed.
- Optional associated skills.
- Publish status and display order.

Experience displays newest first by default. Current roles display as “Present” rather than requiring an end date.

### 6.3 Projects

Each project record stores:

- Unique URL-safe `slug`.
- Title and short summary.
- Business problem or question addressed.
- The candidate's contribution.
- Methods and technologies used.
- Measurable outcome, if available.
- Optional repository URL and live-demo URL.
- Optional associated skills.
- Publish status, featured-on-homepage indicator, and display order.

Project detail pages must be accessible only for published projects. An unrecognized or unpublished slug returns the site's standard not-found page.

### 6.4 Skills

Each skill stores:

- Name.
- Category, such as analytics, programming, data, cloud, business, or collaboration.
- Optional proficiency/context text, such as “used in coursework” or “applied in project.”
- Display order.
- Publish status.

The site must not imply professional mastery solely from a skill label. When useful, project and experience pages supply the context in which a skill was applied.

### 6.5 Education

Each education record stores:

- Institution name.
- Degree or program.
- Field of study.
- Start date and expected or completed end date.
- Optional GPA, honors, relevant coursework, and certifications.
- Publish status and display order.

## 7. Data Design

A SQLite relational database is the source of truth for the first release. The database is a single file, used locally in Codespaces and later stored in a protected persistent directory on the Azure VM. The initial data model includes:

| Table | Responsibility |
| --- | --- |
| `profiles` | Single public professional profile and contact links |
| `experiences` | Roles, organizations, dates, summaries, and visibility |
| `experience_accomplishments` | Ordered impact statements belonging to an experience |
| `projects` | Case studies and public project metadata |
| `skills` | Reusable skills and categories |
| `education` | Degrees, coursework, and certifications |
| `experience_skills` | Many-to-many association between experience and skills |
| `project_skills` | Many-to-many association between projects and skills |

Foreign keys protect relationships: an accomplishment cannot exist without its experience, and association records cannot exist without both referenced records.

Records shown publicly must have `published = true`. Seed data must contain at least one published profile and enough published content to render every public section without blank headings.

## 8. Application Boundaries

The first release is a **modular monolith**: one deployable web application containing both the user interface and the server-side code that reads the database.

| Layer | Responsibility |
| --- | --- |
| Presentation layer | Renders accessible public pages from application data |
| Application/data layer | Validates route parameters and retrieves only published data |
| Database | Stores structured resume content and relationships |
| Seed workflow | Creates repeatable development and deployment content, including the fallback profile snapshot |
| Profile fallback | A deployment-time snapshot of the minimum public profile used only when database access fails |

The browser never connects directly to the database. Only server-side application code holds database credentials and performs queries.

## 9. Functional Requirements

1. Under normal operation, every public page must read its content from the database, not hard-coded page text.
2. The homepage must display a non-empty professional introduction, at least one selected content section, and contact links from the profile record.
3. Experience, projects, skills, and education pages must show only published records.
4. Experience must sort current roles first, then completed roles by most recent start date.
5. Projects must support individual pages identified by a stable slug.
6. Missing, malformed, or unpublished project slugs must produce a not-found response.
7. Empty optional fields must not create broken links, visible “undefined” values, or empty labels.
8. External professional links must open safely in a new browsing context when configured to do so.
9. The site must remain usable on mobile and desktop screen sizes.
10. Pages must use semantic headings, keyboard-accessible navigation, descriptive links, and sufficient color contrast.
11. When database access fails, the homepage must render a version-controlled fallback profile containing the name, headline, professional summary, location, target roles, and configured professional contact links.
12. During a database outage, experience, project, skill, and education content must be omitted rather than served from an unknown or stale source. The homepage must explain that detailed resume information is temporarily unavailable.

## 10. Error Handling

- A database connection or query failure must be logged by the server. For homepage requests, the server must render the defined fallback profile and a clear temporary-availability message; it must not expose credentials, raw queries, or stack traces to visitors.
- A database failure on a non-homepage route must result in a clear generic error response; it must not expose credentials, raw queries, or stack traces to visitors.
- Invalid project slugs and unpublished content must return a normal not-found page, not an application error.
- If optional content is absent, the corresponding UI element is omitted.
- Seed-data validation must fail clearly when required profile content, duplicate project slugs, invalid dates, or invalid relationship references are present.
- The fallback profile must be validated with the same required-profile rules as seed data so it cannot deploy with missing required fields or malformed public URLs.

## 11. Security and Privacy

- Store the configured SQLite database-file path only in server-side environment variables.
- Do not commit secrets, credentials, personal tokens, or private addresses.
- The fallback profile contains only intentionally public professional information. It must not contain database credentials, private contact details, or private resume content.
- Use parameterized database queries or the chosen data-access library's equivalent.
- Keep write operations out of public routes in the first release.
- Treat the public contact email as intentionally public; do not store private contact details in published records.
- Validate and normalize external URLs before rendering links.

## 12. Deployment and Learning Constraints

The deployment design must be cloud-friendly but simple:

- One FastAPI application running locally in Codespaces first, then on a single Azure VM.
- One SQLite database file kept outside the application directory on the Azure VM, with file permissions that allow only the application service account to read or write it.
- Environment-specific configuration for local development and the Azure VM, including the SQLite database-file path.
- A repeatable database schema migration and seed process.
- A documented backup process that copies the SQLite database file to a separate protected location before each application deployment or schema migration. The restore process must be documented and tested locally.
- A short setup guide explaining local development, database setup, seeding, and deployment variables in beginner-friendly language.

The first-release application uses FastAPI with Jinja templates and plain CSS. Local deployment occurs in Codespaces before the application is deployed to an Azure VM.

## 13. Future Growth Path

Later work can add a protected admin dashboard, authentication, multiple profiles, recruiter features, job tracking, and networking. Those features should build on the existing content entities and their published/unpublished distinction.

For multi-user support, ownership fields and access-control tables can be added to the established profile/content model. They are not added now because the first release has exactly one content owner.

## 14. Acceptance Criteria

The first release is complete when:

1. A recruiter can navigate the site and understand the candidate's value proposition, Los Angeles connection, analytics/technical direction, and business-impact focus.
2. The database contains and the site displays published profile, experience, project, skill, and education data.
3. The site has functioning public routes for home, experience, projects, project detail, skills, and education.
4. Content updates can be made through a documented seed/database workflow without changing page templates for ordinary resume updates.
5. Unpublished records never appear on public pages.
6. Invalid project URLs produce a not-found page.
7. The application can be configured with local and Azure VM SQLite database-file paths without exposing secrets or placing the production database file in the application directory.
8. The design is responsive, keyboard navigable, and has no broken optional-content elements.
9. When the database is unavailable, the homepage still shows a validated fallback professional profile, configured contact links, and a temporary-availability message.
10. When the database is unavailable, no detailed experience, project, skill, or education data is rendered from a fallback source.
11. Local setup and the Azure VM setup document the SQLite database-file location, migration/seed process, backup procedure, and restore procedure.

## 15. Decisions Recorded

| Decision | Outcome |
| --- | --- |
| Initial purpose | Landing analytics and technical roles |
| Primary audience | Recruiters and hiring managers |
| Geographic emphasis | Los Angeles area |
| Narrative | Business need to quantifiable value |
| Homepage strategy | Value proposition first, evidence second |
| Content management | Seeded SQLite database initially |
| Initial content | Profile, experience, projects, skills, education |
| Contact default | Public email plus LinkedIn and GitHub links |
| Architecture | Single public, database-backed modular monolith |
| First-release stack | FastAPI, Jinja templates, plain CSS, SQLite |
| Deployment path | Codespaces first, then a single Azure VM with protected persistent SQLite storage |
