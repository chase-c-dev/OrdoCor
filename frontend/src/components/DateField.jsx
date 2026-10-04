/**
 * Provides editable ISO dates with a palette-aware calendar instead of a native popup.
 */
import { useEffect, useRef, useState } from "react";
import { CalendarDays, ChevronLeft, ChevronRight } from "lucide-react";

function parseDate(value) {
  const date = value ? new Date(`${value}T12:00:00`) : new Date();
  return Number.isNaN(date.getTime()) ? new Date() : date;
}

function isoDate(date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

export function DateField({ id, value, required, onChange, label }) {
  const [open, setOpen] = useState(false);
  const [month, setMonth] = useState(() => parseDate(value));
  const container = useRef(null);
  const trigger = useRef(null);

  useEffect(() => {
    if (!open) return;

    const dismiss = (event) => {
      if (!container.current?.contains(event.target)) setOpen(false);
    };

    document.addEventListener("pointerdown", dismiss);
    return () => document.removeEventListener("pointerdown", dismiss);
  }, [open]);

  function choose(date) {
    onChange({ target: { value: isoDate(date) } });
    setOpen(false);
    trigger.current?.focus();
  }

  const year = month.getFullYear();
  const monthIndex = month.getMonth();
  const offset = new Date(year, monthIndex, 1).getDay();
  const count = new Date(year, monthIndex + 1, 0).getDate();
  const today = isoDate(new Date());

  return (
    <div
      className="date-field"
      ref={container}
      onKeyDown={(event) => {
        if (open && event.key === "Escape") {
          event.stopPropagation();
          setOpen(false);
          trigger.current?.focus();
        }
      }}
    >
      <div className="date-input">
        <input
          id={id}
          type="date"
          value={value}
          required={required}
          onChange={onChange}
        />
        <button
          ref={trigger}
          type="button"
          aria-label={`Choose ${label}`}
          aria-expanded={open}
          aria-controls={`${id}-calendar`}
          title={`Choose ${label}`}
          onClick={() => {
            if (!open) setMonth(parseDate(value));
            setOpen(!open);
          }}
        >
          <CalendarDays size={18} />
        </button>
      </div>

      {open && (
        <div
          className="date-calendar"
          id={`${id}-calendar`}
          role="group"
          aria-label={`${label} calendar`}
        >
          <div className="date-calendar-header">
            <button
              type="button"
              className="icon-button"
              aria-label="Previous month"
              onClick={() => setMonth(new Date(year, monthIndex - 1, 1))}
            >
              <ChevronLeft size={18} />
            </button>
            <span aria-live="polite">
              {month.toLocaleDateString(undefined, { month: "long", year: "numeric" })}
            </span>
            <button
              type="button"
              className="icon-button"
              aria-label="Next month"
              onClick={() => setMonth(new Date(year, monthIndex + 1, 1))}
            >
              <ChevronRight size={18} />
            </button>
          </div>
          <div className="date-calendar-grid">
            {["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"].map((day) => (
              <span key={day}>{day}</span>
            ))}
            {Array.from({ length: offset }, (_, index) => (
              <span key={`blank-${index}`} />
            ))}
            {Array.from({ length: count }, (_, index) => {
              const date = new Date(year, monthIndex, index + 1);
              const iso = isoDate(date);

              return (
                <button
                  key={iso}
                  type="button"
                  aria-label={iso}
                  aria-pressed={value === iso}
                  aria-current={iso === today ? "date" : undefined}
                  onClick={() => choose(date)}
                >
                  {index + 1}
                </button>
              );
            })}
          </div>
          <div className="date-calendar-actions">
            <button
              type="button"
              className="button ghost"
              onClick={() => choose(new Date())}
            >
              Today
            </button>
            <button
              type="button"
              className="button ghost"
              onClick={() => {
                onChange({ target: { value: "" } });
                setOpen(false);
                trigger.current?.focus();
              }}
            >
              Clear
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
