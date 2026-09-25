# Admin Dashboard Redesign — Implementation Plan (v2 scope)

Repo: `https://github.com/HudaAtabbal/Your-academic-destination`
- Frontend: branch `Frontend` (React 19 + Vite, folder `Your-academic-destination/`)
- Backend: branch `backend` (FastAPI + SQLAlchemy 2 + PostgreSQL)

Page being redesigned: `src/pages/Admin/GeneralDirectorDashboard.jsx` (route `/dashboard`, role `super_admin`).

This document is the single source of truth for this task. Read it fully before writing code. Work phase by phase (section 8), and stop after each phase so it can be reviewed.

---

## 0. Ground rules (read first)

1. **Do not invent features.** Implement only what is listed here. If something is unclear, stop and ask. Do not add extra cards, metrics, roles, or buttons.
2. **Backend structure is feature-folder:** `app/routers/<feature>/<feature>_router.py` (HTTP only), `<feature>_service.py` (logic), `<feature>_schema.py` (Pydantic). No top-level `schemas/` folder.
3. **All changes are additive on the backend.** Existing endpoints (`/admin/dashboard/stats`, `/analytics`, `/sms-status`, etc.) keep their exact current response shape. Existing tests in `tests/` must keep passing.
4. **Time:** always use `app/time_utils.py` (Asia/Damascus, naive datetimes). Never use server-local time and never use `datetime.now()` directly.
5. **Day boundaries** are Syrian calendar days: `[day 00:00, next day 00:00)`.
6. **UI language is Arabic, RTL.** All UI strings below are exact and must be copied as written.
7. **Responsive is mandatory.** Every section must work from 360px to 1920px wide with no horizontal page scroll (see section 6).
8. Keep the existing polling/auth helpers: `apiGet`, `apiRequest`, `ApiError` from `src/api/api.js`, and the `AdminHeader` component.

### Visual reference (read this too)

The folder `dashboard-reference/` contains `dashboard-reference.html` (a static mockup, desktop 1440px) and `dashboard-reference.png` (its screenshot). **The target look is this mockup.** Rules for using it:

- Take spacing, radii, font sizes, weights, colors, bar/donut/heatmap styling and the order of sections **from the mockup's CSS**. When this document and the mockup disagree on *behavior or data*, this document wins. When they disagree on *look*, the mockup wins.
- All numbers, student names, codes and lecture titles in the mockup are **fake**. Never hardcode them; every value comes from the API as described below.
- The mockup is desktop-only. The responsive behavior comes from section 6.4 of this document.
- The mockup uses one-off class names. Do not copy them; use the `gd-dash-` prefixed classes and the components in section 6.6.
- The mockup's hour labels are 12h (`1:00`); the real UI uses 24h (`13:00`), as section 4.5 says.

---

## 1. Pre-requisite bug fix (frontend)

Case-sensitive imports break the build on Linux. The file is `src/components/Stepprogress.jsx`, but three pages import `../../components/StepProgress`, and that component imports `../style/StepProgress.css` while the file is `src/style/Stepprogress.css`.

Fix: rename the files to `StepProgress.jsx` and `StepProgress.css` with `git mv` (two-step rename via a temp name, because Windows and macOS are case-insensitive). Then confirm `npm run build` succeeds on Linux.

---

## 2. Event days config (shared constant)

The event runs on three non-consecutive days:

| key   | date       | Arabic label |
|-------|------------|--------------|
| `wed` | 2026-09-23 | أربعاء       |
| `thu` | 2026-09-24 | خميس         |
| `sat` | 2026-09-26 | سبت          |

**Backend:** create `app/event_days.py`:
- `EVENT_DAYS: dict[str, date]` with the table above.
- Read the dates from an env var `EVENT_DAYS="2026-09-23,2026-09-24,2026-09-26"` if present, else use these defaults.
- `EVENT_HOURS = range(8, 18)`, i.e. the hours 08:00 through 17:00 inclusive. Used for hourly charts; hours outside this range are still counted but clamped to the nearest edge bucket.
- Helper `day_range(day_key) -> tuple[datetime, datetime] | None`. It returns `None` for `"all"` and raises a 422-style `AppError` for an unknown key.

**Query param convention for every filtered endpoint:** `day: Literal["all", "wed", "thu", "sat"] = "all"`.

**Frontend:** create `src/api/eventDays.js`:

```js
export const EVENT_DAYS = [
  { key: 'all', label: 'الكل' },
  { key: 'wed', label: 'أربعاء' },
  { key: 'thu', label: 'خميس' },
  { key: 'sat', label: 'سبت' },
];
```

---

## 3. Backend — new endpoints

All new admin endpoints go in the existing `app/routers/dashboard/` feature folder: router, service and schema. They inherit its `require_role(AccountRole.super_admin)` dependency. Every response includes `generated_at: datetime` (Damascus time) so the UI can show "آخر تحديث".

### 3.1 Day-filtered counters

| Endpoint | Returns | Logic |
|---|---|---|
| `GET /admin/dashboard/students-inside-count?day=` | `{ day, count, generated_at }` | Distinct `student_id` with `activity_type = campus_entry`. When `day != all`, filter `checked_in_at` to that day. When `day = all`, return the same number as `students_inside_all_days` in `/stats`. |
| `GET /admin/dashboard/game-scans?day=` | `{ day, count, generated_at }` | Count of `activity_type = game` checkins, optionally day-filtered. |
| `GET /admin/dashboard/college-visits?day=` | `{ day, total, items: [{college, count}], generated_at }` | Same logic as `college_visits` inside `get_dashboard_analytics`: the union of `Booking(college, student_id)` and `Checkin(college, student_id)`, distinct students per college, the same `_VISITS_EXCLUDED` set, sorted descending. The day filter applies `booked_at` to bookings and `checked_in_at` to checkins. `total` = sum of counts. **Refactor:** extract the existing logic into a helper that takes an optional `(start, end)` range, and have both `/analytics` and this endpoint call it. |
| `GET /admin/dashboard/union-sections?day=` | `{ day, total, items: [{section, count}], generated_at }` | Same logic as `union_sections` in `/analytics`, plus the optional day filter. All three sections are always present (zero if empty). Extract a shared helper the same way. |

### 3.1a Academic guide tracking (added after v2 shipped)

The Academic Guide (`/academic-guide`) is an embedded iframe, so there is no
checkin to count. A dedicated table measures it instead. This is the only
page-usage tracking in the product, and it is limited to that one page.

| Endpoint | Purpose |
|---|---|
| `POST /students/page-visit/start` | Public. Body: `{ page, visitor_id, student_code? }`. Creates the row with `entered_at = time_utils.now_naive()` and returns `{ visit_id, entered_at }`. Rate-limited per `visitor_id` (30/hour), **never per IP** — all students share one campus network. |
| `POST /students/page-visit/end` | Public. Body: `{ visit_id }` — no duration field exists anywhere in the schema. The server computes `duration_seconds = now_naive() - entered_at`, capped at 12 hours. |
| `GET /admin/dashboard/guide-insights?day=` | `super_admin` only (inherited from the router). Returns `{ day, page, visitors_count, visits_count, avg_duration_seconds, median_duration_seconds, measured_visits, generated_at }`. Cached 300s server-side like `/presence`. |

Table `page_visits`: `id` (PK, also the start↔end correlation handle), `page`,
`visitor_id`, `student_code?`, `entered_at`, `duration_seconds?`, indexed on
`(page, entered_at)` and `(page, visitor_id)`. Created by `create_all` on
restart — no migration.

Rules that keep the numbers honest:
- **Dwell time is server-measured.** No endpoint accepts a client-reported
  duration, so the average cannot be inflated from the browser.
- **Averages and medians, not sums.** Every aggregate except the visit count
  is an average or median, so repeating a visit cannot move the headline much.
- **3-second minimum.** The client only fires `start` after 3 seconds of
  *visible* time, and the server excludes `duration < 3` from the averages.
  Bounces still count as visits, they just don't pollute the dwell figures.
- **No backfill.** Tracking starts at deploy. On non-event days `all` shows
  cumulative data while a specific event day may legitimately be `—`.

Frontend: `usePageVisit(active, page)` in `src/hooks/usePageVisit.js`, called
once from `AcademicGuide.jsx` (`active` arrives from `StudentTabsLayout`).
It uses a `useRef` guard against StrictMode double-effects, freezes its dwell
counter while the tab is hidden, and ends the visit on `pagehide`. Rendering:
a 5th card in the existing `SummaryCards` row, titled **الدليل الأكاديمي**,
carrying the same `<DayFilter>` as the neighbouring cards plus متوسط البقاء,
عدد الأشخاص، وعدد الزيارات.

### 3.2 Presence metrics
`GET /admin/dashboard/presence` returns:

```json
{
  "avg_minutes_all": 162,
  "per_day": [
    {"day": "wed", "avg_minutes": 160, "students_counted": 540},
    {"day": "thu", "avg_minutes": 185, "students_counted": 700},
    {"day": "sat", "avg_minutes": 135, "students_counted": 0}
  ],
  "frequency": {"one_day": 1320, "two_days": 430, "all_days": 154, "total": 1904},
  "generated_at": "..."
}
```

- **Duration per (student, day):** `max(checked_in_at) - min(checked_in_at)` across all of that student's checkins on that day. This is an estimate from first to last activity, not an actual exit time. Do it in SQL with `GROUP BY student_id, CAST(checked_in_at AS DATE)`.
- **Exclude** (student, day) pairs with only one checkin, since their duration is 0. `students_counted` = the number of pairs included.
- `avg_minutes_all` = the average over all included pairs across all event days (not an average of the daily averages). Round to an integer.
- **Frequency:** for each student, count the distinct event days (only dates in `EVENT_DAYS`) that have a `campus_entry`. Bucket into 1, 2 and 3. `total` must equal `students_inside_all_days`, ignoring entries outside event days.

### 3.3 Peak hours

`GET /admin/dashboard/peak-hours` returns:

```json
{
  "hours": [8,9,10,11,12,13,14,15,16,17],
  "days": [
    {"day": "wed", "counts": [0,40,120,210,190,150,90,40,10,0]},
    {"day": "thu", "counts": [...]},
    {"day": "sat", "counts": [...]}
  ],
  "peak": {"day": "thu", "hour": 11, "count": 320},
  "generated_at": "..."
}
```

- Count **all checkins** (every activity type) by `EXTRACT(HOUR FROM checked_in_at)` per event day. This is the default; see open decision D1.
- `peak` is the single highest cell. It is `null` if everything is 0.

### 3.4 Top students (المتميزون)

`GET /admin/dashboard/top-students?metric=&page=1&limit=5`

- `metric`:
  - `lectures`: count of `lecture` checkins.
  - `tours`: count of `tour` checkins.
  - `presence`: total minutes, i.e. the sum of per-day durations from 3.2 (same exclusion rule).
  - `union_all`: students with checkins in **all three** `union_section` values.
- Response: `{ metric, items: [{rank, unique_code, full_name, value}], page, limit, total, total_pages, generated_at }`.
- Sort by `value` desc, then `unique_code` asc. `rank` is the absolute rank, not the rank within the page.
- For `union_all`, `value` is always 3. Order by the time of the student's latest union checkin (asc), i.e. who completed all corners first, and `total` = how many completed.
- `limit` max 100. Same pagination style as `/students-inside`.

### 3.5 Server-side cache

`presence`, `peak-hours` and `top-students` are heavier. Wrap each service call in a simple in-process TTL cache of **300 seconds**, keyed by the full parameter set. `generated_at` is the time the cached value was computed. Put the cache helper in `app/cache.py` (dict + lock + timestamps, no new dependency).

### 3.6 Backend tests

Add `tests/test_dashboard_v2.py` using the existing `conftest.py` fixtures. At minimum:
- each `day` value;
- unknown `day` → 422;
- presence excludes single-checkin days;
- frequency buckets sum to `students_inside_all_days`;
- `union_all` only includes students with all 3 sections;
- a non-super_admin gets 403 on every new admin endpoint.

---

## 4. Frontend — page structure

The final page, top to bottom:

```
AdminHeader (with SMS pill)
1. Hero band
2. Summary cards row (4)
3. Presence row (2)
4. Section title "التحليلات"
5. Peak hours heatmap (full width)
6. College visits | Lecture attendance      (2 cols)
7. Union sections donut | علمي/أدبي donut   (2 cols)
8. Score distribution | Year distribution   (2 cols)
9. Top students (full width)
10. Team accounts summary bar (full width)
```

**Remove:**
- all `CollapsibleSection` usage (everything is open);
- the standalone "حالة إرسال الرسائل النصية" section;
- the "مسحات ركن الترفيه" ring/donut;
- the inline team accounts table (moved, see 4.11).

### 4.0 Header SMS pill (in `AdminHeader`)

- `AdminHeader` gets an optional prop `smsStatus`. When it is provided, render a pill before the role badge: green dot + `المُرسِل متصل` (or a red dot + `المُرسِل منقطع`), followed by muted text `· {pending} بالانتظار · {failed} فاشلة`.
- Only the dashboard passes this prop. Other admin pages look unchanged.
- On screens < 600px, show only the dot + `متصل`/`منقطع`.

### 4.1 Hero band

A single rounded teal block with two zones.

- **Primary zone (right in RTL, ~35% width, darker teal):**
  - Label `داخل الحرم اليوم` with a small pulsing orange dot. Respect `prefers-reduced-motion`: no pulse.
  - Huge number: `students_inside_today`.
  - Caption: `عدد الطلاب اللي دخلوا من البوابة اليوم فقط`.
- **Secondary zone (3 equal columns separated by thin light dividers):**
  1. `مسجّلون إلكترونياً` → `registered_online_count`. Link `عرض القائمة` → `/gate-registered`.
  2. `إجمالي الطلاب داخل الجامعة` + a **DayFilter** → value from `/students-inside-count?day=`. Link `عرض القائمة` → `/dashboard-students-inside`.
  3. `أكملوا الاستبيان` → `survey_completed_count`. Link `عرض القائمة` → `/dashboard-survey-completions`.
- The whole column is the clickable element (`<Link>` or a button with `navigate`). The DayFilter click must `stopPropagation` so it does not navigate.

### 4.2 Summary cards row (4 cards)

1. **`التسجيل الإلكتروني`** (header link `مسجّلون بلا حضور` → `/dashboard-no-shows`)
   - Two numbers: `حضروا` = `registered_online_count - registered_no_show_count` (teal), and `بلا حضور` = `registered_no_show_count` (orange).
   - A stacked progress bar (teal/orange).
   - Caption `{pct}٪ من المسجّلين حضروا فعلاً`.
2. **`سجلات Walk-in`** (header link `تنتظر الإكمال` → `/gate-incomplete`)
   - `تم إكمالها` = `walkin_completed_count` (teal), `تنتظر الإكمال` = `walkin_pending_count` (orange).
   - Stacked bar.
   - Caption `{pct}٪ من السجلات مكتملة`.
3. **`إجمالي الاستشارات`**: `total_consultations`, caption `استشارة وحدة لكل طالب`.
4. **`مسحات ركن الترفيه`**: DayFilter under the title, value from `/game-scans?day=`, caption `مسح واحد لكل طالب طوال الفعالية`.

Percentages: guard against division by zero (show `0٪`).

### 4.3 Presence row (2 cards)

1. **`متوسط مدة التواجد`**
   - Subtitle, muted and small: `تقدير: من أول لآخر نشاط للطالب باليوم`.
   - Left block: big `H:MM` + `ساعة`, caption `متوسط كل الأيام`.
   - Right block: 3 rows (`أربعاء`, `خميس`, `سبت`), each with a horizontal bar (width relative to the max day) and the value as `2س 40د`.
   - Days with `students_counted = 0` show `—` and an empty bar.
2. **`تكرار الحضور`**
   - Header total `{total} طالب`.
   - Three tiles: `يوم واحد`, `يومين`, `كل الأيام الثلاثة`. Each shows the count and `{pct}٪` of `total`.
   - The third tile is highlighted (teal background, white text).

### 4.4 Section title

`التحليلات` + muted text `بتتحدث تلقائياً`.

### 4.5 Peak hours heatmap — `ساعات الذروة`

- Header right: title. Header left: orange text `الذروة: {dayLabel} {HH}:00 – {HH+1}:00`, or hidden if `peak` is null.
- Grid:
  - the first column holds the day labels;
  - the next columns are the hours, with a header row `9:00`… and 24h labels (`13:00`, not `1:00`);
  - each cell shows its number;
  - the background uses a 5-step teal scale based on value / max (see tokens), with dark text on light cells and white on dark;
  - the peak cell gets a 3px orange outline.
- Legend under the grid: `أقل` [5 swatches] `أكثر · عدد المسحات بكل ساعة`.

### 4.6 College visits — `زيارة الكلية (ركن التوجيه)`

- Header: orange total + DayFilter.
- Horizontal bar list: label (use `COLLEGE_VISIT_LABELS`, keeping the existing `dentistry → المجمع الطبي` override), bar (teal, width relative to the max), and the value.
- Show the top 8. Below them, a text button `عرض كل الكليات ({n})` expands the full list in place and toggles to `عرض أقل`.
- In RTL the bars grow from the right.

### 4.7 Lecture attendance — `حضور كل محاضرة`

- Data from the existing `/analytics` `lecture_attendance`, with no day filter.
- Horizontal bars (orange), full `label` text. Truncate with an ellipsis plus a `title` tooltip when too long.
- Header total = sum.
- Sort by count descending.
- This replaces the old vertical bars with rotated tiny labels.

### 4.8 Donuts row

- **`مسحات ركن الاتحاد`**: header total + DayFilter, data from `/union-sections?day=`. Legend `الركن المركزي`, `دليل التخصص`, `نادي التركي`, each with `{pct}٪ ({count})`. Colors: teal, orange, plum.
- **`علمي / أدبي`**: from `/analytics` `certificate_distribution`, no filter. Colors: teal = علمي, orange = أدبي.
- Keep the existing SVG donut technique (stroke-dasharray on r=15.9). Fix the segment offsets so they add up correctly for 3 segments.

### 4.9 Score and year distributions

These keep the vertical column charts from `/analytics`, with these changes:
- the columns are teal, and the single highest column is orange;
- the count sits above each column and the label below;
- the chart height is 170px on desktop and 140px on mobile.

### 4.10 Top students — `الطلاب المتميزون`

- Header link: `عرض القائمة الكاملة` → `/dashboard-top-students?metric={current}`.
- Tabs (single-select pills, active = plum):
  - `أكثر حضور محاضرات` (`lectures`)
  - `أكثر جولات كليات` (`tours`)
  - `أطول تواجد بالجامعة` (`presence`)
  - `زاروا كل أركان الاتحاد ({total})` (`union_all`)
- Content: 5 cards in a row. Each shows the rank `#1`…, the full name (fallback `—`), the `unique_code` (muted), and the value with its unit:
  - `محاضرة` for lectures;
  - `جولة` for tours;
  - `Xس Yد` for presence;
  - for union_all, show `الأركان الثلاثة` instead of a number.
- Card `#1` is highlighted (plum background, white text).
- Fetch on tab change, and cache per tab in component state.

**New page** `src/pages/Admin/TopStudentsPage.jsx`, route `/dashboard-top-students` (inside `TeamPrivateRoute`):
- the same 4 tabs, synced with the `?metric=` query param;
- a paginated table (20/page) with columns `#`, `الاسم`, `الرمز`, `القيمة`;
- copy the layout/pagination pattern from `StudentsInsideAllDaysPage.jsx`.

### 4.11 Team accounts

- **Move** the current team table (search + pagination + edit/delete, all existing logic) **verbatim** into a new page `src/pages/Admin/TeamAccountsPage.jsx`, route `/team-accounts`.
- Restyle edit/delete as small outlined pill buttons (teal outline for `تعديل`, red outline for `حذف`) instead of underlined links.
- In `AdminHeader`, change the nav link `حسابات الفريق` to point to `/team-accounts`.
- In `CreateTeamAccountPage.jsx`, change both `navigate('/dashboard')` calls to `navigate('/team-accounts')`.
- **Dashboard summary bar** (full width card):
  - left side: title `حسابات فريق العمل` and the muted line `{total} حساب`;
  - right side: an outlined button `إدارة الحسابات` → `/team-accounts` and a filled button `+ إنشاء حساب جديد` → `/create-team-account`.
  - `total` comes from `/admin/accounts?page=1&limit=1`.

### 4.12 Loading / empty states

- Before first data arrives, numbers show `—`.
- Each chart card with no data shows its own centered muted message, e.g. `ما في بيانات للآن` (keep the existing per-section messages).
- A failed request keeps the last good data (do not blank the card).

---

## 5. Refresh strategy (polling)

Create `src/hooks/usePolling.js`: `usePolling(fetchFn, intervalMs, deps)`.
- Run immediately, then every `intervalMs`.
- Pause while `document.visibilityState === 'hidden'`, and run once immediately when the tab becomes visible again.
- Clean up on unmount.
- When `deps` change (e.g. the day filter), refetch immediately.

Intervals:

| Data | Interval |
|---|---|
| `/stats`, `/sms-status` | 15 s (unchanged) |
| `/students-inside-count`, `/game-scans`, `/college-visits`, `/union-sections`, `/analytics` | 60 s |
| `/presence`, `/peak-hours`, `/top-students` | 5 min (server caches for 5 min too, so polling faster is pointless) |

---

## 6. Design system and responsive rules

### 6.1 Tokens

Define these tokens as CSS custom properties on `.gd-dash-viewport` and **replace the hardcoded colors** in the dashboard CSS:

```css
--gd-teal: #134f47;       /* primary */
--gd-teal-deep: #0d3a34;  /* hero primary zone */
--gd-orange: #E85B0D;     /* accent / highlights / peaks */
--gd-ivory: #FFF4E0;      /* page background */
--gd-plum: #3D0F28;       /* headings, leaderboard highlight */
--gd-paper: #fffdf8;      /* card background */
--gd-ink: #1d2b28;        /* body text */
--gd-muted: #7a6b5a;      /* labels, captions */
--gd-line: #efe3cc;       /* card borders, dividers */
--gd-track: #f3e6cf;      /* empty bar tracks, filter background */
--gd-hero-muted: #a9c8c1; /* muted text on teal */
/* heatmap scale (low → high): */
--gd-heat-0: #f3ece0; --gd-heat-1: #cfe0da; --gd-heat-2: #8fb5ad; --gd-heat-3: #3d7a70; --gd-heat-4: #134f47;
```

### 6.2 Type and shape

- Font: `'Ghroob'` (already loaded).
- Numbers: weight 800.
- Card titles: 1.05rem, 800 weight, plum.
- Section title: 1.35rem.
- Cards: `background: var(--gd-paper); border: 1px solid var(--gd-line); border-radius: 22px; padding: 24px 26px;`. **No box-shadow on regular cards.**
- The hero uses `border-radius: 28px`.

### 6.3 DayFilter component

`src/pages/Admin/dashboard/DayFilter.jsx` with props `value`, `onChange`, `variant = 'light' | 'onDark'`.

- A segmented pill with 4 buttons from `EVENT_DAYS`.
- Use real `<button type="button">` elements with `aria-pressed`, wrapped in `role="group"` with `aria-label="فلترة حسب اليوم"`.
- Active: teal background with white text on light; white background with teal text on dark.
- Font size 0.78rem, padding 4px 11px.
- Visible `:focus-visible` outline in orange.

### 6.4 Breakpoints

| Width | Rules |
|---|---|
| **≥ 1200px** | Container max-width 1240px, padding 32px. Layout exactly as section 4. |
| **900–1199px** | Hero: primary zone on top (full width), secondary 3 columns below. Summary cards: 2×2 grid. All 2-column rows stay 2 columns. Leaderboard: 5 cards in a horizontally scrollable row with scroll-snap. |
| **600–899px** | Hero: primary on top; secondary becomes 3 columns with smaller numbers (2.2rem). Summary cards: 2×2. **All 2-column rows become 1 column.** Presence row: 1 column. Heatmap: inside an `overflow-x: auto` wrapper with the day-label column `position: sticky; inset-inline-start: 0`. Horizontal bar label column: 140px. |
| **< 600px** | Container padding 16px, section gap 20px. Hero: primary number 4rem; secondary stacks vertically as 3 rows (label + number side by side, link under). Summary cards: 1 column. Frequency tiles: 3 in a row but compact (number 1.5rem). Heatmap: horizontal scroll as above, cell height 36px. Horizontal bars: label column 110px, font 0.82rem. Leaderboard: horizontal scroll-snap, card width 70vw. Team summary bar: stacks, buttons full width. DayFilter: must not wrap; if its container is too narrow, the filter row goes under the card title (use `flex-wrap: wrap` on the card header). |

### 6.5 General responsive requirements

- **No horizontal scroll on `body`** at any width. Only explicit wrappers (heatmap, leaderboard, and the team table on its own page) may scroll horizontally.
- Tap targets ≥ 36px high on touch (`@media (pointer: coarse)` bumps DayFilter/tab padding).
- Test at 360, 390, 768, 1024, 1280 and 1440 wide.

### 6.6 File layout

Split the dashboard into small presentational components under `src/pages/Admin/dashboard/`:

`HeroStats.jsx`, `SummaryCards.jsx`, `PresenceRow.jsx`, `PeakHoursHeatmap.jsx`, `HorizontalBars.jsx` (reused by colleges + lectures), `Donut.jsx` (reused by union + certificate), `ColumnChart.jsx` (reused by score + year), `TopStudents.jsx`, `TeamSummaryBar.jsx`, `DayFilter.jsx`.

`GeneralDirectorDashboard.jsx` keeps data fetching and passes data down. Keep all CSS classes prefixed `gd-dash-` in `src/style/GeneralDirectorDashboard.css`, which is rewritten.

---

## 7. Frontend tests

- Update `GeneralDirectorDashboard.test.jsx` for the new structure: mock all endpoints; assert the hero number renders; assert that the DayFilter change triggers a refetch with `?day=thu`.
- Add a test for `TopStudentsPage`: switching tabs updates `?metric=` and refetches.

---

## 8. Implementation order (stop for review after each phase)

1. **Phase 1:** the section 1 bug fix plus the `event_days` config (backend + frontend).
2. **Phase 2 (backend):** 3.1 → 3.5 + their tests (3.6).
3. **Phase 3 (frontend):** move the team table to `/team-accounts` (4.11) + the header SMS pill (4.0).
4. **Phase 4 (frontend):** the dashboard rebuild, sections 4.1 → 4.10, with `usePolling` + responsive CSS.
5. **Phase 5 (frontend):** the `TopStudentsPage` + tests.
6. **Phase 6:** a manual responsive pass at all widths in 6.5, plus `npm run build` and `pytest`.

---

## 9. Open decisions (defaults already chosen — implement the default unless told otherwise)

- **D1. Peak hours source.** Default: all checkin types. Alternative: `campus_entry` only, which answers "when do students arrive". If switched, only the service filter changes.
- **D2. Presence exclusion.** Default: exclude (student, day) pairs with a single checkin.

## 10. Out of scope — do not do

- Do not change any scanner, gate, registration or student-facing UI.
- Do not change points/scoring logic.
- Do not add charting libraries. Everything stays pure CSS/SVG as today.
- Do not add new roles or permissions.
