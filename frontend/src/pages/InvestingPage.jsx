/**
 * Coordinates the investing dashboard and its account, position, and planning tabs.
 */
import { useState } from "react";
import { ResourceView } from "../components/ResourceView";

const tabs = [
  ["accounts", "Accounts"],
  ["stocks", "Stocks"],
  ["stock-watchlist", "Stock Watchlist"],
  ["mutual-funds", "Mutual Funds"],
  ["mutual-fund-watchlist", "Mutual Fund Watchlist"],
  ["banking", "Banking"],
  ["collectibles", "Collectibles"],
  ["plans", "Investment Plans"],
];

export function InvestingPage() {
  const [tab, setTab] = useState("accounts");

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <span className="eyebrow">Personal finance</span>
          <h1>Investing</h1>
          <p>
            Positions, accounts, research, and future plans in one measured
            view.
          </p>
        </div>
      </header>
      <nav className="subtabs" aria-label="Investing sections">
        {tabs.map(([key, label]) => (
          <button
            key={key}
            className={tab === key ? "active" : ""}
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
