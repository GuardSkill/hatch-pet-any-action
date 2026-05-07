"use strict";

(function () {
const LANGUAGE_STORAGE_KEY = "pet-gallery-language";
const SKILL_GITHUB_URL = "https://github.com/GuardSkill/hatch-pet-any-action/hatch-pet-any-action";
const LEGACY_SKILL_URL = "https://github.com/openai/skills/tree/main/skills/.curated/hatch-pet";

const TRANSLATIONS = {
  zh: {
    documentLang: "zh-CN",
    metaTitle: "Codex 宠物工作台",
    heroEyebrow: "Codex 宠物工作台",
    heroTitle: "共享宠物库",
    heroCopy: "同一台机器上的所有浏览器共享同一个本地宠物库，支持上传、下载和密码删除。",
    languageSwitchLabel: "语言切换",
    libraryPanelLabel: "宠物库",
    viewerSectionLabel: "动画预览",
    spriteLabel: "当前宠物动画",
    controlsSectionLabel: "动画控制",
    actionsSectionLabel: "宠物动作",
    createPanelLabel: "生成宠物提示词",
    refreshLabel: "刷新",
    refreshTitle: "重新加载共享宠物库",
    exportLabel: "导出列表",
    exportTitle: "导出当前宠物列表元数据",
    libraryTitle: "宠物库",
    libraryCopy: "由本地服务持久化，当前机器上的所有浏览器共享同一套宠物。",
    petCount: (count) => `${count} 已加载`,
    uploadTitle: "上传资源包",
    uploadCopy: "把宠物写入磁盘上的共享宠物库。",
    petJsonLabel: "pet.json",
    spritesheetLabel: "spritesheet.webp / png",
    loadPair: "上传选中的文件",
    folderDropLabel: "读取宠物文件夹",
    loadingPetName: "加载中...",
    connectingDescription: "正在连接共享宠物库。",
    playLabel: "播放",
    pauseLabel: "暂停",
    speedLabel: "速度",
    scaleLabel: "缩放",
    actionsTitle: "动作",
    frameUnit: "帧",
    noPetLoaded: "当前未加载宠物",
    noPetName: "没有可用宠物",
    noPetDescription: "上传一个资源包即可开始共享宠物库。",
    defaultPetDescription: "Codex 宠物",
    createTitle: "生成提示词",
    createCopy: "为下一只 Codex 宠物资源包生成提示词。",
    createModeTitle: "创建模式",
    modeCustomLabel: "自定义动作",
    modeCustomCopy: "由 Codex 根据自然语言推断动作集合。",
    modeLegacyLabel: "Codex 默认 9 动作",
    modeLegacyCopy: "兼容旧版固定 9 动作宠物流程。",
    createModeHintCustom: "把下面提示词粘贴到 Codex 使用，Codex 会根据自然语言推断动作集合。",
    createModeHintLegacy: "把下面提示词粘贴到 Codex 使用，Codex 会按默认 9 动作流程生成宠物。",
    nameLabel: "名称",
    namePlaceholder: "雪团",
    conceptLabel: "概念",
    conceptPlaceholder: "一只戴蓝围巾的小像素雪狐",
    styleLabel: "风格说明",
    stylePlaceholder: "Codex 数字宠物风格，粗描边，平涂赛璐璐阴影",
    buildPrompt: "生成 Codex 提示词",
    copyPrompt: "复制提示词",
    copiedPrompt: "已复制",
    atlasTitle: "全部动画",
    atlasCopy: "以下动画从当前选中的 spritesheet 行中裁切展示。",
    emptyState: "共享宠物库里还没有宠物。",
    previewLabel: "预览",
    previewingLabel: "预览中",
    downloadLabel: "下载",
    deleteLabel: "删除",
    sourceLabel: {
      bundled: "内置",
      uploaded: "已上传",
    },
    protectedDeleteBadge: "密码删除",
    readOnlyBadge: "只读",
    deleteModalTitle: "删除宠物",
    deleteModalText: (name) => `输入密码 104228 以从共享宠物库删除“${name}”。`,
    deletePasswordLabel: "密码",
    deletePasswordPlaceholder: "104228",
    cancelDelete: "取消",
    confirmDelete: "删除宠物",
    formatCurrentMeta: (action) => `${action.id} - ${action.frames} 帧`,
    formatAnimationTitle: (action) => `${action.label} - ${action.frames} 帧`,
    legacyContract: (name, error) => `“${name}” 的新动画清单读取失败，已回退到旧版 9 动作协议：${error}`,
    uploadMissingFiles: "请同时选择 pet.json 和 spritesheet.webp/png。",
    bundledConflict: (petId) => `宠物 id “${petId}” 已被内置宠物占用。`,
    overwriteConfirm: (petId) => `宠物“${petId}”已经存在。要覆盖共享版本吗？`,
    uploadCancelled: "已取消上传。",
    uploadSuccess: (name) => `已上传“${name}”。所有浏览器里的共享宠物库都已更新。`,
    folderMissingManifest: "所选文件夹中没有 pet.json。",
    downloadStarted: (name) => `正在下载“${name}”。`,
    exportedLibrary: "已导出当前宠物库元数据。",
    deleteSuccess: (name) => `已从共享宠物库删除“${name}”。`,
    refreshSuccess: "共享宠物库已刷新。",
    libraryReady: "共享宠物库已就绪。",
    serviceFailure: (error) => `无法连接本地宠物服务：${error}`,
    uploadFailure: (error) => `上传宠物失败：${error}`,
    folderFailure: (error) => `读取文件夹失败：${error}`,
    copyFailure: (error) => `复制提示词失败：${error}`,
    refreshFailure: (error) => `刷新共享宠物库失败：${error}`,
    promptDefaults: {
      name: "我的宠物",
      concept: "一只自定义像素风 Codex 宠物",
      style: "Codex 数字宠物风格，紧凑的 Q 版比例，深色粗描边，平涂赛璐璐阴影",
    },
    buildCustomPromptText: ({ name, concept, style }) =>
      [
        `使用 hatch-pet-any-action，帮我孵化一只名叫 ${name} 的宠物。`,
        "",
        `skill GitHub 地址：${SKILL_GITHUB_URL}`,
        "",
        `概念：${concept}`,
        `风格：${style}`,
        "",
        "请根据自然语言描述推断动作集合，",
        "请生成完整 宠物资源包，包括 pet.json、spritesheet.webp、contact sheet 和验证结果。",
        "运行时启用子代理。",
      ].join("\n"),
    buildLegacyPromptText: ({ name, concept, style }) =>
      [
        `使用 hatch-pet，帮我孵化一只名叫 ${name} 的宠物。`,
        "",
        `hatch-pet skill 下载/安装地址：${LEGACY_SKILL_URL}`,
        "",
        `概念：${concept}`,
        `风格：${style}`,
        "",
        "请生成完整 Codex 宠物资源包，包括 pet.json、spritesheet.webp、contact sheet 和验证结果。",
        "运行启用子代理",
      ].join("\n"),
  },
  en: {
    documentLang: "en",
    metaTitle: "Codex Pet Studio",
    heroEyebrow: "Codex Pet Studio",
    heroTitle: "Shared Pet Library",
    heroCopy: "One local library shared across browsers on this machine, with upload, download, and password-protected delete.",
    languageSwitchLabel: "Language switch",
    libraryPanelLabel: "Pet library",
    viewerSectionLabel: "Animation preview",
    spriteLabel: "Current pet animation",
    controlsSectionLabel: "Animation controls",
    actionsSectionLabel: "Pet actions",
    createPanelLabel: "Create pet prompt",
    refreshLabel: "Refresh",
    refreshTitle: "Reload the shared pet library",
    exportLabel: "Export list",
    exportTitle: "Export current pet list metadata",
    libraryTitle: "Library",
    libraryCopy: "Persisted by the local service and shared across every browser on this machine.",
    petCount: (count) => `${count} loaded`,
    uploadTitle: "Upload Package",
    uploadCopy: "Write a pet package into the shared on-disk library.",
    petJsonLabel: "pet.json",
    spritesheetLabel: "spritesheet.webp / png",
    loadPair: "Upload selected files",
    folderDropLabel: "Load a pet folder",
    loadingPetName: "Loading...",
    connectingDescription: "Connecting to the shared library.",
    playLabel: "Play",
    pauseLabel: "Pause",
    speedLabel: "Speed",
    scaleLabel: "Scale",
    actionsTitle: "Actions",
    frameUnit: "frames",
    noPetLoaded: "No pet loaded",
    noPetName: "No pets available",
    noPetDescription: "Upload a package to start the shared library.",
    defaultPetDescription: "Codex pet",
    createTitle: "Create Prompt",
    createCopy: "Build a prompt for your next Codex pet package.",
    createModeTitle: "Creation mode",
    modeCustomLabel: "Custom actions",
    modeCustomCopy: "Let Codex infer the action set from natural language.",
    modeLegacyLabel: "Codex default 9 actions",
    modeLegacyCopy: "Use the legacy fixed 9-action pet flow.",
    createModeHintCustom: "Paste the prompt below into Codex. Codex will infer the action set from your natural-language description.",
    createModeHintLegacy: "Paste the prompt below into Codex. Codex will use the default 9-action pet flow.",
    nameLabel: "Name",
    namePlaceholder: "Frosty",
    conceptLabel: "Concept",
    conceptPlaceholder: "A tiny pixel-art snow fox with a blue scarf",
    styleLabel: "Style notes",
    stylePlaceholder: "Codex digital pet style, thick outline, flat cel shading",
    buildPrompt: "Build Codex prompt",
    copyPrompt: "Copy prompt",
    copiedPrompt: "Copied",
    atlasTitle: "All Animations",
    atlasCopy: "Each row is cropped from the selected spritesheet.",
    emptyState: "No pets in the shared library yet.",
    previewLabel: "Preview",
    previewingLabel: "Previewing",
    downloadLabel: "Download",
    deleteLabel: "Delete",
    sourceLabel: {
      bundled: "bundled",
      uploaded: "uploaded",
    },
    protectedDeleteBadge: "protected delete",
    readOnlyBadge: "read only",
    deleteModalTitle: "Delete pet",
    deleteModalText: (name) => `Enter password 104228 to delete '${name}' from the shared library.`,
    deletePasswordLabel: "Password",
    deletePasswordPlaceholder: "104228",
    cancelDelete: "Cancel",
    confirmDelete: "Delete pet",
    formatCurrentMeta: (action) => `${action.id} - ${action.frames} frames`,
    formatAnimationTitle: (action) => `${action.label} - ${action.frames} frames`,
    legacyContract: (name, error) => `Could not load the new animation manifest for '${name}'. Falling back to the legacy 9-action contract: ${error}`,
    uploadMissingFiles: "Select both pet.json and spritesheet.webp/png.",
    bundledConflict: (petId) => `Pet id '${petId}' is already used by a bundled pet.`,
    overwriteConfirm: (petId) => `Pet '${petId}' already exists. Overwrite the shared version?`,
    uploadCancelled: "Upload cancelled.",
    uploadSuccess: (name) => `Uploaded '${name}'. The shared library is updated for every browser.`,
    folderMissingManifest: "Selected folder does not contain pet.json.",
    downloadStarted: (name) => `Downloading '${name}'.`,
    exportedLibrary: "Exported the current library metadata.",
    deleteSuccess: (name) => `Deleted '${name}' from the shared library.`,
    refreshSuccess: "Shared library refreshed.",
    libraryReady: "Shared library ready.",
    serviceFailure: (error) => `Could not reach the local pet service: ${error}`,
    uploadFailure: (error) => `Could not upload pet: ${error}`,
    folderFailure: (error) => `Could not load folder: ${error}`,
    copyFailure: (error) => `Could not copy prompt: ${error}`,
    refreshFailure: (error) => `Could not refresh library: ${error}`,
    promptDefaults: {
      name: "my-pet",
      concept: "a custom pixel-art Codex pet",
      style: "Codex digital pet style, compact chibi proportions, thick dark outline, flat cel shading",
    },
    buildCustomPromptText: ({ name, concept, style }) =>
      [
        `Use hatch-pet-any-action to hatch a pet named ${name}.`,
        "",
        `Skill GitHub URL: ${SKILL_GITHUB_URL}`,
        "",
        `Concept: ${concept}`,
        `Style: ${style}`,
        "",
        "Infer the action set from the natural-language description, supporting fewer or more than 9 actions.",
        "Generate the full Codex pet package, including pet.json, spritesheet.webp, the contact sheet, and validation outputs.",
        "Use subagents during the run.",
      ].join("\n"),
    buildLegacyPromptText: ({ name, concept, style }) =>
      [
        `Use hatch-pet to hatch a pet named ${name}.`,
        "",
        `hatch-pet skill install URL: ${LEGACY_SKILL_URL}`,
        "",
        `Concept: ${concept}`,
        `Style: ${style}`,
        "",
        "Generate the full Codex pet package, including pet.json, spritesheet.webp, the contact sheet, and validation outputs.",
        "Enable subagents during the run.",
      ].join("\n"),
  },
};

function normalizeLanguage(value) {
  const normalized = String(value || "").trim().toLowerCase();
  if (normalized.startsWith("en")) {
    return "en";
  }
  if (normalized.startsWith("zh")) {
    return "zh";
  }
  return "";
}

function resolveLanguage({ storedLanguage = "", browserLanguage = "" } = {}) {
  const stored = normalizeLanguage(storedLanguage);
  if (stored) {
    return stored;
  }
  return normalizeLanguage(browserLanguage) === "en" ? "en" : "zh";
}

function getTranslations(language) {
  return TRANSLATIONS[normalizeLanguage(language) || "zh"] || TRANSLATIONS.zh;
}

function buildCodexPromptText(language, details = {}) {
  return buildPetPromptText("custom", language, details);
}

function buildPetPromptText(mode, language, details = {}) {
  const strings = getTranslations(language);
  const defaults = strings.promptDefaults;
  const normalizedMode = mode === "legacy" ? "legacy" : "custom";
  const builder = normalizedMode === "legacy" ? strings.buildLegacyPromptText : strings.buildCustomPromptText;
  return builder({
    name: String(details.name || "").trim() || defaults.name,
    concept: String(details.concept || "").trim() || defaults.concept,
    style: String(details.style || "").trim() || defaults.style,
  });
}

const petGalleryI18nApi = {
  LANGUAGE_STORAGE_KEY,
  SKILL_GITHUB_URL,
  TRANSLATIONS,
  resolveLanguage,
  getTranslations,
  buildPetPromptText,
  buildCodexPromptText,
};

if (typeof globalThis !== "undefined") {
  globalThis.PetGalleryI18n = petGalleryI18nApi;
}

if (typeof exports !== "undefined") {
  exports.LANGUAGE_STORAGE_KEY = LANGUAGE_STORAGE_KEY;
  exports.SKILL_GITHUB_URL = SKILL_GITHUB_URL;
  exports.TRANSLATIONS = TRANSLATIONS;
  exports.resolveLanguage = resolveLanguage;
  exports.getTranslations = getTranslations;
  exports.buildPetPromptText = buildPetPromptText;
  exports.buildCodexPromptText = buildCodexPromptText;
}
})();
