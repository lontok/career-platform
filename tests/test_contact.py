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
        data={
            "name": "A" * 101,
            "email": "a" * 243 + "@example.com",
            "message": "B" * 5001,
        },
    )

    assert response.status_code == 400
    assert "Name must be 100 characters or fewer." in response.text
    assert "Email must be 254 characters or fewer." in response.text
    assert "Message must be 5000 characters or fewer." in response.text


def test_contact_submission_accepts_values_at_the_limits(contact_client) -> None:
    response = contact_client.post(
        "/contact",
        data={
            "name": "A" * 100,
            "email": "a" * 242 + "@example.com",
            "message": "B" * 5000,
        },
    )

    assert response.status_code == 200
    assert "Message received" in response.text


def test_contact_form_fields_carry_the_same_limits(contact_client) -> None:
    response = contact_client.get("/contact")

    assert 'maxlength="100"' in response.text
    assert 'maxlength="254"' in response.text
    assert 'maxlength="5000"' in response.text


def test_contact_submission_tolerates_missing_fields(contact_client) -> None:
    response = contact_client.post("/contact", data={})

    assert response.status_code == 400
    assert "Enter your name." in response.text


def test_contact_link_appears_in_navigation(contact_client) -> None:
    response = contact_client.get("/contact")

    assert 'href="http://testserver/contact"' in response.text
    assert 'aria-current="page"' in response.text


def test_contact_submission_trims_whitespace(contact_client) -> None:
    response = contact_client.post(
        "/contact",
        data={
            "name": "  Jordan Lee  ",
            "email": " jordan@example.com ",
            "message": " Hi ",
        },
    )

    assert response.status_code == 200
    assert "<dd>Jordan Lee</dd>" in response.text
    assert "<dd>jordan@example.com</dd>" in response.text


def test_contact_error_page_escapes_redisplayed_values(contact_client) -> None:
    response = contact_client.post(
        "/contact",
        data={"name": '"><script>alert(1)</script>', "email": "", "message": ""},
    )

    assert response.status_code == 400
    assert "<script>alert(1)</script>" not in response.text
    assert "&#34;&gt;&lt;script&gt;" in response.text


def test_contact_page_works_when_database_is_unavailable(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:////nonexistent/dir/resume.db")
    with TestClient(create_app()) as app_client:
        assert app_client.get("/contact").status_code == 200
        response = app_client.post(
            "/contact",
            data={"name": "Jordan", "email": "j@example.com", "message": "Hi"},
        )
        assert response.status_code == 200
