#!/usr/bin/env node

const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const rootDir = process.env.OPENCLAW_RUNTIME_ROOT
  ? path.resolve(process.env.OPENCLAW_RUNTIME_ROOT)
  : fs.existsSync(path.resolve(process.cwd(), "openclaw.json"))
    ? path.resolve(process.cwd())
    : path.resolve(__dirname, "..", "..");
const envFile = path.join(rootDir, ".env");
const configFile = path.join(rootDir, "openclaw.json");
const mem0ModulePath = path.join(
  rootDir,
  "extensions",
  "openclaw-mem0",
  "node_modules",
  "mem0ai",
  "dist",
  "oss",
  "index.js"
);

function loadEnv(filePath) {
  if (!fs.existsSync(filePath)) return;
  for (const rawLine of fs.readFileSync(filePath, "utf8").split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) continue;
    const idx = line.indexOf("=");
    if (idx === -1) continue;
    const key = line.slice(0, idx);
    const value = line.slice(idx + 1);
    if (!(key in process.env)) process.env[key] = value;
  }
}

function resolveEnvVars(value) {
  if (typeof value === "string") {
    return value.replace(/\$\{([^}]+)\}/g, (_, key) => process.env[key] || "");
  }
  if (Array.isArray(value)) {
    return value.map(resolveEnvVars);
  }
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, resolveEnvVars(v)]));
  }
  return value;
}

function buildMemoryConfig() {
  const rawConfig = JSON.parse(fs.readFileSync(configFile, "utf8"));
  const mem0Entry = rawConfig?.plugins?.entries?.["openclaw-mem0"];
  if (!mem0Entry?.config?.oss) {
    throw new Error("openclaw-mem0 OSS config not found in openclaw.json");
  }

  const resolvedConfig = resolveEnvVars(mem0Entry.config);
  return {
    version: "v1.1",
    ...resolvedConfig.oss,
    ...(resolvedConfig.customPrompt ? { customPrompt: resolvedConfig.customPrompt } : {}),
  };
}

async function cleanup(memory, ids, marker, userId) {
  const seen = new Set();
  for (const id of ids) {
    if (!id || seen.has(id)) continue;
    seen.add(id);
    try {
      await memory.delete(id);
    } catch (error) {
      console.warn(`cleanup delete failed for ${id}: ${error}`);
    }
  }

  try {
    const searchResults = await memory.search(marker, { userId, limit: 10, threshold: 0.0 });
    for (const item of searchResults?.results || searchResults || []) {
      if ((item.memory || "").includes(marker) && !seen.has(item.id)) {
        seen.add(item.id);
        try {
          await memory.delete(item.id);
        } catch (error) {
          console.warn(`cleanup search-delete failed for ${item.id}: ${error}`);
        }
      }
    }
  } catch (error) {
    console.warn(`cleanup search failed: ${error}`);
  }
}

async function main() {
  loadEnv(envFile);
  const { Memory } = require(mem0ModulePath);
  const memory = new Memory(buildMemoryConfig());
  const userId = process.env.MEM0_BASE_USER_ID;
  if (!userId) {
    throw new Error("MEM0_BASE_USER_ID is missing");
  }

  const marker = `OPENCLAW_MEM0_E2E_${new Date().toISOString()}_${crypto.randomUUID()}`;
  const fact = `The temporary verification phrase for the OpenClaw memory pipeline is ${marker}.`;

  let addedIds = [];
  try {
    const addResult = await memory.add([{ role: "user", content: fact }], {
      userId,
      infer: false,
      deduced_memories: [fact],
      metadata: { health_check: true, marker, source: "knowledge-watchdog" },
    });

    addedIds = (addResult?.results || []).map((item) => item.id).filter(Boolean);

    const searchResult = await memory.search(marker, { userId, limit: 10, threshold: 0.0 });
    const found = (searchResult?.results || searchResult || []).filter((item) =>
      (item.memory || "").includes(marker)
    );

    if (found.length === 0) {
      throw new Error(`memory marker not found after add: ${marker}`);
    }

    await cleanup(memory, [...addedIds, ...found.map((item) => item.id)], marker, userId);

    const verifyGone = await memory.search(marker, { userId, limit: 10, threshold: 0.0 });
    const leftovers = (verifyGone?.results || verifyGone || []).filter((item) =>
      (item.memory || "").includes(marker)
    );
    if (leftovers.length > 0) {
      throw new Error(`cleanup incomplete for marker: ${marker}`);
    }

    console.log(
      JSON.stringify(
        {
          status: "ok",
          marker,
          addedCount: addResult?.results?.length || 0,
          matchedCount: found.length,
        },
        null,
        2
      )
    );
  } catch (error) {
    await cleanup(memory, addedIds, marker, userId);
    throw error;
  }
}

main().catch((error) => {
  console.error(error && error.stack ? error.stack : String(error));
  process.exit(1);
});
