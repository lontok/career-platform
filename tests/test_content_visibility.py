from app.models import Skill


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
