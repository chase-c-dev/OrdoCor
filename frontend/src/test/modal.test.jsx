/**
 * Verifies dialogs escape animated page containers and retain close interactions.
 */
import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { Modal } from "../components/Modal";

it("mounts investment dialogs at the document root outside animated pages", () => {
  const close = vi.fn();
  const { container, unmount } = render(
    <div className="page embedded-view" style={{ transform: "translateY(0)" }}>
      <Modal title="Example stock" size="wide-modal" onClose={close}>
        <p>Investment details</p>
      </Modal>
    </div>,
  );

  const dialog = screen.getByRole("dialog", { name: "Example stock" });
  expect(dialog).toHaveClass("wide-modal");
  expect(dialog.parentElement.parentElement).toBe(document.body);
  expect(container.querySelector(".modal-backdrop")).toBeNull();

  fireEvent.click(screen.getByRole("button", { name: "Close" }));
  expect(close).toHaveBeenCalledTimes(1);
  fireEvent.keyDown(window, { key: "Escape" });
  expect(close).toHaveBeenCalledTimes(2);

  unmount();
  expect(document.querySelector(".modal-backdrop")).toBeNull();
  fireEvent.keyDown(window, { key: "Escape" });
  expect(close).toHaveBeenCalledTimes(2);
});
