from datetime import date

from app.models import Skill
from app.models.experience import Experience, ExperienceAccomplishment


def test_unpublished_records_never_render_in_public_html(
    client, seeded_session
) -> None:
    seeded_session.add(
        Skill(name="Secret Skill", category="analytics", published=False)
    )
    seeded_session.commit()

    response = client.get("/skills")

    assert response.status_code == 200
    assert "Secret Skill" not in response.text


def test_homepage_impact_summary_uses_published_accomplishment_metrics_only(
    client, seeded_session
) -> None:
    unpublished_experience = Experience(
        role_title="Private Role",
        organization="Private Organization",
        location="Los Angeles, CA",
        start_date=date(2026, 8, 1),
        end_date=None,
        is_current=True,
        summary="Private work must not be rendered.",
        published=False,
    )
    unpublished_experience.accomplishments.append(
        ExperienceAccomplishment(
            statement="Private accomplishment",
            metric="99% private impact",
        )
    )
    seeded_session.add(unpublished_experience)
    seeded_session.commit()

    response = client.get("/")

    assert response.status_code == 200
    assert "Impact summary" in response.text
    assert "6 hours saved per week" in response.text
    assert "99% private impact" not in response.text
