/**
 * Organizes household reminders, maintenance tasks, and planned improvements.
 */
import { useState } from "react";
import { ResourceView } from "../components/ResourceView";

const tabs = [
  ["house-reminders", "Tax & Insurance"],
  ["house-maintenance", "Maintenance"],
  ["house-improvements", "Improvements"],
];

export function HousePage() {
  const [tab, setTab] = useState(tabs[0][0]);

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <span className="eyebrow">Property</span>
          <h1>House</h1>
          <p>Keep bills, care, and future improvements organized.</p>
        </div>
      </header>
      <nav className="subtabs">
        {tabs.map(([key, label]) => (
          <button
            className={tab === key ? "active" : ""}
            key={key}
            onClick={() => setTab(key)}
          >
            {label}
          </button>
        ))}
      </nav>
      <ResourceView name={tab} embedded />
    </div>
  );
}
