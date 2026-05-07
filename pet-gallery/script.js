"use strict";

(function () {
const API_PETS = "/api/pets";
const resolvePetAnimationContractFromManifest = window.PetManifest.resolvePetAnimationContract;
const {
  LANGUAGE_STORAGE_KEY,
  resolveLanguage,
  getTranslations,
  buildPetPromptText,
} = window.PetGalleryI18n;

const els = {
  appEyebrow: document.querySelector("#appEyebrow"),
  heroTitle: document.querySelector("#heroTitle"),
  heroCopy: document.querySelector("#heroCopy"),
  langZh: document.querySelector("#langZh"),
  langEn: document.querySelector("#langEn"),
  sprite: document.querySelector("#sprite"),
  actionButtons: document.querySelector("#actionButtons"),
  animationGrid: document.querySelector("#animationGrid"),
  currentMeta: document.querySelector("#currentMeta"),
  playPause: document.querySelector("#playPause"),
  speed: document.querySelector("#speed"),
  speedLabel: document.querySelector("#speedLabel"),
  scale: document.querySelector("#scale"),
  scaleLabel: document.querySelector("#scaleLabel"),
  petList: document.querySelector("#petList"),
  petCount: document.querySelector("#petCount"),
  libraryPanel: document.querySelector("#libraryPanel"),
  libraryTitle: document.querySelector("#libraryTitle"),
  libraryCopy: document.querySelector("#libraryCopy"),
  uploadTitle: document.querySelector("#uploadTitle"),
  uploadCopy: document.querySelector("#uploadCopy"),
  petJsonLabel: document.querySelector("#petJsonLabel"),
  spritesheetLabel: document.querySelector("#spritesheetLabel"),
  petId: document.querySelector("#petId"),
  petName: document.querySelector("#petName"),
  petDescription: document.querySelector("#petDescription"),
  viewerSection: document.querySelector("#viewerSection"),
  petJsonInput: document.querySelector("#petJsonInput"),
  spritesheetInput: document.querySelector("#spritesheetInput"),
  loadPair: document.querySelector("#loadPair"),
  folderInput: document.querySelector("#folderInput"),
  folderDropLabel: document.querySelector("#folderDropLabel"),
  buildPrompt: document.querySelector("#buildPrompt"),
  copyPrompt: document.querySelector("#copyPrompt"),
  codexPrompt: document.querySelector("#codexPrompt"),
  createTitle: document.querySelector("#createTitle"),
  createCopy: document.querySelector("#createCopy"),
  createModeTitle: document.querySelector("#createModeTitle"),
  modeCustomOption: document.querySelector("#modeCustomOption"),
  modeCustom: document.querySelector("#modeCustom"),
  modeCustomLabel: document.querySelector("#modeCustomLabel"),
  modeCustomCopy: document.querySelector("#modeCustomCopy"),
  modeLegacyOption: document.querySelector("#modeLegacyOption"),
  modeLegacy: document.querySelector("#modeLegacy"),
  modeLegacyLabel: document.querySelector("#modeLegacyLabel"),
  modeLegacyCopy: document.querySelector("#modeLegacyCopy"),
  createModeHint: document.querySelector("#createModeHint"),
  nameLabel: document.querySelector("#nameLabel"),
  createName: document.querySelector("#createName"),
  conceptLabel: document.querySelector("#conceptLabel"),
  createConcept: document.querySelector("#createConcept"),
  styleLabel: document.querySelector("#styleLabel"),
  createStyle: document.querySelector("#createStyle"),
  exportState: document.querySelector("#exportState"),
  refreshPets: document.querySelector("#refreshPets"),
  controlsSection: document.querySelector("#controlsSection"),
  actionsTitle: document.querySelector("#actionsTitle"),
  actionsSection: document.querySelector("#actionsSection"),
  atlasTitle: document.querySelector("#atlasTitle"),
  atlasCopy: document.querySelector("#atlasCopy"),
  statusBanner: document.querySelector("#statusBanner"),
  spriteAria: document.querySelector("#sprite"),
  createPanel: document.querySelector("#createPanel"),
  deleteModal: document.querySelector("#deleteModal"),
  deleteModalTitle: document.querySelector("#deleteModalTitle"),
  deleteModalText: document.querySelector("#deleteModalText"),
  deletePasswordLabel: document.querySelector("#deletePasswordLabel"),
  deletePassword: document.querySelector("#deletePassword"),
  deleteError: document.querySelector("#deleteError"),
  cancelDelete: document.querySelector("#cancelDelete"),
  confirmDelete: document.querySelector("#confirmDelete"),
};

let pets = [];
let currentPet = null;
let currentContract = resolvePetAnimationContractFromManifest({});
let currentAction = currentContract.actions[0];
let frame = 0;
let playing = true;
let timer = null;
let miniTimers = [];
let pendingDeletePet = null;
let selectionVersion = 0;
let currentCreateMode = "custom";
let currentLanguage = resolveLanguage({
  storedLanguage: readStoredLanguage(),
  browserLanguage: navigator.language,
});

function getSelectedCreateMode() {
  return els.modeLegacy.checked ? "legacy" : "custom";
}

function strings() {
  return getTranslations(currentLanguage);
}

function readStoredLanguage() {
  try {
    return window.localStorage.getItem(LANGUAGE_STORAGE_KEY) || "";
  } catch (error) {
    return "";
  }
}

function persistLanguage(language) {
  try {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
  } catch (error) {
    // Ignore storage errors; the selected language still applies for this session.
  }
}

function syncLanguageButtons() {
  els.langZh.setAttribute("aria-pressed", String(currentLanguage === "zh"));
  els.langEn.setAttribute("aria-pressed", String(currentLanguage === "en"));
}

function syncPlayPauseLabel() {
  els.playPause.textContent = playing ? strings().pauseLabel : strings().playLabel;
}

function syncCreateModeStyles() {
  const isLegacy = getSelectedCreateMode() === "legacy";
  els.modeCustomOption.setAttribute("data-selected", String(!isLegacy));
  els.modeLegacyOption.setAttribute("data-selected", String(isLegacy));
}

function applyLanguage(language, { persist = false } = {}) {
  currentLanguage = resolveLanguage({ storedLanguage: language });
  if (persist) {
    persistLanguage(currentLanguage);
  }

  const copy = strings();
  document.documentElement.lang = copy.documentLang;
  document.documentElement.dataset.preferredLang = currentLanguage;
  document.title = copy.metaTitle;
  els.appEyebrow.textContent = copy.heroEyebrow;
  els.heroTitle.textContent = copy.heroTitle;
  els.heroCopy.textContent = copy.heroCopy;
  els.langZh.parentElement.setAttribute("aria-label", copy.languageSwitchLabel);
  els.libraryPanel.setAttribute("aria-label", copy.libraryPanelLabel);
  els.viewerSection.setAttribute("aria-label", copy.viewerSectionLabel);
  els.spriteAria.setAttribute("aria-label", copy.spriteLabel);
  els.controlsSection.setAttribute("aria-label", copy.controlsSectionLabel);
  els.actionsSection.setAttribute("aria-label", copy.actionsSectionLabel);
  els.createPanel.setAttribute("aria-label", copy.createPanelLabel);
  els.refreshPets.textContent = copy.refreshLabel;
  els.refreshPets.title = copy.refreshTitle;
  els.exportState.textContent = copy.exportLabel;
  els.exportState.title = copy.exportTitle;
  els.libraryTitle.textContent = copy.libraryTitle;
  els.libraryCopy.textContent = copy.libraryCopy;
  els.uploadTitle.textContent = copy.uploadTitle;
  els.uploadCopy.textContent = copy.uploadCopy;
  els.petJsonLabel.textContent = copy.petJsonLabel;
  els.spritesheetLabel.textContent = copy.spritesheetLabel;
  els.loadPair.textContent = copy.loadPair;
  els.folderDropLabel.textContent = copy.folderDropLabel;
  els.speedLabel.textContent = copy.speedLabel;
  els.scaleLabel.textContent = copy.scaleLabel;
  els.actionsTitle.textContent = copy.actionsTitle;
  els.createTitle.textContent = copy.createTitle;
  els.createCopy.textContent = copy.createCopy;
  els.createModeTitle.textContent = copy.createModeTitle;
  els.modeCustomLabel.textContent = copy.modeCustomLabel;
  els.modeCustomCopy.textContent = copy.modeCustomCopy;
  els.modeLegacyLabel.textContent = copy.modeLegacyLabel;
  els.modeLegacyCopy.textContent = copy.modeLegacyCopy;
  els.nameLabel.textContent = copy.nameLabel;
  els.createName.placeholder = copy.namePlaceholder;
  els.conceptLabel.textContent = copy.conceptLabel;
  els.createConcept.placeholder = copy.conceptPlaceholder;
  els.styleLabel.textContent = copy.styleLabel;
  els.createStyle.placeholder = copy.stylePlaceholder;
  els.buildPrompt.textContent = copy.buildPrompt;
  els.copyPrompt.textContent = copy.copyPrompt;
  els.atlasTitle.textContent = copy.atlasTitle;
  els.atlasCopy.textContent = copy.atlasCopy;
  els.deleteModalTitle.textContent = copy.deleteModalTitle;
  els.deletePasswordLabel.textContent = copy.deletePasswordLabel;
  els.deletePassword.placeholder = copy.deletePasswordPlaceholder;
  els.cancelDelete.textContent = copy.cancelDelete;
  els.confirmDelete.textContent = copy.confirmDelete;
  syncLanguageButtons();
  syncPlayPauseLabel();
  syncCreateModeStyles();
  currentCreateMode = getSelectedCreateMode();
  els.createModeHint.textContent =
    currentCreateMode === "legacy" ? copy.createModeHintLegacy : copy.createModeHintCustom;

  if (!currentPet) {
    els.petName.textContent = copy.loadingPetName;
    els.petDescription.textContent = copy.connectingDescription;
  }
  if (pendingDeletePet) {
    els.deleteModalText.textContent = copy.deleteModalText(pendingDeletePet.displayName || pendingDeletePet.id);
  }

  renderPetList();
  renderViewer();
  buildCodexPrompt();
  document.documentElement.dataset.i18nReady = "true";
}

function setStatus(type, message) {
  if (!message) {
    els.statusBanner.hidden = true;
    els.statusBanner.textContent = "";
    els.statusBanner.className = "status-banner";
    return;
  }
  els.statusBanner.hidden = false;
  els.statusBanner.textContent = message;
  els.statusBanner.className = `status-banner is-${type}`;
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : {};
  if (!response.ok) {
    throw new Error(payload.error || `Request failed with ${response.status}`);
  }
  return payload;
}

function setSpritesheet(url) {
  els.sprite.style.backgroundImage = url ? `url("${url}")` : "none";
  applySheetMetrics(els.sprite);
  for (const node of document.querySelectorAll(".mini-sprite")) {
    node.style.backgroundImage = url ? `url("${url}")` : "none";
    applySheetMetrics(node);
  }
}

function applySheetMetrics(element) {
  element.style.width = `${currentContract.cellWidth}px`;
  element.style.height = `${currentContract.cellHeight}px`;
  element.style.backgroundSize = `${currentContract.sheetWidth}px ${currentContract.sheetHeight}px`;
}

function setFrame(element, action, frameIndex) {
  element.style.backgroundPosition = `${-frameIndex * currentContract.cellWidth}px ${-action.row * currentContract.cellHeight}px`;
}

function clearAnimationTimers() {
  window.clearInterval(timer);
  timer = null;
  for (const timerId of miniTimers) {
    window.clearInterval(timerId);
  }
  miniTimers = [];
}

function renderMainFrame() {
  if (!currentPet) {
    els.currentMeta.textContent = strings().noPetLoaded;
    return;
  }
  setFrame(els.sprite, currentAction, frame);
  els.currentMeta.textContent = strings().formatCurrentMeta(currentAction);
}

function restartTimer() {
  window.clearInterval(timer);
  if (!playing || !currentPet) return;
  timer = window.setInterval(() => {
    frame = (frame + 1) % currentAction.frames;
    renderMainFrame();
  }, Number(els.speed.value));
}

function selectAction(action) {
  currentAction = action;
  frame = 0;
  renderMainFrame();
  for (const button of els.actionButtons.querySelectorAll("button")) {
    button.setAttribute("aria-pressed", String(button.dataset.action === action.id));
  }
  restartTimer();
}

function setCurrentContract(contract, preferredActionId) {
  if (typeof preferredActionId === "undefined") {
    preferredActionId = currentAction ? currentAction.id : undefined;
  }
  currentContract = contract;
  currentAction = contract.actions.find((action) => action.id === preferredActionId) || contract.actions[0];
}

function renderViewer() {
  if (!currentPet) {
    clearAnimationTimers();
    els.petId.textContent = "-";
    els.petName.textContent = strings().noPetName;
    els.petDescription.textContent = strings().noPetDescription;
    els.actionButtons.innerHTML = "";
    setSpritesheet("");
    els.animationGrid.innerHTML = "";
    renderMainFrame();
    return;
  }

  els.petId.textContent = currentPet.id;
  els.petName.textContent = currentPet.displayName || currentPet.id;
  els.petDescription.textContent = currentPet.description || strings().defaultPetDescription;
  buildActionButtons();
  setSpritesheet(currentPet.spritesheetUrl);
  rebuildAnimationGrid();
  selectAction(currentAction);
}

async function loadPetManifest(pet) {
  if (!pet || !pet.manifestUrl) {
    return resolvePetAnimationContractFromManifest({});
  }

  try {
    const manifest = await fetchJson(pet.manifestUrl);
    return resolvePetAnimationContractFromManifest(manifest);
  } catch (error) {
    setStatus("info", strings().legacyContract(pet.displayName || pet.id, error.message));
    return resolvePetAnimationContractFromManifest({});
  }
}

async function selectPet(pet) {
  const requestId = ++selectionVersion;
  currentPet = pet;
  renderPetList();
  const contract = await loadPetManifest(pet);
  if (requestId !== selectionVersion) {
    return;
  }
  setCurrentContract(contract);
  renderViewer();
}

function renderPetList() {
  els.petList.innerHTML = "";
  els.petCount.textContent = strings().petCount(pets.length);

  if (!pets.length) {
    const empty = document.createElement("p");
    empty.className = "empty-state";
    empty.textContent = strings().emptyState;
    els.petList.append(empty);
    return;
  }

  for (const pet of pets) {
    const card = document.createElement("article");
    card.className = "pet-card";
    card.setAttribute("data-selected", String(currentPet && pet.id === currentPet.id));
    card.setAttribute("role", "button");
    card.setAttribute("tabindex", "0");
    card.setAttribute("aria-pressed", String(currentPet && pet.id === currentPet.id));
    card.addEventListener("click", () => {
      if (pet.id !== (currentPet && currentPet.id)) {
        selectPet(pet);
      }
    });
    card.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" && event.key !== " ") {
        return;
      }
      event.preventDefault();
      if (pet.id !== (currentPet && currentPet.id)) {
        selectPet(pet);
      }
    });

    const cardHead = document.createElement("div");
    cardHead.className = "pet-card-head";
    cardHead.innerHTML = `
      <div>
        <h3>${escapeHtml(pet.displayName || pet.id)}</h3>
        <p>${escapeHtml(pet.id)}</p>
      </div>
      <div class="pet-badges">
        <span class="pet-badge">${escapeHtml(strings().sourceLabel[pet.source] || pet.source)}</span>
        ${pet.canDelete ? `<span class="pet-badge is-alert">${escapeHtml(strings().protectedDeleteBadge)}</span>` : `<span class="pet-badge">${escapeHtml(strings().readOnlyBadge)}</span>`}
      </div>
    `;

    const description = document.createElement("p");
    description.className = "pet-card-copy";
    description.textContent = pet.description || strings().defaultPetDescription;

    const actionsRow = document.createElement("div");
    actionsRow.className = "pet-card-actions";

    const downloadButton = document.createElement("button");
    downloadButton.type = "button";
    downloadButton.textContent = strings().downloadLabel;
    downloadButton.addEventListener("click", (event) => {
      event.stopPropagation();
      downloadPet(pet);
    });

    actionsRow.append(downloadButton);

    if (pet.canDelete) {
      const deleteButton = document.createElement("button");
      deleteButton.type = "button";
      deleteButton.textContent = strings().deleteLabel;
      deleteButton.className = "danger-button";
      deleteButton.addEventListener("click", (event) => {
        event.stopPropagation();
        openDeleteModal(pet);
      });
      actionsRow.append(deleteButton);
    }

    card.append(cardHead, description, actionsRow);
    els.petList.append(card);
  }
}

function buildActionButtons() {
  els.actionButtons.innerHTML = "";
  for (const action of currentContract.actions) {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.action = action.id;
    button.textContent = action.label;
    button.setAttribute("aria-pressed", String(action.id === currentAction.id));
    button.addEventListener("click", () => selectAction(action));
    els.actionButtons.append(button);
  }
}

function rebuildAnimationGrid() {
  for (const timerId of miniTimers) {
    window.clearInterval(timerId);
  }
  miniTimers = [];
  els.animationGrid.innerHTML = "";
  if (!currentPet) return;

  for (const action of currentContract.actions) {
    const card = document.createElement("article");
    card.className = "animation-card";

    const title = document.createElement("h3");
    title.textContent = strings().formatAnimationTitle(action);

    const miniStage = document.createElement("div");
    miniStage.className = "mini-stage";

    const miniSprite = document.createElement("div");
    miniSprite.className = "mini-sprite";
    miniSprite.style.backgroundImage = `url("${currentPet.spritesheetUrl}")`;
    applySheetMetrics(miniSprite);
    miniStage.append(miniSprite);

    card.append(title, miniStage);
    els.animationGrid.append(card);

    let miniFrame = 0;
    setFrame(miniSprite, action, miniFrame);
    const timerId = window.setInterval(() => {
      miniFrame = (miniFrame + 1) % action.frames;
      setFrame(miniSprite, action, miniFrame);
    }, 170);
    miniTimers.push(timerId);
  }
}

async function fileToDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

async function fileToJson(file) {
  return JSON.parse(await file.text());
}

async function loadPets({ keepSelection = true } = {}) {
  const previousId = keepSelection && currentPet ? currentPet.id : null;
  const payload = await fetchJson(API_PETS);
  pets = payload.pets || [];
  currentPet = pets.find((pet) => pet.id === previousId) || pets[0] || null;
  renderPetList();
  if (!currentPet) {
    setCurrentContract(resolvePetAnimationContractFromManifest({}));
    renderViewer();
    return;
  }
  await selectPet(currentPet);
}

async function uploadPetFromFiles(jsonFile, spritesheetFile, overwrite = false) {
  if (!jsonFile || !spritesheetFile) {
    throw new Error(strings().uploadMissingFiles);
  }

  const manifest = await fileToJson(jsonFile);
  const spritesheetContent = await fileToDataUrl(spritesheetFile);
  const candidateId = buildUploadCandidateId(manifest);
  const existing = pets.find((pet) => pet.id === candidateId);

  if (existing && !overwrite) {
    if (existing.source === "bundled") {
      throw new Error(strings().bundledConflict(candidateId));
    }
    const confirmed = window.confirm(strings().overwriteConfirm(candidateId));
    if (!confirmed) {
      setStatus("info", strings().uploadCancelled);
      return;
    }
    await uploadPetFromFiles(jsonFile, spritesheetFile, true);
    return;
  }

  const payload = await fetchJson(API_PETS, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      manifest,
      spritesheetName: spritesheetFile.name,
      spritesheetContent,
      overwrite,
    }),
  });

  await loadPets({ keepSelection: false });
  const uploadedPet = pets.find((pet) => pet.id === payload.pet.id) || pets[0] || null;
  if (uploadedPet) selectPet(uploadedPet);
  resetUploadInputs();
  setStatus("success", strings().uploadSuccess(payload.pet.displayName));
}

async function loadPetFolder(files) {
  const list = Array.from(files);
  const jsonFile = list.find((file) => file.name.toLowerCase() === "pet.json");
  if (!jsonFile) {
    throw new Error(strings().folderMissingManifest);
  }
  const manifest = await fileToJson(jsonFile);
  const sheetName = manifest.spritesheetPath || "spritesheet.webp";
  const spritesheetFile =
    list.find((file) => file.name === sheetName) ||
    list.find((file) => file.name.endsWith(`/${sheetName}`)) ||
    list.find((file) => /\.(webp|png)$/i.test(file.name));
  await uploadPetFromFiles(jsonFile, spritesheetFile);
}

function resetUploadInputs() {
  els.petJsonInput.value = "";
  els.spritesheetInput.value = "";
  els.folderInput.value = "";
}

function downloadPet(pet) {
  const link = document.createElement("a");
  link.href = pet.downloadUrl;
  link.download = `${pet.id}.zip`;
  document.body.append(link);
  link.click();
  link.remove();
  setStatus("info", strings().downloadStarted(pet.displayName || pet.id));
}

function openDeleteModal(pet) {
  pendingDeletePet = pet;
  els.deleteModalText.textContent = strings().deleteModalText(pet.displayName || pet.id);
  els.deletePassword.value = "";
  els.deleteError.hidden = true;
  els.deleteError.textContent = "";
  els.deleteModal.hidden = false;
  window.setTimeout(() => els.deletePassword.focus(), 0);
}

function closeDeleteModal() {
  pendingDeletePet = null;
  els.deleteModal.hidden = true;
  els.deletePassword.value = "";
  els.deleteError.hidden = true;
  els.deleteError.textContent = "";
}

async function confirmDelete() {
  if (!pendingDeletePet) return;
  const deletedName = pendingDeletePet.displayName || pendingDeletePet.id;
  try {
    await fetchJson(`${API_PETS}/${encodeURIComponent(pendingDeletePet.id)}`, {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password: els.deletePassword.value }),
    });
    closeDeleteModal();
    await loadPets({ keepSelection: false });
    setStatus("success", strings().deleteSuccess(deletedName));
  } catch (error) {
    els.deleteError.hidden = false;
    els.deleteError.textContent = error.message;
  }
}

function exportState() {
  const data = JSON.stringify(
    pets.map(({ id, displayName, description, source, downloadUrl }) => ({
      id,
      displayName,
      description,
      source,
      downloadUrl,
    })),
    null,
    2,
  );
  const blob = new Blob([data], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "pet-studio-library.json";
  link.click();
  URL.revokeObjectURL(url);
  setStatus("info", strings().exportedLibrary);
}

function buildCodexPrompt() {
  currentCreateMode = getSelectedCreateMode();
  syncCreateModeStyles();
  els.createModeHint.textContent =
    currentCreateMode === "legacy" ? strings().createModeHintLegacy : strings().createModeHintCustom;
  els.codexPrompt.value = buildPetPromptText(currentCreateMode, currentLanguage, {
    name: els.createName.value,
    concept: els.createConcept.value,
    style: els.createStyle.value,
  });
}

async function copyPrompt() {
  if (!els.codexPrompt.value.trim()) buildCodexPrompt();
  await navigator.clipboard.writeText(els.codexPrompt.value);
  els.copyPrompt.textContent = strings().copiedPrompt;
  window.setTimeout(() => {
    els.copyPrompt.textContent = strings().copyPrompt;
  }, 900);
}

function slugify(value) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 40);
}

function stableHash(value) {
  let hash = 2166136261;
  for (const char of Array.from(String(value))) {
    hash ^= char.codePointAt(0);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0).toString(36);
}

function buildUploadCandidateId(manifest) {
  const explicitId = slugify((manifest && manifest.id) || "");
  if (explicitId) {
    return explicitId;
  }

  const displayNameId = slugify((manifest && manifest.displayName) || "");
  if (displayNameId) {
    return displayNameId;
  }

  const fallbackSeed =
    String((manifest && manifest.displayName) || "").trim() || JSON.stringify(manifest && typeof manifest === "object" ? manifest : {});
  return `uploaded-${stableHash(fallbackSeed)}`.slice(0, 40);
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => {
    return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[char];
  });
}

els.playPause.addEventListener("click", () => {
  playing = !playing;
  syncPlayPauseLabel();
  restartTimer();
});
els.speed.addEventListener("input", restartTimer);
els.scale.addEventListener("input", () => {
  document.documentElement.style.setProperty("--scale", els.scale.value);
});
els.loadPair.addEventListener("click", async () => {
  try {
    await uploadPetFromFiles(els.petJsonInput.files[0], els.spritesheetInput.files[0]);
  } catch (error) {
    setStatus("error", strings().uploadFailure(error.message));
  }
});
els.folderInput.addEventListener("change", async () => {
  try {
    await loadPetFolder(els.folderInput.files);
  } catch (error) {
    setStatus("error", strings().folderFailure(error.message));
  }
});
els.buildPrompt.addEventListener("click", buildCodexPrompt);
els.modeCustom.addEventListener("change", () => {
  if (!els.modeCustom.checked) return;
  buildCodexPrompt();
});
els.modeLegacy.addEventListener("change", () => {
  if (!els.modeLegacy.checked) return;
  buildCodexPrompt();
});
els.copyPrompt.addEventListener("click", () => {
  copyPrompt().catch((error) => {
    setStatus("error", strings().copyFailure(error.message));
  });
});
els.exportState.addEventListener("click", exportState);
els.refreshPets.addEventListener("click", async () => {
  try {
    await loadPets();
    setStatus("success", strings().refreshSuccess);
  } catch (error) {
    setStatus("error", strings().refreshFailure(error.message));
  }
});
els.langZh.addEventListener("click", () => applyLanguage("zh", { persist: true }));
els.langEn.addEventListener("click", () => applyLanguage("en", { persist: true }));
els.cancelDelete.addEventListener("click", closeDeleteModal);
els.confirmDelete.addEventListener("click", () => {
  confirmDelete().catch((error) => {
    els.deleteError.hidden = false;
    els.deleteError.textContent = error.message;
  });
});
els.deleteModal.addEventListener("click", (event) => {
  if (event.target === els.deleteModal) closeDeleteModal();
});
els.deletePassword.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    confirmDelete().catch((error) => {
      els.deleteError.hidden = false;
      els.deleteError.textContent = error.message;
    });
  }
});

document.documentElement.style.setProperty("--scale", els.scale.value);
applyLanguage(currentLanguage);
loadPets()
  .then(() => {
    setStatus("success", strings().libraryReady);
    restartTimer();
  })
  .catch((error) => {
    renderPetList();
    renderViewer();
    setStatus("error", strings().serviceFailure(error.message));
  });
})();
