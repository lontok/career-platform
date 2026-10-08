from datetime import date

from sqlalchemy.orm import Session

from app.models import Experience, Project, Skill


def _skills_listed_out_of_display_order(session: Session) -> list[Skill]:
    # Linked in reverse of display_order, so only an explicit ORDER BY fixes it.
    second = Skill(name="Second", category="tools", published=True, display_order=2)
    first = Skill(name="First", category="tools", published=True, display_order=1)
    session.add_all([second, first])
    session.flush()
    return [second, first]


def test_experience_skills_follow_display_order(session: Session) -> None:
    experience = Experience(
        role_title="Analyst",
        organization="Acme",
        location="Los Angeles",
        start_date=date(2024, 1, 1),
        is_current=True,
        summary="Built reports.",
        published=True,
        display_order=1,
    )
    experience.skills = _skills_listed_out_of_display_order(session)
    session.add(experience)
    session.commit()
    session.expire_all()

    assert [skill.name for skill in experience.skills] == ["First", "Second"]


def test_project_skills_follow_display_order(session: Session) -> None:
    project = Project(
        slug="reports",
        title="Reports",
        summary="Summary",
        problem="Problem",
        contribution="Contribution",
        methods="Methods",
        published=True,
        featured=False,
        display_order=1,
    )
    project.skills = _skills_listed_out_of_display_order(session)
    session.add(project)
    session.commit()
    session.expire_all()

    assert [skill.name for skill in project.skills] == ["First", "Second"]
