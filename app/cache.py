"""
ذاكرة تخزين مؤقتة بسيطة (in-process, TTL) لنتائج الاستعلامات الثقيلة
(presence / peak-hours / top-students). لا اعتماد خارجي — dict + قفل + طوابع زمنية.

الاستخدام:
    value = cached_call("presence:all", ttl_seconds=300, factory=lambda: compute_presence(db))
"""

import threading
import time
from typing import Any, Callable

_cache: dict[str, tuple[float, Any]] = {}
_lock = threading.Lock()


def cached_call(key: str, ttl_seconds: int, factory: Callable[[], Any]) -> Any:
    """
    يرجع القيمة المخزنة إن كانت ما تزال طازجة (ضمن ttl_seconds)، وإلا يحسبها
    عبر factory ويخزّنها ويعيدها. لا يخزّن القيم الفاشلة (الاستثناء يخرج مباشرة).
    """
    now = time.time()
    with _lock:
        entry = _cache.get(key)
        if entry is not None and now - entry[0] < ttl_seconds:
            return entry[1]

    value = factory()

    with _lock:
        _cache[key] = (now, value)
    return value


def clear_cache() -> None:
    """إفراغ الذاكرة المؤقتة بالكامل — للاختبارات ولأي إعادة ضبط يدوية."""
    with _lock:
        _cache.clear()