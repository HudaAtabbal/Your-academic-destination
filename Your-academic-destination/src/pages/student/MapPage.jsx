import React, { useState, useRef, useCallback } from 'react';
import HeaderStep from '../../components/HeaderStep';
import BottomNav from '../../components/BottomNav';
import { MAP_BUILDINGS } from '../../api/mapData';
import '../../style/UniversityMap.css';

// خريطة الجامعة التفاعلية:
// - عرض الصورة مع إمكانية التكبير/التحريك (pinch + drag)
// - hotspots فوق المباني (دائرة) والبوابات (سهم أخضر)
// - ضغطة على أي نقطة تفتح bottom-sheet بالاسم + الوصف + الكليات
const MapPage = () => {
  const [selected, setSelected] = useState(null);
  const [transform, setTransform] = useState({ scale: 1, x: 0, y: 0 });
  const dragState = useRef(null);
  const pinchState = useRef(null);
  const containerRef = useRef(null);

  const clamp = useCallback((value, min, max) => Math.min(Math.max(value, min), max), []);

  const clampTransform = useCallback(
    (next) => {
      const maxOffset = ((next.scale - 1) * 400);
      return {
        scale: clamp(next.scale, 1, 4),
        x: clamp(next.x, -maxOffset, maxOffset),
        y: clamp(next.y, -maxOffset, maxOffset),
      };
    },
    [clamp],
  );

  const handlePointerDown = (e) => {
    if (e.isPrimary && e.pointerType === 'mouse') {
      dragState.current = { startX: e.clientX, startY: e.clientY, originX: transform.x, originY: transform.y };
      e.currentTarget.setPointerCapture(e.pointerId);
    }
  };

  const handlePointerMove = (e) => {
    if (!dragState.current) return;
    const dx = e.clientX - dragState.current.startX;
    const dy = e.clientY - dragState.current.startY;
    setTransform((prev) => clampTransform({ ...prev, x: dragState.current.originX + dx, y: dragState.current.originY + dy }));
  };

  const handlePointerUp = () => {
    dragState.current = null;
  };

  const handleWheel = (e) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? -0.2 : 0.2;
    setTransform((prev) => clampTransform({ ...prev, scale: prev.scale + delta }));
  };

  const handleTouchStart = (e) => {
    if (e.touches.length === 2) {
      const dist = Math.hypot(
        e.touches[0].clientX - e.touches[1].clientX,
        e.touches[0].clientY - e.touches[1].clientY,
      );
      pinchState.current = { dist, scale: transform.scale };
    } else if (e.touches.length === 1) {
      dragState.current = {
        startX: e.touches[0].clientX,
        startY: e.touches[0].clientY,
        originX: transform.x,
        originY: transform.y,
      };
    }
  };

  const handleTouchMove = (e) => {
    if (e.touches.length === 2 && pinchState.current) {
      e.preventDefault();
      const dist = Math.hypot(
        e.touches[0].clientX - e.touches[1].clientX,
        e.touches[0].clientY - e.touches[1].clientY,
      );
      const ratio = dist / pinchState.current.dist;
      setTransform((prev) => clampTransform({ ...prev, scale: pinchState.current.scale * ratio }));
    } else if (e.touches.length === 1 && dragState.current && transform.scale > 1) {
      const dx = e.touches[0].clientX - dragState.current.startX;
      const dy = e.touches[0].clientY - dragState.current.startY;
      setTransform((prev) => clampTransform({ ...prev, x: dragState.current.originX + dx, y: dragState.current.originY + dy }));
    }
  };

  const handleTouchEnd = () => {
    pinchState.current = null;
    dragState.current = null;
  };

  const resetZoom = () => setTransform({ scale: 1, x: 0, y: 0 });

  const closeSheet = () => setSelected(null);

  return (
    <div className="ag-card-wrapper">
      <div className="ag-card-container">
        <HeaderStep title="خريطة الجامعة" stepText="طريقك إلى الكلية" />

        <main
          className="um-map-viewport"
          ref={containerRef}
          onWheel={handleWheel}
          onTouchStart={handleTouchStart}
          onTouchMove={handleTouchMove}
          onTouchEnd={handleTouchEnd}
          onMouseDown={handlePointerDown}
          onMouseMove={handlePointerMove}
          onMouseUp={handlePointerUp}
          onMouseLeave={handlePointerUp}
        >
          <div
            className="um-map-canvas"
            style={{
              transform: `translate(${transform.x}px, ${transform.y}px) scale(${transform.scale})`,
            }}
          >
            <img src="/university-map.jpg" alt="خريطة الجامعة" className="um-map-image" draggable={false} />

            {MAP_BUILDINGS.map((spot) => (
              <button
                key={spot.id}
                type="button"
                className={`um-hotspot um-hotspot--${spot.type}${spot.featured ? ' um-hotspot--featured' : ''}`}
                style={{ left: `${spot.x}%`, top: `${spot.y}%` }}
                onClick={(e) => {
                  e.stopPropagation();
                  setSelected(spot);
                }}
                aria-label={spot.name}
              >
                {spot.type === 'gate' ? (
                  <svg viewBox="0 0 24 24" className="um-hotspot-arrow" aria-hidden="true">
                    <polygon points="4,12 20,4 20,20" fill="currentColor" />
                  </svg>
                ) : (
                  <span className="um-hotspot-dot" />
                )}
              </button>
            ))}
          </div>

          {transform.scale > 1 && (
            <button type="button" className="um-reset-zoom" onClick={resetZoom} aria-label="إعادة التكبير">
              ⟲
            </button>
          )}
        </main>

        {selected && (
          <>
            <div className="um-sheet-backdrop" onClick={closeSheet} role="presentation" />
            <div className="um-sheet" role="dialog" aria-modal="true" aria-label={selected.name}>
              <div className="um-sheet-handle" />
              <div className="um-sheet-header">
                <h3 className={`um-sheet-title${selected.featured ? ' um-sheet-title--featured' : ''}`}>
                  {selected.name}
                </h3>
                <button type="button" className="um-sheet-close" onClick={closeSheet} aria-label="إغلاق">
                  ✕
                </button>
              </div>

              {selected.description && <p className="um-sheet-desc">{selected.description}</p>}

              {selected.colleges?.length > 0 && (
                <ul className="um-sheet-list">
                  {selected.colleges.map((college) => (
                    <li key={college} className="um-sheet-item">
                      {college}
                    </li>
                  ))}
                </ul>
              )}

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

              {selected.type === 'gate' && !selected.description && !selected.colleges?.length && (
                <p className="um-sheet-desc">بوابة من مداخل الجامعة</p>
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
