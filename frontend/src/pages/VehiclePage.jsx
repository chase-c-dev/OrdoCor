/**
 * Manages vehicles together with their maintenance items and wishlists.
 */
import { CarFront, Plus } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { resourceApi } from "../api";
import { FormModal } from "../components/FormModal";
import { PageHeader } from "../components/PageHeader";
import { ResourceView } from "../components/ResourceView";
import { resources } from "../config/resources";

export function VehiclePage() {
  const store = useMemo(() => resourceApi("vehicles"), []);
  const [vehicles, setVehicles] = useState([]);
  const [selected, setSelected] = useState(null);
  const [editing, setEditing] = useState(null);
  const [tab, setTab] = useState("vehicle-maintenance");
  const [refresh, setRefresh] = useState(0);

  const load = useCallback(async () => {
    const rows = await store.list();
    setVehicles(rows);
    setSelected(
      (current) =>
        rows.find((item) => item.id === current?.id) || rows[0] || null,
    );
  }, [store]);

  useEffect(() => {
    load();
  }, [load]);

  async function save(values) {
    if (editing?.id) await store.update(editing.id, values);
    else await store.create(values);
    setEditing(null);
    await load();
  }

  async function remove() {
    await store.remove(editing.id);
    setEditing(null);
    await load();
  }

  return (
    <div className="page">
      <PageHeader
        eyebrow="Garage"
        title="Vehicles"
        description="Maintenance records and planned purchases for each vehicle."
        actions={
          <button className="button primary" onClick={() => setEditing({})}>
            <Plus size={16} /> Add vehicle
          </button>
        }
      />
      <div className="vehicle-strip">
        {vehicles.map((vehicle) => (
          <button
            className={selected?.id === vehicle.id ? "active" : ""}
            onClick={() => setSelected(vehicle)}
            onDoubleClick={() => setEditing(vehicle)}
            key={vehicle.id}
          >
            <CarFront size={20} />
            <span>
              <strong>{vehicle.name}</strong>
              <small>
                {[vehicle.vehicle_year, vehicle.make, vehicle.model]
                  .filter(Boolean)
                  .join(" ") || "Vehicle details"}
              </small>
            </span>
          </button>
        ))}
      </div>
      {selected ? (
        <>
          <div className="vehicle-heading">
            <div>
              <span className="eyebrow">Selected vehicle</span>
              <h2>{selected.name}</h2>
            </div>
            <button
              className="button ghost"
              onClick={() => setEditing(selected)}
            >
              Edit vehicle
            </button>
          </div>
          <nav className="subtabs">
            <button
              className={tab === "vehicle-maintenance" ? "active" : ""}
              onClick={() => setTab("vehicle-maintenance")}
            >
              Maintenance
            </button>
            <button
              className={tab === "vehicle-wishlist" ? "active" : ""}
              onClick={() => setTab("vehicle-wishlist")}
            >
              Wishlist
            </button>
          </nav>
          <ResourceView
            name={tab}
            embedded
            parentId={selected.id}
            extraValues={{ vehicle_id: selected.id }}
            refreshKey={refresh}
            key={`${selected.id}-${tab}`}
          />
        </>
      ) : (
        <div className="empty-state">Add a vehicle to begin.</div>
      )}
      {editing && (
        <FormModal
          config={resources.vehicles}
          item={editing.id ? editing : null}
          onSave={async (values) => {
            await save(values);
            setRefresh((value) => value + 1);
          }}
          onDelete={editing.id ? remove : null}
          onClose={() => setEditing(null)}
        />
      )}
    </div>
  );
}
