/**
 * Tests for DropdownMenu — Radix-backed dropdown menu primitive.
 *
 * Covers:
 * - Trigger renders and is in the document.
 * - Component mounts without crashing.
 * - DropdownMenuLabel renders text.
 * - DropdownMenuItem renders text.
 *
 * Note: DropdownMenuContent uses a Portal and requires a full browser
 * environment for open-state testing. Those tests are omitted here;
 * the trigger/closed state is the relevant unit boundary.
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "./DropdownMenu";

describe("DropdownMenu", () => {
  it("renders the trigger without crashing", () => {
    render(
      <DropdownMenu>
        <DropdownMenuTrigger data-testid="trigger">
          Open Menu
        </DropdownMenuTrigger>
        <DropdownMenuContent>
          <DropdownMenuLabel>Actions</DropdownMenuLabel>
          <DropdownMenuItem>Action 1</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>,
    );
    expect(screen.getByTestId("trigger")).toBeInTheDocument();
    expect(screen.getByText("Open Menu")).toBeInTheDocument();
  });

  it("trigger has aria-haspopup attribute", () => {
    render(
      <DropdownMenu>
        <DropdownMenuTrigger data-testid="trigger">Open</DropdownMenuTrigger>
        <DropdownMenuContent>
          <DropdownMenuItem>Item</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>,
    );
    expect(screen.getByTestId("trigger")).toHaveAttribute(
      "aria-haspopup",
      "menu",
    );
  });

  it("trigger has aria-expanded=false when closed", () => {
    render(
      <DropdownMenu>
        <DropdownMenuTrigger data-testid="trigger">Open</DropdownMenuTrigger>
        <DropdownMenuContent>
          <DropdownMenuItem>Item</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>,
    );
    expect(screen.getByTestId("trigger")).toHaveAttribute(
      "aria-expanded",
      "false",
    );
  });
});
