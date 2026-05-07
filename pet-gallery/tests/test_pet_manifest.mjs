import test from "node:test";
import assert from "node:assert/strict";

import { resolvePetAnimationContract } from "../pet-manifest.js";

test("resolvePetAnimationContract uses manifest-provided dynamic actions", () => {
  const contract = resolvePetAnimationContract({
    cellWidth: 192,
    cellHeight: 208,
    atlas: { columns: 8, rows: 3 },
    actions: [
      { id: "idle", label: "Idle", row: 0, frames: 6 },
      { id: "coding", label: "Coding", row: 1, frames: 8 },
      { id: "sleeping", label: "Sleeping", row: 2, frames: 4 },
    ],
  });

  assert.equal(contract.actions.length, 3);
  assert.equal(contract.actions[1].id, "coding");
  assert.equal(contract.sheetWidth, 1536);
  assert.equal(contract.sheetHeight, 624);
  assert.equal(contract.actions[2].row, 2);
});

test("resolvePetAnimationContract falls back to the legacy 9-action contract", () => {
  const contract = resolvePetAnimationContract({});

  assert.equal(contract.actions.length, 9);
  assert.equal(contract.actions[0].id, "idle");
  assert.equal(contract.actions[8].id, "review");
  assert.equal(contract.sheetWidth, 1536);
  assert.equal(contract.sheetHeight, 1872);
});

test("resolvePetAnimationContract clamps undersized atlas metadata to fit actions", () => {
  const contract = resolvePetAnimationContract({
    cellWidth: 64,
    cellHeight: 32,
    atlas: { columns: 2, rows: 1 },
    actions: [
      { id: "idle", row: 0, frames: 3 },
      { id: "dash", row: 4, frames: 7 },
    ],
  });

  assert.equal(contract.atlas.columns, 7);
  assert.equal(contract.atlas.rows, 5);
  assert.equal(contract.sheetWidth, 448);
  assert.equal(contract.sheetHeight, 160);
});

test("resolvePetAnimationContract ignores invalid actions and keeps valid ones", () => {
  const contract = resolvePetAnimationContract({
    atlas: { columns: 1, rows: 1 },
    actions: [
      null,
      { label: "Missing id", row: 0, frames: 4 },
      { id: "coding", label: "Coding", row: "2", frames: "5" },
      { id: "sleeping", row: -3, frames: 0 },
    ],
  });

  assert.equal(contract.actions.length, 2);
  assert.deepEqual(
    contract.actions.map(({ id, row, frames }) => ({ id, row, frames })),
    [
      { id: "coding", row: 2, frames: 5 },
      { id: "sleeping", row: 3, frames: 1 },
    ],
  );
  assert.equal(contract.atlas.columns, 5);
  assert.equal(contract.atlas.rows, 4);
});
