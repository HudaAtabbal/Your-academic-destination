import React, { useState, useRef, useCallback, useEffect } from 'react';
import HeaderStep from '../../components/HeaderStep';
import BottomNav from '../../components/BottomNav';
import { MAP_BUILDINGS } from '../../api/mapData';
import '../../style/UniversityMap.css';

// خريطة الجامعة التفاعلية — مسطحة 2D بالكامل:
// - hotspots غير مرئية فوق نصوص الكليات فقط
// - السحب والتكبير عبر DOM مباشرة (بدون إعادة رسم React)
// - أسماء البوابات برّا حدود صورة الخريطة بجانب كل سهم
const MapPage = () => {
  const [selected, setSelected] = useState(null);
  const [showReset, setShowReset] = useState(false);
  const viewportRef = useRef(null);
  const stageRef = useRef(null);
  const canvasRef = useRef(null);
  const tr = useRef({ scale: 1, x: 0, y: 0 });
  const drag = useRef(null);
  const pinch = useRef(null);
  const dragged = useRef(false);
  const rafRef = useRef(0);
  const sheetOpenRef = useRef(false);
  const sheetDrag = useRef(null);
  const sheetRef = useRef(null);

  const clamp = useCallback((value, min, max) => Math.min(Math.max(value, min), max), []);

  const clampT = useCallback(
    (next) => {
      const vp = viewportRef.current;
      const stage = stageRef.current;
      if (!vp || !stage) return next;
      const scale = clamp(next.scale, 1, 4);
      const baseMaxX = Math.max(0, (stage.offsetWidth * scale - vp.clientWidth) / 2);
      const baseMaxY = Math.max(0, (stage.offsetHeight * scale - vp.clientHeight) / 2);
      const slackY = sheetOpenRef.current ? vp.clientHeight * 0.55 : 56;
      const maxX = Math.max(baseMaxX, 24);
      const maxY = Math.max(baseMaxY, slackY);
      return {
        scale,
        x: clamp(next.x, -maxX, maxX),
        y: clamp(next.y, -maxY, maxY),
      };
    },
    [clamp],
  );

  // رسم مباشر على DOM — بدون setState أثناء السحب، وبلا أي منظور 3D
  const paint = useCallback(
    (next, animate = false) => {
      const t = clampT(next);
      tr.current = t;
      const el = canvasRef.current;
      if (el) {
        if (animate) el.classList.add('um-map-canvas--animate');
        else el.classList.remove('um-map-canvas--animate');
        el.style.transform = `translate(${t.x}px, ${t.y}px) scale(${t.scale})`;
      }
      const shouldShow = t.scale > 1.01;
      setShowReset((prev) => (prev === shouldShow ? prev : shouldShow));
    },
    [clampT],
  );

  const schedulePaint = useCallback(
    (next, animate = false) => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      rafRef.current = requestAnimationFrame(() => {
        rafRef.current = 0;
        paint(next, animate);
      });
    },
    [paint],
  );

  useEffect(() => {
    const vp = viewportRef.current;
    if (!vp) return undefined;
    const onWheel = (e) => {
      e.preventDefault();
      const rect = vp.getBoundingClientRect();
      const cx = e.clientX - rect.left - rect.width / 2;
      const cy = e.clientY - rect.top - rect.height / 2;
      const prev = tr.current;
      const dir = e.deltaY > 0 ? -1 : 1;
      const target = clamp(prev.scale + dir * 0.15, 1, 4);
      if (target === prev.scale) {
        paint({ ...prev, x: prev.x - e.deltaX, y: prev.y - e.deltaY });
        return;
      }
      const ratio = target / prev.scale;
      paint({
        scale: target,
        x: cx - (cx - prev.x) * ratio,
        y: cy - (cy - prev.y) * ratio,
      });
    };
    vp.addEventListener('wheel', onWheel, { passive: false });
    return () => {
      vp.removeEventListener('wheel', onWheel);
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [clamp, paint]);

  const beginDrag = (clientX, clientY) => {
    drag.current = {
      startX: clientX,
      startY: clientY,
      originX: tr.current.x,
      originY: tr.current.y,
    };
    dragged.current = false;
  };

  const moveDrag = (clientX, clientY) => {
    if (!drag.current) return;
    const dx = clientX - drag.current.startX;
    const dy = clientY - drag.current.startY;
    if (!dragged.current) {
      if (Math.hypot(dx, dy) < 4) return;
      dragged.current = true;
    }
    schedulePaint({
      scale: tr.current.scale,
      x: drag.current.originX + dx,
      y: drag.current.originY + dy,
    });
  };

  const endDrag = () => {
    drag.current = null;
    pinch.current = null;
  };

  const handleMouseDown = (e) => {
    if (e.button !== 0) return;
    beginDrag(e.clientX, e.clientY);
    try {
      e.currentTarget.setPointerCapture(e.pointerId);
    } catch {
      /* ignore */
    }
  };

  const handleMouseMove = (e) => {
    if (!drag.current || pinch.current) return;
    moveDrag(e.clientX, e.clientY);
  };

  const handleTouchStart = (e) => {
    if (e.touches.length === 2) {
      drag.current = null;
      const dist = Math.hypot(
        e.touches[0].clientX - e.touches[1].clientX,
        e.touches[0].clientY - e.touches[1].clientY,
      );
      pinch.current = { dist, scale: tr.current.scale };
      dragged.current = true;
    } else if (e.touches.length === 1) {
      beginDrag(e.touches[0].clientX, e.touches[0].clientY);
    }
  };

  const handleTouchMove = (e) => {
    if (e.touches.length === 2 && pinch.current) {
      e.preventDefault();
      const dist = Math.hypot(
        e.touches[0].clientX - e.touches[1].clientX,
        e.touches[0].clientY - e.touches[1].clientY,
      );
      const ratio = dist / pinch.current.dist;
      schedulePaint({ ...tr.current, scale: pinch.current.scale * ratio });
    } else if (e.touches.length === 1) {
      moveDrag(e.touches[0].clientX, e.touches[0].clientY);
    }
  };

  const resetZoom = () => {
    paint({ scale: 1, x: 0, y: 0 }, true);
  };

  const openSpot = (spot) => {
    if (dragged.current) return;
    sheetOpenRef.current = true;
    const vp = viewportRef.current;
    const stage = stageRef.current;
    if (vp && stage) {
      const s = tr.current.scale;
      const wx = stage.offsetWidth * (spot.x / 100) * s;
      const wy = stage.offsetHeight * (spot.y / 100) * s;
      paint({ scale: s, x: vp.clientWidth / 2 - wx, y: vp.clientHeight * 0.26 - wy }, true);
    }
    setSelected(spot);
  };

  const closeSheet = () => {
    sheetOpenRef.current = false;
    setSelected(null);
    paint(tr.current, true);
  };

  const handleSheetPointerDown = (e) => {
    sheetDrag.current = { startY: e.clientY, dy: 0 };
    try {
      e.currentTarget.setPointerCapture(e.pointerId);
    } catch {
      /* ignore */
    }
  };

  const handleSheetPointerMove = (e) => {
    if (!sheetDrag.current) return;
    const dy = Math.max(0, e.clientY - sheetDrag.current.startY);
    sheetDrag.current.dy = dy;
    const el = sheetRef.current;
    if (el) {
      el.classList.remove('um-sheet--animating');
      el.style.transform = `translateY(${dy}px)`;
    }
  };

  const handleSheetPointerUp = () => {
    if (!sheetDrag.current) return;
    const { dy } = sheetDrag.current;
    sheetDrag.current = null;
    const el = sheetRef.current;
    if (dy > 80) {
      closeSheet();
    } else if (el) {
      el.classList.add('um-sheet--animating');
      el.style.transform = '';
    }
  };

  const gates = MAP_BUILDINGS.filter((s) => s.type === 'gate');

  return (
    <div className="ag-card-wrapper">
      <div className="ag-card-container">
        <HeaderStep title="خريطة الجامعة" stepText="طريقك إلى الكلية" />

        <main
          className="um-map-viewport"
          ref={viewportRef}
          onTouchStart={handleTouchStart}
          onTouchMove={handleTouchMove}
          onTouchEnd={endDrag}
          onTouchCancel={endDrag}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={endDrag}
          onMouseLeave={endDrag}
        >
          <div className="um-map-canvas" ref={canvasRef}>
            <div className="um-map-stage" ref={stageRef}>
              <img
                src="/university-map.jpg"
                alt="خريطة الجامعة"
                className="um-map-image"
                draggable={false}
              />

              {MAP_BUILDINGS.map((spot) => (
                <button
                  key={spot.id}
                  type="button"
                  className={`um-hotspot${selected?.id === spot.id ? ' um-hotspot--open' : ''}`}
                  style={{
                    left: `${spot.x}%`,
                    top: `${spot.y}%`,
                    width: `${spot.w ?? 12}%`,
                    height: `${spot.h ?? 10}%`,
                  }}
                  onClick={(e) => {
                    e.stopPropagation();
                    openSpot(spot);
                  }}
                  aria-label={spot.name}
                />
              ))}

              {gates.map((gate) => (
                <button
                  key={`lbl-${gate.id}`}
                  type="button"
                  className={`um-gate-label um-gate-label--${gate.side}`}
                  style={
                    gate.side === 'right'
                      ? { left: `${gate.x + gate.w / 2}%`, top: `${gate.y}%` }
                      : { top: `${gate.y + gate.h / 2}%`, left: `${gate.x}%` }
                  }
                  onClick={(e) => {
                    e.stopPropagation();
                    openSpot(gate);
                  }}
                >
                  {gate.name}
                </button>
              ))}
            </div>
          </div>

          {showReset && (
            <button type="button" className="um-reset-zoom" onClick={resetZoom} aria-label="إعادة التكبير">
              ⟲
            </button>
          )}
        </main>

        {selected && (
          <>
            <div className="um-sheet-backdrop" onClick={closeSheet} role="presentation" />
            <div
              className="um-sheet"
              role="dialog"
              aria-modal="true"
              aria-label={selected.name}
              ref={sheetRef}
            >
              <div
                className="um-sheet-handle"
                onPointerDown={handleSheetPointerDown}
                onPointerMove={handleSheetPointerMove}
                onPointerUp={handleSheetPointerUp}
                onPointerCancel={handleSheetPointerUp}
              />
              <div className="um-sheet-header">
                <h3 className={`um-sheet-title${selected.featured ? ' um-sheet-title--featured' : ''}`}>
                  {selected.name}
                </h3>
                <button type="button" className="um-sheet-close" onClick={closeSheet} aria-label="إغلاق">
                  ✕
                </button>
              </div>

              {selected.colleges?.length > 0 && (
                <ul className="um-sheet-list">
                  {selected.colleges.map((college) => (
                    <li key={college} className="um-sheet-item">
                      {college}
                    </li>
                  ))}
                </ul>
              )}

              {selected.description && <p className="um-sheet-desc">{selected.description}</p>}

              {selected.groups?.map((group) => (
                <div key={group.name} className="um-sheet-group">
                  <h4 className="um-sheet-group-title">{group.name}</h4>
                  <ul className="um-sheet-list">
                    {group.items.map((item) => (
                      <li key={item} className="um-sheet-item um-sheet-item--sub">
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}

              {!selected.description && !selected.colleges?.length && !selected.groups?.length && (
                <p className="um-sheet-desc">
                  {selected.type === 'gate' ? 'بوابة مدخل الجامعة' : 'مكان على خريطة الجامعة'}
                </p>
              )}
            </div>
          </>
        )}

        <BottomNav />
      </div>
    </div>
  );
};

export default MapPage;
