"""اختبارات تتبّع الدليل الأكاديمي — مسارا start/end + إحصاءات guide-insights."""

from datetime import datetime, timedelta

import pytest

from app import time_utils
from app.event_days import EVENT_DAYS
from app.models import PageVisit
from app.models.page_visit import MIN_COUNTED_DURATION_SECONDS

PAGE = "academic-guide"


def _start(client, visitor_id: str, student_code: str | None = None) -> int:
    payload = {"page": PAGE, "visitor_id": visitor_id}
    if student_code is not None:
        payload["student_code"] = student_code
    resp = client.post("/students/page-visit/start", json=payload)
    assert resp.status_code == 200, resp.text
    return resp.json()["visit_id"]


def _visit_at(
    db,
    *,
    visitor_id: str,
    entered_at: datetime,
    duration: float | None,
    page: str = PAGE,
) -> PageVisit:
    """ينشئ زيارة بتاريخ ومدّة محدّدين مباشرة (لفحص التجميعات)."""
    visit = PageVisit(
        page=page,
        visitor_id=visitor_id,
        student_code=None,
        entered_at=entered_at,
        duration_seconds=duration,
    )
    db.add(visit)
    db.commit()
    db.refresh(visit)
    return visit


# ---------------------------------------------------------------------------
# مسار البداية والنهاية
# ---------------------------------------------------------------------------


def test_start_records_server_time(client):
    before = time_utils.now_naive()
    visit_id = _start(client, "visitor-aaaa-0001")
    assert isinstance(visit_id, int) and visit_id > 0
    assert time_utils.now_naive() >= before


def test_end_measures_duration_on_server(client, db):
    visit_id = _start(client, "visitor-bbbb-0002")
    resp = client.post("/students/page-visit/end", json={"visit_id": visit_id})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["visit_id"] == visit_id
    # المدّة محسوبة بالسيرفر — من 0 لحد أقصى 12 ساعة، ومش من المتصفح.
    assert 0 <= body["duration_seconds"] <= 12 * 60 * 60

    stored = db.get(PageVisit, visit_id)
    assert stored.duration_seconds == body["duration_seconds"]


def test_end_ignores_client_reported_duration(client):
    """أي حقل مدّة يرسله المتصفح ما بيأثّر — الـ schema ما بيقبله أصلاً."""
    visit_id = _start(client, "visitor-cccc-0003")
    resp = client.post(
        "/students/page-visit/end",
        json={"visit_id": visit_id, "duration_seconds": 99999},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["duration_seconds"] < 99999


def test_end_is_idempotent(client):
    visit_id = _start(client, "visitor-dddd-0004")
    first = client.post("/students/page-visit/end", json={"visit_id": visit_id}).json()
    second = client.post("/students/page-visit/end", json={"visit_id": visit_id}).json()
    assert first["duration_seconds"] == second["duration_seconds"]


def test_end_unknown_visit_returns_404(client):
    resp = client.post("/students/page-visit/end", json={"visit_id": 987654321})
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "page_visit_not_found"


def test_start_requires_visitor_id(client):
    resp = client.post("/students/page-visit/start", json={"page": PAGE})
    assert resp.status_code == 422


def test_start_does_not_need_auth(client):
    """المسار عامّ — المتصفح بيسجّل الزيارة قبل ما يسجّل دخول أصلاً."""
    assert _start(client, "visitor-eeee-0005") > 0


def test_start_rate_limit_is_per_visitor(client):
    """الحدّ على visitor_id مش على الـ IP — بعد 30 بداية لنفس المعرّف بيرفض."""
    visitor = "visitor-ffff-0006"
    for _ in range(30):
        assert _start(client, visitor) > 0
    blocked = client.post(
        "/students/page-visit/start", json={"page": PAGE, "visitor_id": visitor}
    )
    assert blocked.status_code == 429
    # ومعرّف تاني عادي ما تأثّر.
    assert _start(client, "visitor-gggg-0007") > 0


# ---------------------------------------------------------------------------
# guide-insights
# ---------------------------------------------------------------------------


def test_guide_insights_requires_super_admin(client, students_admin_headers):
    assert client.get("/admin/dashboard/guide-insights").status_code == 401
    assert (
        client.get(
            "/admin/dashboard/guide-insights", headers=students_admin_headers
        ).status_code
        == 403
    )


def test_guide_insights_empty(client, super_headers):
    resp = client.get("/admin/dashboard/guide-insights", headers=super_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["day"] == "all"
    assert body["visitors_count"] == 0
    assert body["visits_count"] == 0
    assert body["avg_duration_seconds"] is None
    assert body["median_duration_seconds"] is None
    assert body["measured_visits"] == 0


def test_guide_insights_counts_people_and_visits(client, super_headers, db):
    _visit_at(db, visitor_id="v1", entered_at=time_utils.now_naive(), duration=120)
    _visit_at(db, visitor_id="v1", entered_at=time_utils.now_naive(), duration=60)
    _visit_at(db, visitor_id="v2", entered_at=time_utils.now_naive(), duration=180)

    body = client.get("/admin/dashboard/guide-insights", headers=super_headers).json()
    assert body["visitors_count"] == 2
    assert body["visits_count"] == 3
    assert body["measured_visits"] == 3


def test_guide_insights_ignores_other_pages(client, super_headers, db):
    _visit_at(
        db,
        visitor_id="v1",
        entered_at=time_utils.now_naive(),
        duration=120,
        page="some-other-page",
    )
    body = client.get("/admin/dashboard/guide-insights", headers=super_headers).json()
    assert body["visits_count"] == 0


def test_guide_insights_excludes_bounces_and_open_visits(client, super_headers, db):
    now = time_utils.now_naive()
    # أقل من الحد الأدنى → ما بتدخل المتوسط
    _visit_at(
        db,
        visitor_id="v1",
        entered_at=now - timedelta(seconds=1),
        duration=1,
    )
    # إشارة النهاية ما وصلت → مدّتها لسا فارغة
    _visit_at(db, visitor_id="v2", entered_at=now, duration=None)
    # زيارة حقيقية
    _visit_at(
        db,
        visitor_id="v3",
        entered_at=now - timedelta(seconds=60),
        duration=60,
    )

    body = client.get("/admin/dashboard/guide-insights", headers=super_headers).json()
    assert body["visits_count"] == 3
    assert body["visitors_count"] == 3
    assert body["measured_visits"] == 1
    assert body["avg_duration_seconds"] == pytest.approx(60.0, abs=0.5)


def test_guide_insights_median(client, super_headers, db):
    now = time_utils.now_naive()
    for seconds in (10, 20, 30, 4000):
        _visit_at(
            db,
            visitor_id=f"v-{seconds}",
            entered_at=now - timedelta(seconds=seconds),
            duration=float(seconds),
        )
    body = client.get("/admin/dashboard/guide-insights", headers=super_headers).json()
    # الوسيط resistant لoutlier الـ 4000 — لازم 25 مش 1015.
    assert body["median_duration_seconds"] == pytest.approx(25.0, abs=0.5)
    assert body["avg_duration_seconds"] > 1000


def test_guide_insights_day_filter(client, super_headers, db):
    """'all' تراكمي، واليوم المحدد بيقصّ على نطاقه."""
    now = time_utils.now_naive()
    _visit_at(db, visitor_id="old", entered_at=now - timedelta(days=5), duration=300)
    for day_key in EVENT_DAYS:
        _visit_at(
            db,
            visitor_id=day_key,
            entered_at=datetime.combine(EVENT_DAYS[day_key], datetime.min.time())
            + timedelta(hours=10),
            duration=100,
        )

    all_body = client.get(
        "/admin/dashboard/guide-insights", headers=super_headers
    ).json()
    assert all_body["visits_count"] == 4

    sat_body = client.get(
        "/admin/dashboard/guide-insights?day=sat", headers=super_headers
    ).json()
    assert sat_body["day"] == "sat"
    assert sat_body["visits_count"] == 1


def test_guide_insights_rejects_unknown_day(client, super_headers):
    resp = client.get(
        "/admin/dashboard/guide-insights?day=funday", headers=super_headers
    )
    assert resp.status_code == 422


def test_guide_insights_uses_cache(client, super_headers, db):
    from app import cache as cache_module

    _visit_at(db, visitor_id="v1", entered_at=time_utils.now_naive(), duration=100)
    first = client.get("/admin/dashboard/guide-insights", headers=super_headers).json()
    _visit_at(db, visitor_id="v2", entered_at=time_utils.now_naive(), duration=100)
    cached = client.get("/admin/dashboard/guide-insights", headers=super_headers).json()
    assert cached["visits_count"] == first["visits_count"] == 1

    cache_module.clear_cache()
    fresh = client.get("/admin/dashboard/guide-insights", headers=super_headers).json()
    assert fresh["visits_count"] == 2


def test_measured_minimum_matches_model_constant():
    assert MIN_COUNTED_DURATION_SECONDS == 3


# ---------- purge (مؤقت — 2026-09-26) ----------

_PURGE_PHRASE = "reset-guide-stats-2026-09-26"


def test_purge_requires_auth(client, db):
    _visit_at(db, visitor_id="v1", entered_at=time_utils.now_naive(), duration=100)
    assert client.delete(f"/students/page-visits?confirm={_PURGE_PHRASE}").status_code == 401


def test_purge_forbidden_for_non_super(client, students_admin_headers, db):
    _visit_at(db, visitor_id="v1", entered_at=time_utils.now_naive(), duration=100)
    resp = client.delete(
        f"/students/page-visits?confirm={_PURGE_PHRASE}", headers=students_admin_headers
    )
    assert resp.status_code == 403


def test_purge_rejects_wrong_phrase(client, super_headers, db):
    _visit_at(db, visitor_id="v1", entered_at=time_utils.now_naive(), duration=100)
    resp = client.delete("/students/page-visits?confirm=nope", headers=super_headers)
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "confirm_mismatch"
    assert db.query(PageVisit).count() == 1


def test_purge_deletes_rows_and_clears_cache(client, super_headers, db):
    from app import cache as cache_module

    _visit_at(db, visitor_id="v1", entered_at=time_utils.now_naive(), duration=100)
    _visit_at(db, visitor_id="v2", entered_at=time_utils.now_naive(), duration=None)
    db.commit()
    # يملأ الكاش قبل المسح عشان نتأكد إنه اتفرّغ معه
    before = client.get("/admin/dashboard/guide-insights", headers=super_headers).json()
    assert before["visits_count"] == 2

    resp = client.delete(
        f"/students/page-visits?confirm={_PURGE_PHRASE}", headers=super_headers
    )
    assert resp.status_code == 200
    assert resp.json()["deleted"] == 2
    assert db.query(PageVisit).count() == 0

    after = client.get("/admin/dashboard/guide-insights", headers=super_headers).json()
    assert after["visits_count"] == 0
    assert after["visitors_count"] == 0
    assert after["avg_duration_seconds"] is None
