"""اختبارات الاستبيان البعدي — endpoints عامة بدون auth."""

STUDENT = "R-9001"
OPINION = "decided"
MAJOR = "college_placeholder_1"


def _status(client, code=STUDENT):
    return client.get(f"/survey/{code}/status")


def _submit(client, code=STUDENT, opinion_change=OPINION, preferred_major=MAJOR):
    return client.post(
        f"/survey/{code}",
        json={"opinion_change": opinion_change, "preferred_major": preferred_major},
    )


def test_status_not_answered(client, student_factory):
    student_factory(STUDENT)
    resp = _status(client)
    assert resp.status_code == 200
    assert resp.json() == {"answered": False}


def test_submit_201(client, student_factory):
    student_factory(STUDENT)
    resp = _submit(client)
    assert resp.status_code == 201
    assert "answered_at" in resp.json()


def test_status_answered_after_submit(client, student_factory):
    student_factory(STUDENT)
    assert _submit(client).status_code == 201
    resp = _status(client)
    assert resp.json() == {"answered": True}


def test_submit_duplicate_409(client, student_factory):
    student_factory(STUDENT)
    assert _submit(client).status_code == 201
    resp = _submit(client)
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "duplicate_survey"


def test_submit_unknown_code_404(client):
    resp = _submit(client, code="R-9999")
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "student_not_found"


def test_submit_invalid_opinion_change_422(client, student_factory):
    student_factory(STUDENT)
    resp = _submit(client, opinion_change="bogus")
    assert resp.status_code == 422


def test_submit_invalid_preferred_major_422(client, student_factory):
    student_factory(STUDENT)
    resp = _submit(client, preferred_major="bogus")
    assert resp.status_code == 422


def test_submit_not_chosen_yet_201(client, student_factory):
    student_factory(STUDENT)
    resp = _submit(client, preferred_major="not_chosen_yet")
    assert resp.status_code == 201


def test_submit_all_opinion_values(client, student_factory):
    for opinion in (
        "decided",
        "changed_completely",
        "confirmed_choice",
        "still_confused",
    ):
        code = f"R-{opinion[:3].upper()}1"
        student_factory(code)
        assert _submit(client, code=code, opinion_change=opinion).status_code == 201