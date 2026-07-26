import { fmt } from "../format.js";
import IsoView from "./IsoView.jsx";

const COL_W = 230;
const ROW_H = 250;
const CARD_W = 210;
const CARD_H = 230;

function layoutOptions(options) {
  const byParent = new Map();
  const roots = [];
  for (const option of options) {
    if (option.parent_id) {
      const list = byParent.get(option.parent_id) ?? [];
      list.push(option);
      byParent.set(option.parent_id, list);
    } else {
      roots.push(option);
    }
  }
  const cells = [];
  const links = [];
  let nextRow = -1;
  function walk(option, row, col) {
    cells.push({ option, row, col });
    const children = byParent.get(option.id) ?? [];
    children.forEach((child, index) => {
      if (index === 0) {
        links.push({ fromRow: row, fromCol: col, toRow: row, toCol: col + 1 });
        walk(child, row, col + 1);
      } else {
        nextRow += 1;
        const childRow = nextRow;
        links.push({ fromRow: row, fromCol: col, toRow: childRow, toCol: col });
        walk(child, childRow, col);
      }
    });
  }
  for (const root of roots) {
    nextRow += 1;
    walk(root, nextRow, 0);
  }
  return { cells, links, rows: nextRow + 1 };
}

export default function Board({ options, onOpen, compareIds, onToggleCompare }) {
  const { cells, links, rows } = layoutOptions(options);
  const cols = Math.max(...cells.map((cell) => cell.col)) + 1;
  const width = cols * COL_W + 40;
  const height = rows * ROW_H + 20;

  return (
    <div className="board-scroll">
      <div className="board" style={{ width, height }}>
        <svg className="board-links" width={width} height={height}>
          {links.map((link, index) => {
            if (link.fromRow === link.toRow) {
              const y = link.fromRow * ROW_H + CARD_H / 2;
              return <line key={index} x1={link.fromCol * COL_W + CARD_W} y1={y} x2={link.toCol * COL_W} y2={y} />;
            }
            const x = link.fromCol * COL_W + CARD_W / 2;
            return <line key={index} x1={x} y1={link.fromRow * ROW_H + CARD_H} x2={x} y2={link.toRow * ROW_H} />;
          })}
        </svg>
        {cells.map(({ option, row, col }, index) => (
          <div
            key={option.id}
            className={`card${compareIds.includes(option.id) ? " selected" : ""}`}
            style={{ left: col * COL_W, top: row * ROW_H }}
          >
            <div className="card-title">{option.name || `Вариант ${index + 1}`}</div>
            <IsoView result={option.result} width={CARD_W - 16} height={110} />
            <div className="card-metrics">
              <span>GFA {fmt(option.result.metrics.gfa_m2)} м²</span>
              <span>
                зданий: {option.result.metrics.building_count} · выс. {fmt(option.result.metrics.max_height_m)} м
              </span>
              <span>
                покрытие {fmt(option.result.metrics.coverage, 2)} · FAR {fmt(option.result.metrics.far, 2)}
              </span>
            </div>
            <div className="card-actions">
              <button type="button" onClick={() => onOpen(option)}>
                Открыть
              </button>
              <label>
                <input
                  type="checkbox"
                  checked={compareIds.includes(option.id)}
                  onChange={() => onToggleCompare(option.id)}
                />
                сравнить
              </label>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
