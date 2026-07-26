import { fmt, fmtDelta } from "../format.js";

const ROWS = [
  ["Пятно застройки, м²", "footprint_area_m2", 1],
  ["GFA, м²", "gfa_m2", 1],
  ["Объём, м³", "volume_m3", 1],
  ["Покрытие", "coverage", 3],
  ["FAR", "far", 3],
  ["Макс. высота, м", "max_height_m", 1],
  ["Зданий", "building_count", 0],
];

export default function CompareModal({ comparison, onClose }) {
  return (
    <div className="modal-backdrop">
      <div className="modal compare">
        <div className="editor-header">
          <h2>Сравнение вариантов</h2>
          <button type="button" onClick={onClose}>
            Закрыть
          </button>
        </div>
        <table className="compare-table">
          <thead>
            <tr>
              <th>Метрика</th>
              <th>{comparison.left.name || "Первый"}</th>
              <th>{comparison.right.name || "Второй"}</th>
              <th>Разница</th>
            </tr>
          </thead>
          <tbody>
            {ROWS.map(([label, key, digits]) => (
              <tr key={key}>
                <td>{label}</td>
                <td>{fmt(comparison.left.metrics[key], digits)}</td>
                <td>{fmt(comparison.right.metrics[key], digits)}</td>
                <td>{fmtDelta(comparison.delta[key], digits)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
