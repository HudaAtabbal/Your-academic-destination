# عجلة الحظ — خطة الفرونت (v1)

Plan doc, نفس اصطلاح `admin-dashboard-plan-v2.md`. الترتيب: `0. Ground rules`,
`1..n` التفاصيل، `Tests`, `Implementation order`, `Open decisions`, `Out of scope`.

---

## 0. Ground rules (read first)

### 0.1 القرارات المقفلة

| # | القرار | ليه |
|---|---|---|
| D1 | **العجلة بتعرض الـpool كامل** بدون عينة | طلب المستخدم. كل طالب مؤهل = قطاع |
| D2 | **كل تاب عنده قائمته الخاصة، والتداخل مسموح** | طلب المستخدم. طالب 60 نقطة بيظهر بالأربع تابات. الاستبعاد العالمي **بينكتب بعد القرار** بس — مش قبل |
| D3 | **صفحة أدمن + شاشة عرض مستقلة** | `/admin/wheel` و `/wheel/live` |
| D4 | **السحب Authority للباك**، والفرونت بينفّذ الحركة على الفائز | عشان السهم يطلع على الفائز الحقيقي مضموناً، مش على زاوية عشوائية |
| D5 | **الصوت مولّد بالكامل** بالـWeb Audio — بلا ملفات، بلا CDN | موجود جاهز بالـprototype |

### 0.2 شو بيتغيّر عن `wheel-v4.html`

الـprototype **مش نفس المنتج** — دوّرت عليه هون قبل ما نبلّش:

| `wheel-v4.html` | v1 |
|---|---|
| 8 قطاعات = **أسماء جوائز** | 8+ قطاعات = **أسماء طلاب** |
| الطالب بيدوّر على حاله | `super_admin` بيدوّر |
| "سجل جوائزي" + "استلام الجائزة" | "سجل الفائزين" (read-only) + popup قبول/رفض |
| "تنتهي فرصة اليوم 12:00" | مرّة واحدة، بدون مؤقّت |
| "إجمالي الجوائز الموزعة اليوم: 184" | عدد المؤهلين بالتاب (`eligible_count`) |
| `Math.random()` بيسمح بأي قطاع | الفائز من الباك،الحركة محسوبة عليه |

**بيننقل كما هو:** التوكنز (`:root` custom properties)، أسماء CSS، `renderWheelFace`، نظام الـRAF، **محرّك الصوت كامل**، القصاصات، والـstate machine.

### 0.3 في فخ لازم نتجنّبو

`wheel-v4.html:369-376` — الب pajPrototype كان **بجيب الفائز أول وبعدين بينفّذ لزاوية عشوائية**. فالسهم كان بيوقف على قطاع غير الفائز. التخطيط بيشيل هاد السلوك (§5).

---

## 1. المسارات (Routes)

### 1.1 صفحة الأدمن

```
/admin/wheel                    → AdminWheelPage        (4 تابات + العجلة + علبة القرار)
  ?tab=first_prize|second_prize|third_prize|final_prize
```

- Guard: `TeamPrivateRoute` + **role = `super_admin`**. أي دور تاني → 403.
- `?tab=` بالـquery string مش state داخلي — فالتاب برجع بعد F5، ومنحفظ كـURL للمشاركة.
- Guard موجود فعلاً: `src/components/TeamPrivateRoute.jsx` + `src/api/roles.js`.

### 1.2 شاشة العرض

```
/wheel/live                     → WheelLivePage         (للجمهور)
```

- Guard: **`get_current_account`** — أي حساب مسجّل، **مش** `super_admin`. (ماشي مع الباك: `/wheel/live` مفتوح لأي حساب.)
- بتقرأ نفس معلومة الأدمن، بتعرضها بشكل كبير على بروجيكتور.
- **بتعرض ٦ حقول بس**: `winner_name`, `winner_code`, `tab_label`, `revealed_at`. ممنوع: أسماء المؤهلين، درجاتهم، وقت التجميد، عدد السحوبات.

### 1.3 وين بالـ`App.jsx`

```jsx
<Route path="/admin/wheel" element={<TeamPrivateRoute><AdminWheelPage /></TeamPrivateRoute>} />
<Route path="/wheel/live"  element={<TeamPrivateRoute><WheelLivePage /></TeamPrivateRoute>} />
```

`WheelLivePage` بستعمل `TeamPrivateRoute` لأن هاد المكوّن بيتحقق من الأدوار بنفسه — مش لأنه `super_admin`. ولمّا بدك جمهور بلا حساب، الباك ما يسمح — القرار ذلك و(Server-side) مش بالفرونت.

### 1.4 لينك بال-header

`src/components/AdminHeader.jsx` — أضف `<NavLink to="/admin/wheel">عجلة الحظ</NavLink>`، بس لـ`super_admin` (الـheader أصلاً بيخفي روابط حسب الدور).

---

## 2. شكل الملفات

```
src/
  api/
    wheel.js                        ← كل نداءات الـ8 endpoints
    wheel.test.js

  pages/
    Admin/
      AdminWheelPage.jsx            ← orchestrator: التاب، الـboard، الحالة
      AdminWheelPage.test.jsx
      WheelLivePage.jsx             ← شاشة العرض
      WheelLivePage.test.jsx
      wheel/
        WheelTabs.jsx               ← 4 تابات (SegmentedControl)
        WheelBoard.jsx              ← عمود: قائمة الأسماء + التصنيف
        WheelCanvas.jsx             ← الـcanvas (يرث من wheel-v4)
        WheelSpinButton.jsx         ← "دوّر الآن" + eligibility
        WheelRevealModal.jsx        ← popup الكشف + التشويق
        WheelDecisionBar.jsx        ← التحقق اليدوي + قبول/رفض
        WheelArchivePanel.jsx       ← سجل الفائزين
        WheelFreezePanel.jsx        ← وقت التجميد + معاينة الأثر
        WheelTabTable.jsx           ← الجدول (متل اشكال الجداول يلي عنا)

  hooks/
    useWheelPool.js                 ← يحمّل pool التاب الحالي، يبني الـboard
    useWheelSpin.js                 ← حالة السحب + رياضيات الهبوط
    useWheelAudio.js                ← محرّك الصوت (منقول من الـprototype)
    useWheelLive.js                 ← polling شاشة العرض

  lib/
    wheelGeometry.js                ← SLICE, pegIndex, targetRotation
    wheelGeometry.test.js           ← اختبارات الرياضيات
```

`WheelTabTable.jsx` بياخذ شكل جداول `TopStudentsPage.jsx` (نفس الجدول/الـpadding/الخط).

---

## 3. الـAPI layer

`src/api/wheel.js` — بنفس اصطلاح `api.js` الموجود:

| fn | endpoint |
|---|---|
| `getWheelTabs()` | `GET /admin/wheel/tabs` |
| `getWheelSettings(prospectiveIso?)` | `GET /admin/wheel/settings` |
| `updateWheelSettings(freeze_at, reason?)` | `PUT /admin/wheel/settings` |
| `drawWheel(tab, idempotencyKey)` | `POST /admin/wheel/draws` |
| `decideWheelDraw(drawId, {decision, presence_verified, confirmed})` | `POST /admin/wheel/draws/{id}/decision` |
| `getWheelArchive()` | `GET /admin/wheel/archive` |
| `getCeremonySnapshot()` | `GET /admin/wheel/ceremony-snapshot` |
| `getWheelLive()` | `GET /wheel/live` |

`useWheelPool` بيستعمل `getCeremonySnapshot()` بدل `drawWheelPool` — الـsnapshot بيرجّع **الأربعة تابات دفعة وحدة**، فبدّو نداء واحد بدل ٤. بينخزّن بالـstate وبـ`localStorage` (key: `wheel:snapshot:<generated_at>`).

### 3.1 `idempotency_key`

`crypto.randomUUID()` لكل ضغطة. بتولّد **قبل** النداء وبتحفظها بالـstate — لأن لو الشبكة طارت، إعادة الإرسال بنفس المفتاح بترجّع نفس السحبة بدل ما تطلع طالب ثاني.

---

## 4. الـBoard — من التاب للقطاع

**تعريف:** الـboard = ترتيب ثابت لطلاب الـpool الحالي على قطاعات العجلة. بينحسب مرّة لكل تاب، وبينخزّن بالـstate.

```js
// per tab, in useWheelPool
board = pool.map(c => ({ student_id, unique_code, full_name, rank }))
N = board.length
```

- **`N` التاب Fourth = كل الـpool (D1).** مافي take ولا sample.
- **الترتيب**: بنحط الـboard بنفس ترتيب الباك (`rank`) أول مرّة (الإعجاب بشكل الـpool)، وبيصير **shuffle بعد أول سحب** (مش قبل) — أول وحدة بتطلع مرتّبة، بعدها بتختلط. هالشي بيخلي الحفل متحرك.
- **`slices` بالـcanvas = `N` دايماً.**

### 4.1 لما `N` كبير

| `N` | العجلة | القائمة الجانبية |
|---|---|---|
| `2..24` | أسماء على القطاعات | مخفية (العجلة كافية) |
| `> 24` | قطاعات لون بس، **بلا أسماء** | **الكل** بالأسماء، قابلة للتمرير، والفائز بيتملج بالأخضر |

الدzo Lection names 1000 طالب = زاوية 0.006 rad = أقل من بكسل. `wrapLabel()` رح يطلع نصاً مشوّه. فالقاعدة: **ما بنكتب نص إلأ إذا `slices <= 24`**. الأسماء كلها ظاهرة بالقائمة، فما في حدا بخسر اسم.

**ما بنرفض تاب كبير.** بلا سقف. الـbackend بيرجّع `eligible_count` والفرونت بيعرض كل شي.

### 4.2 تبديل التاب

تبديل التاب = تغيير `?tab=` = **board جديد** (قائمة تانية) + إعادة رسم. الحذف: `wheelCache = null; draw()` موجود بالـprototype — عم يُستعمل.

**مش** بنعمل reset للدوران — بيضل مكانه.

---

## 5. السحب — رياضيات الهبوط (الجواب على D4)

هاد قلب الصفحة. ثلاث خطوات.

### 5.1 مين بيختار

```
1. الأدمن يضغط "دوّر الآن"
2. POST /admin/wheel/draws {tab, idempotency_key}     ← الباك بيختار
3. الرد: {draw_id, student_id, unique_code, full_name, ...}
4. الفرونت: winnerSlot = board.findIndex(c => c.student_id === student_id)
5. العجلة بتدور لـwinnerSlot بالظبط
6. التشويق، ثم البطاقة، ثم القرار
```

**ليش 2 مش 1:** لو الفرونت اختر، `Math.random()` عنده = السهم على قطاع بينحطّ فيه anybody، و`fetch` مجرّد call. الباك هو يلي يعرف الـpool الحقيقي. (§9 في ملاحظة الـoffline.)

### 5.2 الهبوط بالظبط على الفائز

في زاويتين مختفتين, وخلطهم هو البج كله: **two different angles**, and conflating them is the whole bug.

**Angle 1 — where the slice is PAINTED** (canvas work, at `rotation = 0`), from `wheel-v4.html:297`:

```js
const segStart  = i * SLICE - Math.PI / 2;   // slice i spans [segStart, segStart + SLICE)
const segCenter = segStart + SLICE / 2;
```

**Angle 2 — how far the wheel has TURNED.** `ctx.rotate(rotation)` (`wheel-v4.html:319`) turns the face clockwise, so slice `i` appears at `[segStart + rotation, segStart + SLICE + rotation)`. The pointer is fixed at `POINTER_ANGLE = -PI/2`. For the pointer to sit inside slice `i`:

```
segStart(i) + rotation   <=  POINTER_ANGLE  <  segStart(i) + SLICE + rotation
i * SLICE + rotation      <=  0              <  i * SLICE + SLICE + rotation
```

Hence:

```js
// which slice sits under the pointer for a given rotation
export function pegIndex(rotation, slices) {
  const raw = Math.floor(-rotation / sliceAngle(slices));
  return ((raw % slices) + slices) % slices;
}
```

> `wheel-v4.html:362` writes `Math.floor((r + Math.PI / 2) / SLICE)` — **the sign is wrong**. It is harmless there, because all it drives is the peg click sound. Here it is fatal: it points the arrow at the mirror image of the announced student. Ours lives in `src/lib/wheelGeometry.js`, and a test asserts it does NOT reproduce that formula.

**The landing angle** — solving `pegIndex(r) === i` for `r`:

```js
export function rotationForSlot(i, slices, rng = Math.random) {
  const jitter = (rng() - 0.5) * sliceAngle(slices) * JITTER_RATIO;  // +/- quarter of a slice
  return POINTER_ANGLE - segmentCenter(i, slices) + jitter;          // = -(i + 0.5) * SLICE + jitter
}
```

> The shortcut "just spin to `segmentCenter(i)`" is **wrong** — it lands on slice `n - 1 - i`, the mirror image. A test counts how many `(n, i)` pairs it gets wrong and asserts the count is `> 0`.

**Proof:** `-r / SLICE = i + 0.5 - jitter / SLICE`, and `jitter / SLICE` lies in `[-0.25, 0.25]`, so the argument lies in `[i + 0.25, i + 0.75]` and `Math.floor` returns exactly `i`, with 0.25 of margin on both sides.

That 0.25 margin is also what absorbs float64 error. The quotient is at most ~10000 in magnitude (8-10 turns on a 1000-slice wheel), where float64 error is ~1e-12, while the margin is ~1e-3 radian. Safe by nine orders of magnitude.

### 5.3 الحركة

```js
const span  = maxTurns - minTurns + 1;              // inclusive
const step  = Math.min(span - 1, Math.floor(rng() * span));
const turns = minTurns + Math.max(0, step);        // MUST be an integer
const delta = r_target - start + turns * TAU;
rotation   = start + delta * easeOut(t);           // easeOut(t) = 1 - (1 - t) ** 4.3
```

> **`turns` must be a whole number.** The prototype uses `8 + Math.random() * 2`, which is fractional. That silently breaks the exact-landing guarantee: a fractional `turns` contributes a fractional `turns * slices` to the quotient `-r / SLICE`, and `Math.floor` tips onto the neighbouring slice. A whole count contributes exactly `turns * slices`, which `Math.floor` absorbs without moving the result. This was a real bug, caught by the tests.

`easeOut` is clamped to `[0, 1]` inside `wheelGeometry.js`: with `(1 - t) ** 4.3`, a `t` slightly above 1 yields `NaN`, and a single `NaN` frame freezes the wheel for good.

`const start = rotation;` is read **after** the 420ms windup, not before. It matters more than it looks: the windup pulls `rotation` back by 0.2 rad, and the main spin then travels 9.4 rad, so an early capture aims the wheel 4.7 rad off — a third of a turn.

`rotation === r_target` **exactly** at `t = 1`, so the arrow stops on the winner. **The endpoint is computed, not random** — the essential difference from `wheel-v4.html:376`. `planSpin` returns `{ start, target: r_target, turns, delta }`.

### 5.4 الـwindup (420ms) قبل الحساب

`windup` بـ`back = -0.2` كيرجّع `rotation` للخلف شوي. الـ`start` لازم ينحسب **بعد** الـwindup مش قبل، وإلا صار خطأ مقدار `0.2 rad`. بالـprototype `start = rotation` بعد الـwindup فعلاً ✓ (سطر 376 بيقرا `rotation` بعد `await animate`). خلّي نفس الترتيب.

### 5.5 حالتا استثناء

| الحالة | السلوك |
|---|---|
| `N === 0` | `wheel_tab_empty` 409 من الباك. الزر `disabled` + رسالة "ما في طلاب مؤهلون". **ما بندور** |
| `N === 1` | `SLICE = 2π`، `center(0) = 0`، لدورة وحدة. شغّال. بس بلا تشويق — بيعرض البطاقة بعد 600ms بدون دوران |
| `N` كبير (> 1000) | الرسم بياخد ~20ms/إطار (1000× `arc`). أول مرّة فقط (الوجه مخبّأ). الـRAF بالمية بيشتغل. إذا كبر عالط — نخفّض عدد الـ`arc` بالـRAF (الأداء) مع بقاء كل الأسماء ظاهرة بالقائمة |

### 5.6 حالة الـstate machine

```js
state: 'idle' | 'winding' | 'spinning' | 'suspense' | 'revealed' | 'deciding'
```

`winding` و`deciding` **إضافيان** عن الـprototype — بيقفلوا الزر أثناء التنفيذ:

| state | زر السحب |.center-btn | overlay |
|---|---|---|---|
| `idle` | ✅ "ابدأ السحب" | ✅ | مغلق |
| `winding` → `spinning` | ❌ "العجلة تدور…" | ❌ | مغلق |
| `suspense` | ❌ | ❌ | مفتوح + "والفائز هو…" |
| `revealed` | ❌ "بانتظار قرارك" | ❌ | مفتوح + البطاقة |
| `deciding` | ❌ "جارٍ الحفظ…" | ❌ | مفتوح |
| بعد القرار | ✅ | ✅ | مغلق → `idle` |

**حارس 409:** لو الباك رد `wheel_pending_draw_exists` (فيه اسم معروض بنفس التاب)، `useWheelSpin` بيرجّع `state='revealed'` وبيجيب الـdraw الحالي من `/admin/wheel/tabs` بدل ما يعمل error. **ما بنعرض error** — بنرجّع للـpopup.

### 5.7 التتابع الزمني (من الـprototype، مع تعديل واحد)

```
idle
 └─ click → sWindUp()
     └─ 420ms windup (back-swing -0.2rad)
         └─ POST /draws ─────────────────┐   (٠ الباك يختار بالتوازي مع الدوران)
             └─ sWhoosh()               │
                 └─ 8600ms spin         │
                     └─ sBoom() → 600ms  │
                         └─ overlay open, sDrumroll(2.8), "والفائز هو…" (2900ms)
                             └─ البطاقة: sCrash() + sFanfare() + celebrate()
                                 └─ state='revealed' ← ينتظر القرار
```

**التديي** الأندا الحد HTTP يي** يي بيلطل الدر بظل بي ر عني رر 8.6 سواني دي فنل انتا يي يي**وي overlay مايبان اصم 6.7 سواني** (fallback صم `Promise.all` وي**:

```js
const drawPromise = drawWheel(tab, idemKey);
await windup(); sWhoosh();
await spin();                       ا// 8.6s
const draw = await drawPromise;     ا// خاص من اي نمي 6.7s
```

```js
const drawPromise = drawWheel(tab, idemKey);
await windup(); sWhoosh();
await spin();           // 8.6s
const draw = await drawPromise;   // خلص من زمان
if (draw instanceof Error) return handleDrawFailure(draw);
```

(بقي بنبلك بالنتائج: `wheel_pending_draw_exists` → 409 → نرجع للـpopup.)

### 5.8 المؤثرات الصوتية — منقول كما هو

`useWheelAudio` = محرّك الـprototype كامل (§0.2). **صفر تصميم جديد.** الجدول:

| اللحظة | الصوت | ملاحظة |
|---|---|---|
| قبل الدوران | `sWindUp()` | 420ms |
| انطلاق | `sWhoosh()` | |
| أثناء الدوران | `sClick(0.6)` per peg | بالت~
`pegIndex()` تغيّر + `pointerKick` kick |
| t > 0.55 | `sRiser(3.6)` | 8600/1000*0.42 |
| توقف | `sBoom()` | |
| التشويق | `sDrumroll(2.8)` | 2900ms |
| الكشف | `sCrash()` + `sFanfare()` | + `celebrate()` |
| كتم | `muted` toggle | ⚠️ يحتاج **زر واضح** |

**⚠️ تجربة المستخدم:** الصوت بيplay بعد **first click** (Chrome autoplay policy). لازم:

- **زر كتم كبير بالـhero** — مو بهيد-small. الحفل بالبرجيكتور و6 أشخاص، الصوت المزعج أخطر من نافع.
- **defaults على**: الخسارة (الأغلب) بتوقف الصوت. الـmaster gain 0.9.
- **حفظ الاختيار** بـ`localStorage` key `wheel:muted` — بينقل بين الأدمن والجمهور.
- **لا صوت بالـ`WheelLivePage`**: شاشة العرض Throne: التاب Off Folio. Sound على جهاز العرض بيضرب ومحدش شايف. `useWheelAudio` بيبقى للـ`AdminWheelPage` بس.
- **التحقق من الصوت: راجعوا** `sFanfare` بيقرا `brass()` بـ`L=.15` على 4 oscillators — هاد loud كفاية؟ مع `DynamicsCompressor` بيبقى معقول. مافي ملفات بصوت.

---

## 6. popup القرار — التحقق اليدوي

**الفري**

`WheelDecisionBar`:
- **القبول** — checkbox إجباري: "تأكدت من حضور الطالب يدوياً" → `POST {decision:"accepted", presence_verified: <bool>, confirmed: false}`.
- **الرفض** — نافذة تأكيد لـ**نفسها** (مش checkbox ثاني): "رفض <الاسم> نهائي؟ عم يتستبعد من **كل** التابات وما في رجعة." → `POST {decision:"rejected", presence_verified: false, confirmed: true}`.
- **الافتراضات**: `decision_requirements` بالرد = `{accept_requires_presence_verified: true, accept_requires_confirmation: false, reject_requires_presence_verified: false, reject_requires_confirmation: true}`.
- **قبل الإرسال**: `if (accept && !presence_verified) disable; if (reject && !confirmDialog) disable;` — الباك بيرجع 400/409 بأي حال، بس الـUI بيمنع قبلها.
- **الاسم بالـpopup**: كبير + الكود. "الفائز هو **سارة العمر** · `R-0011`". الكود بالأحرف الـmonospace.

---

## 7. لوحة التجميد — WheelFreezePanel

- يعرض `freeze_at` الحالي + `frozen: bool` + badge "مجمّد" أو "مفتوح".
- عند التغيير (date-time input) → **معاينة حيّة**: debounce 400ms → `GET /admin/wheel/settings?prospective_freeze_at=...` → بيعرض `delta` لكل تاب: `٤٥ (+٢)`.
- `delta` اخخر/احا حسا الاشار ي ال ماف حف.
- زر "احفظ" → `PUT` + `reason` (اختياري، حد 255). بعد الحفظ بيظهر بالـaudit.
- `min_allowed`/`max_allowed` بالرد — نافذة الـinput محدودة. نافذة الفعالية: من أول يوم فعالية 08:00 → السبت 16:00.
- **ما في countdown ولا lock** (بالمواصفة). بس الـbadge "مجمّد/مفتوح" نص ثابت.

---

## 8. الأرشيف وسجل الفائزين

- `WheelArchivePanel` = جدول: `#draw_id` | التاب (badge) | الاسم | الكود | `presence_verified` (✓/—) | وقت القبول.
- `status=accepted` بس (الباك بيرجّعها مجمّعة). مرتّبة بترتيب التابات ثم وقت القرار.
- **read-only** — مافي حذف ولا تعديل.
- بتصير بـtab ثالث تحت "سجل الفائزين"، لأن "سجل الفائزين" =(معنى "الأسماء") ولا = (حذف).

---

## 9. شاشة العرض — WheelLivePage

- Polling كل **2s** (`useWheelLive`) على `GET /wheel/live`.
- ٦ حقول بس. **ممنوع منعاً باتاً** إضافة أي حقل للـcomponent: أسماء المؤهلين، الدرجات، `freeze_at`، `frozen`، عدد السحوبات. الـBackend `LiveDrawResponse` بالضبط ٦ حقول — **مطابق**.
- حالة فراغ: **"في انتظار السحب…"** — مش شاشة سوداء.
- التسلسل: كارت كبير (اسم + كود + التاب + وقت) يظهر بـfade/scale بعد 600ms من الكشف. قبلها: "والفائز هو…".
- بعد ما القرار ينحسم: ضل الكارت (مش بيختفي). لأ حدا ما رح ينسى.
- `useWheelAudio` **مش** هون. CSS فقط — 3-4 breakpoints.
- `winner_code` بالأحرف الـmonospace. `revealed_at`/`tab_label` صغار تحت الاسم.
- **الدة:** أي ححاجل سجل حاك زهلة راسحا حً اي حسا ي ال رسي دال الت منج بلا سحارة الرار الي. مواع ساصر.

### 9.1 ملاحظة الـoffline — تنازل صريح

`ceremony_snapshot` + `idempotency_key` مكّنت **العرض** يشتغل offline (لقطة مخبّأة). **بس السحب ما بيقدر يشتغل offline** لأن **الباك هو يلي بيختار** (D4).

| بديل | التكلفة |
|---|---|
| ✅ **D4 (server-authority)** | السحب بدو شبكة. العرض بيضل شغال |
| ⬜ لو بدك السحب offline | لازم الفرونت يبعت الـboard والـBاك يتحقق منه — reintroduces client-authority، والمرحلة 4 بتخسر معناها |

**الافتراضي المطبّق: D4.** لو بدك السحب offline — قول، ودّيivo stage D4 وبقيد "لا بدو يوصل طلب للسيرفر".

---

## 10. الحالات (تحميل / فاضي / خطأ)

| الحالة | وين | الشكل |
|---|---|---|
| تحميل أول | `AdminWheelPage` | skeleton cards: 3abarat شفافة + "لحظة…" |
| تحميل تاب | تبديل التاب | الـboard القديم يضل + overlay خفيف؛ العجلة تبقى |
| pool فارغ | كل تاب | رسالة + **"ما في طلاب مؤهلون"** + شارت الصفر. الزر `disabled` |
| `wheel_tab_empty` 409 | الراوتر | نفس الرسالة (D3: ما بنعمل toast مزعج) |
| `wheel_pending_draw_exists` 409 | الراوتر | §5.6 — رجوع للـpopup |
| 403 دور غلط | `TeamPrivateRoute` | صفحة "ما عندك صلاحية" (موجودة بالـguard) |
| 409/400 قرار | `WheelDecisionBar` | toast + الـcheckbox يضل |
| fetch فاشل (syntax) | كل النداءات | toast + زر "أعد المحاولة" + آخر board متاح |
| انلطل العر ي | `WheelLivePage` | "انلع الا الصا الا "امر "انمر "اسالا "ي" | اخر الر |

`src/api/toast.js` موجود — نستعملو.

---

## 11. الاختبارات

### 11.1 `wheelGeometry.test.js` — الأهم

| # | الحالة |
|---|---|
| 1 | `pegIndex(center(i)) === i` لكل `i` من 0 لـ 99 (N=100) |
| 2 | `pegIndex(center(i) ± SLICE·0.25) === i` (الجريـr لا يخرج) |
| 3 | `pegIndex(rotation)` يطابق الرسم البصري: sector at angle `-π/2` بالـcanvas = القطاع تحت المؤشّر |
| 4 | بعد `spin()` محاكى بـfake timers: `pegIndex(rotation) === winnerSlot` |
| 5 | `N=1` ما يكسر (`SLICE=2π`)، `N=2`، `N=24` |
| 6 | `rotation` بعد الدوران ≥ `8·2π` (عدد الدورات) |

### 11.2 `useWheelPool.test.js`
- الـboard تطابق ترتيب الباك لـ`rank`؛ بعد أول سحب بتتبدّل (shuffle) وبترجع نفس الطول.
- `N` = `pool.length` دايماً — **مافي take** (D1).
- تبديل التاب = board تاني + إبدال`wheelCache`.

### 11.3 `AdminWheelPage.test.jsx`
- 4 تابات ظاهرة بترتيب `first, second, third, final` مع `eligible_count` + `criteria[]`.
- `N <= 24` → أسماء على الـcanvas؛ `N > 24` → بلا أسماء على الـcanvas + كل الأسماء بالقائمة.
- Press spin → نداء واحد `POST /admin/wheel/draws` بـ`idempotency_key` موجود.
- الرد `student_id` موجود بالـboard → السهم عليه (عبر `pegIndex`).
- `N=0` → `disabled` + رسالة.
- القبول بـ`presence_verified=false` → زر معطّل (**قبل** النداء).
- الرفض بلا نافذة التأكيد → معطّل.
- `wheel_pending_draw_exists` 409 → popup، بدون toast خطأ.

### 11.4 `WheelLivePage.test.jsx`
- يعرض الـ6 حقول بس — **assert على `Object.keys(body)`**.
- مافي `freeze_at` / `eligible_count` / أسماء مؤهلين بالـDOM (حتى بالـmock).
- فراغ → "في انتظار السحب…".
- polling كل 2s (fake timers).

### 11.5 `useWheelAudio.test.js`
- كتم بيوقف كل الـoscillators.
- `AudioContext` ما بينفتح قبل أول click (autoplay policy).
- الاختيار بينحفظ بـ`localStorage`.

### 11.6 E2E (Playwright)
- draw → decision → archive: 3 خطوات، `status=accepted` بالـarchive.
-Rejected → "أعد السحب" → جديد.
- تبديل التاب بيفصل الـboards.

---

## 12. Implementation order

1. **`lib/wheelGeometry.js` + اختباره.** (§5، بلا UI). هذا **D4-الأساس** — لو الـgeometry غلط، كل شي بعده غلط.
2. **`hooks/useWheelAudio.js`.** منقول كما هو. بلا اعتماديات UI.
3. **`api/wheel.js` + اختباره.** 8 دوال.
4. **`hooks/useWheelPool.js`.** الـboard + تبديل التاب + القوائم.
5. **`pages/Admin/wheel/WheelCanvas.jsx` + `WheelTabs.jsx`.** الرسم + 4 تابات.
6. **`hooks/useWheelSpin.js`.** الـstate machine + الهبوط (§5.3, §5.6).
7. **`WheelSpinButton.jsx` + `WheelRevealModal.jsx`.** المسار الكامل من الضغط للبطاقة.
8. **`WheelDecisionBar.jsx`.** التحقق اليدوي + قبول/رفض (§6).
9. **`WheelLivePage.jsx` + `useWheelLive.js`.** شاشة العرض.
10. **`AdminWheelPage.jsx`.** orchestrator + `/admin/wheel`.
11. **`WheelTabTable.jsx` + `WheelBoard.jsx`.** الجداول (D2 — ترتيب + ترشيح).
12. **`WheelFreezePanel.jsx` + `WheelArchivePanel.jsx`.** لوحات.
13. **الراوتر + `AdminHeader.jsx` + `/wheel/live`.** (§1)
14. **`npm run test:run` + `npm run lint` + `npm run build`.**

**قواعد:**
- كل phase: `test:run` أخضر قبل ما ننتقل.
- **`.jsx` plain**، بدون TS (الوضع الحالي).
- **oxlint** نظيف. `npm run build` أخضر.
- **لا تكسر** الـscanners/الـstudent/الـUniGate. الاختبارات القائمة لازم تضل خضراء.
- **مافيش مكتبات جديدة.** الصفر. Canvas + Web Audio أصليين. (D5.)

---

## 13. Open decisions

| # | السؤال | الافتراضي | بدّلو؟ |
|---|---|---|---|
| O1 | ترتيب الـboard | ترتيب الباك، shuffle بعد أول سحب | |
| O2 | كتابة أسماء التابات فوق الشاشة | نعم — فوق العجلة | ✅ |
| O3 | شو بصوت "أعد السحب"؟ | سحب كامل | ✅ |
| O4 | مؤقّت قبل السحب ("٣، ٢، ١")؟ | **لا** — بلا countdown بالمواصفة | |
| O5 | حد أدنى للـ`N` | **لا** حد أدنى — `N=1` شغّال | ما بصير |
| O6 | زر "ابدأ السحب" vs الدوّر centrally | الاثنين، زي الـprototype | |
| O7 | `WheelLivePage` والمسار العام | `/wheel/live` | |
| O8 | الصوت default | **على** (مع زر كتم كبير) | |

---

## 14. Out of scope — لا تعمل هيك

- ❌ **تعديل الـbackend** — خلص. `decide_dated` مش مفعل عمداً (D5→ server-authority). أي تعديل = إعادة تفاوض.
- ❌ **staff/realtime** — الـdraws `revealed` بـpoll كل 2s. مافي WebSocket. الباك ما عامله.
- ❌ **الطالب بيلعب بنفسه** — الـprototype كان هيك. حُذف. `AdminWheelPage` role = super_admin.
- ❌ **إعادة ضبط يومية** — الـprototype كان عنده. حُذف. مرّة وحدة.
- ❌ **أسماء الجوائز** — ما في. التابات ما عندها prizes.
- ❌ **QR/codes** — ما في QR بالعجلة. الكود نص.
- ❌ **مكتبات جديدة** — canvas + Web Audio.
- ❌ **`localStorage` للـsnapshot التالف** — الآمن: snapshotمؤجت في الذاكرة.
- ❌ **تعديل `api.js`/`App.css`** العام — الإضافة بس.
- ❌ **ترجمة عربية/إنجليزية** — الموقع عربي بالكامل.
- ❌ **عدم تعديل `point_service`** — 🚫 **ممنوع منعاً باتاً** — العجلة تقرأ فقط.
