from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services import DatabaseUnavailableError, ResumeService

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(
    directory=Path(__file__).resolve().parent.parent / "templates"
)
GENERIC_OUTAGE_MESSAGE = (
    "This service is temporarily unavailable. Please try again later."
)


def get_resume_service(request: Request) -> ResumeService:
    return ResumeService(request.app.state.session_factory)


ResumeServiceDependency = Annotated[ResumeService, Depends(get_resume_service)]


def _navigation(
    request: Request, *, include_resume_pages: bool = True
) -> list[dict[str, str | bool]]:
    items = [
        {
            "label": "Home",
            "href": str(request.url_for("homepage")),
            "current": request.url.path == "/",
        },
    ]
    if include_resume_pages:
        items.extend(
            [
                {
                    "label": "Experience",
                    "href": str(request.url_for("experience_page")),
                    "current": request.url.path == "/experience",
                },
                {
                    "label": "Projects",
                    "href": str(request.url_for("projects_page")),
                    "current": request.url.path.startswith("/projects"),
                },
                {
                    "label": "Skills",
                    "href": str(request.url_for("skills_page")),
                    "current": request.url.path == "/skills",
                },
                {
                    "label": "Education",
                    "href": str(request.url_for("education_page")),
                    "current": request.url.path == "/education",
                },
            ]
        )
    return items


def _render(
    request: Request,
    template_name: str,
    context: dict,
    *,
    status_code: int = status.HTTP_200_OK,
    include_resume_pages: bool = True,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        template_name,
        {
            **context,
            "nav_links": _navigation(
                request, include_resume_pages=include_resume_pages
            ),
        },
        status_code=status_code,
    )


def _service_unavailable(request: Request) -> HTMLResponse:
    return _render(
        request,
        "error.html",
        {"message": GENERIC_OUTAGE_MESSAGE},
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        include_resume_pages=False,
    )


def _not_found(request: Request) -> HTMLResponse:
    return _render(
        request,
        "not_found.html",
        {},
        status_code=status.HTTP_404_NOT_FOUND,
    )


def _group_skills(skills: list[Any]) -> list[tuple[str, list[Any]]]:
    grouped: OrderedDict[str, list[Any]] = OrderedDict()
    for skill in skills:
        grouped.setdefault(skill.category, []).append(skill)
    return list(grouped.items())


@router.get("/", response_class=HTMLResponse, name="homepage")
def homepage(
    request: Request,
    service: ResumeServiceDependency,
) -> HTMLResponse:
    homepage_content = service.get_homepage()
    return _render(
        request,
        "home.html",
        {"content": homepage_content},
        include_resume_pages=not homepage_content.is_fallback,
    )


@router.get("/experience", response_class=HTMLResponse, name="experience_page")
def experience_page(
    request: Request,
    service: ResumeServiceDependency,
) -> HTMLResponse:
    try:
        experiences = service.get_experiences()
    except DatabaseUnavailableError:
        return _service_unavailable(request)

    return _render(request, "experience.html", {"experiences": experiences})


@router.get("/projects", response_class=HTMLResponse, name="projects_page")
def projects_page(
    request: Request,
    service: ResumeServiceDependency,
) -> HTMLResponse:
    try:
        projects = service.get_projects()
    except DatabaseUnavailableError:
        return _service_unavailable(request)

    return _render(request, "projects.html", {"projects": projects})


@router.get("/projects/{slug}", response_class=HTMLResponse, name="project_detail")
def project_detail(
    slug: str,
    request: Request,
    service: ResumeServiceDependency,
) -> HTMLResponse:
    try:
        project = service.get_project_by_slug(slug)
    except DatabaseUnavailableError:
        return _service_unavailable(request)

    if project is None:
        return _not_found(request)

    return _render(request, "project_detail.html", {"project": project})


@router.get("/skills", response_class=HTMLResponse, name="skills_page")
def skills_page(
    request: Request,
    service: ResumeServiceDependency,
) -> HTMLResponse:
    try:
        skills = service.get_skills()
    except DatabaseUnavailableError:
        return _service_unavailable(request)

    return _render(
        request,
        "skills.html",
        {"skill_groups": _group_skills(skills)},
    )


@router.get("/education", response_class=HTMLResponse, name="education_page")
def education_page(
    request: Request,
    service: ResumeServiceDependency,
) -> HTMLResponse:
    try:
        education = service.get_education()
    except DatabaseUnavailableError:
        return _service_unavailable(request)

    return _render(request, "education.html", {"education_records": education})
