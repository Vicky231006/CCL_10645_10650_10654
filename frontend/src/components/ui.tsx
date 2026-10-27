import { forwardRef, type ButtonHTMLAttributes, type InputHTMLAttributes, type ReactNode, type SelectHTMLAttributes, type TextareaHTMLAttributes } from "react";
import { AlertCircle, CheckCircle2, Info, Loader2 } from "lucide-react";
import { cn } from "../lib/utils";

/* ------------------------------- Button ------------------------------- */
type Variant = "primary" | "secondary" | "ghost" | "danger";
type Size = "sm" | "md" | "lg";

const variantClasses: Record<Variant, string> = {
  primary: "bg-forest text-ivory-50 hover:bg-forest-dark border border-forest",
  secondary: "bg-ivory-50 text-ink border border-stone-300 hover:bg-ivory-200",
  ghost: "bg-transparent text-ink-soft border border-transparent hover:bg-ivory-200",
  danger: "bg-ivory-50 text-clay border border-clay/40 hover:bg-clay-tint",
};
const sizeClasses: Record<Size, string> = {
  sm: "text-sm px-3 py-1.5 gap-1.5",
  md: "text-sm px-4 py-2 gap-2",
  lg: "text-base px-5 py-2.5 gap-2",
};

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { className, variant = "primary", size = "md", loading, children, disabled, ...props },
  ref,
) {
  return (
    <button
      ref={ref}
      disabled={disabled || loading}
      className={cn(
        "inline-flex items-center justify-center font-medium rounded-md transition-colors",
        "disabled:opacity-50 disabled:cursor-not-allowed",
        variantClasses[variant],
        sizeClasses[size],
        className,
      )}
      {...props}
    >
      {loading && <Loader2 className="h-4 w-4 animate-spin" aria-hidden />}
      {children}
    </button>
  );
});

/* ------------------------------- Inputs ------------------------------- */
export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(function Input(
  { className, ...props },
  ref,
) {
  return (
    <input
      ref={ref}
      className={cn(
        "w-full rounded-md border border-stone-300 bg-ivory-50 px-3 py-2 text-sm text-ink",
        "placeholder:text-ink-faint focus:border-forest focus:outline-none",
        className,
      )}
      {...props}
    />
  );
});

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(function Textarea(
  { className, ...props },
  ref,
) {
  return (
    <textarea
      ref={ref}
      className={cn(
        "w-full rounded-md border border-stone-300 bg-ivory-50 px-3 py-2 text-sm text-ink leading-6",
        "placeholder:text-ink-faint focus:border-forest focus:outline-none",
        className,
      )}
      {...props}
    />
  );
});

export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(function Select(
  { className, children, ...props },
  ref,
) {
  return (
    <select
      ref={ref}
      className={cn(
        "w-full rounded-md border border-stone-300 bg-ivory-50 px-3 py-2 text-sm text-ink focus:border-forest focus:outline-none",
        className,
      )}
      {...props}
    >
      {children}
    </select>
  );
});

export function Field({
  label,
  hint,
  error,
  required,
  children,
  htmlFor,
}: {
  label: string;
  hint?: string;
  error?: string;
  required?: boolean;
  children: ReactNode;
  htmlFor?: string;
}) {
  return (
    <div className="space-y-1.5">
      <label htmlFor={htmlFor} className="block text-sm font-medium text-ink-soft">
        {label}
        {required && <span className="text-clay"> *</span>}
      </label>
      {children}
      {hint && !error && <p className="text-xs text-ink-muted">{hint}</p>}
      {error && (
        <p className="text-xs text-clay" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}

/* ------------------------------- Card / layout ------------------------------- */
export function Card({ className, children, ...rest }: { className?: string; children: ReactNode } & React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("card p-5", className)} {...rest}>
      {children}
    </div>
  );
}

export function SectionHeading({ title, description, action }: { title: string; description?: string; action?: ReactNode }) {
  return (
    <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
      <div>
        <h2 className="font-serif text-xl text-ink">{title}</h2>
        {description && <p className="mt-1 text-sm text-ink-muted max-w-prose">{description}</p>}
      </div>
      {action}
    </div>
  );
}

/* ------------------------------- Badge ------------------------------- */
export function Badge({
  children,
  tone = "neutral",
  className,
}: {
  children: ReactNode;
  tone?: "neutral" | "positive" | "warning" | "critical" | "info";
  className?: string;
}) {
  const tones = {
    neutral: "bg-stone-100 text-ink-soft border-stone-200",
    positive: "bg-forest-tint text-forest border-forest/20",
    warning: "bg-ivory-200 text-ink-soft border-stone-300",
    critical: "bg-clay-tint text-clay border-clay/30",
    info: "bg-ivory-200 text-forest border-forest/20",
  } as const;
  return (
    <span className={cn("inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium", tones[tone], className)}>
      {children}
    </span>
  );
}

/* ------------------------------- Alert ------------------------------- */
export function Alert({ tone = "info", title, children }: { tone?: "info" | "success" | "error" | "warning"; title?: string; children?: ReactNode }) {
  const map = {
    info: { cls: "border-stone-300 bg-ivory-200 text-ink-soft", Icon: Info },
    success: { cls: "border-forest/30 bg-forest-tint text-forest-dark", Icon: CheckCircle2 },
    error: { cls: "border-clay/40 bg-clay-tint text-clay", Icon: AlertCircle },
    warning: { cls: "border-stone-300 bg-ivory-200 text-ink-soft", Icon: AlertCircle },
  } as const;
  const { cls, Icon } = map[tone];
  return (
    <div className={cn("flex gap-2.5 rounded-md border p-3 text-sm", cls)} role={tone === "error" ? "alert" : undefined}>
      <Icon className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
      <div>
        {title && <p className="font-medium">{title}</p>}
        {children}
      </div>
    </div>
  );
}

/* ------------------------------- States ------------------------------- */
export function Spinner({ label = "Loading" }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-2 py-10 text-ink-muted" role="status" aria-live="polite">
      <Loader2 className="h-5 w-5 animate-spin" aria-hidden />
      <span className="text-sm">{label}…</span>
    </div>
  );
}

export function EmptyState({ title, description, action }: { title: string; description?: string; action?: ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-stone-300 px-6 py-12 text-center">
      <h3 className="font-serif text-lg text-ink">{title}</h3>
      {description && <p className="mt-1 max-w-md text-sm text-ink-muted">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

/* ------------------------------- Progress ------------------------------- */
export function Progress({ value, label }: { value: number; label?: string }) {
  const pct = Math.max(0, Math.min(100, value));
  return (
    <div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-stone-100" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100} aria-label={label}>
        <div className="h-full rounded-full bg-forest transition-all" style={{ width: `${pct}%` }} />
      </div>
      {label && <p className="mt-1 text-xs text-ink-muted">{label}</p>}
    </div>
  );
}
