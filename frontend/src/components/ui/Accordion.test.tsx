/**
 * Tests for Accordion — Radix-backed accordion primitive.
 *
 * Covers:
 * - Renders accordion with trigger and content.
 * - Item starts closed.
 * - Clicking trigger opens the item (data-state=open).
 * - Clicking trigger again closes it.
 */
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "./Accordion";

function TestAccordion() {
  return (
    <Accordion type="single" collapsible>
      <AccordionItem value="item-1" data-testid="accordion-item">
        <AccordionTrigger data-testid="accordion-trigger">
          Section 1
        </AccordionTrigger>
        <AccordionContent data-testid="accordion-content">
          Content 1
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
}

describe("Accordion", () => {
  it("renders the accordion trigger", () => {
    render(<TestAccordion />);
    expect(screen.getByTestId("accordion-trigger")).toBeInTheDocument();
    expect(screen.getByText("Section 1")).toBeInTheDocument();
  });

  it("item is closed by default", () => {
    render(<TestAccordion />);
    expect(screen.getByTestId("accordion-item")).toHaveAttribute(
      "data-state",
      "closed",
    );
  });

  it("clicking trigger opens the accordion item", async () => {
    const user = userEvent.setup();
    render(<TestAccordion />);
    await user.click(screen.getByTestId("accordion-trigger"));
    expect(screen.getByTestId("accordion-item")).toHaveAttribute(
      "data-state",
      "open",
    );
    expect(screen.getByText("Content 1")).toBeInTheDocument();
  });

  it("clicking trigger again closes the accordion item", async () => {
    const user = userEvent.setup();
    render(<TestAccordion />);
    await user.click(screen.getByTestId("accordion-trigger"));
    await user.click(screen.getByTestId("accordion-trigger"));
    expect(screen.getByTestId("accordion-item")).toHaveAttribute(
      "data-state",
      "closed",
    );
  });
});
