import { useEffect, useRef } from "react";

const COS30 = Math.cos(Math.PI / 6);
const SIN30 = 0.5;
const LIGHT = { x: -0.8, y: -0.6 };

function project(x, y, z) {
  return [(x - y) * COS30, (x + y) * SIN30 - z];
}

function collectProjected(result) {
  const points = [];
  for (const [x, y] of result.site_outline) {
    points.push(project(x, y, 0));
  }
  for (const building of result.buildings) {
    for (const floor of building.floors) {
      for (const [x, y] of floor.outline) {
        points.push(project(x, y, floor.level_m));
        points.push(project(x, y, floor.level_m + floor.height_m));
      }
    }
  }
  return points;
}

function makeTransform(points, width, height, margin) {
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  for (const [x, y] of points) {
    minX = Math.min(minX, x);
    minY = Math.min(minY, y);
    maxX = Math.max(maxX, x);
    maxY = Math.max(maxY, y);
  }
  const spanX = Math.max(maxX - minX, 1);
  const spanY = Math.max(maxY - minY, 1);
  const scale = Math.min((width - 2 * margin) / spanX, (height - 2 * margin) / spanY);
  const offsetX = (width - spanX * scale) / 2 - minX * scale;
  const offsetY = (height - spanY * scale) / 2 - minY * scale;
  return (x, y, z) => {
    const [px, py] = project(x, y, z);
    return [px * scale + offsetX, py * scale + offsetY];
  };
}

function drawRing(ctx, points) {
  ctx.beginPath();
  points.forEach(([x, y], index) => {
    if (index === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.closePath();
}

function wallShade(p1, p2) {
  const dx = p2[0] - p1[0];
  const dy = p2[1] - p1[1];
  const length = Math.hypot(dx, dy) || 1;
  const nx = dy / length;
  const ny = -dx / length;
  const brightness = 0.55 + 0.45 * Math.max(0, nx * LIGHT.x + ny * LIGHT.y);
  const value = Math.round(120 + 90 * brightness);
  return `rgb(${value - 30}, ${value - 10}, ${value + 20})`;
}

function drawFloor(ctx, toScreen, outline, level, height, highlighted) {
  const edges = outline.map((point, index) => [point, outline[(index + 1) % outline.length]]);
  edges.sort((a, b) => {
    const depthA = Math.max(a[0][0] + a[0][1], a[1][0] + a[1][1]);
    const depthB = Math.max(b[0][0] + b[0][1], b[1][0] + b[1][1]);
    return depthA - depthB;
  });
  for (const [p1, p2] of edges) {
    const quad = [
      toScreen(p1[0], p1[1], level),
      toScreen(p2[0], p2[1], level),
      toScreen(p2[0], p2[1], level + height),
      toScreen(p1[0], p1[1], level + height),
    ];
    drawRing(ctx, quad);
    ctx.fillStyle = highlighted ? "#e8a44c" : wallShade(p1, p2);
    ctx.fill();
    ctx.strokeStyle = "rgba(40, 60, 90, 0.35)";
    ctx.lineWidth = 0.5;
    ctx.stroke();
  }
  const top = outline.map(([x, y]) => toScreen(x, y, level + height));
  drawRing(ctx, top);
  ctx.fillStyle = highlighted ? "#f5c98a" : "#d7e3f2";
  ctx.fill();
  ctx.strokeStyle = "rgba(40, 60, 90, 0.5)";
  ctx.lineWidth = 0.8;
  ctx.stroke();
}

export default function IsoView({ result, width, height, highlight }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !result) return;
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, width, height);
    const toScreen = makeTransform(collectProjected(result), width, height, 12);

    const site = result.site_outline.map(([x, y]) => toScreen(x, y, 0));
    drawRing(ctx, site);
    ctx.fillStyle = "#eef2ee";
    ctx.fill();
    ctx.strokeStyle = "#9aa89a";
    ctx.setLineDash([4, 3]);
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.setLineDash([]);

    const ordered = result.buildings
      .map((building, index) => ({ building, index }))
      .sort((a, b) => {
        const depth = (item) => Math.min(...item.building.contour.map(([x, y]) => x + y));
        return depth(a) - depth(b);
      });
    for (const { building, index } of ordered) {
      building.floors.forEach((floor, floorIndex) => {
        const highlighted =
          highlight && highlight.building === index && (highlight.floor === undefined || highlight.floor === floorIndex);
        drawFloor(ctx, toScreen, floor.outline, floor.level_m, floor.height_m, highlighted);
      });
    }
  }, [result, width, height, highlight]);

  return <canvas ref={canvasRef} width={width} height={height} className="iso-canvas" />;
}
