/**
 * Verifies shared form controls and their keyboard and pointer interactions.
 */
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { FormModal } from "../components/FormModal";

describe("resource forms", () => {
  it("starts new number fields blank and uses themed step controls", async () => {
    const user = userEvent.setup();
    render(
      <FormModal
        config={{
          singular: "Stock",
          fields: [
            { key: "shares", label: "Shares", type: "number", step: "0.0001" },
            {
              key: "purchase_price",
              label: "Purchase Price",
              type: "number",
              step: "0.01",
            },
          ],
        }}
        onSave={vi.fn()}
        onClose={vi.fn()}
      />,
    );

    const shares = screen.getByLabelText("Shares");
    const purchasePrice = screen.getByLabelText("Purchase Price");
    expect(shares).toHaveValue(null);
    expect(purchasePrice).toHaveValue(null);

    await user.click(screen.getByRole("button", { name: "Increase Shares" }));
    expect(shares).toHaveValue(0.0001);
    await user.click(screen.getByRole("button", { name: "Decrease Shares" }));
    expect(shares).toHaveValue(0);
  });
});
