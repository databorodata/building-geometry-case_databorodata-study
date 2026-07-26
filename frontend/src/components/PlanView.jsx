import { useEffect, useRef } from "react";

function makeTransform(outline, width, height, margin) {
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  for (const [x, y] of outline) {
    minX = Math.min(minX, x);
    minY = Math.min(minY, y);
    maxX = Math.max(maxX, x);
    maxY = Math.max(maxY, y);
  }
  const spanX = Math.max(maxX - minX, 1);
  const spanY = Math.max(maxY - minY, 1);
  const scale = Math.min((width - 2 * margin) / spanX, (height - 2 * margin) / spanY);
  const offsetX = (width - spanX * scale) / 2 - minX * scale;
  const offsetY = (height + spanY * scale) / 2 + minY * scale;
  return {
    toScreen: (x, y) => [x * scale + offsetX, offsetY - y * scale],
    bounds: { minX, minY, maxX, maxY },
    scale,
  };
}

function drawPolygon(ctx, points) {
  ctx.beginPath();
  points.forEach(([x, y], index) => {
    if (index === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.closePath();
}

export default function PlanView({ result, width, height, highlight }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !result) return;
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, width, height);
    const { toScreen, bounds, scale } = makeTransform(result.site_outline, width, height, 14);

    if (scale >= 5) {
      ctx.strokeStyle = "#eceff3";
      ctx.lineWidth = 1;
      for (let x = Math.ceil(bounds.minX); x <= bounds.maxX; x += 1) {
        ctx.beginPath();
        ctx.moveTo(...toScreen(x, bounds.minY));
        ctx.lineTo(...toScreen(x, bounds.maxY));
        ctx.stroke();
      }
      for (let y = Math.ceil(bounds.minY); y <= bounds.maxY; y += 1) {
        ctx.beginPath();
        ctx.moveTo(...toScreen(bounds.minX, y));
        ctx.lineTo(...toScreen(bounds.maxX, y));
        ctx.stroke();
      }
    }

    drawPolygon(
      ctx,
      result.site_outline.map(([x, y]) => toScreen(x, y)),
    );
    ctx.fillStyle = "rgba(210, 225, 210, 0.5)";
    ctx.fill();
    ctx.strokeStyle = "#7b8a7b";
    ctx.lineWidth = 1.5;
    ctx.stroke();

    result.buildings.forEach((building, index) => {
      const isSelected = highlight && highlight.building === index;
      drawPolygon(
        ctx,
        building.contour.map(([x, y]) => toScreen(x, y)),
      );
      ctx.fillStyle =
        isSelected && highlight.floor === undefined ? "rgba(232, 164, 76, 0.45)" : "rgba(120, 150, 190, 0.35)";
      ctx.fill();
      ctx.strokeStyle = "#4a6a95";
      ctx.lineWidth = 1.5;
      ctx.stroke();
      building.floors.forEach((floor, floorIndex) => {
        drawPolygon(
          ctx,
          floor.outline.map(([x, y]) => toScreen(x, y)),
        );
        const floorSelected = isSelected && highlight.floor === floorIndex;
        ctx.strokeStyle = floorSelected ? "#d97e18" : "rgba(74, 106, 149, 0.45)";
        ctx.lineWidth = floorSelected ? 2 : 0.8;
        ctx.stroke();
      });
    });
  }, [result, width, height, highlight]);

  return <canvas ref={canvasRef} width={width} height={height} className="plan-canvas" />;
}
