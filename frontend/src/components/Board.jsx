import { fmt } from "../format.js";
import IsoView from "./IsoView.jsx";

const COL_W = 250;
const ROW_H = 260;
const CARD_W = 210;
const CARD_H = 240;

function layoutTree(options) {
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
  let nextRow = 0;
  function walk(option, depth) {
    const children = byParent.get(option.id) ?? [];
    let row;
    if (children.length === 0) {
      row = nextRow;
      nextRow += 1;
    } else {
      const childRows = children.map((child) => walk(child, depth + 1));
      row = (childRows[0] + childRows[childRows.length - 1]) / 2;
    }
    cells.push({ option, row, col: depth });
    for (const child of children) {
      links.push({ fromId: option.id, toId: child.id });
    }
    return row;
  }
  for (const root of roots) {
    walk(root, 0);
  }
  const positions = new Map(cells.map((cell) => [cell.option.id, cell]));
  return { cells, links, positions, rows: nextRow };
}

function linkPath(from, to) {
  const x1 = from.col * COL_W + CARD_W;
  const y1 = from.row * ROW_H + CARD_H / 2;
  const x2 = to.col * COL_W;
  const y2 = to.row * ROW_H + CARD_H / 2;
  const middle = x1 + (COL_W - CARD_W) / 2;
  return `M ${x1} ${y1} H ${middle} V ${y2} H ${x2}`;
}

export default function Board({ options, onOpen, onDelete, compareIds, onToggleCompare }) {
  const { cells, links, positions, rows } = layoutTree(options);
  const cols = Math.max(...cells.map((cell) => cell.col)) + 1;
  const width = cols * COL_W + 40;
  const height = rows * ROW_H + 20;
  const parentIds = new Set(options.filter((option) => option.parent_id).map((option) => option.parent_id));
  const numberById = new Map(options.map((option, index) => [option.id, index + 1]));
  const optionById = new Map(options.map((option) => [option.id, option]));

  function optionLabel(option) {
    return option.name || `Вариант ${numberById.get(option.id)}`;
  }

  return (
    <div className="board-scroll">
      <div className="board" style={{ width, height }}>
        <svg className="board-links" width={width} height={height}>
          {links.map((link) => (
            <path
              key={`${link.fromId}-${link.toId}`}
              d={linkPath(positions.get(link.fromId), positions.get(link.toId))}
            />
          ))}
        </svg>
        {cells.map(({ option, row, col }) => (
          <div
            key={option.id}
            className={`card${compareIds.includes(option.id) ? " selected" : ""}`}
            style={{ left: col * COL_W, top: row * ROW_H }}
          >
            <div className="card-title">
              <span>
                {optionLabel(option)}
                {option.kind === "fork" && <span className="kind-badge">ветка</span>}
              </span>
              {option.parent_id && !parentIds.has(option.id) && (
                <button
                  type="button"
                  className="row-delete"
                  title="Удалить карточку"
                  onClick={() => onDelete(option, optionLabel(option))}
                >
                  ✕
                </button>
              )}
            </div>
            {option.source_id && option.source_id !== option.parent_id && optionById.has(option.source_id) && (
              <div className="card-source">из «{optionLabel(optionById.get(option.source_id))}»</div>
            )}
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
