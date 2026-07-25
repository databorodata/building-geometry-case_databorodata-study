import { useEffect, useRef, useState } from "react";
import { SAMPLE_SITES } from "../samples.js";

const WIDTH = 640;
const HEIGHT = 440;
const MARGIN = 30;

function makeTransform(points) {
  let minX = 0;
  let minY = 0;
  let maxX = 10;
  let maxY = 10;
  for (const [x, y] of points) {
    minX = Math.min(minX, x - 3);
    minY = Math.min(minY, y - 3);
    maxX = Math.max(maxX, x + 3);
    maxY = Math.max(maxY, y + 3);
  }
  const scale = Math.min((WIDTH - 2 * MARGIN) / (maxX - minX), (HEIGHT - 2 * MARGIN) / (maxY - minY));
  const toScreen = (x, y) => [MARGIN + (x - minX) * scale, HEIGHT - MARGIN - (y - minY) * scale];
  const toWorld = (sx, sy) => [
    Math.round((sx - MARGIN) / scale + minX),
    Math.round((HEIGHT - MARGIN - sy) / scale + minY),
  ];
  return { toScreen, toWorld, minX, minY, maxX, maxY, scale };
}

export default function SiteDrawer({ onCreate, busy, error }) {
  const canvasRef = useRef(null);
  const [name, setName] = useState("Участок 1");
  const [points, setPoints] = useState(SAMPLE_SITES.rectangle.map(([x, y]) => [x, y]));
  const [dragIndex, setDragIndex] = useState(null);

  const transform = makeTransform(points);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const { toScreen, minX, minY, maxX, maxY, scale } = transform;
    ctx.clearRect(0, 0, WIDTH, HEIGHT);

    if (scale >= 5) {
      ctx.strokeStyle = "#edf0f4";
      ctx.lineWidth = 1;
      for (let x = Math.ceil(minX); x <= maxX; x += 1) {
        ctx.beginPath();
        ctx.moveTo(...toScreen(x, minY));
        ctx.lineTo(...toScreen(x, maxY));
        ctx.stroke();
      }
      for (let y = Math.ceil(minY); y <= maxY; y += 1) {
        ctx.beginPath();
        ctx.moveTo(...toScreen(minX, y));
        ctx.lineTo(...toScreen(maxX, y));
        ctx.stroke();
      }
    }

    if (points.length >= 2) {
      ctx.beginPath();
      points.forEach(([x, y], index) => {
        const [sx, sy] = toScreen(x, y);
        if (index === 0) ctx.moveTo(sx, sy);
        else ctx.lineTo(sx, sy);
      });
      ctx.closePath();
      ctx.fillStyle = "rgba(150, 180, 150, 0.3)";
      ctx.fill();
      ctx.strokeStyle = "#5a7a5a";
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    points.forEach(([x, y], index) => {
      const [sx, sy] = toScreen(x, y);
      ctx.beginPath();
      ctx.arc(sx, sy, 5, 0, Math.PI * 2);
      ctx.fillStyle = index === dragIndex ? "#d97e18" : "#3a5a3a";
      ctx.fill();
      ctx.fillStyle = "#444";
      ctx.font = "11px sans-serif";
      ctx.fillText(`${index + 1} (${x}, ${y})`, sx + 8, sy - 6);
    });
  }, [points, dragIndex, transform]);

  function canvasPosition(event) {
    const rect = canvasRef.current.getBoundingClientRect();
    return [event.clientX - rect.left, event.clientY - rect.top];
  }

  function findVertex(sx, sy) {
    for (let i = 0; i < points.length; i += 1) {
      const [px, py] = transform.toScreen(points[i][0], points[i][1]);
      if (Math.hypot(px - sx, py - sy) <= 9) return i;
    }
    return null;
  }

  function handleMouseDown(event) {
    const [sx, sy] = canvasPosition(event);
    const vertex = findVertex(sx, sy);
    if (vertex !== null) setDragIndex(vertex);
  }

  function handleMouseMove(event) {
    if (dragIndex === null) return;
    const [sx, sy] = canvasPosition(event);
    const world = transform.toWorld(sx, sy);
    setPoints(points.map((point, index) => (index === dragIndex ? world : point)));
  }

  function updateCoordinate(index, axis, value) {
    const number = Number(value);
    if (!Number.isFinite(number)) return;
    setPoints(points.map((point, i) => (i === index ? (axis === 0 ? [number, point[1]] : [point[0], number]) : point)));
  }

  return (
    <div className="site-drawer">
      <h2>Задайте участок</h2>
      <p className="hint">
        Выберите образец участка или задайте координаты в таблице. Тяните вершину на холсте, чтобы передвинуть её.
      </p>
      <div className="drawer-layout">
        <canvas
          ref={canvasRef}
          width={WIDTH}
          height={HEIGHT}
          className="drawer-canvas"
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={() => setDragIndex(null)}
          onMouseLeave={() => setDragIndex(null)}
        />
        <div className="drawer-side">
          <label>
            Название участка
            <input value={name} onChange={(event) => setName(event.target.value)} />
          </label>
          <div className="samples">
            {Object.keys(SAMPLE_SITES).map((key) => (
              <button key={key} type="button" onClick={() => setPoints(SAMPLE_SITES[key].map(([x, y]) => [x, y]))}>
                {key}
              </button>
            ))}
          </div>
          <table className="coords-table">
            <thead>
              <tr>
                <th>#</th>
                <th>X, м</th>
                <th>Y, м</th>
              </tr>
            </thead>
            <tbody>
              {points.map(([x, y], index) => (
                <tr key={index}>
                  <td>{index + 1}</td>
                  <td>
                    <input type="number" step="1" value={x} onChange={(e) => updateCoordinate(index, 0, e.target.value)} />
                  </td>
                  <td>
                    <input type="number" step="1" value={y} onChange={(e) => updateCoordinate(index, 1, e.target.value)} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {error && <p className="error">{error}</p>}
          <button
            type="button"
            className="primary"
            disabled={busy || points.length < 3}
            onClick={() => onCreate(name, points)}
          >
            {busy ? "Строим…" : "Построить первый вариант"}
          </button>
        </div>
      </div>
    </div>
  );
}
