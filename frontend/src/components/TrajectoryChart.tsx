"use client";

import { useRef, useEffect } from "react";

interface TrajectoryChartProps {
  data: number[];
  threshold?: number;
}

export default function TrajectoryChart({
  data,
  threshold = 0.7,
}: TrajectoryChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const W = canvas.offsetWidth || 500;
    const H = canvas.offsetHeight || 180;
    canvas.width = W;
    canvas.height = H;
    ctx.clearRect(0, 0, W, H);

    const pad = { t: 16, b: 24, l: 32, r: 16 };
    const cW = W - pad.l - pad.r;
    const cH = H - pad.t - pad.b;

    // Grid
    ctx.strokeStyle = "#2d3148";
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const y = pad.t + (cH / 4) * i;
      ctx.beginPath();
      ctx.moveTo(pad.l, y);
      ctx.lineTo(pad.l + cW, y);
      ctx.stroke();
      ctx.fillStyle = "#8892a4";
      ctx.font = "10px sans-serif";
      ctx.fillText((1 - i / 4).toFixed(2), 2, y + 3);
    }

    // Threshold line
    const ty = pad.t + cH * (1 - threshold);
    ctx.strokeStyle = "#ff6b6b44";
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(pad.l, ty);
    ctx.lineTo(pad.l + cW, ty);
    ctx.stroke();
    ctx.setLineDash([]);

    if (!data || data.length < 2) return;

    const xStep = cW / (data.length - 1);

    // Fill
    ctx.beginPath();
    ctx.moveTo(pad.l, pad.t + cH * (1 - data[0]));
    for (let i = 1; i < data.length; i++) {
      ctx.lineTo(pad.l + xStep * i, pad.t + cH * (1 - data[i]));
    }
    ctx.lineTo(pad.l + cW, pad.t + cH);
    ctx.lineTo(pad.l, pad.t + cH);
    ctx.closePath();
    const grad = ctx.createLinearGradient(0, pad.t, 0, pad.t + cH);
    grad.addColorStop(0, "#7c6af766");
    grad.addColorStop(1, "#7c6af700");
    ctx.fillStyle = grad;
    ctx.fill();

    // Line
    ctx.strokeStyle = "#7c6af7";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(pad.l, pad.t + cH * (1 - data[0]));
    for (let i = 1; i < data.length; i++) {
      ctx.lineTo(pad.l + xStep * i, pad.t + cH * (1 - data[i]));
    }
    ctx.stroke();

    // Dots
    data.forEach((v, i) => {
      ctx.beginPath();
      ctx.arc(pad.l + xStep * i, pad.t + cH * (1 - v), 3.5, 0, Math.PI * 2);
      ctx.fillStyle = "#7c6af7";
      ctx.fill();
    });
  }, [data, threshold]);

  return (
    <div className="chart-container">
      <canvas ref={canvasRef} />
    </div>
  );
}
