/**
 * Tests for ToggleGroup — Radix-backed toggle group primitive.
 *
 * Covers:
 * - Renders a group with multiple items.
 * - Toggling an item sets data-state="on".
 * - Active item reflects data-state="on" class styling.
 */
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { ToggleGroup, ToggleGroupItem } from "./ToggleGroup";

describe("ToggleGroup", () => {
  it("renders toggle items", () => {
    render(
      <ToggleGroup type="single">
        <ToggleGroupItem value="a" data-testid="item-a">
          A
        </ToggleGroupItem>
        <ToggleGroupItem value="b" data-testid="item-b">
          B
        </ToggleGroupItem>
      </ToggleGroup>,
    );
    expect(screen.getByTestId("item-a")).toBeInTheDocument();
    expect(screen.getByTestId("item-b")).toBeInTheDocument();
  });

  it("item has data-state=off by default", () => {
    render(
      <ToggleGroup type="single">
        <ToggleGroupItem value="a" data-testid="item-a">
          A
        </ToggleGroupItem>
      </ToggleGroup>,
    );
    expect(screen.getByTestId("item-a")).toHaveAttribute("data-state", "off");
  });

  it("clicking an item sets data-state=on", async () => {
    const user = userEvent.setup();
    render(
      <ToggleGroup type="single">
        <ToggleGroupItem value="a" data-testid="item-a">
          A
        </ToggleGroupItem>
        <ToggleGroupItem value="b" data-testid="item-b">
          B
        </ToggleGroupItem>
      </ToggleGroup>,
    );
    await user.click(screen.getByTestId("item-a"));
    expect(screen.getByTestId("item-a")).toHaveAttribute("data-state", "on");
    expect(screen.getByTestId("item-b")).toHaveAttribute("data-state", "off");
  });

  it("forwards className to ToggleGroupItem", () => {
    render(
      <ToggleGroup type="single">
        <ToggleGroupItem value="a" data-testid="item-a" className="custom-cls">
          A
        </ToggleGroupItem>
      </ToggleGroup>,
    );
    expect(screen.getByTestId("item-a")).toHaveClass("custom-cls");
  });
});
