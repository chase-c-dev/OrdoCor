/**
 * Defines the OrdoCor application shell, navigation, startup flow, and welcome screen.
 */
import {
  CarFront,
  CheckSquare2,
  CookingPot,
  FolderKanban,
  Heart,
  Home,
  House,
  Landmark,
  LockKeyhole,
  Map,
  Menu,
  Power,
  Settings,
  ShoppingBag,
  UnlockKeyhole,
  X,
} from "lucide-react";
import { useEffect, useState } from "react";
import { api, hasSessionToken } from "./api";
import { ResourceView } from "./components/ResourceView";
import { HomePage } from "./pages/HomePage";
import { HousePage } from "./pages/HousePage";
import { InvestingPage } from "./pages/InvestingPage";
import { RecipesPage } from "./pages/RecipesPage";
import { SettingsPage } from "./pages/SettingsPage";
import { VehiclePage } from "./pages/VehiclePage";

const navigation = [
  ["home", "Home", Home],
  ["investing", "Investing", Landmark],
  ["recipes", "Recipes", CookingPot],
  ["projects", "Projects", FolderKanban],
  ["wishlist", "Wishlist", ShoppingBag],
  ["travel", "Travel", Map],
  ["house", "House", House],
  ["vehicle", "Vehicle", CarFront],
];

export function App() {
  const [status, setStatus] = useState(null);
  const [entered, setEntered] = useState(false);
  const [page, setPage] = useState("home");
  const [settings, setSettings] = useState(false);
  const [theme, setTheme] = useState("Moonlit");
  const [menu, setMenu] = useState(false);

  useEffect(() => {
    if (hasSessionToken())
      api("/status")
        .then(setStatus)
        .catch(() => setStatus({ invalid: true }));
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = theme.toLowerCase();
  }, [theme]);

  useEffect(() => {
    if (entered)
      api("/settings")
        .then((value) => {
          setTheme(value.theme || "Moonlit");
        })
        .catch(() => {});
  }, [entered]);

  if (!hasSessionToken() || status?.invalid) return <FatalScreen />;
  if (!status)
    return (
      <div className="boot-screen">
        <Heart className="pulse" />
        <span>Preparing OrdoCor…</span>
      </div>
    );
  if (!entered)
    return (
      <Welcome
        status={status}
        onEnter={() => setEntered(true)}
        onStatus={setStatus}
      />
    );
  async function quit() {
    try {
      await api("/quit", { method: "POST" });
    } catch {
      /* the desktop process may close before the response completes */
    }
  }

  return (
    <div className="app-shell">
      <aside className={menu ? "open" : ""}>
        <div className="brand">
          <div>
            <strong>OrdoCor</strong>
            <span>Life Management · v1.0</span>
          </div>
          <button className="mobile-close" onClick={() => setMenu(false)}>
            <X />
          </button>
        </div>
        <nav>
          {navigation.map(([key, label, Icon]) => (
            <button
              key={key}
              className={page === key ? "active" : ""}
              onClick={() => {
                setPage(key);
                setMenu(false);
              }}
            >
              <Icon size={19} />
              <span>{label}</span>
            </button>
          ))}
        </nav>
        <div className="sidebar-actions">
          <button className="settings-button" onClick={() => setSettings(true)}>
            <Settings size={19} />
            <span>Settings</span>
          </button>
          <button className="quit-button" onClick={quit}>
            <Power size={19} />
            <span>Quit OrdoCor</span>
          </button>
        </div>
      </aside>
      <main>
        <button className="mobile-menu" onClick={() => setMenu(true)}>
          <Menu />
        </button>
        <Page name={page} />
      </main>
      {settings && (
        <SettingsPage
          theme={theme}
          onTheme={setTheme}
          onClose={() => setSettings(false)}
        />
      )}
    </div>
  );
}

function Page({ name }) {
  if (name === "home") return <HomePage />;
  if (name === "investing") return <InvestingPage />;
  if (name === "recipes") return <RecipesPage />;
  if (name === "house") return <HousePage />;
  if (name === "vehicle") return <VehiclePage />;
  return <ResourceView name={name} />;
}

function Welcome({ status, onEnter, onStatus }) {
  const [unlocking, setUnlocking] = useState(false);
  const [password, setPassword] = useState("");
  const [setupPassword, setSetupPassword] = useState("");
  const [error, setError] = useState("");

  async function enter() {
    setUnlocking(true);
    setError("");
    if (status.passwordEnabled && !status.unlocked) {
      try {
        await api("/auth/unlock", {
          method: "POST",
          body: JSON.stringify({ password }),
        });
        window.setTimeout(onEnter, 500);
      } catch (caught) {
        setError(caught.message);
        setUnlocking(false);
      }
    } else if (!status.setupSeen && setupPassword) {
      try {
        await api("/auth/password", {
          method: "POST",
          body: JSON.stringify({ password: setupPassword }),
        });
        window.setTimeout(onEnter, 500);
      } catch (caught) {
        setError(caught.message);
        setUnlocking(false);
      }
    } else if (!status.setupSeen) {
      await api("/auth/setup-skip", { method: "POST" });
      onStatus({ ...status, setupSeen: true, unlocked: true });
      window.setTimeout(onEnter, 500);
    } else window.setTimeout(onEnter, 500);
  }

  const needsUnlock = status.passwordEnabled && !status.unlocked;
  const firstRun = !status.setupSeen && !status.passwordEnabled;

  return (
    <div className="welcome-screen">
      <div className={`welcome-card ${unlocking ? "unlocking" : ""}`}>
        <div className="lock-orbit">
          {unlocking ? <UnlockKeyhole /> : <LockKeyhole />}
        </div>
        <span className="eyebrow">Private. Local. Yours.</span>
        <h1>Welcome to OrdoCor</h1>
        <p>
          {needsUnlock
            ? "Enter your password to open your life dashboard."
            : firstRun
              ? "You may add an optional password now, or continue without one."
              : "Order for the things that matter."}
        </p>
        {needsUnlock && (
          <input
            autoFocus
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            onKeyDown={(event) => event.key === "Enter" && enter()}
            placeholder="Password"
          />
        )}
        {firstRun && (
          <input
            type="password"
            value={setupPassword}
            onChange={(event) => setSetupPassword(event.target.value)}
            placeholder="Optional password"
          />
        )}
        {error && <span className="form-error">{error}</span>}
        <button className="enter-button" onClick={enter} disabled={unlocking}>
          {unlocking
            ? "Unlocking…"
            : firstRun && !setupPassword
              ? "Continue without password"
              : "Enter OrdoCor"}{" "}
          <span>↗</span>
        </button>
      </div>
    </div>
  );
}

function FatalScreen() {
  return (
    <div className="boot-screen">
      <CheckSquare2 />
      <strong>Open OrdoCor from its executable.</strong>
      <span>
        This interface requires the private desktop bridge included with
        OrdoCor.
      </span>
    </div>
  );
}
