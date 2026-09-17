# Task 3 Report — Seed Content, Fallback Validation, and Published Reads

## Scope
- Implemented only Task 3 in `/workspaces/career-platform/.worktrees/fastapi-resume-site`
- Kept the Task 3/Task 4 service ruling from `progress.md`: homepage falls back only after database errors; non-homepage reads raise `DatabaseUnavailableError`
- Did not modify specs, plans, public routes, templates, or deployment files
- Did not use subagents

## Files Changed
- Created `app/schemas/__init__.py`
- Created `app/schemas/content.py`
- Created `app/services/__init__.py`
- Created `app/services/resume.py`
- Created `app/seed.py`
- Created `app/fallback_profile.json`
- Created `tests/test_resume_service.py`
- Created `tests/test_seed.py`
- Updated `README.md`

## TDD Evidence

### RED — tests written first, then run before implementation
Command:
```bash
cd /workspaces/career-platform/.worktrees/fastapi-resume-site && uv run pytest tests/test_resume_service.py tests/test_seed.py -q
```
Output:
```text
==================================== ERRORS ====================================
________________ ERROR collecting tests/test_resume_service.py _________________
ImportError while importing test module '/workspaces/career-platform/.worktrees/fastapi-resume-site/tests/test_resume_service.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/test_resume_service.py:20: in <module>
    from app.services.resume import DatabaseUnavailableError, ResumeService
E   ModuleNotFoundError: No module named 'app.services'
_____________________ ERROR collecting tests/test_seed.py ______________________
ImportError while importing test module '/workspaces/career-platform/.worktrees/fastapi-resume-site/tests/test_seed.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/test_seed.py:13: in <module>
    from app.schemas.content import FallbackProfile
E   ModuleNotFoundError: No module named 'app.schemas'
=========================== short test summary info ============================
ERROR tests/test_resume_service.py
ERROR tests/test_seed.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
2 errors in 0.49s
```

### GREEN attempt 1 — implementation present, one test corrected for the expected assertion path
Command:
```bash
cd /workspaces/career-platform/.worktrees/fastapi-resume-site && uv run pytest tests/test_resume_service.py tests/test_seed.py -q
```
Output:
```text
...........F...                                                          [100%]
=================================== FAILURES ===================================
___________ test_seed_demo_content_validates_fallback_before_writing ___________

session_factory = sessionmaker(class_='Session', bind=Engine(sqlite+pysqlite:///:memory:), autoflush=False, expire_on_commit=False)
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7467e5d3fa10>

    def test_seed_demo_content_validates_fallback_before_writing(
        session_factory, monkeypatch
    ) -> None:
        def raising_fallback_loader():
            raise ValueError("fallback profile is invalid")

        monkeypatch.setattr(seed_module, "load_fallback_profile", raising_fallback_loader)

        with pytest.raises(ValueError, match="fallback profile is invalid"):
>           seed_module.seed_demo_content(session_factory=session_factory)

tests/test_seed.py:69: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

session_factory = sessionmaker(class_='Session', bind=Engine(sqlite+pysqlite:///:memory:), autoflush=False, expire_on_commit=False)
fallback_path = PosixPath('/workspaces/career-platform/.worktrees/fastapi-resume-site/app/fallback_profile.json')

    def seed_demo_content(
        session_factory=SessionLocal, fallback_path: Path = FALLBACK_PROFILE_PATH
    ) -> None:
>       load_fallback_profile(fallback_path)
E       TypeError: test_seed_demo_content_validates_fallback_before_writing.<locals>.raising_fallback_loader() takes 0 positional arguments but 1 was given

app/seed.py:113: TypeError
=========================== short test summary info ============================
FAILED tests/test_seed.py::test_seed_demo_content_validates_fallback_before_writing
1 failed, 14 passed in 0.70s
```
Action taken:
- Fixed the test helper signature so the test failed or passed for the intended seed-validation behavior, not a test harness mistake.

### GREEN attempt 2 — targeted Task 3 tests pass
Command:
```bash
cd /workspaces/career-platform/.worktrees/fastapi-resume-site && uv run pytest tests/test_resume_service.py tests/test_seed.py -q
```
Output:
```text
...............                                                          [100%]
15 passed in 0.58s
```

## Validation and Verification

### Ruff
Command:
```bash
cd /workspaces/career-platform/.worktrees/fastapi-resume-site && uv run ruff check app tests
```
Output:
```text
All checks passed!
```

### Required Task 3 validation command
Command:
```bash
cd /workspaces/career-platform/.worktrees/fastapi-resume-site && uv run alembic upgrade head && uv run python -m app.seed && uv run pytest tests/test_seed.py tests/test_resume_service.py -q
```
Output:
```text
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
Seeded published resume content.
...............                                                          [100%]
15 passed in 0.51s
```

### Real database idempotency check
Command:
```bash
cd /workspaces/career-platform/.worktrees/fastapi-resume-site && uv run python -m app.seed && uv run python -m app.seed && uv run python - <<'PY'
import sqlite3
conn = sqlite3.connect('data/resume.db')
for table in ['profiles', 'experiences', 'experience_accomplishments', 'projects', 'skills', 'education']:
    count = conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
    print(f'{table}: {count}')
conn.close()
PY
```
Output:
```text
Seeded published resume content.
Seeded published resume content.
profiles: 1
experiences: 1
experience_accomplishments: 1
projects: 1
skills: 2
education: 1
```

### Full pytest suite
Command:
```bash
cd /workspaces/career-platform/.worktrees/fastapi-resume-site && uv run pytest -q
```
Output:
```text
...................                                                      [100%]
19 passed in 0.92s
```

## Implementation Notes
- Added strict Pydantic content schemas, including fallback URL validation and unknown-field rejection.
- Added `ResumeService` published read methods with parameterized `select()` usage, published filters, ordering, eager loading, and the required homepage-only fallback behavior.
- Added idempotent demo seeding with pre-commit validation for duplicate project slugs, invalid skill references, and invalid date combinations.
- Updated README with seed usage and safe content update steps; ordinary resume updates stay in seed/fallback data, not templates.

## Commit
- Task 3 changes were committed after the verification steps above. The final commit hash is reported in the CLI status response.
