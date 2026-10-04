/**
 * Displays an editable investment detail view with charts, notes, and market research.
 */
import { ChartNoAxesCombined, ChevronDown, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../api";
import { Modal } from "./Modal";

const ranges = { "1D": 1, "5D": 5, "1M": 31, "6M": 183, "1Y": 366, "5Y": 1900 };
const recommendationColors = [
  "#3ba86a",
  "#73d39a",
  "#d4ad62",
  "#df7379",
  "#a84750",
];

export function SecurityDetail({ config, item, onSave, onDelete, onClose }) {
  const [values, setValues] = useState(() =>
    Object.fromEntries(
      config.fields.map((field) => [field.key, item[field.key] ?? ""]),
    ),
  );
  const [history, setHistory] = useState([]);
  const [fundamentals, setFundamentals] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [recommendationBreakdown, setRecommendationBreakdown] = useState([]);
  const [range, setRange] = useState("5Y");
  const [moreOpen, setMoreOpen] = useState(false);
  const [recommendationsOpen, setRecommendationsOpen] = useState(true);
  const [message, setMessage] = useState("Updating chart…");
  const symbol = item[config.symbol];

  useEffect(() => {
    let active = true;
    Promise.allSettled([
      api(`/market/${encodeURIComponent(symbol)}/history`),
      api(`/market/${encodeURIComponent(symbol)}/fundamentals`),
    ]).then(([chart, info]) => {
      if (!active) return;
      if (chart.status === "fulfilled") {
        setHistory(chart.value);
        setMessage("");
      } else
        setMessage(
          "Live history is unavailable. Cached values will appear when available.",
        );
      if (info.status === "fulfilled") {
        setFundamentals(info.value.rows);
        setRecommendations(info.value.recommendations || []);
        setRecommendationBreakdown(info.value.recommendationBreakdown || []);
      }
    });
    return () => {
      active = false;
    };
  }, [symbol]);

  const visibleHistory = useMemo(
    () => history.slice(-ranges[range]),
    [history, range],
  );

  async function close() {
    await onSave(values);
    onClose();
  }

  async function remove() {
    if (window.confirm(`Remove ${symbol} and its notes?`)) await onDelete();
  }

  return (
    <Modal
      title={`${item[config.name] || symbol} · ${symbol}`}
      onClose={close}
      size="wide-modal"
    >
      <div className="security-summary">
        <Metric
          label="Current price"
          value={
            item.market_price
              ? `$${Number(item.market_price).toFixed(2)}`
              : "Offline"
          }
        />
        <Metric
          label="Dividend yield"
          value={
            item.dividend_yield == null
              ? "—"
              : `${Number(item.dividend_yield).toFixed(2)}%`
          }
        />
        <Metric
          label="Last refresh"
          value={
            item.market_updated_at
              ? new Date(item.market_updated_at).toLocaleString()
              : "No successful refresh"
          }
        />
      </div>
      <div className="detail-grid">
        <section className="chart-panel">
          <div className="chart-header">
            <div>
              <span className="eyebrow">Performance</span>
              <h3>Price history</h3>
            </div>
            <div className="segmented">
              {Object.keys(ranges).map((option) => (
                <button
                  className={range === option ? "active" : ""}
                  onClick={() => setRange(option)}
                  key={option}
                >
                  {option}
                </button>
              ))}
            </div>
          </div>
          {visibleHistory.length ? (
            <div className="chart-canvas">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={visibleHistory}>
                  <CartesianGrid stroke="var(--line)" vertical={false} />
                  <XAxis
                    dataKey="price_date"
                    tickFormatter={(value) => value.slice(5)}
                    minTickGap={45}
                  />
                  <YAxis
                    domain={["auto", "auto"]}
                    width={62}
                    tickFormatter={(value) => `$${value}`}
                  />
                  <Tooltip
                    formatter={(value) => [
                      `$${Number(value).toFixed(2)}`,
                      "Close",
                    ]}
                    labelFormatter={(value) =>
                      new Date(`${value}T12:00:00`).toLocaleDateString()
                    }
                  />
                  <Line
                    dataKey="close_price"
                    stroke="var(--gain)"
                    strokeWidth={2.5}
                    dot={false}
                    activeDot={{ r: 5, fill: "var(--gain)" }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="chart-empty">
              <ChartNoAxesCombined size={28} />
              <span>{message}</span>
            </div>
          )}
        </section>
        <section className="notes-panel">
          <span className="eyebrow">Review notes</span>
          <h3>Your thesis and observations</h3>
          <textarea
            value={values.notes || ""}
            onChange={(event) =>
              setValues({ ...values, notes: event.target.value })
            }
            placeholder="Record research, goals, risks, or questions…"
          />
          <p>Notes save automatically when this view closes.</p>
        </section>
      </div>
      <button
        className="disclosure"
        onClick={() => setRecommendationsOpen(!recommendationsOpen)}
      >
        <span>Analyst Recommendations</span>
        <ChevronDown
          size={18}
          className={recommendationsOpen ? "rotated" : ""}
        />
      </button>
      {recommendationsOpen && (
        <div className="analyst-panel">
          {recommendationBreakdown.some((item) => item.value > 0) && (
            <div className="recommendation-chart">
              <span className="eyebrow">Recommendation mix</span>
              <div className="recommendation-chart-canvas">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={recommendationBreakdown}
                      dataKey="value"
                      nameKey="name"
                      innerRadius="30%"
                      outerRadius="52%"
                      paddingAngle={2}
                    >
                      {recommendationBreakdown.map((item, index) => (
                        <Cell
                          key={item.name}
                          fill={recommendationColors[index]}
                        />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value, name) => [value, name]} />
                    <Legend iconType="circle" iconSize={8} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
          {recommendations.length ? (
            <div className="analyst-recommendations">
              {recommendations.map((row, index) => (
                <Metric
                  key={`${row.label}-${index}`}
                  label={row.label}
                  value={row.value}
                />
              ))}
            </div>
          ) : (
            <p>Analyst recommendations are unavailable for this security.</p>
          )}
        </div>
      )}
      <button className="disclosure" onClick={() => setMoreOpen(!moreOpen)}>
        <span>More Info</span>
        <ChevronDown size={18} className={moreOpen ? "rotated" : ""} />
      </button>
      {moreOpen && (
        <div className="fundamentals">
          {fundamentals.length ? (
            fundamentals.map((row) => (
              <Metric key={row.label} label={row.label} value={row.value} />
            ))
          ) : (
            <p>More information is unavailable while offline.</p>
          )}
        </div>
      )}
      <footer className="modal-actions">
        <button className="button danger" onClick={remove}>
          <Trash2 size={16} /> Remove
        </button>
        <span className="spacer" />
        <button className="button primary" onClick={close}>
          Done
        </button>
      </footer>
    </Modal>
  );
}

function Metric({ label, value }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
