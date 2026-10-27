import { cn } from "../lib/utils";

export function ScoreDial({
  value,
  max = 10,
  size = 120,
  label,
  sublabel,
}: {
  value: number | null | undefined;
  max?: number;
  size?: number;
  label?: string;
  sublabel?: string;
}) {
  const pct = value == null ? 0 : Math.max(0, Math.min(1, value / max));
  const stroke = 8;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const dash = circumference * pct;
  const tone = value == null ? "#9A958A" : value / max >= 0.8 ? "#2E4A3D" : value / max >= 0.5 ? "#6B675E" : "#8C4A31";

  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          className="-rotate-90"
          role="img"
          aria-label={`${label ?? "Score"}: ${value ?? "not available"} out of ${max}`}
        >
          <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="#EDEAE1" strokeWidth={stroke} />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={tone}
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={`${dash} ${circumference}`}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-serif text-3xl text-ink">{value == null ? "—" : value}</span>
          {label && <span className="text-xs text-ink-muted">{label}</span>}
        </div>
      </div>
      {sublabel && <span className={cn("mt-2 text-xs text-ink-muted")}>{sublabel}</span>}
    </div>
  );
}

export function ScoreBar({ label, value, max = 10 }: { label: string; value: number; max?: number }) {
  const pct = Math.max(0, Math.min(100, (value / max) * 100));
  return (
    <div>
      <div className="flex items-center justify-between text-sm">
        <span className="capitalize text-ink-soft">{label.replace(/_/g, " ")}</span>
        <span className="tabular-nums text-ink-muted">
          {value}/{max}
        </span>
      </div>
      <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-stone-100">
        <div className="h-full rounded-full bg-forest" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
