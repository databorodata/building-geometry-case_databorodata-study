import { useEffect, useRef, useState } from "react";
import { previewMassing } from "../api.js";
import { fmt } from "../format.js";
import ThreeView from "./ThreeView.jsx";

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function MetricRow({ label, value }) {
  return (
    <div className="metric-row">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function SliderRow({ label, min, max, step, value, disabled, unit, onChange }) {
  return (
    <label className={`slider-row${disabled ? " disabled" : ""}`}>
      <span className="slider-label">{label}</span>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        disabled={disabled}
        onChange={(event) => onChange(Number(event.target.value))}
      />
      <span className="slider-value">
        {fmt(value)} {unit}
      </span>
      <span className="slider-range">
        {fmt(min)}…{fmt(max)}
      </span>
    </label>
  );
}

export default function Editor({ site, option, onSave, onClose }) {
  const [params, setParams] = useState(() => clone(option.params));
  const [result, setResult] = useState(option.result);
  const [selection, setSelection] = useState({ type: "ensemble" });
  const [name, setName] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const seqRef = useRef(0);
  const skipRef = useRef(false);

  useEffect(() => {
    skipRef.current = true;
    setParams(clone(option.params));
    setResult(option.result);
    setSelection({ type: "ensemble" });
  }, [option.id]);

  useEffect(() => {
    if (skipRef.current) {
      skipRef.current = false;
      return;
    }
    const seq = seqRef.current + 1;
    seqRef.current = seq;
    const timer = setTimeout(async () => {
      try {
        const res = await previewMassing(site.polygon, params);
        if (seq !== seqRef.current) return;
        skipRef.current = true;
        setParams(res.params);
        setResult(res.result);
        setError(null);
      } catch (err) {
        setError(err.message);
      }
    }, 150);
    return () => clearTimeout(timer);
  }, [params]);

  function update(mutate) {
    const next = clone(params);
    mutate(next);
    setParams(next);
  }

  async function handleSave(kind) {
    setSaving(true);
    setError(null);
    try {
      await onSave(option, name.trim() || null, params, kind);
      setName("");
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  const buildings = result.buildings ?? [];
  let active = selection;
  if (active.type !== "ensemble" && !buildings[active.building]) active = { type: "ensemble" };
  if (active.type === "floor" && !buildings[active.building]?.floors[active.floor]) {
    active = { type: "building", building: active.building };
  }
  const highlight =
    active.type === "ensemble"
      ? null
      : { building: active.building, floor: active.type === "floor" ? active.floor : undefined };

  const lockedBuildings = params.buildings
    .map((building, index) => (building.locked ? index + 1 : null))
    .filter(Boolean);
  const activeBuilding = active.type === "ensemble" ? null : params.buildings[active.building];
  const heightLockedFloors = activeBuilding
    ? activeBuilding.floors.map((floor, index) => (floor.height_locked ? index + 1 : null)).filter(Boolean)
    : [];
  const contourLockedFloors = activeBuilding
    ? activeBuilding.floors.map((floor, index) => (floor.contour_locked ? index + 1 : null)).filter(Boolean)
    : [];

  return (
    <div className="modal-backdrop">
      <div className="modal editor">
        <div className="editor-header">
          <h2>Редактор варианта</h2>
          <button type="button" onClick={onClose}>
            Закрыть
          </button>
        </div>
        <div className="editor-body">
          <div className="level-tree">
            <button
              type="button"
              className={active.type === "ensemble" ? "level active" : "level"}
              onClick={() => setSelection({ type: "ensemble" })}
            >
              Ансамбль
            </button>
            {buildings.map((building, b) => (
              <div key={b}>
                <button
                  type="button"
                  className={active.type === "building" && active.building === b ? "level active" : "level"}
                  onClick={() => setSelection({ type: "building", building: b })}
                >
                  Здание {b + 1}
                  {params.buildings[b]?.locked ? " 🔒" : ""}
                </button>
                {building.floors.map((_, f) => (
                  <button
                    key={f}
                    type="button"
                    className={
                      active.type === "floor" && active.building === b && active.floor === f
                        ? "level floor active"
                        : "level floor"
                    }
                    onClick={() => setSelection({ type: "floor", building: b, floor: f })}
                  >
                    Этаж {f + 1}
                    {params.buildings[b]?.floors[f]?.height_locked || params.buildings[b]?.floors[f]?.contour_locked
                      ? " 🔒"
                      : ""}
                  </button>
                ))}
              </div>
            ))}
          </div>

          <div className="views">
            <ThreeView result={result} width={430} height={430} highlight={highlight} />
            <p className="hint">Вращайте мышью, колесо — масштаб</p>
            {result.status === "empty" && <p className="error">Отступ схлопнул участок</p>}
          </div>

          <div className="controls">
            {active.type === "ensemble" && (
              <>
                <h3>Ансамбль</h3>
                <SliderRow
                  label="Отступ"
                  min={0}
                  max={result.max_setback_m}
                  step={0.1}
                  value={params.setback_m}
                  unit="м"
                  disabled={lockedBuildings.length > 0}
                  onChange={(value) => update((p) => (p.setback_m = value))}
                />
                {lockedBuildings.length > 0 && (
                  <p className="hint">
                    Отступ заблокирован. Чтобы менять его, снимите «Зафиксировать здание»:{" "}
                    {lockedBuildings.map((number) => `Здание ${number}`).join(", ")}.
                  </p>
                )}
                <label className="target-row">
                  Цель GFA, м²
                  <input
                    type="number"
                    min="0"
                    value={params.gfa_target_m2 ?? ""}
                    onChange={(event) =>
                      update((p) => (p.gfa_target_m2 = event.target.value === "" ? null : Number(event.target.value)))
                    }
                  />
                </label>
                <p className="hint">GFA — суммарная площадь всех этажей всех зданий. Введите цель, чтобы проверить, достижима ли она.</p>
                {result.gfa_check && (
                  <p className={result.gfa_check.reachable ? "gfa-ok" : "gfa-bad"}>
                    {result.gfa_check.reachable ? "🟢 достижима" : "🔴 недостижима"} — возможный диапазон{" "}
                    {fmt(result.gfa_check.min_possible_m2)}…{fmt(result.gfa_check.max_possible_m2)} м²
                  </p>
                )}
                <MetricRow label="Площадь участка" value={`${fmt(result.metrics.site_area_m2)} м²`} />
                <MetricRow label="Застраиваемая площадь" value={`${fmt(result.metrics.buildable_area_m2)} м²`} />
                <MetricRow label="Пятно застройки" value={`${fmt(result.metrics.footprint_area_m2)} м²`} />
                <MetricRow label="GFA" value={`${fmt(result.metrics.gfa_m2)} м²`} />
                <MetricRow label="Объём" value={`${fmt(result.metrics.volume_m3)} м³`} />
                <MetricRow label="Покрытие" value={fmt(result.metrics.coverage, 3)} />
                <MetricRow label="FAR" value={fmt(result.metrics.far, 3)} />
                <MetricRow label="Макс. высота" value={`${fmt(result.metrics.max_height_m)} м`} />
                <MetricRow label="Зданий" value={result.metrics.building_count} />
              </>
            )}

            {active.type === "building" && (
              <>
                <h3>Здание {active.building + 1}</h3>
                <SliderRow
                  label="Общая высота"
                  min={2.3}
                  max={24}
                  step={0.1}
                  value={buildings[active.building].height_m}
                  unit="м"
                  disabled={heightLockedFloors.length > 0}
                  onChange={(value) => update((p) => (p.buildings[active.building].total_height_m = value))}
                />
                {heightLockedFloors.length > 0 && (
                  <p className="hint">
                    Высота заблокирована. Снимите «Зафиксировать высоту»:{" "}
                    {heightLockedFloors.map((number) => `Этаж ${number}`).join(", ")}.
                  </p>
                )}
                <SliderRow
                  label="Площадь контура"
                  min={buildings[active.building].min_contour_area_m2}
                  max={buildings[active.building].island_area_m2}
                  step={1}
                  value={buildings[active.building].contour_area_m2}
                  unit="м²"
                  disabled={contourLockedFloors.length > 0}
                  onChange={(value) => update((p) => (p.buildings[active.building].contour_area_m2 = value))}
                />
                {contourLockedFloors.length > 0 && (
                  <p className="hint">
                    Контур заблокирован. Снимите «Зафиксировать контур»:{" "}
                    {contourLockedFloors.map((number) => `Этаж ${number}`).join(", ")}.
                  </p>
                )}
                <label className="lock-row">
                  <input
                    type="checkbox"
                    checked={params.buildings[active.building].locked}
                    onChange={(event) => update((p) => (p.buildings[active.building].locked = event.target.checked))}
                  />
                  Зафиксировать здание (блокирует отступ участка)
                </label>
                <MetricRow label="Этажей" value={buildings[active.building].floor_count} />
                <MetricRow label="Высота" value={`${fmt(buildings[active.building].height_m)} м`} />
                <MetricRow label="GFA здания" value={`${fmt(buildings[active.building].gfa_m2)} м²`} />
                <MetricRow label="Объём" value={`${fmt(buildings[active.building].volume_m3)} м³`} />
                <MetricRow label="Контур" value={`${fmt(buildings[active.building].contour_area_m2)} м²`} />
              </>
            )}

            {active.type === "floor" && (
              <>
                <h3>
                  Здание {active.building + 1} — этаж {active.floor + 1}
                </h3>
                <SliderRow
                  label="Высота этажа"
                  min={2.3}
                  max={4.6}
                  step={0.1}
                  value={buildings[active.building].floors[active.floor].height_m}
                  unit="м"
                  disabled={params.buildings[active.building].floors[active.floor].height_locked}
                  onChange={(value) => update((p) => (p.buildings[active.building].floors[active.floor].height_m = value))}
                />
                <SliderRow
                  label="Доля пятна"
                  min={0.5}
                  max={1}
                  step={0.01}
                  value={params.buildings[active.building].floors[active.floor].area_ratio}
                  unit=""
                  disabled={params.buildings[active.building].floors[active.floor].contour_locked}
                  onChange={(value) =>
                    update((p) => (p.buildings[active.building].floors[active.floor].area_ratio = value))
                  }
                />
                <label className="lock-row">
                  <input
                    type="checkbox"
                    checked={params.buildings[active.building].floors[active.floor].height_locked}
                    onChange={(event) =>
                      update((p) => (p.buildings[active.building].floors[active.floor].height_locked = event.target.checked))
                    }
                  />
                  Зафиксировать высоту (блокирует высоту здания)
                </label>
                <label className="lock-row">
                  <input
                    type="checkbox"
                    checked={params.buildings[active.building].floors[active.floor].contour_locked}
                    onChange={(event) =>
                      update((p) => (p.buildings[active.building].floors[active.floor].contour_locked = event.target.checked))
                    }
                  />
                  Зафиксировать контур (блокирует контур здания)
                </label>
                <MetricRow label="Площадь" value={`${fmt(buildings[active.building].floors[active.floor].area_m2)} м²`} />
                <MetricRow label="Объём" value={`${fmt(buildings[active.building].floors[active.floor].volume_m3)} м³`} />
                <MetricRow label="Отметка" value={`${fmt(buildings[active.building].floors[active.floor].level_m)} м`} />
              </>
            )}
          </div>
        </div>
        <div className="editor-footer">
          {error && <span className="error">{error}</span>}
          <input
            placeholder="Имя новой карточки (необязательно)"
            value={name}
            onChange={(event) => setName(event.target.value)}
          />
          <button type="button" className="primary" disabled={saving} onClick={() => handleSave("save")}>
            {saving ? "Сохраняем…" : "Сохранить"}
          </button>
          <button type="button" disabled={saving} onClick={() => handleSave("fork")}>
            Скопировать в ветку
          </button>
        </div>
      </div>
    </div>
  );
}
