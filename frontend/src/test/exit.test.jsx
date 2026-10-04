/**
 * Ensures the Exit action requests immediate shutdown without a confirmation popup.
 */
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { api } from "../api";
import { App } from "../App";

vi.mock("../api", () => ({
  api: vi.fn(),
  hasSessionToken: () => true,
}));
vi.mock("../pages/HomePage", () => ({ HomePage: () => null }));

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.resetAllMocks();
});

it("exits directly without prompting or rendering a closing screen", async () => {
  api.mockImplementation((route) => Promise.resolve(route === "/status"
    ? { setupSeen: true, unlocked: true }
    : { theme: "Moonlit" }));
  const confirm = vi.spyOn(window, "confirm");
  render(<App />);
  fireEvent.click(await screen.findByRole("button", { name: /Enter OrdoCor/ }));
  fireEvent.click(await screen.findByRole("button", { name: "Quit OrdoCor" }));
  expect(api).toHaveBeenCalledWith("/quit", { method: "POST" });
  expect(confirm).not.toHaveBeenCalled();
  expect(screen.queryByText("OrdoCor is closing.")).toBeNull();
});
