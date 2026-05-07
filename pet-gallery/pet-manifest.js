"use strict";

(function () {
const LEGACY_ACTIONS = Object.freeze([
  Object.freeze({ id: "idle", label: "Idle", row: 0, frames: 6 }),
  Object.freeze({ id: "running-right", label: "Run Right", row: 1, frames: 8 }),
  Object.freeze({ id: "running-left", label: "Run Left", row: 2, frames: 8 }),
  Object.freeze({ id: "waving", label: "Waving", row: 3, frames: 4 }),
  Object.freeze({ id: "jumping", label: "Jumping", row: 4, frames: 5 }),
  Object.freeze({ id: "failed", label: "Failed", row: 5, frames: 8 }),
  Object.freeze({ id: "waiting", label: "Waiting", row: 6, frames: 6 }),
  Object.freeze({ id: "running", label: "Running Task", row: 7, frames: 6 }),
  Object.freeze({ id: "review", label: "Review", row: 8, frames: 6 }),
]);

const LEGACY_CONTRACT = Object.freeze({
  cellWidth: 192,
  cellHeight: 208,
  atlas: Object.freeze({ columns: 8, rows: 9 }),
  actions: LEGACY_ACTIONS,
});

function normalizePositiveInt(value, fallback) {
  const normalized = Number.parseInt(value, 10);
  return Number.isInteger(normalized) && normalized > 0 ? normalized : fallback;
}

function normalizeNonNegativeInt(value, fallback) {
  const normalized = Number.parseInt(value, 10);
  return Number.isInteger(normalized) && normalized >= 0 ? normalized : fallback;
}

function normalizeAction(action, index) {
  if (!action || typeof action !== "object") {
    return null;
  }

  const id = String(action.id || "").trim();
  if (!id) {
    return null;
  }

  return {
    id,
    label: String(action.label || id),
    row: normalizeNonNegativeInt(action.row, index),
    frames: normalizePositiveInt(action.frames, 1),
  };
}

function buildDynamicActions(manifestActions) {
  if (!Array.isArray(manifestActions) || !manifestActions.length) {
    return null;
  }

  const actions = manifestActions.map(normalizeAction).filter(Boolean);
  return actions.length ? actions : null;
}

function cloneLegacyActions() {
  return LEGACY_ACTIONS.map((action) => ({
    id: action.id,
    label: action.label,
    row: action.row,
    frames: action.frames,
  }));
}

function resolvePetAnimationContract(manifest = {}) {
  const atlas = manifest && typeof manifest.atlas === "object" && manifest.atlas ? manifest.atlas : {};
  const actions = buildDynamicActions(manifest.actions) || cloneLegacyActions();
  const maxFrames = actions.reduce((largest, action) => Math.max(largest, action.frames), 1);
  const maxRow = actions.reduce((largest, action) => Math.max(largest, action.row), 0);
  const cellWidth = normalizePositiveInt(manifest.cellWidth, LEGACY_CONTRACT.cellWidth);
  const cellHeight = normalizePositiveInt(manifest.cellHeight, LEGACY_CONTRACT.cellHeight);
  const atlasColumns = Math.max(normalizePositiveInt(atlas.columns, maxFrames), maxFrames);
  const atlasRows = Math.max(normalizePositiveInt(atlas.rows, maxRow + 1), maxRow + 1);

  return {
    cellWidth,
    cellHeight,
    atlas: {
      columns: atlasColumns,
      rows: atlasRows,
    },
    sheetWidth: cellWidth * atlasColumns,
    sheetHeight: cellHeight * atlasRows,
    actions,
  };
}

const petManifestApi = {
  LEGACY_ACTIONS,
  LEGACY_CONTRACT,
  resolvePetAnimationContract,
};

if (typeof globalThis !== "undefined") {
  globalThis.PetManifest = petManifestApi;
}

if (typeof exports !== "undefined") {
  exports.LEGACY_ACTIONS = LEGACY_ACTIONS;
  exports.LEGACY_CONTRACT = LEGACY_CONTRACT;
  exports.resolvePetAnimationContract = resolvePetAnimationContract;
}
})();
