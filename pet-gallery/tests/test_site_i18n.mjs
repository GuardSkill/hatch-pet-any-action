import test from "node:test";
import assert from "node:assert/strict";

import {
  LANGUAGE_STORAGE_KEY,
  SKILL_GITHUB_URL,
  buildPetPromptText,
  buildCodexPromptText,
  getTranslations,
  resolveLanguage,
} from "../site-i18n.js";

test("resolveLanguage defaults to Chinese unless the browser language is English", () => {
  assert.equal(resolveLanguage({ browserLanguage: "zh-CN" }), "zh");
  assert.equal(resolveLanguage({ browserLanguage: "en-US" }), "en");
  assert.equal(resolveLanguage({ browserLanguage: "ja-JP" }), "zh");
});

test("resolveLanguage prefers a stored manual selection", () => {
  assert.equal(resolveLanguage({ storedLanguage: "en", browserLanguage: "zh-CN" }), "en");
  assert.equal(resolveLanguage({ storedLanguage: "zh", browserLanguage: "en-US" }), "zh");
});

test("buildCodexPromptText points at the GuardSkill GitHub repo in Chinese", () => {
  const prompt = buildCodexPromptText("zh", {
    name: "雪团",
    concept: "一只戴围巾的雪狐",
    style: "粗描边像素风",
  });

  assert.match(prompt, /hatch-pet-any-action/);
  assert.match(prompt, /GuardSkill\/hatch-pet-any-action/);
  assert.match(prompt, /推断动作集合/);
});

test("buildPetPromptText keeps the legacy 9-action Codex prompt path", () => {
  const prompt = buildPetPromptText("legacy", "zh", {
    name: "雪团",
    concept: "一只戴围巾的雪狐",
    style: "粗描边像素风",
  });

  assert.match(prompt, /使用 hatch-pet/);
  assert.match(prompt, /openai\/skills\/tree\/main\/skills\/\.curated\/hatch-pet/);
  assert.doesNotMatch(prompt, /hatch-pet-any-action/);
});

test("buildPetPromptText uses the revised custom-action wording in Chinese", () => {
  const prompt = buildPetPromptText("custom", "zh", {
    name: "雪团",
    concept: "一只戴围巾的雪狐",
    style: "粗描边像素风",
  });

  assert.match(prompt, /请根据自然语言描述推断动作集合，/);
  assert.match(prompt, /请生成完整 宠物资源包/);
  assert.doesNotMatch(prompt, /支持少于或多于 9 个动作/);
});

test("buildCodexPromptText points at the GuardSkill GitHub repo in English", () => {
  const prompt = buildCodexPromptText("en", {
    name: "Frosty",
    concept: "A scarf-wearing snow fox",
    style: "Chunky pixel pet",
  });

  assert.match(prompt, /Use hatch-pet-any-action/);
  assert.match(prompt, /Skill GitHub URL/);
  assert.match(prompt, /GuardSkill\/hatch-pet-any-action/);
});

test("translation helpers expose the configured language storage key and English UI copy", () => {
  assert.equal(LANGUAGE_STORAGE_KEY, "pet-gallery-language");
  assert.equal(SKILL_GITHUB_URL, "https://github.com/GuardSkill/hatch-pet-any-action/hatch-pet-any-action");
  assert.equal(getTranslations("en").refreshLabel, "Refresh");
  assert.equal(getTranslations("zh").refreshLabel, "刷新");
});
