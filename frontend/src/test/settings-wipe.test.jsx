/**
 * Verifies database wiping requires confirmation and exposes recoverable errors.
 */
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { api } from "../api";
import { SettingsPage } from "../pages/SettingsPage";

vi.mock("../api", () => ({ api: vi.fn(), downloadBackup: vi.fn() }));

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.resetAllMocks();
});

it("does not erase data when confirmation is canceled", async () => {
  api.mockResolvedValue({});
  vi.spyOn(window, "confirm").mockReturnValue(false);
  render(<SettingsPage theme="Moonlit" onTheme={vi.fn()} onClose={vi.fn()} />);
  await waitFor(() => expect(api).toHaveBeenCalledWith("/settings"));
  fireEvent.click(screen.getByRole("button", { name: "Wipe database" }));
  expect(window.confirm).toHaveBeenCalled();
  expect(api).not.toHaveBeenCalledWith("/database/wipe", expect.anything());
});

it("sends explicit confirmation and re-enables controls after a failed wipe", async () => {
  api.mockImplementation((route) => route === "/settings"
    ? Promise.resolve({})
    : Promise.reject(new Error("Unable to erase database.")));
  vi.spyOn(window, "confirm").mockReturnValue(true);
  render(<SettingsPage theme="Moonlit" onTheme={vi.fn()} onClose={vi.fn()} />);
  fireEvent.click(screen.getByRole("button", { name: "Wipe database" }));
  expect(api).toHaveBeenCalledWith("/database/wipe", {
    method: "POST",
    body: JSON.stringify({ confirm: true }),
  });
  expect(await screen.findByText("Unable to erase database.")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Wipe database" })).toBeEnabled();
});
