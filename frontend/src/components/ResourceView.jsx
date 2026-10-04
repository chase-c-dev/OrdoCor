/**
 * Renders configurable resource lists and their create, edit, and delete workflows.
 */
import { ExternalLink, Plus, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { api, resourceApi } from "../api";
import { displayValue, resources } from "../config/resources";
import { FormModal } from "./FormModal";
import { PageHeader } from "./PageHeader";
import { SecurityDetail } from "./SecurityDetail";

export function ResourceView({
  name,
  embedded = false,
  parentId,
  extraValues = {},
  refreshKey = 0,
}) {
  const config = resources[name];
  const store = useMemo(() => resourceApi(name), [name]);
  const [items, setItems] = useState([]);
  const [editing, setEditing] = useState(null);
  const [adding, setAdding] = useState(false);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setItems(await store.list(parentId));
    } catch (caught) {
      setError(caught.message);
    } finally {
      setLoading(false);
    }
  }, [parentId, store]);

  useEffect(() => {
    load();
  }, [load, refreshKey]);

  useEffect(() => {
    if (config.market) refreshMarket(true);
  }, [name]); // eslint-disable-line react-hooks/exhaustive-deps

  async function refreshMarket(silent = false) {
    setRefreshing(true);
    if (!silent) setError("");
    try {
      await api(`/market/${name}/refresh`, { method: "POST" });
      await load();
    } catch (caught) {
      if (!silent) setError(caught.message);
    } finally {
      setRefreshing(false);
    }
  }

  async function save(values) {
    if (editing) await store.update(editing.id, values);
    else await store.create(values);
    setEditing(null);
    setAdding(false);
    await load();
  }

  async function remove() {
    await store.remove(editing.id);
    setEditing(null);
    await load();
  }

  const actions = (
    <>
      <button className="button primary" onClick={() => setAdding(true)}>
        <Plus size={16} /> Add
      </button>
      {config.market && (
        <button
          className="button ghost"
          onClick={() => refreshMarket()}
          disabled={refreshing}
        >
          <RefreshCw size={16} className={refreshing ? "spin" : ""} /> Refresh
        </button>
      )}
    </>
  );

  return (
    <div className={embedded ? "embedded-view" : "page"}>
      {embedded ? (
        <div className="section-heading">
          <div>
            <h2>{config.title}</h2>
            {config.description && <p>{config.description}</p>}
          </div>
          <div className="page-actions">{actions}</div>
        </div>
      ) : (
        <PageHeader
          eyebrow="Life ledger"
          title={config.title}
          description={config.description}
          actions={actions}
        />
      )}
      {error && <div className="notice error">{error}</div>}
      {config.market && (
        <p className="helper">
          Market data refreshes when this view opens. Select a row for charts,
          notes, and more information. Last successful values remain available
          offline.
        </p>
      )}
      <ResourceContent
        config={config}
        items={items}
        loading={loading}
        onSelect={setEditing}
      />
      {adding && (
        <FormModal
          config={config}
          extraValues={extraValues}
          onSave={save}
          onClose={() => setAdding(false)}
        />
      )}
      {editing && config.market ? (
        <SecurityDetail
          config={config}
          item={editing}
          onSave={save}
          onDelete={remove}
          onClose={() => setEditing(null)}
        />
      ) : (
        editing && (
          <FormModal
            config={config}
            item={editing}
            extraValues={extraValues}
            onSave={save}
            onDelete={remove}
            onClose={() => setEditing(null)}
          />
        )
      )}
    </div>
  );
}

function ResourceContent({ config, items, loading, onSelect }) {
  if (loading) return <div className="empty-state">Loading…</div>;
  if (!items.length)
    return (
      <div className="empty-state">
        <strong>Nothing here yet.</strong>
        <span>
          Add your first {config.singular.toLowerCase()} when you are ready.
        </span>
      </div>
    );

  if (config.card)
    return (
      <div className="card-grid">
        {items.map((item) => (
          <button
            className="project-card"
            key={item.id}
            onClick={() => onSelect(item)}
          >
            <span className="eyebrow">Active project</span>
            <h3>{item.name}</h3>
            <p>{item.description || "No description yet."}</p>
          </button>
        ))}
      </div>
    );

  const availableFields = config.fields.filter(
    (field) => field.type !== "textarea",
  );
  const fields = config.market
    ? availableFields
        .filter((field) => !["purchase_date"].includes(field.key))
        .slice(0, 5)
    : availableFields.slice(0, 7);

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {fields.map((field) => (
              <th key={field.key}>{field.label}</th>
            ))}
            {config.market && (
              <>
                <th>Market Price</th>
                <th>{config.watchlist ? "From Target" : "Gain / Loss"}</th>
                <th>Dividend</th>
              </>
            )}
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <ResourceRow
              key={item.id}
              item={item}
              config={config}
              fields={fields}
              onSelect={onSelect}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ResourceRow({ item, config, fields, onSelect }) {
  const target = Number(item.target_buy_price || 0);
  const market = Number(item.market_price || 0);
  const purchase = Number(item.purchase_price || 0);
  const shares = Number(item.shares || 0);
  const difference = config.watchlist
    ? market - target
    : (market - purchase) * shares;
  const percent = config.watchlist
    ? target
      ? (difference / target) * 100
      : 0
    : purchase
      ? ((market - purchase) / purchase) * 100
      : 0;
  const ready = config.watchlist && market > 0 && market <= target;

  return (
    <tr
      className={ready ? "ready" : ""}
      onDoubleClick={() => onSelect(item)}
      onClick={() => onSelect(item)}
      tabIndex="0"
      onKeyDown={(event) => event.key === "Enter" && onSelect(item)}
    >
      {fields.map((field) => (
        <td key={field.key}>
          <CellValue field={field} item={item} />
        </td>
      ))}
      {config.market && (
        <>
          <td>
            {market ? (
              <>
                {displayValue({ format: "money" }, market)}
                {!config.watchlist && (
                  <small>
                    {displayValue({ format: "money" }, market * shares)} total
                  </small>
                )}
              </>
            ) : (
              "Offline"
            )}
          </td>
          <td
            className={difference > 0 ? "gain" : difference < 0 ? "loss" : ""}
          >
            {market
              ? `${difference >= 0 ? "+" : ""}${displayValue({ format: "money" }, difference)} · ${percent.toFixed(1)}%`
              : "—"}
          </td>
          <td>
            {item.dividend_yield == null
              ? "—"
              : `${Number(item.dividend_yield).toFixed(2)}%`}
          </td>
        </>
      )}
    </tr>
  );
}

function CellValue({ field, item }) {
  const value = item[field.key];

  if (field.type === "url" && value)
    return (
      <a
        href={value}
        target="_blank"
        rel="noreferrer"
        onClick={(event) => event.stopPropagation()}
      >
        <ExternalLink size={15} /> Open
      </a>
    );

  const shares = Number(item.shares || 0);

  if (field.key === "purchase_price")
    return (
      <>
        {displayValue(field, value)}
        <small>
          {displayValue({ format: "money" }, Number(value || 0) * shares)} cost
        </small>
      </>
    );

  if (field.key === "target_sell_price")
    return (
      <>
        {displayValue(field, value)}
        <small>
          {displayValue({ format: "money" }, Number(value || 0) * shares)}{" "}
          target
        </small>
      </>
    );

  return displayValue(field, value);
}
