/**
 * Checks themed calendar selection, month boundaries, clearing, and dismissal.
 */
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { DateField } from "../components/DateField";

afterEach(cleanup);

it("selects leap-day dates and returns ISO values without submitting the form", () => {
  const change = vi.fn();
  const submit = vi.fn();
  render(
    <form onSubmit={submit}>
      <DateField id="due" label="Due date" value="2024-01-31" onChange={change} />
    </form>,
  );

  fireEvent.click(screen.getByRole("button", { name: "Choose Due date" }));
  fireEvent.click(screen.getByRole("button", { name: "Next month" }));
  expect(screen.queryByRole("button", { name: "2024-02-30" })).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "2024-02-29" }));
  expect(change).toHaveBeenCalledWith({ target: { value: "2024-02-29" } });
  expect(submit).not.toHaveBeenCalled();
  expect(screen.queryByRole("group")).toBeNull();
});

it("supports year boundaries, clearing, manual input, and keyboard dismissal", () => {
  const change = vi.fn();
  const { container } = render(<DateField id="due" label="Date" value="2025-01-01" onChange={change} />);
  const trigger = screen.getByRole("button", { name: "Choose Date" });

  fireEvent.click(trigger);
  fireEvent.click(screen.getByRole("button", { name: "Previous month" }));
  expect(screen.getByRole("button", { name: "2024-12-31" })).toBeInTheDocument();
  fireEvent.keyDown(trigger, { key: "Escape" });
  expect(trigger).toHaveAttribute("aria-expanded", "false");
  fireEvent.click(trigger);
  fireEvent.click(screen.getByRole("button", { name: "Clear" }));
  expect(change).toHaveBeenCalledWith({ target: { value: "" } });
  fireEvent.change(container.querySelector("input"), { target: { value: "2025-06-15" } });
  expect(change).toHaveBeenCalledTimes(2);
  fireEvent.click(trigger);
  fireEvent.pointerDown(document.body);
  expect(trigger).toHaveAttribute("aria-expanded", "false");
});
