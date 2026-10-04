/**
 * Presents the home dashboard with todos, the yearly calendar, and upcoming events.
 */
import {
  CalendarDays,
  Check,
  ChevronLeft,
  ChevronRight,
  Clock3,
  Plus,
  Trash2,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { api, resourceApi } from "../api";
import { FormModal } from "../components/FormModal";
import { Modal } from "../components/Modal";
import { PageHeader } from "../components/PageHeader";

const calendarConfig = {
  singular: "Calendar Item",
  fields: [
    { key: "item_date", label: "Date", type: "date", required: true },
    {
      key: "title",
      label: "Appointment or Item",
      type: "text",
      required: true,
    },
    { key: "notes", label: "Notes", type: "textarea", wide: true },
  ],
};

export function HomePage() {
  const [todos, setTodos] = useState([]);
  const [calendarItems, setCalendarItems] = useState([]);
  const [upcoming, setUpcoming] = useState([]);
  const [year, setYear] = useState(new Date().getFullYear());
  const [selectedDate, setSelectedDate] = useState(null);
  const [addingCalendar, setAddingCalendar] = useState(false);
  const [newTodo, setNewTodo] = useState("");

  const todoStore = useMemo(() => resourceApi("todos"), []);
  const calendarStore = useMemo(() => resourceApi("calendar"), []);

  const load = useCallback(async () => {
    const [todoRows, dateRows, upcomingRows] = await Promise.all([
      todoStore.list(),
      calendarStore.list(),
      api("/home/upcoming"),
    ]);
    setTodos(todoRows);
    setCalendarItems(dateRows);
    setUpcoming(upcomingRows);
  }, [calendarStore, todoStore]);

  useEffect(() => {
    load();
  }, [load]);

  async function addTodo(event) {
    event.preventDefault();
    if (!newTodo.trim()) return;
    await todoStore.create({
      title: newTodo.trim(),
      notes: "",
      is_completed: 0,
    });
    setNewTodo("");
    await load();
  }

  async function toggleTodo(todo) {
    await todoStore.update(todo.id, {
      ...todo,
      is_completed: todo.is_completed ? 0 : 1,
    });
    await load();
  }

  async function removeTodo(id) {
    await todoStore.remove(id);
    await load();
  }

  async function saveCalendar(values) {
    await calendarStore.create(values);
    setAddingCalendar(false);
    await load();
  }

  async function removeCalendar(id) {
    await calendarStore.remove(id);
    await load();
  }

  const selectedItems = calendarItems.filter(
    (item) => item.item_date === selectedDate,
  );

  return (
    <div className="page home-page">
      <PageHeader
        eyebrow="Today at a glance"
        title="Home"
        description="A quiet overview of what needs your attention."
      />
      <div className="home-layout">
        <section className="panel todo-panel">
          <div className="section-heading">
            <div>
              <span className="eyebrow">Focus</span>
              <h2>TODO list</h2>
            </div>
            <span className="count-badge">
              {todos.filter((todo) => !todo.is_completed).length} open
            </span>
          </div>
          <form className="quick-add" onSubmit={addTodo}>
            <input
              value={newTodo}
              onChange={(event) => setNewTodo(event.target.value)}
              placeholder="Add something to your list"
              aria-label="New TODO"
            />
            <button className="icon-button primary" aria-label="Add TODO">
              <Plus size={18} />
            </button>
          </form>
          <div className="todo-list">
            {todos.map((todo) => (
              <div
                className={`todo-row ${todo.is_completed ? "complete" : ""}`}
                key={todo.id}
              >
                <button
                  className="check-button"
                  onClick={() => toggleTodo(todo)}
                  aria-label="Toggle completed"
                >
                  {todo.is_completed ? <Check size={15} /> : null}
                </button>
                <span>{todo.title}</span>
                <button
                  className="row-action"
                  onClick={() => removeTodo(todo.id)}
                  aria-label="Remove TODO"
                >
                  <Trash2 size={15} />
                </button>
              </div>
            ))}
            {!todos.length && (
              <div className="empty-compact">Your list is clear.</div>
            )}
          </div>
        </section>
        <section className="panel upcoming-panel">
          <div className="section-heading">
            <div>
              <span className="eyebrow">Next seven days</span>
              <h2>Upcoming</h2>
            </div>
            <Clock3 size={20} />
          </div>
          <div className="upcoming-list">
            {upcoming.map((item) => (
              <button
                key={item.id}
                onClick={() => setSelectedDate(item.item_date)}
              >
                <time>
                  {new Date(`${item.item_date}T12:00:00`).toLocaleDateString(
                    undefined,
                    { month: "short", day: "numeric" },
                  )}
                </time>
                <span>{item.title}</span>
              </button>
            ))}
            {!upcoming.length && (
              <div className="empty-compact">No upcoming calendar items.</div>
            )}
          </div>
        </section>
      </div>
      <section className="panel calendar-panel">
        <div className="calendar-toolbar">
          <div>
            <span className="eyebrow">Year planner</span>
            <h2>{year}</h2>
          </div>
          <div>
            <button
              className="icon-button"
              onClick={() => setYear(year - 1)}
              aria-label="Previous year"
            >
              <ChevronLeft />
            </button>
            <button
              className="button ghost"
              onClick={() => setYear(new Date().getFullYear())}
            >
              Today
            </button>
            <button
              className="icon-button"
              onClick={() => setYear(year + 1)}
              aria-label="Next year"
            >
              <ChevronRight />
            </button>
          </div>
        </div>
        <div className="year-grid">
          {Array.from({ length: 12 }, (_, month) => (
            <MiniMonth
              key={month}
              year={year}
              month={month}
              items={calendarItems}
              onSelect={setSelectedDate}
            />
          ))}
        </div>
      </section>
      {selectedDate && (
        <DayModal
          date={selectedDate}
          items={selectedItems}
          onClose={() => setSelectedDate(null)}
          onAdd={() => setAddingCalendar(true)}
          onRemove={removeCalendar}
        />
      )}
      {addingCalendar && (
        <FormModal
          config={calendarConfig}
          item={{ item_date: selectedDate }}
          onSave={saveCalendar}
          onClose={() => setAddingCalendar(false)}
        />
      )}
    </div>
  );
}

function MiniMonth({ year, month, items, onSelect }) {
  const first = new Date(year, month, 1);
  const days = new Date(year, month + 1, 0).getDate();
  const cells = [
    ...Array(first.getDay()).fill(null),
    ...Array.from({ length: days }, (_, index) => index + 1),
  ];
  const today = new Date();

  return (
    <div className="mini-month">
      <h3>{first.toLocaleDateString(undefined, { month: "long" })}</h3>
      <div className="weekdays">
        {"SMTWTFS".split("").map((day, index) => (
          <span key={`${day}-${index}`}>{day}</span>
        ))}
      </div>
      <div className="month-days">
        {cells.map((day, index) => {
          const iso = day
            ? `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`
            : "";
          const count = items.filter((item) => item.item_date === iso).length;
          const isToday =
            day === today.getDate() &&
            month === today.getMonth() &&
            year === today.getFullYear();
          return day ? (
            <button
              className={isToday ? "today" : ""}
              key={iso}
              onClick={() => onSelect(iso)}
            >
              <span>{day}</span>
              {count > 0 && <i>{count}</i>}
            </button>
          ) : (
            <span key={`empty-${index}`} />
          );
        })}
      </div>
    </div>
  );
}

function DayModal({ date, items, onClose, onAdd, onRemove }) {
  return (
    <Modal
      title={new Date(`${date}T12:00:00`).toLocaleDateString(undefined, {
        weekday: "long",
        month: "long",
        day: "numeric",
        year: "numeric",
      })}
      onClose={onClose}
    >
      <div className="day-items">
        {items.map((item) => (
          <article key={item.id}>
            <CalendarDays size={18} />
            <div>
              <strong>{item.title}</strong>
              <p>{item.notes || "No notes"}</p>
            </div>
            <button className="row-action" onClick={() => onRemove(item.id)}>
              <Trash2 size={16} />
            </button>
          </article>
        ))}
        {!items.length && (
          <div className="empty-state">Nothing scheduled for this day.</div>
        )}
      </div>
      <footer className="modal-actions">
        <span className="spacer" />
        <button className="button primary" onClick={onAdd}>
          <Plus size={16} /> Add item
        </button>
      </footer>
    </Modal>
  );
}
