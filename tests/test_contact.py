from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def contact_client(monkeypatch):
    monkeypatch.setattr(
        "app.services.resume.ResumeService.get_site_name", lambda _: "Test Owner"
    )
    with TestClient(create_app()) as app_client:
        yield app_client


def test_contact_page_shows_a_form_that_posts_to_contact(contact_client) -> None:
    response = contact_client.get("/contact")

    assert response.status_code == 200
    assert "<h1>Contact</h1>" in response.text
    assert '<form class="contact-form" method="post" action="/contact"' in response.text
    for field in ('name="name"', 'name="email"', 'name="message"'):
        assert field in response.text
    assert '<button class="button" type="submit">Submit</button>' in response.text
    assert ">Contact</a>" in response.text
    assert 'aria-current="page"' in response.text


def test_contact_submission_shows_the_received_values(contact_client) -> None:
    response = contact_client.post(
        "/contact",
        data={
            "name": "Ada Lovelace",
            "email": "ada@example.com",
            "message": "Hello.\nSecond line.",
        },
    )

    assert response.status_code == 200
    assert "Message received" in response.text
    assert "Ada Lovelace" in response.text
    assert "ada@example.com" in response.text
    assert "Hello.\nSecond line." in response.text


def test_contact_submission_escapes_html(contact_client) -> None:
    response = contact_client.post(
        "/contact",
        data={
            "name": "<script>alert(1)</script>",
            "email": "x@example.com",
            "message": '<img src=x onerror="alert(2)">',
        },
    )

    assert response.status_code == 200
    assert "<script>alert(1)</script>" not in response.text
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in response.text
    assert "<img src=x" not in response.text
    assert "&lt;img src=x onerror=&#34;alert(2)&#34;&gt;" in response.text


def test_contact_submission_reports_missing_and_invalid_fields(contact_client) -> None:
    response = contact_client.post(
        "/contact", data={"name": "  ", "email": "not-an-email", "message": ""}
    )

    assert response.status_code == 400
    assert "Message received" not in response.text
    assert "Enter your name." in response.text
    assert "Enter a valid email address." in response.text
    assert "Enter a message." in response.text
    assert 'value="not-an-email"' in response.text
    assert 'aria-invalid="true"' in response.text


def test_contact_submission_rejects_overlong_values(contact_client) -> None:
    response = contact_client.post(
        "/contact",
        data={"name": "A" * 201, "email": "a@example.com", "message": "Hi"},
    )

    assert response.status_code == 400
    assert "Keep your name under 200 characters." in response.text


def test_contact_submission_tolerates_missing_fields(contact_client) -> None:
    response = contact_client.post("/contact", data={})

    assert response.status_code == 400
    assert "Enter your name." in response.text
