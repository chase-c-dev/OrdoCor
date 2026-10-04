/**
 * Hosts application preferences, privacy controls, password tools, and backups.
 */
import {
  DatabaseBackup,
  KeyRound,
  Palette,
  RotateCcw,
  ShieldCheck,
  Trash2,
  Upload,
} from "lucide-react";
import { useEffect, useState } from "react";
import { api, downloadBackup } from "../api";
import { Modal } from "../components/Modal";

const themes = ["Moonlit", "Woodland", "Cathedral", "Hearth"];

export function SettingsPage({ onClose, theme, onTheme }) {
  const [settings, setSettings] = useState(null);
  const [message, setMessage] = useState("");
  const [passwordMode, setPasswordMode] = useState(false);
  const [wiping, setWiping] = useState(false);

  useEffect(() => {
    api("/settings").then(setSettings);
  }, []);

  async function selectTheme(value) {
    onTheme(value);
    await api("/settings", {
      method: "PUT",
      body: JSON.stringify({ theme: value }),
    });
  }

  async function restore() {
    if (
      !window.confirm(
        "Loading a backup will replace the current local OrdoCor database. Continue?",
      )
    )
      return;
    try {
      const result = await api("/backup/restore", { method: "POST" });
      if (result.canceled) return;
      setMessage("Backup loaded. Restarting this view…");
      window.setTimeout(() => window.location.reload(), 500);
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function toggleScreenCapture(enabled) {
    setSettings((current) => ({ ...current, screenCaptureEnabled: enabled }));
    await api("/settings", {
      method: "PUT",
      body: JSON.stringify({ screenCaptureEnabled: enabled }),
    });
  }

  async function wipeDatabase() {
    if (!window.confirm(
      "Permanently erase ALL OrdoCor database records, images, notes, cached market data, settings, and password information? This cannot be undone. Existing backup files will not be deleted. Create a backup first if you need one.",
    )) return;

    setWiping(true);
    setPasswordMode(false);
    setMessage("");
    try {
      await api("/database/wipe", {
        method: "POST",
        body: JSON.stringify({ confirm: true }),
      });
      window.location.reload();
    } catch (error) {
      setMessage(error.message);
      setWiping(false);
    }
  }

  return (
    <Modal title="Settings" onClose={onClose} size="settings-modal">
      <div className="settings-sections">
        <fieldset disabled={wiping} className="settings-controls">
        <section>
          <div className="settings-title">
            <Palette />
            <div>
              <h3>Appearance</h3>
              <p>Choose the atmosphere used throughout OrdoCor.</p>
            </div>
          </div>
          <div className="palette-grid">
            {themes.map((name) => (
              <button
                key={name}
                className={`${name.toLowerCase()} ${theme === name ? "active" : ""}`}
                onClick={() => selectTheme(name)}
              >
                <i />
                <span>{name}</span>
              </button>
            ))}
          </div>
        </section>
        <section>
          <div className="settings-title">
            <DatabaseBackup />
            <div>
              <h3>Database backup</h3>
              <p>
                Create or load one protected file containing all OrdoCor data.
              </p>
            </div>
          </div>
          <p className="backup-status">
            Last backup:{" "}
            {settings?.lastBackup
              ? new Date(settings.lastBackup).toLocaleString()
              : "Never"}
          </p>
          <div className="button-row">
            <button
              className="button primary"
              onClick={async () => {
                try {
                  const result = await downloadBackup();
                  if (!result.canceled)
                    setMessage("Backup created successfully.");
                } catch (error) {
                  setMessage(error.message);
                }
              }}
            >
              <DatabaseBackup size={16} /> Create backup
            </button>
            <button className="button ghost" onClick={restore}>
              <Upload size={16} /> Load backup
            </button>
          </div>
        </section>
        <section>
          <div className="settings-title">
            <ShieldCheck />
            <div>
              <h3>Access security</h3>
              <p>
                {settings?.passwordEnabled
                  ? "Password protection is enabled."
                  : "Password protection is optional and currently disabled."}
              </p>
            </div>
          </div>
          <label className="toggle-row">
            <input
              type="checkbox"
              checked={settings?.screenCaptureEnabled ?? true}
              onChange={(event) => toggleScreenCapture(event.target.checked)}
            />
            <span>
              <strong>Screen capture resistance</strong>
              <small>
                Enabled by default. Turn off while intentionally sharing
                OrdoCor.
              </small>
            </span>
          </label>
          <button
            className="button ghost"
            onClick={() => setPasswordMode(true)}
          >
            <KeyRound size={16} />{" "}
            {settings?.passwordEnabled
              ? "Change or disable password"
              : "Enable password"}
          </button>
        </section>
        <section>
          <div className="settings-title">
            <Trash2 />
            <div>
              <h3>Erase personal data</h3>
              <p>
                Permanently delete all database content and reset OrdoCor.
                Saved backup files are not deleted.
              </p>
            </div>
          </div>
          <button className="button danger" onClick={wipeDatabase} disabled={wiping}>
            <Trash2 size={16} /> {wiping ? "Erasing..." : "Wipe database"}
          </button>
        </section>
        </fieldset>
      </div>
      {message && <div className="notice">{message}</div>}
      {passwordMode && (
        <PasswordPanel
          enabled={settings?.passwordEnabled}
          onDone={() => {
            setPasswordMode(false);
            api("/settings").then(setSettings);
          }}
        />
      )}
    </Modal>
  );
}

function PasswordPanel({ enabled, onDone }) {
  const [currentPassword, setCurrent] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function save(event) {
    event.preventDefault();
    try {
      await api("/auth/password", {
        method: "POST",
        body: JSON.stringify({ currentPassword, password }),
      });
      onDone();
    } catch (caught) {
      setError(caught.message);
    }
  }

  async function disable() {
    try {
      await api("/auth/password", {
        method: "DELETE",
        body: JSON.stringify({ password: currentPassword }),
      });
      onDone();
    } catch (caught) {
      setError(caught.message);
    }
  }

  return (
    <div className="inline-dialog">
      <form onSubmit={save}>
        {enabled && (
          <label className="field">
            <span>Current password</span>
            <input
              type="password"
              value={currentPassword}
              onChange={(event) => setCurrent(event.target.value)}
            />
          </label>
        )}
        <label className="field">
          <span>{enabled ? "New password" : "Password"}</span>
          <input
            type="password"
            minLength="4"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </label>
        {error && <p className="form-error">{error}</p>}
        <div className="button-row">
          <button className="button primary">Save password</button>
          {enabled && (
            <button type="button" className="button danger" onClick={disable}>
              <RotateCcw size={16} /> Disable
            </button>
          )}
          <button type="button" className="button ghost" onClick={onDone}>
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
