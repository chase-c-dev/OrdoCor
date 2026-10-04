/**
 * Builds reusable data-entry modals from resource field configurations.
 */
import { useState } from "react";
import { ChevronDown, ChevronUp, Save, Trash2 } from "lucide-react";
import { Modal } from "./Modal";

function initialValues(fields, item) {
  return Object.fromEntries(
    fields.map((field) => [
      field.key,
      item?.[field.key] ?? (field.type === "select" ? field.options[0] : ""),
    ]),
  );
}

export function FormModal({
  config,
  item,
  onSave,
  onDelete,
  onClose,
  extraValues = {},
}) {
  const [values, setValues] = useState(() =>
    initialValues(config.fields, item),
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function submit(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      await onSave({ ...values, ...extraValues });
    } catch (caught) {
      setError(caught.message);
      setSaving(false);
    }
  }

  async function remove() {
    if (!window.confirm(`Remove this ${config.singular.toLowerCase()}?`))
      return;
    setSaving(true);
    try {
      await onDelete();
    } catch (caught) {
      setError(caught.message);
      setSaving(false);
    }
  }

  return (
    <Modal
      title={`${item ? "Edit" : "Add"} ${config.singular}`}
      onClose={onClose}
    >
      <form onSubmit={submit}>
        <div className="form-grid">
          {config.fields.map((field) => (
            <FormField
              key={field.key}
              field={field}
              value={values[field.key]}
              onChange={(value) =>
                setValues((current) => ({ ...current, [field.key]: value }))
              }
            />
          ))}
        </div>
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        <footer className="modal-actions">
          {item && onDelete && (
            <button type="button" className="button danger" onClick={remove}>
              <Trash2 size={16} /> Remove
            </button>
          )}
          <span className="spacer" />
          <button type="button" className="button ghost" onClick={onClose}>
            Cancel
          </button>
          <button className="button primary" disabled={saving}>
            <Save size={16} /> {saving ? "Saving…" : "Save"}
          </button>
        </footer>
      </form>
    </Modal>
  );
}

function FormField({ field, value, onChange }) {
  const common = {
    id: field.key,
    value,
    required: field.required,
    onChange: (event) =>
      onChange(
        field.type === "number" && event.target.value !== ""
          ? Number(event.target.value)
          : event.target.value,
      ),
  };
  const step = Number(field.step || 1);

  const adjust = (direction) => {
    const precision = String(step).split(".")[1]?.length || 0;
    const next = (value === "" ? 0 : Number(value)) + direction * step;
    onChange(Number(Math.max(field.min ?? 0, next).toFixed(precision)));
  };

  return (
    <label className={`field ${field.wide ? "wide" : ""}`} htmlFor={field.key}>
      <span>{field.label}</span>
      {field.type === "textarea" ? (
        <textarea {...common} rows="5" />
      ) : field.type === "select" ? (
        <select {...common}>
          {field.options.map((option) => (
            <option key={option}>{option}</option>
          ))}
        </select>
      ) : field.type === "number" ? (
        <div className="number-input">
          <input
            {...common}
            type="number"
            step={field.step}
            min={field.min ?? 0}
          />
          <div className="number-controls">
            <button
              type="button"
              onClick={() => adjust(1)}
              aria-label={`Increase ${field.label}`}
              title={`Increase ${field.label}`}
            >
              <ChevronUp />
            </button>
            <button
              type="button"
              onClick={() => adjust(-1)}
              aria-label={`Decrease ${field.label}`}
              title={`Decrease ${field.label}`}
            >
              <ChevronDown />
            </button>
          </div>
        </div>
      ) : (
        <input {...common} type={field.type} />
      )}
    </label>
  );
}
