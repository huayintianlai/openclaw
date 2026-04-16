const fs = require("node:fs");
const fsp = require("node:fs/promises");
const path = require("node:path");
const os = require("node:os");
const crypto = require("node:crypto");
const { execFile } = require("node:child_process");
const { promisify } = require("node:util");

const execFileAsync = promisify(execFile);

const DEFAULT_TIMEOUT_MS = 180000;
const DEFAULT_AUTOGLM_TIMEOUT_MS = 300000;
const DEFAULT_ADB_PATH = "/opt/homebrew/bin/adb";
const DEFAULT_AUTOGLM_DIR = "/Users/xiaojiujiu2/Documents/coding/AutoGLM";
const DEFAULT_APP_PACKAGES = {
  chrome: "com.android.chrome",
  rednote: "com.xingin.xhs",
  settings: "com.android.settings",
  wechat: "com.tencent.mm",
  xhs: "com.xingin.xhs",
  xiaohongshu: "com.xingin.xhs"
};
const SAFE_ACTION_KINDS = new Set([
  "back",
  "home",
  "open_app",
  "run_flow",
  "scroll",
  "snapshot",
  "tap_element",
  "wait_for"
]);
const WRITE_ACTION_KINDS = new Set(["input_text"]);
const DANGER_FLOW_IDS = new Set(["draft_message", "mobile-publish"]);

function readPluginString(pluginConfig, key) {
  const value = pluginConfig?.[key];
  return typeof value === "string" && value.trim() ? value.trim() : undefined;
}

function readPluginNumber(pluginConfig, key) {
  const value = pluginConfig?.[key];
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}

function nowIso() {
  return new Date().toISOString();
}

function clone(value) {
  return value == null ? value : JSON.parse(JSON.stringify(value));
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function sanitizeName(value, fallback = "artifact") {
  return String(value || fallback)
    .trim()
    .replace(/[^a-zA-Z0-9._-]+/g, "-")
    .replace(/^-+|-+$/g, "") || fallback;
}

function ensureDirSync(dirPath) {
  fs.mkdirSync(dirPath, { recursive: true });
}

async function ensureDir(dirPath) {
  await fsp.mkdir(dirPath, { recursive: true });
}

function exists(filePath) {
  try {
    fs.accessSync(filePath);
    return true;
  } catch {
    return false;
  }
}

function readJsonSync(filePath, fallback) {
  try {
    if (!exists(filePath)) {
      return clone(fallback);
    }
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch {
    return clone(fallback);
  }
}

async function writeJson(filePath, value) {
  await ensureDir(path.dirname(filePath));
  const payload = `${JSON.stringify(value, null, 2)}\n`;
  await fsp.writeFile(filePath, payload, "utf8");
}

async function appendJsonl(filePath, value) {
  await ensureDir(path.dirname(filePath));
  await fsp.appendFile(filePath, `${JSON.stringify(value)}\n`, "utf8");
}

async function writeText(filePath, value) {
  await ensureDir(path.dirname(filePath));
  await fsp.writeFile(filePath, value, "utf8");
}

async function writeBuffer(filePath, buffer) {
  await ensureDir(path.dirname(filePath));
  await fsp.writeFile(filePath, buffer);
}

function normalizeArray(value) {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter(Boolean);
}

function normalizeSelector(selector) {
  if (!selector) {
    return null;
  }
  if (typeof selector === "string") {
    return { textContains: selector, descriptionContains: selector };
  }
  return selector;
}

function decodeXml(value) {
  return String(value || "")
    .replace(/&quot;/g, "\"")
    .replace(/&apos;/g, "'")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&amp;/g, "&");
}

function parseBounds(bounds) {
  const match = /^\[(\d+),(\d+)\]\[(\d+),(\d+)\]$/.exec(String(bounds || ""));
  if (!match) {
    return null;
  }
  const left = Number(match[1]);
  const top = Number(match[2]);
  const right = Number(match[3]);
  const bottom = Number(match[4]);
  return {
    left,
    top,
    right,
    bottom,
    centerX: Math.round((left + right) / 2),
    centerY: Math.round((top + bottom) / 2),
    width: right - left,
    height: bottom - top
  };
}

function summarizeElement(node) {
  const label = [node.text, node.contentDesc, node.resourceId, node.className]
    .map((item) => String(item || "").trim())
    .filter(Boolean)
    .join(" | ");
  return label || "(anonymous element)";
}

function parseUiNodes(xml) {
  const nodes = [];
  const source = String(xml || "");
  const regex = /<node\b([^>]*)\/>/g;
  let match;
  while ((match = regex.exec(source))) {
    const attrChunk = match[1];
    const attrs = {};
    const attrRegex = /([a-zA-Z0-9_-]+)="([^"]*)"/g;
    let attrMatch;
    while ((attrMatch = attrRegex.exec(attrChunk))) {
      attrs[attrMatch[1]] = decodeXml(attrMatch[2]);
    }
    const bounds = parseBounds(attrs.bounds);
    nodes.push({
      index: Number(attrs.index || 0),
      text: attrs.text || "",
      resourceId: attrs["resource-id"] || "",
      className: attrs.class || "",
      packageName: attrs.package || "",
      contentDesc: attrs["content-desc"] || "",
      clickable: attrs.clickable === "true",
      enabled: attrs.enabled !== "false",
      focusable: attrs.focusable === "true",
      focused: attrs.focused === "true",
      scrollable: attrs.scrollable === "true",
      selected: attrs.selected === "true",
      bounds,
      raw: attrs
    });
  }
  return nodes;
}

function scoreNode(node, selector) {
  if (!selector) {
    return 0;
  }
  if (Array.isArray(selector.anyOf) && selector.anyOf.length > 0) {
    return Math.max(...selector.anyOf.map((item) => scoreNode(node, item)));
  }
  let score = 0;
  const check = [
    ["text", 10, (expected) => node.text === expected],
    ["textContains", 6, (expected) => node.text.includes(expected)],
    ["description", 10, (expected) => node.contentDesc === expected],
    ["descriptionContains", 6, (expected) => node.contentDesc.includes(expected)],
    ["resourceId", 9, (expected) => node.resourceId === expected],
    ["className", 5, (expected) => node.className === expected],
    ["packageName", 4, (expected) => node.packageName === expected]
  ];
  for (const [key, weight, predicate] of check) {
    if (typeof selector[key] === "string" && selector[key]) {
      if (!predicate(selector[key])) {
        return -1;
      }
      score += weight;
    }
  }
  if (typeof selector.clickable === "boolean") {
    if (node.clickable !== selector.clickable) {
      return -1;
    }
    score += 2;
  }
  if (typeof selector.focused === "boolean") {
    if (node.focused !== selector.focused) {
      return -1;
    }
    score += 2;
  }
  if (typeof selector.index === "number") {
    if (node.index !== selector.index) {
      return -1;
    }
    score += 1;
  }
  if (score === 0 && selector.preferInteractive) {
    score += node.clickable || node.focusable ? 1 : 0;
  }
  return score;
}

function findNode(nodes, selector) {
  const normalized = normalizeSelector(selector);
  if (!normalized) {
    return null;
  }
  const scored = nodes
    .map((node) => ({ node, score: scoreNode(node, normalized) }))
    .filter((item) => item.score >= 0)
    .sort((a, b) => b.score - a.score);
  if (scored.length === 0) {
    return null;
  }
  const nth = typeof normalized.nth === "number" ? normalized.nth : 0;
  return scored[nth]?.node || scored[0].node;
}

function summarizeNodes(nodes) {
  return nodes
    .filter((node) => node.enabled)
    .slice(0, 15)
    .map((node, index) => `${index + 1}. ${summarizeElement(node)}`)
    .join("\n");
}

function formatDeviceLine(device) {
  return [
    `${device.alias} (${device.display_name || device.id})`,
    `backend=${device.backend}`,
    `status=${device.status}`,
    device.lock_state?.locked ? `locked_by=${device.lock_state.task_id}` : "",
    normalizeArray(device.labels).length ? `labels=${device.labels.join(",")}` : ""
  ].filter(Boolean).join(" | ");
}

function escapeAdbText(value) {
  return String(value)
    .replace(/ /g, "%s")
    .replace(/&/g, "\\&")
    .replace(/\(/g, "\\(")
    .replace(/\)/g, "\\)")
    .replace(/</g, "\\<")
    .replace(/>/g, "\\>")
    .replace(/"/g, "\\\"")
    .replace(/'/g, "\\'");
}

function isAsciiText(value) {
  return /^[\x20-\x7E]*$/.test(String(value || ""));
}

function resolveAppPackage(app) {
  if (!app) {
    return "";
  }
  const key = String(app).trim();
  return DEFAULT_APP_PACKAGES[key] || key;
}

function isXhsPackage(app) {
  const pkg = resolveAppPackage(app);
  return pkg === DEFAULT_APP_PACKAGES.xhs;
}

async function runCommand(command, args, options = {}) {
  return execFileAsync(command, args, {
    cwd: options.cwd,
    env: options.env,
    timeout: options.timeout ?? DEFAULT_TIMEOUT_MS,
    maxBuffer: options.maxBuffer ?? 10 * 1024 * 1024,
    encoding: options.encoding ?? "utf8"
  });
}

async function runBinaryCommand(command, args, options = {}) {
  return execFileAsync(command, args, {
    cwd: options.cwd,
    env: options.env,
    timeout: options.timeout ?? DEFAULT_TIMEOUT_MS,
    maxBuffer: options.maxBuffer ?? 20 * 1024 * 1024,
    encoding: "buffer"
  });
}

function resolveConfig(pluginConfig, logger) {
  const repoRoot = readPluginString(pluginConfig, "repoRoot") || process.cwd();
  const stateDir = readPluginString(pluginConfig, "stateDir") || path.join(repoRoot, "state", "mobile-runtime");
  const config = {
    repoRoot,
    stateDir,
    adbPath: readPluginString(pluginConfig, "adbPath") || DEFAULT_ADB_PATH,
    autoGlmDir: readPluginString(pluginConfig, "autoGlmDir") || DEFAULT_AUTOGLM_DIR,
    flowDir: readPluginString(pluginConfig, "flowDir") || path.join(repoRoot, "flows", "mobile"),
    registryPath: readPluginString(pluginConfig, "registryPath") || path.join(repoRoot, "devices", "mobile.registry.json"),
    devicesPairedPath: path.join(repoRoot, "devices", "paired.json"),
    nodesPairedPath: path.join(repoRoot, "nodes", "paired.json"),
    nodesPendingPath: path.join(repoRoot, "nodes", "pending.json"),
    artifactsDir: path.join(stateDir, "artifacts"),
    tasksFile: path.join(stateDir, "tasks.json"),
    locksFile: path.join(stateDir, "locks.json"),
    approvalsFile: path.join(stateDir, "approvals.json"),
    auditFile: path.join(stateDir, "audit.jsonl"),
    defaultBackend: readPluginString(pluginConfig, "defaultBackend") || "mac-proxy",
    defaultTaskTimeoutMs: readPluginNumber(pluginConfig, "defaultTaskTimeoutMs") || DEFAULT_TIMEOUT_MS,
    autoGlmTimeoutMs: readPluginNumber(pluginConfig, "autoGlmTimeoutMs") || DEFAULT_AUTOGLM_TIMEOUT_MS
  };
  if (logger?.info) {
    logger.info(`mobile-runtime-plugin: config registry=${config.registryPath}`);
  }
  return config;
}

class FileControlPlane {
  constructor(config) {
    this.config = config;
  }

  async init() {
    await ensureDir(this.config.stateDir);
    await ensureDir(this.config.artifactsDir);
    if (!exists(this.config.tasksFile)) {
      await writeJson(this.config.tasksFile, {});
    }
    if (!exists(this.config.locksFile)) {
      await writeJson(this.config.locksFile, {});
    }
    if (!exists(this.config.approvalsFile)) {
      await writeJson(this.config.approvalsFile, {});
    }
  }

  loadTasks() {
    return readJsonSync(this.config.tasksFile, {});
  }

  loadLocks() {
    return readJsonSync(this.config.locksFile, {});
  }

  loadApprovals() {
    return readJsonSync(this.config.approvalsFile, {});
  }

  async saveTasks(tasks) {
    await writeJson(this.config.tasksFile, tasks);
  }

  async saveLocks(locks) {
    await writeJson(this.config.locksFile, locks);
  }

  async saveApprovals(approvals) {
    await writeJson(this.config.approvalsFile, approvals);
  }

  async log(event) {
    await appendJsonl(this.config.auditFile, event);
  }
}

class MacProxyBackend {
  constructor(runtime) {
    this.runtime = runtime;
    this.kind = "mac-proxy";
  }

  async status(device) {
    const adbState = await this.runtime.getAdbDeviceState(device.adbSerial);
    return {
      backend: this.kind,
      online: adbState === "device",
      transport: "adb",
      adb_state: adbState || "offline"
    };
  }

  async observe(device, options = {}) {
    const observation = await this.runtime.captureAdbObservation(device, options);
    return {
      observation,
      fallback_used: []
    };
  }

  async act(device, action) {
    return this.runtime.executeMacProxyAction(device, action);
  }

  async runTask(device, request) {
    return this.runtime.executeTaskWithMacProxy(device, request);
  }
}

class AndroidNodeBackend {
  constructor(runtime) {
    this.runtime = runtime;
    this.kind = "android-node";
  }

  async status(device) {
    const paired = this.runtime.getPairedNode(device.nodeId);
    const pending = this.runtime.getPendingNode(device.nodeId);
    return {
      backend: this.kind,
      online: Boolean(paired || pending),
      transport: paired ? "node" : (device.adbSerial ? "adb-bridge" : "unavailable"),
      node_id: device.nodeId || null,
      remote_ip: paired?.remoteIp || pending?.remoteIp || null,
      commands: normalizeArray(pending?.commands)
    };
  }

  async observe(device, options = {}) {
    if (device.adbSerial) {
      const delegated = await this.runtime.macProxyBackend.observe(device, options);
      delegated.fallback_used = normalizeArray(delegated.fallback_used).concat("android-node:adb-bridge");
      return delegated;
    }
    return {
      observation: {
        foreground_app: "",
        screen_ref: "",
        ui_tree_ref: "",
        elements_summary: "",
        timestamp: nowIso(),
        backend: this.kind
      },
      fallback_used: ["android-node:metadata-only"]
    };
  }

  async act(device, action) {
    if (device.adbSerial) {
      const delegated = await this.runtime.macProxyBackend.act(device, action);
      delegated.fallback_used = normalizeArray(delegated.fallback_used).concat("android-node:adb-bridge");
      return delegated;
    }
    throw new Error("android-node transport is not connected yet");
  }

  async runTask(device, request) {
    if (device.adbSerial) {
      const delegated = await this.runtime.macProxyBackend.runTask(device, request);
      delegated.fallback_used = normalizeArray(delegated.fallback_used).concat("android-node:adb-bridge");
      return delegated;
    }
    throw new Error("android-node transport is not connected yet");
  }
}

class MobileRuntime {
  constructor(config, logger) {
    this.config = config;
    this.logger = logger || console;
    this.controlPlane = new FileControlPlane(config);
    this.macProxyBackend = new MacProxyBackend(this);
    this.androidNodeBackend = new AndroidNodeBackend(this);
  }

  async init() {
    await this.controlPlane.init();
  }

  loadRegistry() {
    const payload = readJsonSync(this.config.registryPath, { version: 1, devices: [] });
    const devices = Array.isArray(payload.devices) ? payload.devices : [];
    return {
      version: payload.version || 1,
      defaults: payload.defaults || {},
      appPackages: payload.appPackages || {},
      devices
    };
  }

  getPairedNode(nodeId) {
    if (!nodeId) {
      return null;
    }
    const paired = readJsonSync(this.config.devicesPairedPath, {});
    return paired[nodeId] || null;
  }

  getPendingNode(nodeId) {
    if (!nodeId) {
      return null;
    }
    const pending = readJsonSync(this.config.nodesPendingPath, {});
    const entries = Object.values(pending);
    return entries.find((item) => item && item.nodeId === nodeId) || null;
  }

  async getAdbDeviceState(serial) {
    if (!serial) {
      return "";
    }
    try {
      const { stdout } = await runCommand(this.config.adbPath, ["devices"], {
        timeout: 10000
      });
      const line = String(stdout || "")
        .split(/\r?\n/)
        .slice(1)
        .find((item) => item.trim().startsWith(serial));
      if (!line) {
        return "";
      }
      return line.trim().split(/\s+/)[1] || "";
    } catch {
      return "";
    }
  }

  async describeDevices(filters = {}) {
    const registry = this.loadRegistry();
    const locks = this.controlPlane.loadLocks();
    const descriptors = [];
    for (const device of registry.devices) {
      const backend = this.resolvePreferredBackend(device);
      const backendImpl = this.getBackend(backend);
      const statusDetails = await backendImpl.status(device);
      descriptors.push({
        id: device.id || device.alias,
        alias: device.alias,
        platform: device.platform || "android",
        backend,
        status: statusDetails.online ? (locks[device.alias] ? "busy" : "online") : "offline",
        capabilities: normalizeArray(device.capabilities).concat(normalizeArray(statusDetails.commands)),
        labels: normalizeArray(device.labels),
        lock_state: locks[device.alias]
          ? {
              locked: true,
              task_id: locks[device.alias].task_id,
              agent_id: locks[device.alias].agent_id,
              acquired_at: locks[device.alias].acquired_at
            }
          : { locked: false },
        risk_profile: device.risk_profile || "standard",
        display_name: device.display_name || device.alias,
        transport: statusDetails.transport,
        fallback_backend: device.fallback_backend || null,
        remote_ip: statusDetails.remote_ip || null
      });
    }
    return descriptors.filter((device) => {
      if (filters.alias && device.alias !== filters.alias) {
        return false;
      }
      if (filters.backend && device.backend !== filters.backend) {
        return false;
      }
      if (filters.platform && device.platform !== filters.platform) {
        return false;
      }
      if (Array.isArray(filters.labels) && filters.labels.length > 0) {
        return filters.labels.every((label) => device.labels.includes(label));
      }
      return true;
    });
  }

  resolvePreferredBackend(device) {
    const preferred = device.preferred_backend || this.config.defaultBackend;
    if (preferred === "android-node" && device.nodeId) {
      return "android-node";
    }
    return "mac-proxy";
  }

  getBackend(kind) {
    return kind === "android-node" ? this.androidNodeBackend : this.macProxyBackend;
  }

  async selectDevice(deviceSelector = {}, options = {}) {
    const devices = await this.describeDevices(deviceSelector);
    const alias = deviceSelector?.alias;
    const primary = alias ? devices.find((item) => item.alias === alias) : null;
    const unlocked = devices.filter((item) => item.status === "online");
    if (primary && primary.status === "online") {
      return primary;
    }
    if (primary && primary.status === "busy" && !options.allowAlternateDevice) {
      return primary;
    }
    if (unlocked.length > 0) {
      return unlocked[0];
    }
    if (primary) {
      return primary;
    }
    return devices[0] || null;
  }

  async ensureLock(deviceAlias, task) {
    const locks = this.controlPlane.loadLocks();
    const existing = locks[deviceAlias];
    if (existing && existing.task_id !== task.task_id) {
      return { ok: false, lock: existing };
    }
    locks[deviceAlias] = {
      task_id: task.task_id,
      agent_id: task.agent_id,
      session_key: task.session_key || "",
      acquired_at: nowIso()
    };
    await this.controlPlane.saveLocks(locks);
    return { ok: true, lock: locks[deviceAlias] };
  }

  async releaseLock(deviceAlias, taskId) {
    const locks = this.controlPlane.loadLocks();
    if (locks[deviceAlias] && (!taskId || locks[deviceAlias].task_id === taskId)) {
      delete locks[deviceAlias];
      await this.controlPlane.saveLocks(locks);
    }
  }

  async upsertTask(task) {
    const tasks = this.controlPlane.loadTasks();
    tasks[task.task_id] = task;
    await this.controlPlane.saveTasks(tasks);
  }

  async writeArtifact(taskId, alias, extension, content, isBinary = false) {
    const fileName = `${sanitizeName(alias)}-${Date.now()}-${crypto.randomUUID().slice(0, 8)}.${extension}`;
    const destination = path.join(this.config.artifactsDir, sanitizeName(taskId), fileName);
    if (isBinary) {
      await writeBuffer(destination, content);
    } else {
      await writeText(destination, content);
    }
    return destination;
  }

  async captureAdbObservation(device, options = {}) {
    const screenshotPath = options.include_screenshot === false
      ? ""
      : await this.captureScreenshot(device);
    const uiDump = await this.captureUiTree(device);
    const uiTreePath = await this.writeArtifact(
      crypto.randomUUID(),
      device.alias,
      "xml",
      uiDump
    );
    const nodes = parseUiNodes(uiDump);
    const foreground = await this.getForegroundActivity(device);
    return {
      foreground_app: foreground.packageName || "",
      foreground_activity: foreground.activity || "",
      screen_ref: screenshotPath,
      ui_tree_ref: uiTreePath,
      elements_summary: summarizeNodes(nodes),
      timestamp: nowIso(),
      backend: "mac-proxy",
      node_count: nodes.length
    };
  }

  async getForegroundActivity(device) {
    try {
      const { stdout } = await runCommand(this.config.adbPath, [
        "-s",
        device.adbSerial,
        "shell",
        "dumpsys",
        "activity",
        "activities"
      ], {
        timeout: 10000
      });
      const line = String(stdout || "")
        .split(/\r?\n/)
        .find((item) => item.includes("mResumedActivity"));
      if (!line) {
        return { packageName: "", activity: "" };
      }
      const match = / ([A-Za-z0-9._$]+)\/([A-Za-z0-9._$]+) /.exec(line);
      if (!match) {
        return { packageName: "", activity: "" };
      }
      return {
        packageName: match[1],
        activity: match[2]
      };
    } catch {
      return { packageName: "", activity: "" };
    }
  }

  async captureUiTree(device) {
    const { stdout } = await runCommand(this.config.adbPath, [
      "-s",
      device.adbSerial,
      "shell",
      "sh",
      "-c",
      "uiautomator dump /sdcard/window_dump.xml >/dev/null 2>&1 && cat /sdcard/window_dump.xml"
    ], {
      timeout: 20000,
      maxBuffer: 20 * 1024 * 1024
    });
    return String(stdout || "").trim();
  }

  async captureScreenshot(device) {
    const taskId = crypto.randomUUID();
    const destination = path.join(this.config.artifactsDir, sanitizeName(taskId), `${sanitizeName(device.alias)}-screen.png`);
    await ensureDir(path.dirname(destination));
    const { stdout } = await runBinaryCommand(this.config.adbPath, [
      "-s",
      device.adbSerial,
      "exec-out",
      "screencap",
      "-p"
    ], {
      timeout: 20000
    });
    await writeBuffer(destination, Buffer.from(stdout));
    return destination;
  }

  async executeAdb(device, adbArgs, options = {}) {
    return runCommand(this.config.adbPath, ["-s", device.adbSerial, ...adbArgs], options);
  }

  async getWifiStatus(device) {
    try {
      const { stdout } = await this.executeAdb(device, ["shell", "cmd", "wifi", "status"], {
        timeout: 10000
      });
      const text = String(stdout || "");
      return {
        enabled: /Wifi is enabled/i.test(text),
        connected: /Wifi is connected/i.test(text),
        raw: text.trim()
      };
    } catch (error) {
      return {
        enabled: false,
        connected: false,
        raw: String(error)
      };
    }
  }

  async setWifiEnabled(device, enabled) {
    await this.executeAdb(device, ["shell", "svc", "wifi", enabled ? "enable" : "disable"], {
      timeout: 15000
    });
    await sleep(1500);
    return this.getWifiStatus(device);
  }

  async enforceAppLaunchGuard(device, app, precondition = {}) {
    if (!isXhsPackage(app)) {
      return null;
    }
    const wifi = await this.getWifiStatus(device);
    if (!wifi.enabled) {
      return wifi;
    }
    if (precondition?.wifi === "off" && precondition?.auto_disable === true) {
      return this.setWifiEnabled(device, false);
    }
    throw new Error("xhs_wifi_guard: Wi-Fi is enabled; refusing to open XHS without an explicit wifi-off precondition");
  }

  async executeMacProxyAction(device, action) {
    const steps = [];
    const fallbackUsed = [];
    const observation = action.observe_first
      ? await this.captureAdbObservation(device, {})
      : null;
    let lastObservation = observation;
    if (action.kind === "open_app") {
      const pkg = resolveAppPackage(action.app);
      await this.enforceAppLaunchGuard(device, pkg, action.precondition);
      await this.executeAdb(device, ["shell", "monkey", "-p", pkg, "-c", "android.intent.category.LAUNCHER", "1"]);
      steps.push({ kind: action.kind, status: "completed", package: pkg, at: nowIso() });
      lastObservation = await this.captureAdbObservation(device, {});
    } else if (action.kind === "wait_for") {
      const timeoutMs = Number(action.timeout_ms || 10000);
      const startedAt = Date.now();
      const selector = normalizeSelector(action.selector);
      let matched = !selector;
      while (Date.now() - startedAt < timeoutMs) {
        lastObservation = await this.captureAdbObservation(device, { include_screenshot: false });
        if (!selector) {
          matched = true;
          break;
        }
        const xml = await fsp.readFile(lastObservation.ui_tree_ref, "utf8");
        const node = findNode(parseUiNodes(xml), selector);
        if (node) {
          matched = true;
          break;
        }
        await sleep(750);
      }
      if (!matched) {
        throw new Error(`wait_for timed out after ${timeoutMs}ms`);
      }
      steps.push({ kind: action.kind, status: "completed", at: nowIso() });
    } else if (action.kind === "tap_element") {
      const observed = lastObservation || await this.captureAdbObservation(device, { include_screenshot: false });
      const xml = await fsp.readFile(observed.ui_tree_ref, "utf8");
      const node = findNode(parseUiNodes(xml), action.selector);
      if (!node || !node.bounds) {
        throw new Error("semantic element not found");
      }
      await this.executeAdb(device, [
        "shell",
        "input",
        "tap",
        String(node.bounds.centerX),
        String(node.bounds.centerY)
      ]);
      steps.push({
        kind: action.kind,
        status: "completed",
        target: summarizeElement(node),
        at: nowIso()
      });
      lastObservation = await this.captureAdbObservation(device, {});
    } else if (action.kind === "input_text") {
      if (action.selector) {
        const tapResult = await this.executeMacProxyAction(device, {
          kind: "tap_element",
          selector: action.selector
        });
        steps.push(...tapResult.steps);
        fallbackUsed.push(...normalizeArray(tapResult.fallback_used));
      }
      const text = String(action.text || "");
      if (isAsciiText(text) && text) {
        await this.executeAdb(device, ["shell", "input", "text", escapeAdbText(text)]);
      } else {
        const fallback = await this.runAutoGlmTask(device, `在当前页面输入以下文本，不要发送：${text}`);
        fallbackUsed.push("autoglm-input");
        steps.push({
          kind: "input_text",
          status: "completed",
          mode: "autoglm",
          at: nowIso()
        });
        return {
          status: "completed",
          steps,
          last_observation: await this.captureAdbObservation(device, {}),
          fallback_used: fallbackUsed,
          backend: "mac-proxy",
          details: {
            autoglm: fallback
          }
        };
      }
      steps.push({
        kind: action.kind,
        status: "completed",
        text_preview: text.slice(0, 32),
        at: nowIso()
      });
      lastObservation = await this.captureAdbObservation(device, {});
    } else if (action.kind === "scroll") {
      const direction = String(action.direction || "down");
      const size = await this.getScreenSize(device);
      const midX = Math.floor(size.width / 2);
      const startY = direction === "down" ? Math.floor(size.height * 0.72) : Math.floor(size.height * 0.32);
      const endY = direction === "down" ? Math.floor(size.height * 0.28) : Math.floor(size.height * 0.72);
      await this.executeAdb(device, [
        "shell",
        "input",
        "swipe",
        String(midX),
        String(startY),
        String(midX),
        String(endY),
        String(Number(action.duration_ms || 250))
      ]);
      steps.push({ kind: action.kind, status: "completed", direction, at: nowIso() });
      lastObservation = await this.captureAdbObservation(device, {});
    } else if (action.kind === "back" || action.kind === "home") {
      const keycode = action.kind === "back" ? "4" : "3";
      await this.executeAdb(device, ["shell", "input", "keyevent", keycode]);
      steps.push({ kind: action.kind, status: "completed", at: nowIso() });
      lastObservation = await this.captureAdbObservation(device, {});
    } else if (action.kind === "snapshot") {
      lastObservation = await this.captureAdbObservation(device, {});
      steps.push({ kind: action.kind, status: "completed", at: nowIso() });
    } else if (action.kind === "run_flow") {
      return this.executeTaskWithMacProxy(device, {
        task_id: crypto.randomUUID(),
        agent_id: "mobile-runtime",
        session_key: "",
        flow_id: action.flow_id,
        inputs: action.inputs || {},
        risk_level: action.risk_level || "safe",
        approval_policy: action.approval_policy || "auto",
        max_steps: action.max_steps || 20
      });
    } else {
      throw new Error(`unsupported action kind: ${action.kind}`);
    }

    return {
      status: "completed",
      steps,
      last_observation: lastObservation,
      fallback_used: fallbackUsed,
      backend: "mac-proxy"
    };
  }

  async getScreenSize(device) {
    try {
      const { stdout } = await this.executeAdb(device, ["shell", "wm", "size"], {
        timeout: 10000
      });
      const match = /Physical size:\s*(\d+)x(\d+)/.exec(String(stdout || ""));
      if (match) {
        return { width: Number(match[1]), height: Number(match[2]) };
      }
    } catch {}
    return { width: 1080, height: 2400 };
  }

  async loadFlow(flowId) {
    const filePath = path.join(this.config.flowDir, `${sanitizeName(flowId)}.json`);
    if (!exists(filePath)) {
      throw new Error(`flow not found: ${flowId}`);
    }
    return readJsonSync(filePath, {});
  }

  resolveTemplateValue(template, inputs) {
    if (typeof template === "string") {
      return template.replace(/\$([a-zA-Z0-9_]+)/g, (_match, name) => {
        const value = inputs?.[name];
        return value == null ? "" : String(value);
      });
    }
    if (Array.isArray(template)) {
      return template.map((item) => this.resolveTemplateValue(item, inputs));
    }
    if (template && typeof template === "object") {
      const output = {};
      for (const [key, value] of Object.entries(template)) {
        output[key] = this.resolveTemplateValue(value, inputs);
      }
      return output;
    }
    return template;
  }

  inferRiskLevel(actionOrTask) {
    if (actionOrTask.risk_level) {
      return actionOrTask.risk_level;
    }
    if (actionOrTask.flow_id && DANGER_FLOW_IDS.has(actionOrTask.flow_id)) {
      return "danger";
    }
    if (actionOrTask.flow_id) {
      return "safe";
    }
    if (WRITE_ACTION_KINDS.has(actionOrTask.kind)) {
      return "write";
    }
    if (SAFE_ACTION_KINDS.has(actionOrTask.kind)) {
      return "safe";
    }
    if (actionOrTask.intent) {
      return "danger";
    }
    return "danger";
  }

  resolveTaskApp(request) {
    return request.app || request.inputs?.app || "";
  }

  async enforceTaskGuards(device, request) {
    const app = this.resolveTaskApp(request);
    if (!app) {
      return null;
    }
    return this.enforceAppLaunchGuard(device, app, request.precondition || {});
  }

  async maybeRequireApproval(task, actionOrTask) {
    const riskLevel = this.inferRiskLevel(actionOrTask);
    const policy = actionOrTask.approval_policy || task.approval_policy || "auto";
    if (actionOrTask.requires_approval === true && policy !== "approved" && policy !== "auto-approved") {
      const approvalId = crypto.randomUUID();
      const approval = {
        approval_id: approvalId,
        task_id: task.task_id,
        agent_id: task.agent_id,
        risk_level: "danger",
        requested_at: nowIso(),
        status: "pending",
        reason: actionOrTask.intent || actionOrTask.flow_id || actionOrTask.kind || "manual_approval"
      };
      const approvals = this.controlPlane.loadApprovals();
      approvals[approvalId] = approval;
      await this.controlPlane.saveApprovals(approvals);
      return approval;
    }
    if (riskLevel === "safe") {
      return null;
    }
    if (policy === "approved" || policy === "auto-approved") {
      return null;
    }
    const approvalId = crypto.randomUUID();
    const approval = {
      approval_id: approvalId,
      task_id: task.task_id,
      agent_id: task.agent_id,
      risk_level: riskLevel,
      requested_at: nowIso(),
      status: "pending",
      reason: actionOrTask.intent || actionOrTask.flow_id || actionOrTask.kind
    };
    const approvals = this.controlPlane.loadApprovals();
    approvals[approvalId] = approval;
    await this.controlPlane.saveApprovals(approvals);
    return approval;
  }

  async executeTaskWithMacProxy(device, request) {
    const flow = request.flow_id ? await this.loadFlow(request.flow_id) : null;
    await this.enforceTaskGuards(device, request);
    const approval = await this.maybeRequireApproval(request, request);
    if (approval) {
      return {
        status: "needs_approval",
        completion_reason: "approval_required",
        steps: [],
        last_observation: null,
        fallback_used: [],
        approval_events: [approval],
        backend: "mac-proxy"
      };
    }

    const steps = [];
    const fallbackUsed = [];
    let lastObservation = null;
    if (flow) {
      const flowSteps = normalizeArray(flow.steps).slice(0, Number(request.max_steps || 20));
      for (const rawStep of flowSteps) {
        const action = this.resolveTemplateValue(rawStep, request.inputs || {});
        const actionApproval = await this.maybeRequireApproval(request, action);
        if (actionApproval) {
          return {
            status: "needs_approval",
            completion_reason: "approval_required",
            steps,
            last_observation: lastObservation,
            fallback_used: fallbackUsed,
            approval_events: [actionApproval],
            backend: "mac-proxy"
          };
        }
        try {
          const result = await this.executeMacProxyAction(device, action);
          steps.push(...normalizeArray(result.steps));
          fallbackUsed.push(...normalizeArray(result.fallback_used));
          lastObservation = result.last_observation || lastObservation;
          if (action.postcondition && lastObservation?.ui_tree_ref) {
            const xml = await fsp.readFile(lastObservation.ui_tree_ref, "utf8");
            const matched = findNode(parseUiNodes(xml), action.postcondition.selector);
            if (!matched) {
              throw new Error("postcondition failed");
            }
          }
        } catch (error) {
          const fallbackIntent = this.buildFallbackIntent(request);
          if (fallbackIntent) {
            await this.enforceTaskGuards(device, {
              ...request,
              intent: fallbackIntent
            });
            const autoglm = await this.runAutoGlmTask(device, fallbackIntent);
            fallbackUsed.push("autoglm-task");
            steps.push({
              kind: "fallback",
              status: "completed",
              mode: "autoglm",
              note: String(error),
              at: nowIso()
            });
            lastObservation = await this.captureAdbObservation(device, {});
            return {
              status: "completed",
              completion_reason: "completed_with_fallback",
              steps,
              last_observation: lastObservation,
              fallback_used: fallbackUsed,
              approval_events: [],
              backend: "mac-proxy",
              details: {
                autoglm
              }
            };
          }
          throw error;
        }
      }
      return {
        status: "completed",
        completion_reason: "flow_completed",
        steps,
        last_observation: lastObservation,
        fallback_used: fallbackUsed,
        approval_events: [],
        backend: "mac-proxy"
      };
    }

    if (request.intent) {
      await this.enforceTaskGuards(device, request);
      const autoglm = await this.runAutoGlmTask(device, request.intent);
      lastObservation = await this.captureAdbObservation(device, {});
      return {
        status: "completed",
        completion_reason: "intent_completed_with_autoglm",
        steps: [
          {
            kind: "intent",
            status: "completed",
            at: nowIso()
          }
        ],
        last_observation: lastObservation,
        fallback_used: ["autoglm-task"],
        approval_events: [],
        backend: "mac-proxy",
        details: {
          autoglm
        }
      };
    }

    lastObservation = await this.captureAdbObservation(device, {});
    return {
      status: "completed",
      completion_reason: "observe_only",
      steps,
      last_observation: lastObservation,
      fallback_used: fallbackUsed,
      approval_events: [],
      backend: "mac-proxy"
    };
  }

  async runAutoGlmTask(device, intent) {
    if (!device.autoglm_device_number) {
      throw new Error(`device ${device.alias} has no AutoGLM mapping`);
    }
    const scriptPath = path.join(this.config.autoGlmDir, "start_phone.sh");
    if (!exists(scriptPath)) {
      throw new Error(`AutoGLM launcher not found at ${scriptPath}`);
    }
    const { stdout, stderr } = await runCommand(scriptPath, [
      String(device.autoglm_device_number),
      String(intent)
    ], {
      cwd: this.config.autoGlmDir,
      timeout: this.config.autoGlmTimeoutMs,
      maxBuffer: 20 * 1024 * 1024
    });
    return {
      command: scriptPath,
      stdout: String(stdout || "").trim().slice(-4000),
      stderr: String(stderr || "").trim().slice(-2000)
    };
  }

  buildFallbackIntent(request) {
    if (request.intent) {
      return request.intent;
    }
    const inputs = request.inputs || {};
    if (request.flow_id === "search_in_app") {
      return `打开${inputs.app || request.app || "目标应用"}并搜索${inputs.query || "目标关键词"}`;
    }
    if (request.flow_id === "wechat_read_only") {
      return `打开微信，搜索${inputs.chat_name || "目标会话"}并进入聊天页面，只查看不要发送消息`;
    }
    if (request.flow_id === "draft_message") {
      return `打开微信，搜索${inputs.chat_name || "目标会话"}，进入聊天后输入以下内容但不要发送：${inputs.message || ""}`;
    }
    if (request.app) {
      return `打开${request.app}`;
    }
    return "";
  }

  async createTaskRecord(toolCtx, params, device) {
    const taskId = params.task_id || crypto.randomUUID();
    return {
      task_id: taskId,
      agent_id: toolCtx.agentId || params.agent_id || "unknown",
      session_key: toolCtx.sessionKey || "",
      created_at: nowIso(),
      updated_at: nowIso(),
      device_alias: device.alias,
      backend: device.backend,
      request: clone(params),
      status: "created",
      steps: [],
      fallback_used: [],
      approval_events: [],
      artifacts: [],
      completion_reason: ""
    };
  }

  async runManagedTask(toolCtx, params, executeFn) {
    const allowAlternate = params.allow_alternate_device !== false;
    const deviceSelector = typeof params.device_selector === "object" ? params.device_selector : {};
    const selected = await this.selectDevice(deviceSelector, {
      allowAlternateDevice: allowAlternate
    });
    if (!selected) {
      throw new Error("no mobile device matched the selector");
    }
    const registry = this.loadRegistry();
    const registryDevice = registry.devices.find((item) => item.alias === selected.alias);
    const task = await this.createTaskRecord(toolCtx, params, registryDevice || selected);
    const lock = await this.ensureLock(selected.alias, task);
    if (!lock.ok) {
      task.status = params.queue_if_busy ? "queued" : "blocked";
      task.completion_reason = params.queue_if_busy ? "device_busy_queued" : "device_busy";
      task.updated_at = nowIso();
      await this.upsertTask(task);
      return {
        task,
        result: {
          status: task.status,
          completion_reason: task.completion_reason,
          steps: [],
          last_observation: null,
          fallback_used: [],
          approval_events: [],
          backend: selected.backend
        }
      };
    }

    try {
      task.status = "running";
      task.updated_at = nowIso();
      await this.upsertTask(task);
      const result = await executeFn(registryDevice || selected, task);
      task.status = result.status;
      task.updated_at = nowIso();
      task.steps = normalizeArray(result.steps);
      task.fallback_used = normalizeArray(result.fallback_used);
      task.approval_events = normalizeArray(result.approval_events);
      task.completion_reason = result.completion_reason || "";
      if (result.last_observation) {
        const observation = result.last_observation;
        if (observation.screen_ref) {
          task.artifacts.push({ kind: "screen", path: observation.screen_ref });
        }
        if (observation.ui_tree_ref) {
          task.artifacts.push({ kind: "ui_tree", path: observation.ui_tree_ref });
        }
      }
      await this.upsertTask(task);
      await this.controlPlane.log({
        type: "task.completed",
        task_id: task.task_id,
        device_alias: selected.alias,
        agent_id: task.agent_id,
        status: task.status,
        completion_reason: task.completion_reason,
        at: nowIso()
      });
      return { task, result };
    } finally {
      await this.releaseLock(selected.alias, task.task_id);
    }
  }
}

function schemaObject(properties, required = []) {
  return {
    type: "object",
    additionalProperties: false,
    properties,
    required
  };
}

function buildRuntimeContent(title, lines) {
  return `${title}\n${normalizeArray(lines).filter(Boolean).join("\n")}`.trim();
}

const plugin = {
  id: "mobile-runtime-plugin",
  name: "Mobile Runtime Plugin",
  description: "Expose mobile_* tools with a file-backed control plane and backend adapters.",
  configSchema: {
    type: "object",
    properties: {},
    additionalProperties: true
  },
  register(api) {
    const runtime = new MobileRuntime(resolveConfig(api.pluginConfig, api.logger), api.logger);
    runtime.init().catch((error) => {
      api.logger?.error?.(`mobile-runtime-plugin init failed: ${String(error)}`);
    });

    api.registerTool((toolCtx) => ({
      name: "mobile_list_devices",
      label: "Mobile List Devices",
      description: "List registered mobile devices with resolved backend, lock state, labels, and availability.",
      parameters: schemaObject({
        alias: { type: "string", description: "Optional exact alias filter." },
        backend: { type: "string", description: "Optional backend filter: mac-proxy or android-node." },
        platform: { type: "string", description: "Optional platform filter, default android." },
        labels: {
          type: "array",
          items: { type: "string" },
          description: "Require all labels to match."
        }
      }),
      async execute(_toolCallId, params) {
        const devices = await runtime.describeDevices(params || {});
        return {
          content: [
            {
              type: "text",
              text: devices.length
                ? buildRuntimeContent("Mobile devices", devices.map(formatDeviceLine))
                : "No mobile devices matched the selector."
            }
          ],
          details: {
            devices
          }
        };
      }
    }), { name: "mobile_list_devices" });

    api.registerTool((toolCtx) => ({
      name: "mobile_observe",
      label: "Mobile Observe",
      description: "Capture current screen, UI tree, and foreground app from a selected mobile device.",
      parameters: schemaObject({
        device_selector: schemaObject({
          alias: { type: "string" },
          labels: { type: "array", items: { type: "string" } },
          backend: { type: "string" },
          platform: { type: "string" }
        }),
        include_screenshot: { type: "boolean" },
        include_ui_tree: { type: "boolean" }
      }),
      async execute(_toolCallId, params) {
        const selected = await runtime.selectDevice(params.device_selector || {}, {
          allowAlternateDevice: true
        });
        if (!selected) {
          return {
            content: [{ type: "text", text: "No mobile device matched the selector." }],
            details: { error: "device_not_found" },
            isError: true
          };
        }
        const registry = runtime.loadRegistry();
        const device = registry.devices.find((item) => item.alias === selected.alias) || selected;
        const backend = runtime.getBackend(selected.backend);
        const observed = await backend.observe(device, params || {});
        return {
          content: [
            {
              type: "text",
              text: buildRuntimeContent(`Observed ${selected.alias}`, [
                `backend: ${selected.backend}`,
                `foreground_app: ${observed.observation.foreground_app || "(unknown)"}`,
                observed.observation.elements_summary ? `elements:\n${observed.observation.elements_summary}` : ""
              ])
            }
          ],
          details: {
            device: selected,
            observation: observed.observation,
            fallback_used: observed.fallback_used
          }
        };
      }
    }), { name: "mobile_observe" });

    api.registerTool((toolCtx) => ({
      name: "mobile_act",
      label: "Mobile Act",
      description: "Execute one semantic mobile action such as open_app, tap_element, input_text, scroll, back, home, snapshot, or run_flow.",
      parameters: schemaObject({
        task_id: { type: "string" },
        device_selector: schemaObject({
          alias: { type: "string" },
          labels: { type: "array", items: { type: "string" } },
          backend: { type: "string" },
          platform: { type: "string" }
        }),
        queue_if_busy: { type: "boolean" },
        allow_alternate_device: { type: "boolean" },
        approval_policy: { type: "string", description: "auto, approved, or observe-only." },
        risk_level: { type: "string", description: "safe, write, or danger." },
        action: schemaObject({
          kind: { type: "string" },
          app: { type: "string" },
          selector: {
            type: "object",
            additionalProperties: true
          },
          text: { type: "string" },
          direction: { type: "string" },
          flow_id: { type: "string" },
          inputs: {
            type: "object",
            additionalProperties: true
          },
          precondition: {
            type: "object",
            additionalProperties: true
          },
          postcondition: {
            type: "object",
            additionalProperties: true
          },
          requires_approval: { type: "boolean" },
          timeout_ms: { type: "number" }
        }, ["kind"])
      }, ["device_selector", "action"]),
      async execute(_toolCallId, params) {
        try {
          const managed = await runtime.runManagedTask(toolCtx, params, async (device, task) => {
            const backend = runtime.getBackend(device.preferred_backend || params.device_selector.backend || "mac-proxy");
            return backend.act(device, {
              ...params.action,
              approval_policy: params.approval_policy,
              risk_level: params.risk_level
            });
          });
          return {
            content: [
              {
                type: "text",
                text: buildRuntimeContent(`mobile_act ${managed.result.status}`, [
                  `task_id: ${managed.task.task_id}`,
                  `device: ${managed.task.device_alias}`,
                  `backend: ${managed.result.backend}`,
                  managed.result.completion_reason ? `reason: ${managed.result.completion_reason}` : "",
                  normalizeArray(managed.result.fallback_used).length
                    ? `fallback: ${managed.result.fallback_used.join(", ")}`
                    : ""
                ])
              }
            ],
            details: {
              task: managed.task,
              result: managed.result
            },
            isError: managed.result.status === "blocked"
          };
        } catch (error) {
          return {
            content: [{ type: "text", text: `mobile_act failed: ${String(error)}` }],
            details: { error: String(error) },
            isError: true
          };
        }
      }
    }), { name: "mobile_act" });

    api.registerTool((toolCtx) => ({
      name: "mobile_run_task",
      label: "Mobile Run Task",
      description: "Run a structured mobile task with device selection, locking, approval gating, and flow/template support.",
      parameters: schemaObject({
        task_id: { type: "string" },
        agent_id: { type: "string" },
        device_selector: schemaObject({
          alias: { type: "string" },
          labels: { type: "array", items: { type: "string" } },
          backend: { type: "string" },
          platform: { type: "string" }
        }),
        intent: { type: "string" },
        app: { type: "string" },
        flow_id: { type: "string" },
        inputs: {
          type: "object",
          additionalProperties: true
        },
        precondition: {
          type: "object",
          additionalProperties: true
        },
        max_steps: { type: "number" },
        queue_if_busy: { type: "boolean" },
        allow_alternate_device: { type: "boolean" },
        risk_level: { type: "string" },
        approval_policy: { type: "string" },
        artifacts: {
          type: "array",
          items: { type: "string" }
        }
      }, ["device_selector"]),
      async execute(_toolCallId, params) {
        try {
          const managed = await runtime.runManagedTask(toolCtx, params, async (device, task) => {
            const backend = runtime.getBackend(device.preferred_backend || runtime.resolvePreferredBackend(device));
            return backend.runTask(device, {
              ...params,
              task_id: task.task_id,
              agent_id: task.agent_id,
              session_key: task.session_key
            });
          });
          return {
            content: [
              {
                type: "text",
                text: buildRuntimeContent(`mobile_run_task ${managed.result.status}`, [
                  `task_id: ${managed.task.task_id}`,
                  `device: ${managed.task.device_alias}`,
                  `backend: ${managed.result.backend}`,
                  managed.result.completion_reason ? `reason: ${managed.result.completion_reason}` : "",
                  normalizeArray(managed.result.fallback_used).length
                    ? `fallback: ${managed.result.fallback_used.join(", ")}`
                    : ""
                ])
              }
            ],
            details: {
              task: managed.task,
              result: managed.result
            },
            isError: managed.result.status === "blocked"
          };
        } catch (error) {
          return {
            content: [{ type: "text", text: `mobile_run_task failed: ${String(error)}` }],
            details: { error: String(error) },
            isError: true
          };
        }
      }
    }), { name: "mobile_run_task" });

    api.registerTool({
      name: "mobile_status",
      label: "Mobile Status",
      description: "Inspect current mobile tasks, locks, and approval records.",
      parameters: schemaObject({
        task_id: { type: "string" },
        device_alias: { type: "string" }
      }),
      async execute(_toolCallId, params) {
        const tasks = runtime.controlPlane.loadTasks();
        const locks = runtime.controlPlane.loadLocks();
        const approvals = runtime.controlPlane.loadApprovals();
        const filteredTasks = Object.values(tasks).filter((task) => {
          if (params.task_id && task.task_id !== params.task_id) {
            return false;
          }
          if (params.device_alias && task.device_alias !== params.device_alias) {
            return false;
          }
          return true;
        });
        return {
          content: [
            {
              type: "text",
              text: buildRuntimeContent("Mobile status", [
                `tasks: ${filteredTasks.length}`,
                `locks: ${Object.keys(locks).length}`,
                `approvals: ${Object.keys(approvals).length}`
              ])
            }
          ],
          details: {
            tasks: filteredTasks,
            locks,
            approvals
          }
        };
      }
    }, { name: "mobile_status" });

    api.registerTool({
      name: "mobile_cancel",
      label: "Mobile Cancel",
      description: "Cancel a queued task or force-release a device lock when needed.",
      parameters: schemaObject({
        task_id: { type: "string" },
        device_alias: { type: "string" },
        force: { type: "boolean" }
      }),
      async execute(_toolCallId, params) {
        const tasks = runtime.controlPlane.loadTasks();
        const locks = runtime.controlPlane.loadLocks();
        let changed = false;
        if (params.task_id && tasks[params.task_id]) {
          tasks[params.task_id].status = "cancelled";
          tasks[params.task_id].updated_at = nowIso();
          tasks[params.task_id].completion_reason = "cancelled";
          changed = true;
          for (const [alias, lock] of Object.entries(locks)) {
            if (lock.task_id === params.task_id) {
              delete locks[alias];
            }
          }
        }
        if (params.device_alias && locks[params.device_alias] && params.force) {
          delete locks[params.device_alias];
          changed = true;
        }
        if (changed) {
          await runtime.controlPlane.saveTasks(tasks);
          await runtime.controlPlane.saveLocks(locks);
        }
        return {
          content: [{ type: "text", text: changed ? "Mobile task/lock cancelled." : "Nothing to cancel." }],
          details: {
            changed
          }
        };
      }
    }, { name: "mobile_cancel" });

    api.registerTool({
      name: "mobile_artifacts",
      label: "Mobile Artifacts",
      description: "List artifacts collected for a mobile task.",
      parameters: schemaObject({
        task_id: { type: "string" }
      }, ["task_id"]),
      async execute(_toolCallId, params) {
        const tasks = runtime.controlPlane.loadTasks();
        const task = tasks[params.task_id];
        if (!task) {
          return {
            content: [{ type: "text", text: `Unknown task_id: ${params.task_id}` }],
            details: { error: "task_not_found" },
            isError: true
          };
        }
        const lines = normalizeArray(task.artifacts).map((artifact, index) => `${index + 1}. ${artifact.kind}: ${artifact.path}`);
        return {
          content: [
            {
              type: "text",
              text: lines.length ? buildRuntimeContent(`Artifacts for ${params.task_id}`, lines) : "No artifacts collected yet."
            }
          ],
          details: {
            task_id: params.task_id,
            artifacts: task.artifacts || []
          }
        };
      }
    }, { name: "mobile_artifacts" });
  }
};

plugin.__internal = {
  MobileRuntime,
  parseUiNodes,
  findNode,
  parseBounds,
  resolveConfig
};

module.exports = plugin;
