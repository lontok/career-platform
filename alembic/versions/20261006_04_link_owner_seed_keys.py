"""link the owner's imported resume rows to their seed keys

Revision ID: 20261006_04
Revises: 20261006_03
Create Date: 2026-10-06 13:00:00.000000

The owner's profile was imported into SQLite without seed keys. Without them,
running the seed would add a second copy of every row instead of updating the
existing ones. This migration matches the imported rows to the keys in
app/seed.py. A fictional sample profile holding the primary key gives it up first.
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20261006_04"
down_revision: str | Sequence[str] | None = "20261006_03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OWNER_NAME = "Greg Lontok"

ROW_KEYS = [
    (
        "experiences",
        "experience:lmu:clinical-associate-professor",
        "role_title = 'Clinical Associate Professor - Information Systems & Business Analytics' AND organization = 'Loyola Marymount University' AND start_date = '2026-06-01'",
    ),
    (
        "experiences",
        "experience:lmu:clinical-assistant-professor",
        "role_title = 'Clinical Assistant Professor - Information Systems & Business Analytics' AND organization = 'Loyola Marymount University' AND start_date = '2019-08-01'",
    ),
    (
        "experiences",
        "experience:lmu:lecturer",
        "role_title = 'Lecturer - Information Systems & Business Analytics' AND organization = 'Loyola Marymount University' AND start_date = '2018-01-01'",
    ),
    (
        "experiences",
        "experience:globalwide-media:vp-technology-data-science",
        "role_title = 'VP Technology and Data Science' AND organization = 'GlobalWide Media' AND start_date = '2007-01-01'",
    ),
    (
        "experiences",
        "experience:valueclick:development-manager",
        "role_title = 'Development Manager' AND organization = 'ValueClick' AND start_date = '2004-01-01'",
    ),
    (
        "experiences",
        "experience:hispeed-media:vp-engineering-it",
        "role_title = 'VP of Engineering and Information Technology' AND organization = 'HiSpeed Media' AND start_date = '2002-07-01'",
    ),
    (
        "experiences",
        "experience:aesop-marketing:web-developer-sysadmin",
        "role_title = 'Web Developer / System Administrator' AND organization = 'Aesop Marketing' AND start_date = '2000-01-01'",
    ),
    ("skills", "skill:affiliate-marketing", "name = 'Affiliate Marketing'"),
    ("skills", "skill:social-media-marketing", "name = 'Social Media Marketing'"),
    ("skills", "skill:sem", "name = 'SEM'"),
    (
        "skills",
        "skill:professional-scrum-master-i",
        "name = 'Professional Scrum Master I (PSM I)'",
    ),
    (
        "education",
        "education:regis-university:data-science-ms",
        "institution_name = 'Regis University' AND degree_or_program = 'MS'",
    ),
    (
        "education",
        "education:loyola-marymount-university:business-administration-ba",
        "institution_name = 'Loyola Marymount University' AND degree_or_program = 'BA'",
    ),
]


def upgrade() -> None:
    op.execute(
        "UPDATE profiles SET seed_key = 'profile:sample' "
        "WHERE seed_key = 'profile:primary' AND full_name != '" + OWNER_NAME + "'"
    )
    op.execute(
        "UPDATE profiles SET seed_key = 'profile:primary' "
        "WHERE seed_key IS NULL AND full_name = '" + OWNER_NAME + "' "
        "AND id = (SELECT MIN(id) FROM profiles "
        "WHERE seed_key IS NULL AND full_name = '" + OWNER_NAME + "') "
        "AND NOT EXISTS (SELECT 1 FROM profiles WHERE seed_key = 'profile:primary')"
    )
    for table, seed_key, match in ROW_KEYS:
        op.execute(
            f"UPDATE {table} SET seed_key = '{seed_key}' "
            f"WHERE seed_key IS NULL AND {match} "
            f"AND NOT EXISTS (SELECT 1 FROM {table} WHERE seed_key = '{seed_key}')"
        )


def downgrade() -> None:
    for table, seed_key, _match in ROW_KEYS:
        op.execute(f"UPDATE {table} SET seed_key = NULL WHERE seed_key = '{seed_key}'")
    op.execute(
        "UPDATE profiles SET seed_key = NULL "
        "WHERE seed_key = 'profile:primary' AND full_name = '" + OWNER_NAME + "'"
    )
    op.execute(
        "UPDATE profiles SET seed_key = 'profile:primary' "
        "WHERE seed_key = 'profile:sample'"
    )
