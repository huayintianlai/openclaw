// index.ts
import { Type } from "@sinclair/typebox";

// providers.ts
function normalizeMemoryItem(raw) {
  return {
    id: raw.id ?? raw.memory_id ?? "",
    memory: raw.memory ?? raw.text ?? raw.content ?? "",
    // Handle both platform (user_id, created_at) and OSS (userId, createdAt) field names
    user_id: raw.user_id ?? raw.userId,
    score: raw.score,
    categories: raw.categories,
    metadata: raw.metadata,
    created_at: raw.created_at ?? raw.createdAt,
    updated_at: raw.updated_at ?? raw.updatedAt
  };
}
function normalizeSearchResults(raw) {
  if (Array.isArray(raw)) return raw.map(normalizeMemoryItem);
  if (raw?.results && Array.isArray(raw.results))
    return raw.results.map(normalizeMemoryItem);
  return [];
}
function normalizeAddResult(raw) {
  if (raw?.results && Array.isArray(raw.results)) {
    return {
      results: raw.results.map((r) => ({
        id: r.id ?? r.memory_id ?? "",
        memory: r.memory ?? r.text ?? "",
        // Platform API may return PENDING status (async processing)
        // OSS stores event in metadata.event
        event: r.event ?? r.metadata?.event ?? (r.status === "PENDING" ? "ADD" : "ADD")
      }))
    };
  }
  if (Array.isArray(raw)) {
    return {
      results: raw.map((r) => ({
        id: r.id ?? r.memory_id ?? "",
        memory: r.memory ?? r.text ?? "",
        event: r.event ?? r.metadata?.event ?? (r.status === "PENDING" ? "ADD" : "ADD")
      }))
    };
  }
  return { results: [] };
}
var PlatformProvider = class {
  constructor(apiKey, orgId, projectId) {
    this.apiKey = apiKey;
    this.orgId = orgId;
    this.projectId = projectId;
  }
  client;
  // MemoryClient from mem0ai
  initPromise = null;
  async ensureClient() {
    if (this.client) return;
    if (this.initPromise) return this.initPromise;
    this.initPromise = this._init().catch((err) => {
      this.initPromise = null;
      throw err;
    });
    return this.initPromise;
  }
  async _init() {
    const { default: MemoryClient } = await import("mem0ai");
    const opts = { apiKey: this.apiKey };
    if (this.orgId) opts.org_id = this.orgId;
    if (this.projectId) opts.project_id = this.projectId;
    this.client = new MemoryClient(opts);
  }
  async add(messages, options) {
    await this.ensureClient();
    const opts = { user_id: options.user_id };
    if (options.run_id) opts.run_id = options.run_id;
    if (options.custom_instructions)
      opts.custom_instructions = options.custom_instructions;
    if (options.custom_categories)
      opts.custom_categories = options.custom_categories;
    if (options.enable_graph) opts.enable_graph = options.enable_graph;
    if (options.output_format) opts.output_format = options.output_format;
    if (options.source) opts.source = options.source;
    if (options.infer !== void 0) opts.infer = options.infer;
    if (options.deduced_memories) opts.deduced_memories = options.deduced_memories;
    if (options.metadata) opts.metadata = options.metadata;
    if (options.expiration_date) opts.expiration_date = options.expiration_date;
    if (options.immutable) opts.immutable = options.immutable;
    const result = await this.client.add(messages, opts);
    return normalizeAddResult(result);
  }
  async search(query, options) {
    await this.ensureClient();
    const baseFilters = { user_id: options.user_id };
    if (options.run_id) baseFilters.run_id = options.run_id;
    const mergedFilters = options.filters ? { AND: [baseFilters, options.filters] } : baseFilters;
    const opts = {
      api_version: "v2",
      filters: mergedFilters
    };
    if (options.top_k != null) opts.top_k = options.top_k;
    if (options.threshold != null) opts.threshold = options.threshold;
    if (options.keyword_search != null) opts.keyword_search = options.keyword_search;
    if (options.reranking != null) opts.rerank = options.reranking;
    if (options.filter_memories != null) opts.filter_memories = options.filter_memories;
    if (options.categories != null) opts.categories = options.categories;
    const results = await this.client.search(query, opts);
    return normalizeSearchResults(results);
  }
  async get(memoryId) {
    await this.ensureClient();
    const result = await this.client.get(memoryId);
    return normalizeMemoryItem(result);
  }
  async getAll(options) {
    await this.ensureClient();
    const opts = { user_id: options.user_id };
    if (options.run_id) opts.run_id = options.run_id;
    if (options.page_size != null) opts.page_size = options.page_size;
    if (options.source) opts.source = options.source;
    const results = await this.client.getAll(opts);
    if (Array.isArray(results)) return results.map(normalizeMemoryItem);
    if (results?.results && Array.isArray(results.results))
      return results.results.map(normalizeMemoryItem);
    return [];
  }
  async update(memoryId, text) {
    await this.ensureClient();
    await this.client.update(memoryId, { text });
  }
  async delete(memoryId) {
    await this.ensureClient();
    await this.client.delete(memoryId);
  }
  async deleteAll(userId) {
    await this.ensureClient();
    await this.client.deleteAll({ user_id: userId });
  }
  async history(memoryId) {
    await this.ensureClient();
    const result = await this.client.history(memoryId);
    return Array.isArray(result) ? result : [];
  }
};
var OSSProvider = class {
  constructor(ossConfig, customPrompt, resolvePath) {
    this.ossConfig = ossConfig;
    this.customPrompt = customPrompt;
    this.resolvePath = resolvePath;
  }
  memory;
  // Memory from mem0ai/oss
  initPromise = null;
  async ensureMemory() {
    if (this.memory) return;
    if (this.initPromise) return this.initPromise;
    this.initPromise = this._init().catch((err) => {
      this.initPromise = null;
      throw err;
    });
    return this.initPromise;
  }
  async _init() {
    const { Memory } = await import("mem0ai/oss");
    const config = { version: "v1.1" };
    if (this.ossConfig?.embedder) config.embedder = this.ossConfig.embedder;
    if (this.ossConfig?.vectorStore)
      config.vectorStore = this.ossConfig.vectorStore;
    if (this.ossConfig?.llm) config.llm = this.ossConfig.llm;
    if (this.ossConfig?.historyDbPath) {
      const dbPath = this.resolvePath ? this.resolvePath(this.ossConfig.historyDbPath) : this.ossConfig.historyDbPath;
      config.historyDbPath = dbPath;
    }
    if (this.ossConfig?.disableHistory) {
      config.disableHistory = true;
    }
    if (this.customPrompt) config.customPrompt = this.customPrompt;
    try {
      this.memory = new Memory(config);
    } catch (err) {
      if (!config.disableHistory) {
        console.warn(
          "[mem0] Memory initialization failed, retrying with history disabled:",
          err instanceof Error ? err.message : err
        );
        config.disableHistory = true;
        this.memory = new Memory(config);
      } else {
        throw err;
      }
    }
  }
  async add(messages, options) {
    await this.ensureMemory();
    const addOpts = { userId: options.user_id };
    if (options.run_id) addOpts.runId = options.run_id;
    if (options.source) addOpts.source = options.source;
    if (options.infer !== void 0) addOpts.infer = options.infer;
    if (options.metadata) addOpts.metadata = options.metadata;
    if (options.expiration_date) addOpts.expirationDate = options.expiration_date;
    if (options.immutable) addOpts.immutable = options.immutable;
    let effectiveMessages = messages;
    if (options.infer === false && options.deduced_memories?.length) {
      effectiveMessages = options.deduced_memories.map((fact) => ({
        role: "user",
        content: fact
      }));
    }
    const result = await this.memory.add(effectiveMessages, addOpts);
    return normalizeAddResult(result);
  }
  async search(query, options) {
    await this.ensureMemory();
    const opts = { userId: options.user_id };
    if (options.run_id) opts.runId = options.run_id;
    if (options.limit != null) opts.limit = options.limit;
    else if (options.top_k != null) opts.limit = options.top_k;
    if (options.keyword_search != null) opts.keyword_search = options.keyword_search;
    if (options.reranking != null) opts.reranking = options.reranking;
    if (options.source) opts.source = options.source;
    if (options.threshold != null) opts.threshold = options.threshold;
    const results = await this.memory.search(query, opts);
    const normalized = normalizeSearchResults(results);
    if (options.threshold != null) {
      return normalized.filter((item) => (item.score ?? 0) >= options.threshold);
    }
    return normalized;
  }
  async get(memoryId) {
    await this.ensureMemory();
    const result = await this.memory.get(memoryId);
    return normalizeMemoryItem(result);
  }
  async getAll(options) {
    await this.ensureMemory();
    const getAllOpts = { userId: options.user_id };
    if (options.run_id) getAllOpts.runId = options.run_id;
    if (options.source) getAllOpts.source = options.source;
    const results = await this.memory.getAll(getAllOpts);
    if (Array.isArray(results)) return results.map(normalizeMemoryItem);
    if (results?.results && Array.isArray(results.results))
      return results.results.map(normalizeMemoryItem);
    return [];
  }
  async update(memoryId, text) {
    await this.ensureMemory();
    await this.memory.update(memoryId, { data: text });
  }
  async delete(memoryId) {
    await this.ensureMemory();
    await this.memory.delete(memoryId);
  }
  async deleteAll(userId) {
    await this.ensureMemory();
    await this.memory.deleteAll({ userId });
  }
  async history(memoryId) {
    await this.ensureMemory();
    try {
      const result = await this.memory.history(memoryId);
      return Array.isArray(result) ? result : [];
    } catch {
      return [];
    }
  }
};
function createProvider(cfg, api) {
  if (cfg.mode === "open-source") {
    return new OSSProvider(
      cfg.oss,
      cfg.customPrompt,
      (p) => api.resolvePath(p)
    );
  }
  return new PlatformProvider(cfg.apiKey, cfg.orgId, cfg.projectId);
}

// config.ts
var DEFAULT_CUSTOM_INSTRUCTIONS = `Your Task: Extract durable, actionable facts from conversations between a user and an AI assistant. Only store information that would be useful to an agent in a FUTURE session, days or weeks later.

Before storing any fact, ask: "Would a new agent \u2014 with no prior context \u2014 benefit from knowing this?" If the answer is no, do not store it.

Information to Extract (in priority order):

1. Configuration & System State Changes:
   - Tools/services configured, installed, or removed (with versions/dates)
   - Model assignments for agents, API keys configured (NEVER the key itself \u2014 see Exclude)
   - Cron schedules, automation pipelines, deployment configurations
   - Architecture decisions (agent hierarchy, system design, deployment strategy)
   - Specific identifiers: file paths, sheet IDs, channel IDs, user IDs, folder IDs

2. Standing Rules & Policies:
   - Explicit user directives about behavior ("never create accounts without consent")
   - Workflow policies ("each agent must review model selection before completing a task")
   - Security constraints, permission boundaries, access patterns

3. Identity & Demographics:
   - Name, location, timezone, language preferences
   - Occupation, employer, job role, industry

4. Preferences & Opinions:
   - Communication style preferences
   - Tool and technology preferences (with specifics: versions, configs)
   - Strong opinions or values explicitly stated
   - The WHY behind preferences when stated

5. Goals, Projects & Milestones:
   - Active projects (name, description, current status)
   - Completed setup milestones ("ElevenLabs fully configured as of 2026-02-20")
   - Deadlines, roadmaps, and progress tracking
   - Problems actively being solved

6. Technical Context:
   - Tech stack, tools, development environment
   - Agent ecosystem structure (names, roles, relationships)
   - Skill levels in different areas

7. Relationships & People:
   - Names and roles of people mentioned (colleagues, family, clients)
   - Team structure, key contacts

8. Decisions & Lessons:
   - Important decisions made and their reasoning
   - Lessons learned, strategies that worked or failed

Guidelines:

TEMPORAL ANCHORING (critical):
- ALWAYS include temporal context for time-sensitive facts using "As of YYYY-MM-DD, ..."
- Extract dates from message timestamps, dates mentioned in the text, or the system-provided current date
- If no date is available, note "date unknown" rather than omitting temporal context
- Examples: "As of 2026-02-20, ElevenLabs setup is complete" NOT "ElevenLabs setup is complete"

CONCISENESS:
- Use third person ("User prefers..." not "I prefer...")
- Keep related facts together in a single memory to preserve context
- "User's Tailscale machine 'mac' (IP 100.71.135.41) is configured under beau@rizedigital.io (as of 2026-02-20)"
- NOT a paragraph retelling the whole conversation

OUTCOMES OVER INTENT:
- When an assistant message summarizes completed work, extract the durable OUTCOMES
- "Call scripts sheet (ID: 146Qbb...) was updated with truth-based templates" NOT "User wants to update call scripts"
- Extract what WAS DONE, not what was requested

DEDUPLICATION:
- Before creating a new memory, check if a substantially similar fact already exists
- If so, UPDATE the existing memory with any new details rather than creating a duplicate

LANGUAGE:
- ALWAYS preserve the original language of the conversation
- If the user speaks Spanish, store the memory in Spanish; do not translate

Exclude (NEVER store):
- Passwords, API keys, tokens, secrets, or any credentials \u2014 even when embedded in configuration blocks, setup logs, or tool output. This includes strings starting with sk-, m0-, ak_, ghp_, bot tokens (digits followed by colon and alphanumeric string), bearer tokens, webhook URLs containing tokens, pairing codes, and any long alphanumeric strings that appear in config/env contexts. Never include the actual secret value in a memory. Instead, record that the credential was configured:
  WRONG: "User's API key is sk-abc123..." or "Bot token is 12345:AABcd..."
  RIGHT: "API key was configured for the service (as of YYYY-MM-DD)" or "Telegram bot token was set up"
- One-time commands or instructions ("stop the script", "continue where you left off")
- Acknowledgments or emotional reactions ("ok", "sounds good", "you're right", "sir")
- Transient UI/navigation states ("user is in the admin panel", "relay is attached")
- Ephemeral process status ("download at 50%", "daemon not running", "still syncing")
- Cron heartbeat outputs, NO_REPLY responses, compaction flush directives
- The current date/time as a standalone fact \u2014 timestamps are conversation context, not durable knowledge. "User indicates current time is 3:25 PM" is NEVER worth storing. However, DO use timestamps to anchor other facts: "User installed Ollama on 2026-03-21" is correct.
- System routing metadata (message IDs, sender IDs, channel routing info)
- Generic small talk with no informational content
- Raw code snippets (capture the intent/decision, not the code itself)
- Information the user explicitly asks not to remember`;
var DEFAULT_CUSTOM_CATEGORIES = {
  identity: "Personal identity information: name, age, location, timezone, occupation, employer, education, demographics",
  preferences: "Explicitly stated likes, dislikes, preferences, opinions, and values across any domain",
  goals: "Current and future goals, aspirations, objectives, targets the user is working toward",
  projects: "Specific projects, initiatives, or endeavors the user is working on, including status and details",
  technical: "Technical skills, tools, tech stack, development environment, programming languages, frameworks",
  decisions: "Important decisions made, reasoning behind choices, strategy changes, and their outcomes",
  relationships: "People mentioned by the user: colleagues, family, friends, their roles and relevance",
  routines: "Daily habits, work patterns, schedules, productivity routines, health and wellness habits",
  life_events: "Significant life events, milestones, transitions, upcoming plans and changes",
  lessons: "Lessons learned, insights gained, mistakes acknowledged, changed opinions or beliefs",
  work: "Work-related context: job responsibilities, workplace dynamics, career progression, professional challenges",
  health: "Health-related information voluntarily shared: conditions, medications, fitness, wellness goals"
};
var ALLOWED_KEYS = [
  "mode",
  "apiKey",
  "userId",
  "orgId",
  "projectId",
  "autoCapture",
  "autoRecall",
  "customInstructions",
  "customCategories",
  "customPrompt",
  "enableGraph",
  "searchThreshold",
  "topK",
  "oss",
  "skills"
];
function assertAllowedKeys(value, allowed, label) {
  const unknown = Object.keys(value).filter((key) => !allowed.includes(key));
  if (unknown.length === 0) return;
  throw new Error(`${label} has unknown keys: ${unknown.join(", ")}`);
}
var mem0ConfigSchema = {
  parse(value) {
    if (!value || typeof value !== "object" || Array.isArray(value)) {
      throw new Error("openclaw-mem0 config required");
    }
    const cfg = value;
    assertAllowedKeys(cfg, ALLOWED_KEYS, "openclaw-mem0 config");
    const mode = cfg.mode === "oss" || cfg.mode === "open-source" ? "open-source" : "platform";
    const needsSetup = mode === "platform" && (typeof cfg.apiKey !== "string" || !cfg.apiKey);
    let ossConfig;
    if (cfg.oss && typeof cfg.oss === "object" && !Array.isArray(cfg.oss)) {
      ossConfig = cfg.oss;
    }
    return {
      mode,
      apiKey: typeof cfg.apiKey === "string" ? cfg.apiKey : void 0,
      userId: typeof cfg.userId === "string" && cfg.userId ? cfg.userId : "default",
      orgId: typeof cfg.orgId === "string" ? cfg.orgId : void 0,
      projectId: typeof cfg.projectId === "string" ? cfg.projectId : void 0,
      autoCapture: cfg.autoCapture !== false,
      autoRecall: cfg.autoRecall !== false,
      customInstructions: typeof cfg.customInstructions === "string" ? cfg.customInstructions : DEFAULT_CUSTOM_INSTRUCTIONS,
      customCategories: cfg.customCategories && typeof cfg.customCategories === "object" && !Array.isArray(cfg.customCategories) ? cfg.customCategories : DEFAULT_CUSTOM_CATEGORIES,
      customPrompt: typeof cfg.customPrompt === "string" ? cfg.customPrompt : DEFAULT_CUSTOM_INSTRUCTIONS,
      enableGraph: cfg.enableGraph === true,
      searchThreshold: typeof cfg.searchThreshold === "number" ? cfg.searchThreshold : 0.5,
      topK: typeof cfg.topK === "number" ? cfg.topK : 5,
      needsSetup,
      oss: ossConfig,
      skills: cfg.skills && typeof cfg.skills === "object" && !Array.isArray(cfg.skills) ? cfg.skills : void 0
    };
  }
};

// filtering.ts
var NOISE_MESSAGE_PATTERNS = [
  /^(HEARTBEAT_OK|NO_REPLY)$/i,
  /^Current time:.*\d{4}/,
  /^Pre-compaction memory flush/i,
  /^(ok|yes|no|sir|sure|thanks|done|good|nice|cool|got it|it's on|continue)$/i,
  /^System: \[.*\] (Slack message edited|Gateway restart|Exec (failed|completed))/,
  /^System: \[.*\] ⚠️ Post-Compaction Audit:/
];
var NOISE_CONTENT_PATTERNS = [
  { pattern: /Conversation info \(untrusted metadata\):\s*```json\s*\{[\s\S]*?\}\s*```/g, replacement: "" },
  { pattern: /\[media attached:.*?\]/g, replacement: "" },
  { pattern: /To send an image back, prefer the message tool[\s\S]*?Keep caption in the text body\./g, replacement: "" },
  { pattern: /System: \[\d{4}-\d{2}-\d{2}.*?\] ⚠️ Post-Compaction Audit:[\s\S]*?after memory compaction\./g, replacement: "" },
  { pattern: /Replied message \(untrusted, for context\):\s*```json[\s\S]*?```/g, replacement: "" }
];
var MAX_MESSAGE_LENGTH = 2e3;
var GENERIC_ASSISTANT_PATTERNS = [
  /^(I see you'?ve shared|Thanks for sharing|Got it[.!]?\s*(I see|Let me|How can)|I understand[.!]?\s*(How can|Is there|Would you))/i,
  /^(How can I help|Is there anything|Would you like me to|Let me know (if|how|what))/i,
  /^(I('?ll| will) (help|assist|look into|review|take a look))/i,
  /^(Sure[.!]?\s*(How|What|Is)|Understood[.!]?\s*(How|What|Is))/i,
  /^(That('?s| is) (noted|understood|clear))/i
];
function isNoiseMessage(content) {
  const trimmed = content.trim();
  if (!trimmed) return true;
  return NOISE_MESSAGE_PATTERNS.some((p) => p.test(trimmed));
}
function isGenericAssistantMessage(content) {
  const trimmed = content.trim();
  if (trimmed.length > 300) return false;
  return GENERIC_ASSISTANT_PATTERNS.some((p) => p.test(trimmed));
}
function stripNoiseFromContent(content) {
  let cleaned = content;
  for (const { pattern, replacement } of NOISE_CONTENT_PATTERNS) {
    cleaned = cleaned.replace(pattern, replacement);
  }
  cleaned = cleaned.replace(/\n{3,}/g, "\n\n").trim();
  return cleaned;
}
function truncateMessage(content) {
  if (content.length <= MAX_MESSAGE_LENGTH) return content;
  return content.slice(0, MAX_MESSAGE_LENGTH) + "\n[...truncated]";
}
function filterMessagesForExtraction(messages) {
  const filtered = [];
  for (const msg of messages) {
    if (isNoiseMessage(msg.content)) continue;
    if (msg.role === "assistant" && isGenericAssistantMessage(msg.content)) continue;
    const cleaned = stripNoiseFromContent(msg.content);
    if (!cleaned) continue;
    filtered.push({ role: msg.role, content: truncateMessage(cleaned) });
  }
  return filtered;
}

// isolation.ts
var SKIP_TRIGGERS = /* @__PURE__ */ new Set(["cron", "heartbeat", "automation", "schedule"]);
function isNonInteractiveTrigger(trigger, sessionKey) {
  if (trigger && SKIP_TRIGGERS.has(trigger.toLowerCase())) return true;
  if (sessionKey) {
    if (/:cron:/i.test(sessionKey) || /:heartbeat:/i.test(sessionKey)) return true;
  }
  return false;
}
function isSubagentSession(sessionKey) {
  if (!sessionKey) return false;
  return /:subagent:/i.test(sessionKey);
}
function extractAgentId(sessionKey) {
  if (!sessionKey) return void 0;
  const subagentMatch = sessionKey.match(/:subagent:([^:]+)$/);
  if (subagentMatch?.[1]) return `subagent-${subagentMatch[1]}`;
  const match = sessionKey.match(/^agent:([^:]+):/);
  const agentId = match?.[1];
  if (!agentId || agentId === "main") return void 0;
  return agentId;
}
function effectiveUserId(baseUserId, sessionKey) {
  const agentId = extractAgentId(sessionKey);
  return agentId ? `${baseUserId}:agent:${agentId}` : baseUserId;
}
function agentUserId(baseUserId, agentId) {
  return `${baseUserId}:agent:${agentId}`;
}
function resolveUserId(baseUserId, opts, currentSessionId) {
  if (opts.agentId) return agentUserId(baseUserId, opts.agentId);
  if (opts.userId) return opts.userId;
  return effectiveUserId(baseUserId, currentSessionId);
}

// skill-loader.ts
import * as fs from "fs";
import * as path from "path";
import { fileURLToPath } from "url";
var DEFAULT_CATEGORIES = {
  configuration: { importance: 0.95, ttl: null },
  rule: { importance: 0.9, ttl: null },
  identity: { importance: 0.95, ttl: null, immutable: true },
  preference: { importance: 0.85, ttl: null },
  decision: { importance: 0.8, ttl: null },
  technical: { importance: 0.8, ttl: null },
  relationship: { importance: 0.75, ttl: null },
  project: { importance: 0.75, ttl: "90d" },
  operational: { importance: 0.6, ttl: "7d" }
};
var DEFAULT_CREDENTIAL_PATTERNS = [
  "sk-",
  "m0-",
  "ghp_",
  "AKIA",
  "ak_",
  "Bearer ",
  "bot\\d+:AA",
  "password=",
  "token=",
  "secret="
];
function parseSkillFile(content) {
  const fmMatch = content.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
  if (!fmMatch) {
    return {
      frontmatter: { name: "unknown" },
      body: content
    };
  }
  const fmBlock = fmMatch[1];
  const body = fmMatch[2].trim();
  const fm = {};
  for (const line of fmBlock.split("\n")) {
    const colonIdx = line.indexOf(":");
    if (colonIdx === -1) continue;
    const key = line.slice(0, colonIdx).trim();
    let value = line.slice(colonIdx + 1).trim();
    if (value === "false") value = false;
    else if (value === "true") value = true;
    fm[key] = value;
  }
  return {
    frontmatter: fm,
    body
  };
}
function resolveSkillsDir() {
  const candidates = [];
  try {
    const metaDir = path.dirname(fileURLToPath(import.meta.url));
    candidates.push(path.join(metaDir, "skills"));
    candidates.push(path.join(metaDir, "..", "skills"));
  } catch {
  }
  if (typeof __dirname !== "undefined") {
    candidates.push(path.join(__dirname, "skills"));
    candidates.push(path.join(__dirname, "..", "skills"));
  }
  for (const dir of candidates) {
    if (fs.existsSync(path.join(dir, "memory-triage", "SKILL.md"))) {
      return dir;
    }
  }
  return candidates[0] ?? "skills";
}
var SKILLS_DIR = resolveSkillsDir();
var RESOLVED_SKILLS_DIR = path.resolve(SKILLS_DIR);
function safePath(...segments) {
  const resolved = path.resolve(SKILLS_DIR, ...segments);
  if (resolved !== RESOLVED_SKILLS_DIR && !resolved.startsWith(RESOLVED_SKILLS_DIR + path.sep)) {
    return null;
  }
  return resolved;
}
function readSkillFile(skillName) {
  const filePath = safePath(skillName, "SKILL.md");
  if (!filePath) return null;
  try {
    return fs.readFileSync(filePath, "utf-8");
  } catch {
    return null;
  }
}
function readDomainOverlay(domain, targetSkill) {
  const filePath = safePath(targetSkill, "domains", `${domain}.md`);
  if (!filePath) return null;
  try {
    const content = fs.readFileSync(filePath, "utf-8");
    const parsed = parseSkillFile(content);
    const appliesTo = parsed.frontmatter.applies_to;
    if (appliesTo && appliesTo !== targetSkill) {
      return null;
    }
    return parsed.body;
  } catch {
    return null;
  }
}
function renderCategoriesBlock(categories) {
  const lines = ["\n## Active Category Configuration (overrides defaults above)\n"];
  for (const [name, cat] of Object.entries(categories)) {
    const ttlLabel = cat.ttl ? `expires: ${cat.ttl}` : "permanent";
    const immLabel = cat.immutable ? ", immutable" : "";
    lines.push(`- **${name.toUpperCase()}** (importance: ${cat.importance} | ${ttlLabel}${immLabel})`);
  }
  return lines.join("\n");
}
function renderTriageKnobs(config) {
  const triage = config.triage;
  if (!triage) return "";
  const lines = [];
  if (triage.importanceThreshold !== void 0) {
    lines.push(`- Only store facts with importance >= ${triage.importanceThreshold}`);
  }
  const patterns = resolveCredentialPatterns(config);
  if (config.triage?.credentialPatterns) {
    lines.push(`- Credential patterns to scan: ${patterns.join(", ")}`);
  }
  if (lines.length === 0) return "";
  return "\n## Active Configuration Overrides\n\n" + lines.join("\n");
}
function ttlToExpirationDate(ttl) {
  if (!ttl) return null;
  const match = ttl.match(/^(\d+)d$/);
  if (!match) return null;
  const days = parseInt(match[1], 10);
  const date = /* @__PURE__ */ new Date();
  date.setDate(date.getDate() + days);
  return date.toISOString().split("T")[0];
}
function loadSkill(skillName, config = {}) {
  const raw = readSkillFile(skillName);
  if (!raw) return null;
  const parsed = parseSkillFile(raw);
  const parts = [parsed.body];
  if (config.domain) {
    const overlay = readDomainOverlay(config.domain, skillName);
    if (overlay) {
      parts.push("\n" + overlay);
    }
  }
  if (skillName === "memory-triage" && config.categories) {
    const mergedCats = resolveCategories(config);
    parts.push(renderCategoriesBlock(mergedCats));
  }
  if (skillName === "memory-triage") {
    const knobs = renderTriageKnobs(config);
    if (knobs) parts.push(knobs);
  }
  if (skillName === "memory-triage" && config.customRules) {
    const rulesBlock = ["\n## User Custom Rules\n"];
    if (config.customRules.include?.length) {
      rulesBlock.push("Additionally extract:");
      for (const rule of config.customRules.include) {
        rulesBlock.push(`- ${rule}`);
      }
    }
    if (config.customRules.exclude?.length) {
      rulesBlock.push("\nAdditionally skip:");
      for (const rule of config.customRules.exclude) {
        rulesBlock.push(`- ${rule}`);
      }
    }
    parts.push(rulesBlock.join("\n"));
  }
  return {
    name: skillName,
    prompt: parts.join("\n"),
    frontmatter: parsed.frontmatter
  };
}
function loadTriagePrompt(config = {}) {
  const triage = loadSkill("memory-triage", config);
  if (triage) {
    const parts2 = [];
    parts2.push("<memory-system>");
    parts2.push("IMPORTANT: Use `memory_store` tool for ALL user facts. NEVER write user info to workspace files (USER.md, memory/).");
    parts2.push("");
    parts2.push(triage.prompt);
    parts2.push("");
    parts2.push("## Tool Usage");
    parts2.push("");
    parts2.push("Batch facts by CATEGORY. All facts in one memory_store call must share the same category because category determines retention policy (TTL, immutability). If a turn has facts in different categories, make one call per category.");
    parts2.push("");
    parts2.push("FORMAT (single category):");
    parts2.push('  memory_store(facts: ["User is Alex, backend engineer at Stripe, PST timezone"], category: "identity")');
    parts2.push("FORMAT (mixed categories in one turn, separate calls):");
    parts2.push('  memory_store(facts: ["User is Alex, backend engineer at Stripe, PST timezone"], category: "identity")');
    parts2.push('  memory_store(facts: ["As of 2026-04-01, migrating from Postgres to CockroachDB"], category: "decision")');
    if (config.recall?.enabled !== false) {
      const strategy = config.recall?.strategy ?? "smart";
      parts2.push("");
      parts2.push("## Searching Memory");
      parts2.push("");
      if (strategy === "manual") {
        parts2.push("You control all memory search. No automatic recall happens. Use memory_search proactively:");
        parts2.push("- At the start of a new conversation, search for user identity and context.");
        parts2.push("- When the user references something you do not have context for.");
        parts2.push("- When the conversation topic shifts to a new domain.");
        parts2.push("- Before updating a memory, search to find the existing version.");
        parts2.push("");
      }
      parts2.push("When calling memory_search, ALWAYS rewrite the query. NEVER pass the user's raw message.");
      parts2.push("Stored memories are third-person factual statements. Write a query that matches storage language, not conversation language.");
      parts2.push("Process: (1) Name your target. (2) Extract signal: proper nouns, technical terms, domain concepts. (3) Bridge to storage language: add terms the stored memory contains (user, decided, prefers, rule, configured, based in). (4) Compose 3-6 keywords.");
      parts2.push('WRONG: memory_search("Who was that nutritionist my wife recommended?")');
      parts2.push('RIGHT: memory_search("nutritionist wife recommended relationship")');
      parts2.push('WRONG: memory_search("What timezone am I in?")');
      parts2.push('RIGHT: memory_search("user timezone location based")');
      parts2.push("");
      parts2.push("ENTITY SCOPING: Memories are scoped by user_id, agent_id, and run_id. You do not need to pass these in most cases. The plugin handles scoping automatically based on the current session.");
      parts2.push("- Default behavior: all memory operations use the configured userId and current session. You do not need to pass userId or agentId.");
      parts2.push("- Use agentId only when you need to read or write memories for a DIFFERENT agent (e.g., querying what the 'researcher' agent knows). This accesses a separate namespace.");
      parts2.push("- Use userId only when explicitly instructed to operate on a different user's memories.");
      parts2.push("- Do not pass run_id directly. The plugin manages session scoping through the scope parameter.");
      parts2.push("- In multi-agent setups, each agent has isolated memory. The main agent's memories are separate from subagent memories.");
      parts2.push("");
      parts2.push("SEARCH SCOPE: Choose the right scope for each search:");
      parts2.push('- scope: "long-term" for user context, identity, preferences, decisions (default, most common)');
      parts2.push('- scope: "session" for facts from this conversation only');
      parts2.push('- scope: "all" only when you truly need both scopes combined');
      parts2.push("Using a specific scope avoids unnecessary backend fan-out.");
      parts2.push("");
      parts2.push("SEARCH FILTERS: When the user's intent implies a time range or category constraint, pass a `filters` object alongside your rewritten query.");
      parts2.push('- Time: "last week" -> filters: {"created_at": {"gte": "2026-03-24"}}');
      parts2.push('- Category: "my preferences" -> categories: ["preference"]');
      parts2.push("- Available operators: eq, ne, gt, gte, lt, lte, in, contains. Logical: AND, OR, NOT.");
    }
    parts2.push("</memory-system>");
    return parts2.join("\n");
  }
  const parts = [];
  parts.push("<memory-system>");
  parts.push("You have persistent long-term memory via mem0. After EVERY response, evaluate the turn for facts worth storing.");
  parts.push("Use `memory_store` tool for ALL user facts. NEVER write user info to workspace files (USER.md, memory/).");
  parts.push("Most turns produce ZERO memory operations. That is correct.");
  parts.push("Only store facts a new agent would need days later: identity, preferences, decisions, rules, projects, configs.");
  parts.push("Batch facts by CATEGORY. All facts in one call must share the same category.");
  parts.push('Format: memory_store(facts: ["fact text"], category: "identity")');
  parts.push("NEVER store credentials (sk-, m0-, ghp_, AKIA, Bearer tokens, passwords).");
  if (config.recall?.enabled !== false) {
    parts.push("When searching, rewrite queries for retrieval. Do not pass raw user messages.");
  }
  parts.push("</memory-system>");
  return parts.join("\n");
}
function loadDreamPrompt(config = {}) {
  const dream = loadSkill("memory-dream", config);
  if (!dream) return "";
  return dream.prompt;
}
function resolveCategories(config = {}) {
  return { ...DEFAULT_CATEGORIES, ...config.categories || {} };
}
function resolveCredentialPatterns(config = {}) {
  return config.triage?.credentialPatterns ?? DEFAULT_CREDENTIAL_PATTERNS;
}
function isSkillsMode(config) {
  if (!config) return false;
  return config.triage?.enabled !== false;
}

// recall.ts
var DEFAULT_TOKEN_BUDGET = 1500;
var DEFAULT_MAX_MEMORIES = 15;
var DEFAULT_THRESHOLD = 0.4;
var DEFAULT_CATEGORY_ORDER = [
  "identity",
  "configuration",
  "rule",
  "preference",
  "decision",
  "technical",
  "relationship",
  "project",
  "operational"
];
var CHARS_PER_TOKEN = 4;
function getMemoryCategory(memory) {
  if (memory.metadata?.category && typeof memory.metadata.category === "string") {
    return memory.metadata.category;
  }
  if (memory.categories?.length) {
    return memory.categories[0];
  }
  return "uncategorized";
}
function getMemoryImportance(memory) {
  if (memory.metadata?.importance && typeof memory.metadata.importance === "number") {
    return memory.metadata.importance;
  }
  const cat = getMemoryCategory(memory);
  const defaults = {
    identity: 0.95,
    configuration: 0.95,
    rule: 0.9,
    preference: 0.85,
    decision: 0.8,
    technical: 0.8,
    relationship: 0.75,
    project: 0.75,
    operational: 0.6
  };
  return defaults[cat] ?? 0.5;
}
function estimateTokens(text) {
  return Math.ceil(text.length / CHARS_PER_TOKEN);
}
function rankMemories(memories, categoryOrder) {
  const orderMap = new Map(categoryOrder.map((cat, i) => [cat, i]));
  return [...memories].sort((a, b) => {
    const catA = getMemoryCategory(a);
    const catB = getMemoryCategory(b);
    const orderA = orderMap.get(catA) ?? 999;
    const orderB = orderMap.get(catB) ?? 999;
    if (orderA !== orderB) return orderA - orderB;
    const impA = getMemoryImportance(a);
    const impB = getMemoryImportance(b);
    if (impA !== impB) return impB - impA;
    return (b.score ?? 0) - (a.score ?? 0);
  });
}
function budgetMemories(rankedMemories, tokenBudget, maxMemories, identityAlwaysInclude) {
  const selected = [];
  let usedTokens = 0;
  for (const memory of rankedMemories) {
    if (selected.length >= maxMemories) break;
    const memTokens = estimateTokens(memory.memory);
    const isIdentity = getMemoryCategory(memory) === "identity" || getMemoryCategory(memory) === "configuration";
    if (identityAlwaysInclude && isIdentity) {
      selected.push(memory);
      usedTokens += memTokens;
      continue;
    }
    if (usedTokens + memTokens > tokenBudget) continue;
    selected.push(memory);
    usedTokens += memTokens;
  }
  return selected;
}
function formatRecalledMemories(memories, userId) {
  if (memories.length === 0) {
    return `<recalled-memories>
No stored memories found for "${userId}".
</recalled-memories>`;
  }
  const grouped = /* @__PURE__ */ new Map();
  for (const mem of memories) {
    const cat = getMemoryCategory(mem);
    const existing = grouped.get(cat) || [];
    existing.push(mem);
    grouped.set(cat, existing);
  }
  const lines = [
    `<recalled-memories>`,
    `Stored memories for "${userId}" (${memories.length} total, ranked by importance):`,
    ""
  ];
  for (const [category, mems] of grouped.entries()) {
    const label = category.charAt(0).toUpperCase() + category.slice(1);
    lines.push(`${label}:`);
    for (const mem of mems) {
      const imp = getMemoryImportance(mem);
      const cats = mem.categories?.length ? ` [${mem.categories.join(", ")}]` : "";
      lines.push(`- ${mem.memory}${cats} (${Math.round(imp * 100)}%)`);
    }
    lines.push("");
  }
  lines.push("</recalled-memories>");
  return lines.join("\n");
}
function sanitizeQuery(raw) {
  let cleaned = raw.replace(/Sender\s*\(untrusted metadata\):\s*```json[\s\S]*?```\s*/gi, "");
  cleaned = cleaned.replace(/^\[.*?\]\s*/g, "");
  cleaned = cleaned.trim();
  return cleaned || raw;
}
async function recall(provider, query, userId, config = {}, sessionId) {
  const recallConfig = config.recall ?? {};
  const tokenBudget = recallConfig.tokenBudget ?? DEFAULT_TOKEN_BUDGET;
  const maxMemories = recallConfig.maxMemories ?? DEFAULT_MAX_MEMORIES;
  const threshold = recallConfig.threshold ?? DEFAULT_THRESHOLD;
  const categoryOrder = recallConfig.categoryOrder ?? DEFAULT_CATEGORY_ORDER;
  const identityAlwaysInclude = recallConfig.identityAlwaysInclude !== false;
  const searchOpts = {
    user_id: userId,
    top_k: maxMemories * 2,
    // Over-fetch for ranking
    threshold,
    keyword_search: recallConfig.keywordSearch !== false,
    // Default on
    reranking: recallConfig.rerank !== false
    // Default on
  };
  if (recallConfig.filterMemories) {
    searchOpts.filter_memories = true;
  }
  const cleanQuery = sanitizeQuery(query);
  let longTermMemories = [];
  try {
    longTermMemories = await provider.search(cleanQuery, searchOpts);
  } catch (err) {
    console.warn("[mem0] Recall search failed:", err instanceof Error ? err.message : err);
  }
  let sessionMemories = [];
  if (sessionId) {
    try {
      sessionMemories = await provider.search(cleanQuery, {
        ...searchOpts,
        run_id: sessionId,
        top_k: 5
      });
    } catch {
    }
  }
  const longTermIds = new Set(longTermMemories.map((m) => m.id));
  const uniqueSession = sessionMemories.filter((m) => !longTermIds.has(m.id));
  const allMemories = [...longTermMemories, ...uniqueSession];
  const ranked = rankMemories(allMemories, categoryOrder);
  const budgeted = budgetMemories(ranked, tokenBudget, maxMemories, identityAlwaysInclude);
  const context = formatRecalledMemories(budgeted, userId);
  const tokenEstimate = estimateTokens(context);
  return { context, memories: budgeted, tokenEstimate };
}

// dream-gate.ts
import * as fs2 from "fs";
import * as path2 from "path";
var DEFAULTS = {
  minHours: 24,
  minSessions: 5,
  minMemories: 20
};
var LOCK_STALE_MS = 60 * 60 * 1e3;
function statePath(stateDir) {
  return path2.join(stateDir, "dream-state.json");
}
function lockPath(stateDir) {
  return path2.join(stateDir, "dream.lock");
}
function ensureDir(dir) {
  try {
    fs2.mkdirSync(dir, { recursive: true });
  } catch {
  }
}
function readState(stateDir) {
  try {
    const raw = fs2.readFileSync(statePath(stateDir), "utf-8");
    return JSON.parse(raw);
  } catch {
    return { lastConsolidatedAt: 0, sessionsSince: 0, lastSessionId: null };
  }
}
function writeState(stateDir, state) {
  ensureDir(stateDir);
  fs2.writeFileSync(statePath(stateDir), JSON.stringify(state, null, 2));
}
function incrementSessionCount(stateDir, sessionId) {
  const state = readState(stateDir);
  if (state.lastSessionId !== sessionId) {
    state.sessionsSince++;
    state.lastSessionId = sessionId;
    writeState(stateDir, state);
  }
}
function checkCheapGates(stateDir, config) {
  const minHours = config.minHours ?? DEFAULTS.minHours;
  const minSessions = config.minSessions ?? DEFAULTS.minSessions;
  const state = readState(stateDir);
  const hoursSince = (Date.now() - state.lastConsolidatedAt) / 36e5;
  if (hoursSince < minHours) {
    return { proceed: false, reason: `time: ${hoursSince.toFixed(1)}h < ${minHours}h` };
  }
  if (state.sessionsSince < minSessions) {
    return { proceed: false, reason: `sessions: ${state.sessionsSince} < ${minSessions}` };
  }
  return { proceed: true };
}
function checkMemoryGate(memoryCount, config) {
  const minMemories = config.minMemories ?? DEFAULTS.minMemories;
  if (memoryCount < minMemories) {
    return { pass: false, reason: `memories: ${memoryCount} < ${minMemories}` };
  }
  return { pass: true };
}
function acquireDreamLock(stateDir) {
  ensureDir(stateDir);
  const lp = lockPath(stateDir);
  try {
    const raw = fs2.readFileSync(lp, "utf-8");
    const lock2 = JSON.parse(raw);
    const age = Date.now() - lock2.startedAt;
    if (age < LOCK_STALE_MS) {
      return false;
    }
    try {
      fs2.unlinkSync(lp);
    } catch {
    }
  } catch {
  }
  const lock = { pid: process.pid, startedAt: Date.now() };
  try {
    fs2.writeFileSync(lp, JSON.stringify(lock), { flag: "wx" });
    return true;
  } catch {
    return false;
  }
}
function releaseDreamLock(stateDir) {
  try {
    fs2.unlinkSync(lockPath(stateDir));
  } catch {
  }
}
function recordDreamCompletion(stateDir) {
  const state = readState(stateDir);
  state.lastConsolidatedAt = Date.now();
  state.sessionsSince = 0;
  state.lastSessionId = null;
  writeState(stateDir, state);
}

// index.ts
function categoriesToArray(cats) {
  return Object.entries(cats).map(([key, value]) => ({ [key]: value }));
}
var memoryPlugin = {
  id: "openclaw-mem0",
  name: "Memory (Mem0)",
  description: "Mem0 memory backend \u2014 Mem0 platform or self-hosted open-source",
  kind: "memory",
  configSchema: mem0ConfigSchema,
  register(api) {
    const cfg = mem0ConfigSchema.parse(api.pluginConfig);
    if (cfg.needsSetup) {
      api.logger.warn(
        'openclaw-mem0: API key not configured. Memory features are disabled.\n  To set up, run:\n  openclaw config set plugins.entries.openclaw-mem0.config.apiKey "m0-your-key"\n  openclaw gateway restart\n  Get your key at: https://app.mem0.ai/dashboard/api-keys'
      );
      api.registerService({
        id: "openclaw-mem0",
        start: () => {
          api.logger.info("openclaw-mem0: waiting for API key configuration");
        },
        stop: () => {
        }
      });
      return;
    }
    const provider = createProvider(cfg, api);
    let currentSessionId;
    const _effectiveUserId = (sessionKey) => effectiveUserId(cfg.userId, sessionKey);
    const _agentUserId = (id) => agentUserId(cfg.userId, id);
    const _resolveUserId = (opts) => resolveUserId(cfg.userId, opts, currentSessionId);
    const skillsActive = isSkillsMode(cfg.skills);
    api.logger.info(
      `openclaw-mem0: registered (mode: ${cfg.mode}, user: ${cfg.userId}, graph: ${cfg.enableGraph}, autoRecall: ${cfg.autoRecall}, autoCapture: ${cfg.autoCapture}, skills: ${skillsActive})`
    );
    function buildAddOptions(userIdOverride, runId, sessionKey) {
      const opts = {
        user_id: userIdOverride || _effectiveUserId(sessionKey),
        source: "OPENCLAW"
      };
      if (runId) opts.run_id = runId;
      if (cfg.mode === "platform") {
        opts.custom_instructions = cfg.customInstructions;
        opts.custom_categories = categoriesToArray(cfg.customCategories);
        opts.enable_graph = cfg.enableGraph;
        opts.output_format = "v1.1";
      }
      return opts;
    }
    function buildSearchOptions(userIdOverride, limit, runId, sessionKey) {
      const recallCfg = cfg.skills?.recall;
      const opts = {
        user_id: userIdOverride || _effectiveUserId(sessionKey),
        top_k: limit ?? cfg.topK,
        limit: limit ?? cfg.topK,
        threshold: recallCfg?.threshold ?? cfg.searchThreshold,
        keyword_search: recallCfg?.keywordSearch !== false,
        reranking: recallCfg?.rerank !== false,
        source: "OPENCLAW"
      };
      if (recallCfg?.filterMemories) opts.filter_memories = true;
      if (runId) opts.run_id = runId;
      return opts;
    }
    registerTools(api, provider, cfg, _resolveUserId, _effectiveUserId, _agentUserId, buildAddOptions, buildSearchOptions, () => currentSessionId, skillsActive);
    registerCli(api, provider, cfg, _effectiveUserId, _agentUserId, buildSearchOptions, () => currentSessionId);
    registerHooks(api, provider, cfg, _effectiveUserId, buildAddOptions, buildSearchOptions, {
      setCurrentSessionId: (id) => {
        currentSessionId = id;
      },
      getStateDir: () => pluginStateDir
    }, skillsActive);
    let pluginStateDir;
    api.registerService({
      id: "openclaw-mem0",
      start: (...args) => {
        pluginStateDir = args[0]?.stateDir;
        api.logger.info(
          `openclaw-mem0: initialized (mode: ${cfg.mode}, user: ${cfg.userId}, autoRecall: ${cfg.autoRecall}, autoCapture: ${cfg.autoCapture}, stateDir: ${pluginStateDir ?? "none"})`
        );
      },
      stop: () => {
        api.logger.info("openclaw-mem0: stopped");
      }
    });
  }
};
function registerTools(api, provider, cfg, _resolveUserId, _effectiveUserId, _agentUserId, buildAddOptions, buildSearchOptions, getCurrentSessionId, skillsActive = false) {
  api.registerTool(
    {
      name: "memory_search",
      label: "Memory Search",
      description: "Search through long-term memories stored in Mem0. Use when you need context about user preferences, past decisions, or previously discussed topics.",
      parameters: Type.Object({
        query: Type.String({ description: "Search query" }),
        limit: Type.Optional(
          Type.Number({
            description: `Max results (default: ${cfg.topK})`
          })
        ),
        userId: Type.Optional(
          Type.String({
            description: "User ID to scope search (default: configured userId)"
          })
        ),
        agentId: Type.Optional(
          Type.String({
            description: 'Agent ID to search memories for a specific agent (e.g. "researcher"). Overrides userId.'
          })
        ),
        scope: Type.Optional(
          Type.Union([
            Type.Literal("session"),
            Type.Literal("long-term"),
            Type.Literal("all")
          ], {
            description: 'Memory scope: "session" (current session only), "long-term" (user-scoped only), or "all" (both). Default: "all"'
          })
        ),
        categories: Type.Optional(
          Type.Array(Type.String(), {
            description: 'Filter results by category (e.g. ["identity", "preference"]). Only returns memories tagged with these categories.'
          })
        ),
        filters: Type.Optional(
          Type.Record(Type.String(), Type.Unknown(), {
            description: 'Advanced filters object. Supports date ranges and metadata filtering. Examples: {"created_at": {"gte": "2026-03-01"}} for recent memories, {"AND": [{"categories": {"contains": "decision"}}, {"created_at": {"gte": "2026-01-01"}}]} for decisions this year. Operators: eq, ne, gt, gte, lt, lte, in, contains, icontains. Logical: AND, OR, NOT.'
          })
        )
      }),
      async execute(_toolCallId, params) {
        const { query, limit, userId, agentId, scope = "all", categories: filterCategories, filters: agentFilters } = params;
        try {
          let results = [];
          const uid = _resolveUserId({ agentId, userId });
          const currentSessionId = getCurrentSessionId();
          const applyFilters = (opts) => {
            if (filterCategories?.length) opts.categories = filterCategories;
            if (agentFilters) opts.filters = agentFilters;
            return opts;
          };
          if (scope === "session") {
            if (currentSessionId) {
              results = await provider.search(
                query,
                applyFilters(buildSearchOptions(uid, limit, currentSessionId))
              );
            }
          } else if (scope === "long-term") {
            results = await provider.search(
              query,
              applyFilters(buildSearchOptions(uid, limit))
            );
          } else {
            const longTermResults = await provider.search(
              query,
              applyFilters(buildSearchOptions(uid, limit))
            );
            let sessionResults = [];
            if (currentSessionId) {
              sessionResults = await provider.search(
                query,
                applyFilters(buildSearchOptions(uid, limit, currentSessionId))
              );
            }
            const seen = new Set(longTermResults.map((r) => r.id));
            results = [
              ...longTermResults,
              ...sessionResults.filter((r) => !seen.has(r.id))
            ];
          }
          if (!results || results.length === 0) {
            return {
              content: [
                { type: "text", text: "No relevant memories found." }
              ],
              details: { count: 0 }
            };
          }
          const text = results.map(
            (r, i) => `${i + 1}. ${r.memory} (score: ${((r.score ?? 0) * 100).toFixed(0)}%, id: ${r.id})`
          ).join("\n");
          const sanitized = results.map((r) => ({
            id: r.id,
            memory: r.memory,
            score: r.score,
            categories: r.categories,
            created_at: r.created_at
          }));
          return {
            content: [
              {
                type: "text",
                text: `Found ${results.length} memories:

${text}`
              }
            ],
            details: { count: results.length, memories: sanitized }
          };
        } catch (err) {
          return {
            content: [
              {
                type: "text",
                text: `Memory search failed: ${String(err)}`
              }
            ],
            details: { error: String(err) }
          };
        }
      }
    },
    { name: "memory_search" }
  );
  api.registerTool(
    {
      name: "memory_store",
      label: "Memory Store",
      description: "Save important information in long-term memory via Mem0. Use for preferences, facts, decisions, and anything worth remembering.",
      parameters: Type.Object({
        text: Type.Optional(
          Type.String({ description: "Single fact to remember. Use 'facts' array instead when storing multiple facts from one conversation turn." })
        ),
        facts: Type.Optional(
          Type.Array(Type.String(), {
            description: "Array of facts to store in one call. ALL facts MUST share the same category. If a turn has facts in different categories, make one call per category. Category determines retention policy (TTL, immutability)."
          })
        ),
        category: Type.Optional(
          Type.String({
            description: 'Memory category. Determines retention policy (TTL, immutability). All facts in this call inherit this category. Options: "identity", "preference", "decision", "rule", "project", "configuration", "technical", "relationship"'
          })
        ),
        importance: Type.Optional(
          Type.Number({
            description: "Importance override (0.0-1.0). Omit to use category default. Applies to all facts in this call. Defaults: identity/config 0.95, rules 0.90, preferences 0.85, decisions 0.80, projects 0.75, operational 0.60"
          })
        ),
        userId: Type.Optional(
          Type.String({
            description: "User ID to scope this memory"
          })
        ),
        agentId: Type.Optional(
          Type.String({
            description: `Agent ID to store memory under a specific agent's namespace (e.g. "researcher"). Overrides userId.`
          })
        ),
        metadata: Type.Optional(
          Type.Record(Type.String(), Type.Unknown(), {
            description: "Additional metadata to attach to this memory"
          })
        ),
        longTerm: Type.Optional(
          Type.Boolean({
            description: "Store as long-term (user-scoped) memory. Default: true. Set to false for session-scoped memory."
          })
        )
      }),
      async execute(_toolCallId, params) {
        const p = params;
        const { userId, agentId, longTerm = true } = p;
        const allFacts = p.facts?.length ? p.facts : p.text ? [p.text] : [];
        if (allFacts.length === 0) {
          return {
            content: [{ type: "text", text: "No facts provided. Pass 'text' or 'facts' array." }],
            details: { error: "missing_facts" }
          };
        }
        try {
          const currentSessionId = getCurrentSessionId();
          if (isSubagentSession(currentSessionId)) {
            api.logger.warn("openclaw-mem0: blocked memory_store from subagent session");
            return {
              content: [{ type: "text", text: "Memory storage is not available in subagent sessions. The main agent handles memory." }],
              details: { error: "subagent_blocked" }
            };
          }
          const uid = _resolveUserId({ agentId, userId });
          const runId = !longTerm && currentSessionId ? currentSessionId : void 0;
          if (skillsActive) {
            if (allFacts.length > 1 && !p.category) {
              api.logger.warn(
                `openclaw-mem0: multi-fact batch (${allFacts.length} facts) without category. Retention policy defaults to uncategorized. Prompt instructs batch-by-category.`
              );
            }
            const rawMetadata = p.metadata;
            const category = p.category ?? rawMetadata?.category;
            const importance = p.importance ?? rawMetadata?.importance;
            const parsedMetadata = {
              ...rawMetadata ?? {},
              ...category && { category },
              ...importance !== void 0 && { importance }
            };
            const categories = resolveCategories(cfg.skills);
            const catConfig = category ? categories[category] : void 0;
            const expirationDate = catConfig ? ttlToExpirationDate(catConfig.ttl) : void 0;
            const isImmutable = catConfig?.immutable ?? false;
            const addOpts = {
              user_id: uid,
              source: "OPENCLAW",
              infer: false,
              deduced_memories: allFacts,
              metadata: parsedMetadata ?? {},
              ...expirationDate && { expiration_date: expirationDate },
              ...isImmutable && { immutable: true }
            };
            if (runId) addOpts.run_id = runId;
            if (cfg.mode === "platform") {
              addOpts.output_format = "v1.1";
              if (cfg.enableGraph || cfg.skills?.triage?.enableGraph) {
                addOpts.enable_graph = true;
              }
            }
            const result2 = await provider.add(
              [{ role: "user", content: allFacts.join("\n") }],
              addOpts
            );
            const count = result2.results?.length ?? 0;
            api.logger.info(
              `openclaw-mem0: skills-mode stored ${count} memor${count === 1 ? "y" : "ies"} from ${allFacts.length} fact(s) in 1 API call (infer=false, category=${category ?? "none"})`
            );
            return {
              content: [
                {
                  type: "text",
                  text: `Stored ${allFacts.length} fact(s) [${category ?? "uncategorized"}]: ${allFacts.map((f) => `"${f.slice(0, 60)}${f.length > 60 ? "..." : ""}"`).join(", ")}`
                }
              ],
              details: {
                action: "stored",
                mode: "skills",
                infer: false,
                category,
                factCount: allFacts.length,
                results: result2.results
              }
            };
          }
          const combinedText = allFacts.join("\n");
          const preview = combinedText.slice(0, 200);
          const dedupOpts = buildSearchOptions(uid, 3);
          dedupOpts.threshold = 0.85;
          const existing = await provider.search(preview, dedupOpts);
          if (existing.length > 0) {
            api.logger.info(
              `openclaw-mem0: found ${existing.length} similar existing memories \u2014 mem0 may update instead of add`
            );
          }
          const result = await provider.add(
            [{ role: "user", content: combinedText }],
            {
              ...buildAddOptions(uid, runId, currentSessionId),
              infer: false,
              deduced_memories: allFacts,
              metadata: p.metadata ?? {}
            }
          );
          const added = result.results?.filter((r) => r.event === "ADD") ?? [];
          const updated = result.results?.filter((r) => r.event === "UPDATE") ?? [];
          const summary = [];
          if (added.length > 0)
            summary.push(
              `${added.length} new memor${added.length === 1 ? "y" : "ies"} added`
            );
          if (updated.length > 0)
            summary.push(
              `${updated.length} memor${updated.length === 1 ? "y" : "ies"} updated`
            );
          if (summary.length === 0)
            summary.push("No new memories extracted");
          return {
            content: [
              {
                type: "text",
                text: `Stored: ${summary.join(", ")}. ${result.results?.map((r) => `[${r.event}] ${r.memory}`).join("; ") ?? ""}`
              }
            ],
            details: {
              action: "stored",
              results: result.results
            }
          };
        } catch (err) {
          return {
            content: [
              {
                type: "text",
                text: `Memory store failed: ${String(err)}`
              }
            ],
            details: { error: String(err) }
          };
        }
      }
    },
    { name: "memory_store" }
  );
  api.registerTool(
    {
      name: "memory_get",
      label: "Memory Get",
      description: "Retrieve a specific memory by its ID from Mem0.",
      parameters: Type.Object({
        memoryId: Type.String({ description: "The memory ID to retrieve" })
      }),
      async execute(_toolCallId, params) {
        const { memoryId } = params;
        try {
          const memory = await provider.get(memoryId);
          return {
            content: [
              {
                type: "text",
                text: `Memory ${memory.id}:
${memory.memory}

Created: ${memory.created_at ?? "unknown"}
Updated: ${memory.updated_at ?? "unknown"}`
              }
            ],
            details: { memory }
          };
        } catch (err) {
          return {
            content: [
              {
                type: "text",
                text: `Memory get failed: ${String(err)}`
              }
            ],
            details: { error: String(err) }
          };
        }
      }
    },
    { name: "memory_get" }
  );
  api.registerTool(
    {
      name: "memory_list",
      label: "Memory List",
      description: "List all stored memories for a user or agent. Use this when you want to see everything that's been remembered, rather than searching for something specific.",
      parameters: Type.Object({
        userId: Type.Optional(
          Type.String({
            description: "User ID to list memories for (default: configured userId)"
          })
        ),
        agentId: Type.Optional(
          Type.String({
            description: 'Agent ID to list memories for a specific agent (e.g. "researcher"). Overrides userId.'
          })
        ),
        scope: Type.Optional(
          Type.Union([
            Type.Literal("session"),
            Type.Literal("long-term"),
            Type.Literal("all")
          ], {
            description: 'Memory scope: "session" (current session only), "long-term" (user-scoped only), or "all" (both). Default: "all"'
          })
        )
      }),
      async execute(_toolCallId, params) {
        const { userId, agentId, scope = "all" } = params;
        try {
          let memories = [];
          const uid = _resolveUserId({ agentId, userId });
          const currentSessionId = getCurrentSessionId();
          if (scope === "session") {
            if (currentSessionId) {
              memories = await provider.getAll({
                user_id: uid,
                run_id: currentSessionId,
                source: "OPENCLAW"
              });
            }
          } else if (scope === "long-term") {
            memories = await provider.getAll({ user_id: uid, source: "OPENCLAW" });
          } else {
            const longTerm = await provider.getAll({ user_id: uid, source: "OPENCLAW" });
            let session = [];
            if (currentSessionId) {
              session = await provider.getAll({
                user_id: uid,
                run_id: currentSessionId,
                source: "OPENCLAW"
              });
            }
            const seen = new Set(longTerm.map((r) => r.id));
            memories = [
              ...longTerm,
              ...session.filter((r) => !seen.has(r.id))
            ];
          }
          if (!memories || memories.length === 0) {
            return {
              content: [
                { type: "text", text: "No memories stored yet." }
              ],
              details: { count: 0 }
            };
          }
          const text = memories.map(
            (r, i) => `${i + 1}. ${r.memory} (id: ${r.id})`
          ).join("\n");
          const sanitized = memories.map((r) => ({
            id: r.id,
            memory: r.memory,
            categories: r.categories,
            created_at: r.created_at
          }));
          return {
            content: [
              {
                type: "text",
                text: `${memories.length} memories:

${text}`
              }
            ],
            details: { count: memories.length, memories: sanitized }
          };
        } catch (err) {
          return {
            content: [
              {
                type: "text",
                text: `Memory list failed: ${String(err)}`
              }
            ],
            details: { error: String(err) }
          };
        }
      }
    },
    { name: "memory_list" }
  );
  api.registerTool(
    {
      name: "memory_forget",
      label: "Memory Forget",
      description: "Delete memories from Mem0. Provide a specific memoryId to delete directly, or a query to search and delete matching memories. Supports agent-scoped deletion. GDPR-compliant.",
      parameters: Type.Object({
        query: Type.Optional(
          Type.String({
            description: "Search query to find memory to delete"
          })
        ),
        memoryId: Type.Optional(
          Type.String({ description: "Specific memory ID to delete" })
        ),
        agentId: Type.Optional(
          Type.String({
            description: `Agent ID to scope deletion to a specific agent's memories (e.g. "researcher").`
          })
        )
      }),
      async execute(_toolCallId, params) {
        const { query, memoryId, agentId } = params;
        try {
          const currentSessionId = getCurrentSessionId();
          if (isSubagentSession(currentSessionId)) {
            api.logger.warn("openclaw-mem0: blocked memory_forget from subagent session");
            return {
              content: [{ type: "text", text: "Memory deletion is not available in subagent sessions. The main agent handles memory." }],
              details: { error: "subagent_blocked" }
            };
          }
          if (memoryId) {
            await provider.delete(memoryId);
            return {
              content: [
                { type: "text", text: `Memory ${memoryId} forgotten.` }
              ],
              details: { action: "deleted", id: memoryId }
            };
          }
          if (query) {
            const uid = _resolveUserId({ agentId });
            const results = await provider.search(
              query,
              buildSearchOptions(uid, 5)
            );
            if (!results || results.length === 0) {
              return {
                content: [
                  { type: "text", text: "No matching memories found." }
                ],
                details: { found: 0 }
              };
            }
            if (results.length === 1 || (results[0].score ?? 0) > 0.9) {
              await provider.delete(results[0].id);
              return {
                content: [
                  {
                    type: "text",
                    text: `Forgotten: "${results[0].memory}"`
                  }
                ],
                details: { action: "deleted", id: results[0].id }
              };
            }
            const list = results.map(
              (r) => `- [${r.id}] ${r.memory.slice(0, 80)}${r.memory.length > 80 ? "..." : ""} (score: ${((r.score ?? 0) * 100).toFixed(0)}%)`
            ).join("\n");
            const candidates = results.map((r) => ({
              id: r.id,
              memory: r.memory,
              score: r.score
            }));
            return {
              content: [
                {
                  type: "text",
                  text: `Found ${results.length} candidates. Specify memoryId to delete:
${list}`
                }
              ],
              details: { action: "candidates", candidates }
            };
          }
          return {
            content: [
              { type: "text", text: "Provide a query or memoryId." }
            ],
            details: { error: "missing_param" }
          };
        } catch (err) {
          return {
            content: [
              {
                type: "text",
                text: `Memory forget failed: ${String(err)}`
              }
            ],
            details: { error: String(err) }
          };
        }
      }
    },
    { name: "memory_forget" }
  );
  api.registerTool(
    {
      name: "memory_update",
      label: "Memory Update",
      description: "Update an existing memory's text in place. Use when a fact has changed and you have the memory ID. This is atomic and preserves the memory's history. Preferred over delete-then-store for corrections.",
      parameters: Type.Object({
        memoryId: Type.String({ description: "The memory ID to update" }),
        text: Type.String({ description: "The new text for this memory (replaces the old text)" })
      }),
      async execute(_toolCallId, params) {
        const { memoryId, text } = params;
        try {
          const currentSessionId = getCurrentSessionId();
          if (isSubagentSession(currentSessionId)) {
            api.logger.warn("openclaw-mem0: blocked memory_update from subagent session");
            return {
              content: [{ type: "text", text: "Memory update is not available in subagent sessions." }],
              details: { error: "subagent_blocked" }
            };
          }
          await provider.update(memoryId, text);
          return {
            content: [
              { type: "text", text: `Updated memory ${memoryId}: "${text.slice(0, 80)}${text.length > 80 ? "..." : ""}"` }
            ],
            details: { action: "updated", id: memoryId }
          };
        } catch (err) {
          return {
            content: [
              { type: "text", text: `Memory update failed: ${String(err)}` }
            ],
            details: { error: String(err) }
          };
        }
      }
    },
    { name: "memory_update" }
  );
  api.registerTool(
    {
      name: "memory_delete_all",
      label: "Memory Delete All",
      description: "Delete ALL memories for a user. Use with extreme caution. This is irreversible. Only use when the user explicitly asks to forget everything or reset their memory.",
      parameters: Type.Object({
        confirm: Type.Boolean({
          description: "Must be true to proceed. Safety gate to prevent accidental bulk deletion."
        }),
        userId: Type.Optional(
          Type.String({ description: "User ID to delete all memories for (default: configured userId)" })
        )
      }),
      async execute(_toolCallId, params) {
        const { confirm, userId } = params;
        try {
          const currentSessionId = getCurrentSessionId();
          if (isSubagentSession(currentSessionId)) {
            api.logger.warn("openclaw-mem0: blocked memory_delete_all from subagent session");
            return {
              content: [{ type: "text", text: "Bulk memory deletion is not available in subagent sessions." }],
              details: { error: "subagent_blocked" }
            };
          }
          if (!confirm) {
            return {
              content: [{ type: "text", text: "Bulk deletion requires confirm: true. Ask the user to confirm before proceeding." }],
              details: { error: "confirmation_required" }
            };
          }
          const uid = _resolveUserId({ userId });
          await provider.deleteAll(uid);
          api.logger.info(`openclaw-mem0: deleted all memories for user ${uid}`);
          return {
            content: [
              { type: "text", text: `All memories deleted for user "${uid}".` }
            ],
            details: { action: "deleted_all", user_id: uid }
          };
        } catch (err) {
          return {
            content: [
              { type: "text", text: `Bulk memory deletion failed: ${String(err)}` }
            ],
            details: { error: String(err) }
          };
        }
      }
    },
    { name: "memory_delete_all" }
  );
  api.registerTool(
    {
      name: "memory_history",
      label: "Memory History",
      description: "View the edit history of a specific memory. Shows all changes over time including previous values, new values, and timestamps. Useful for understanding how a memory evolved.",
      parameters: Type.Object({
        memoryId: Type.String({ description: "The memory ID to view history for" })
      }),
      async execute(_toolCallId, params) {
        const { memoryId } = params;
        try {
          const history = await provider.history(memoryId);
          if (!history || history.length === 0) {
            return {
              content: [{ type: "text", text: `No history found for memory ${memoryId}.` }],
              details: { count: 0 }
            };
          }
          const text = history.map((h, i) => `${i + 1}. [${h.event}] ${h.created_at}
   Old: ${h.old_memory || "(none)"}
   New: ${h.new_memory || "(none)"}`).join("\n\n");
          return {
            content: [
              { type: "text", text: `History for memory ${memoryId} (${history.length} entries):

${text}` }
            ],
            details: { count: history.length, history }
          };
        } catch (err) {
          return {
            content: [
              { type: "text", text: `Memory history failed: ${String(err)}` }
            ],
            details: { error: String(err) }
          };
        }
      }
    },
    { name: "memory_history" }
  );
}
function registerCli(api, provider, cfg, _effectiveUserId, _agentUserId, buildSearchOptions, getCurrentSessionId) {
  api.registerCli(
    ({ program }) => {
      const mem0 = program.command("mem0").description("Mem0 memory plugin commands");
      mem0.command("search").description("Search memories in Mem0").argument("<query>", "Search query").option("--limit <n>", "Max results", String(cfg.topK)).option("--scope <scope>", 'Memory scope: "session", "long-term", or "all"', "all").option("--agent <agentId>", "Search a specific agent's memory namespace").action(async (query, opts) => {
        try {
          const limit = parseInt(opts.limit, 10);
          const scope = opts.scope;
          const currentSessionId = getCurrentSessionId();
          const uid = opts.agent ? _agentUserId(opts.agent) : _effectiveUserId(currentSessionId);
          let allResults = [];
          if (scope === "session" || scope === "all") {
            if (currentSessionId) {
              const sessionResults = await provider.search(
                query,
                buildSearchOptions(uid, limit, currentSessionId)
              );
              if (sessionResults?.length) {
                allResults.push(...sessionResults.map((r) => ({ ...r, _scope: "session" })));
              }
            } else if (scope === "session") {
              console.log("No active session ID available for session-scoped search.");
              return;
            }
          }
          if (scope === "long-term" || scope === "all") {
            const longTermResults = await provider.search(
              query,
              buildSearchOptions(uid, limit)
            );
            if (longTermResults?.length) {
              allResults.push(...longTermResults.map((r) => ({ ...r, _scope: "long-term" })));
            }
          }
          if (scope === "all") {
            const seen = /* @__PURE__ */ new Set();
            allResults = allResults.filter((r) => {
              if (seen.has(r.id)) return false;
              seen.add(r.id);
              return true;
            });
          }
          if (!allResults.length) {
            console.log("No memories found.");
            return;
          }
          const output = allResults.map((r) => ({
            id: r.id,
            memory: r.memory,
            score: r.score,
            scope: r._scope,
            categories: r.categories,
            created_at: r.created_at
          }));
          console.log(JSON.stringify(output, null, 2));
        } catch (err) {
          console.error(`Search failed: ${String(err)}`);
        }
      });
      mem0.command("stats").description("Show memory statistics from Mem0").option("--agent <agentId>", "Show stats for a specific agent").action(async (opts) => {
        try {
          const uid = opts.agent ? _agentUserId(opts.agent) : cfg.userId;
          const memories = await provider.getAll({
            user_id: uid,
            source: "OPENCLAW"
          });
          console.log(`Mode: ${cfg.mode}`);
          console.log(`User: ${uid}${opts.agent ? ` (agent: ${opts.agent})` : ""}`);
          console.log(
            `Total memories: ${Array.isArray(memories) ? memories.length : "unknown"}`
          );
          console.log(`Graph enabled: ${cfg.enableGraph}`);
          console.log(
            `Auto-recall: ${cfg.autoRecall}, Auto-capture: ${cfg.autoCapture}`
          );
        } catch (err) {
          console.error(`Stats failed: ${String(err)}`);
        }
      });
      mem0.command("dream").description("Run memory consolidation (review, merge, prune stored memories)").option("--dry-run", "Show memory inventory without running consolidation").action(async (opts) => {
        try {
          const uid = cfg.userId;
          const memories = await provider.getAll({ user_id: uid, source: "OPENCLAW" });
          const count = Array.isArray(memories) ? memories.length : 0;
          if (count === 0) {
            console.log("No memories to consolidate.");
            return;
          }
          const catCounts = /* @__PURE__ */ new Map();
          for (const mem of memories) {
            const cat = mem.metadata?.category ?? mem.categories?.[0] ?? "uncategorized";
            catCounts.set(cat, (catCounts.get(cat) ?? 0) + 1);
          }
          process.stderr.write(`
Memory inventory for "${uid}":
`);
          for (const [cat, num] of [...catCounts.entries()].sort((a, b) => b[1] - a[1])) {
            process.stderr.write(`  ${cat}: ${num}
`);
          }
          process.stderr.write(`  TOTAL: ${count}

`);
          if (opts.dryRun) {
            process.stderr.write("Dry run \u2014 no changes made.\n");
            return;
          }
          const dreamPrompt = loadDreamPrompt(cfg.skills ?? {});
          if (!dreamPrompt) {
            process.stderr.write("Dream skill file not found at skills/memory-dream/SKILL.md\n");
            return;
          }
          const memoryDump = memories.map((m, i) => {
            const cat = m.metadata?.category ?? m.categories?.[0] ?? "uncategorized";
            const imp = m.metadata?.importance ?? "?";
            const created = m.created_at ?? "unknown";
            return `${i + 1}. [${m.id}] (${cat}, importance: ${imp}, created: ${created}) ${m.memory}`;
          }).join("\n");
          const fullPrompt = [
            "<dream-protocol>",
            dreamPrompt,
            "</dream-protocol>",
            "",
            `<all-memories count="${count}" user="${uid}">`,
            memoryDump,
            "</all-memories>",
            "",
            "Begin consolidation. Review all memories above and execute merge, delete, and rewrite operations using the available tools."
          ].join("\n");
          process.stdout.write(fullPrompt + "\n");
          process.stderr.write(`Dream prompt written to stdout (${fullPrompt.length} chars). Pipe with: openclaw mem0 dream | openclaw run --stdin
`);
        } catch (err) {
          console.error(`Dream failed: ${String(err)}`);
        }
      });
    },
    { commands: ["mem0"] }
  );
}
function registerHooks(api, provider, cfg, _effectiveUserId, buildAddOptions, buildSearchOptions, session, skillsActive = false) {
  if (skillsActive) {
    api.on("before_prompt_build", async (event, ctx) => {
      if (!event.prompt || event.prompt.length < 5) return;
      const trigger = ctx?.trigger ?? void 0;
      const sessionId = ctx?.sessionKey ?? void 0;
      if (isNonInteractiveTrigger(trigger, sessionId)) {
        api.logger.info("openclaw-mem0: skills-mode skipping non-interactive trigger");
        return;
      }
      const promptLower = event.prompt.toLowerCase();
      const isSystemPrompt = promptLower.includes("a new session was started") || promptLower.includes("session startup sequence") || promptLower.includes("/new or /reset") || promptLower.startsWith("system:") || promptLower.startsWith("run your session");
      if (isSystemPrompt) {
        api.logger.info("openclaw-mem0: skills-mode skipping recall for system/bootstrap prompt");
        const systemContext2 = loadTriagePrompt(cfg.skills ?? {});
        return { prependSystemContext: systemContext2 };
      }
      if (sessionId) session.setCurrentSessionId(sessionId);
      const isSubagent = isSubagentSession(sessionId);
      const userId = _effectiveUserId(isSubagent ? void 0 : sessionId);
      let systemContext = loadTriagePrompt(cfg.skills ?? {});
      if (isSubagent) {
        systemContext = "You are a subagent \u2014 use these memories for context but do not assume you are this user. Do NOT store new memories.\n\n" + systemContext;
      }
      let recallContext = "";
      const recallEnabled = cfg.skills?.recall?.enabled !== false;
      const recallStrategy = cfg.skills?.recall?.strategy ?? "smart";
      if (recallEnabled && recallStrategy !== "manual") {
        try {
          const query = sanitizeQuery(event.prompt);
          const sessionIdForRecall = recallStrategy === "always" ? isSubagent ? void 0 : sessionId : void 0;
          const recallResult = await recall(
            provider,
            query,
            userId,
            cfg.skills ?? {},
            sessionIdForRecall
          );
          api.logger.info(
            `openclaw-mem0: skills-mode recall (strategy=${recallStrategy}) injecting ${recallResult.memories.length} memories (~${recallResult.tokenEstimate} tokens)`
          );
          recallContext = recallResult.context;
        } catch (err) {
          api.logger.warn(`openclaw-mem0: skills-mode recall failed: ${String(err)}`);
        }
      } else if (recallEnabled && recallStrategy === "manual") {
        api.logger.info("openclaw-mem0: skills-mode recall strategy=manual, agent controls search");
      }
      const stateDir = session.getStateDir();
      const dreamEnabled = cfg.skills?.dream?.enabled !== false && cfg.skills?.dream?.auto !== false;
      let dreamContext = "";
      if (dreamEnabled && stateDir && !isSubagent) {
        try {
          const cheapResult = checkCheapGates(stateDir, cfg.skills?.dream ?? {});
          if (cheapResult.proceed) {
            const memories = await provider.getAll({ user_id: userId, source: "OPENCLAW" });
            const memCount = Array.isArray(memories) ? memories.length : 0;
            const memResult = checkMemoryGate(memCount, cfg.skills?.dream ?? {});
            if (memResult.pass && acquireDreamLock(stateDir)) {
              const dreamPrompt = loadDreamPrompt(cfg.skills ?? {});
              if (dreamPrompt) {
                dreamContext = "\n\n<auto-dream>\nIMPORTANT: Before responding to the user, run a memory consolidation pass. Follow the protocol below, then respond normally.\n\n" + dreamPrompt + "\n</auto-dream>";
                dreamSessionId = sessionId;
                api.logger.info(`openclaw-mem0: auto-dream triggered (${memCount} memories, gate passed)`);
              } else {
                releaseDreamLock(stateDir);
              }
            }
          }
        } catch (err) {
          api.logger.warn(`openclaw-mem0: auto-dream gate check failed: ${String(err)}`);
        }
      }
      return {
        prependSystemContext: systemContext,
        // cached by provider
        prependContext: recallContext + dreamContext
        // per-turn dynamic
      };
    });
    let dreamSessionId;
    api.on("agent_end", async (event, ctx) => {
      const sessionId = ctx?.sessionKey ?? void 0;
      const trigger = ctx?.trigger ?? void 0;
      if (sessionId) session.setCurrentSessionId(sessionId);
      const stateDir = session.getStateDir();
      if (dreamSessionId && dreamSessionId === sessionId && stateDir) {
        dreamSessionId = void 0;
        if (!event.success) {
          releaseDreamLock(stateDir);
          api.logger.warn("openclaw-mem0: auto-dream turn failed, lock released, will retry");
          return;
        }
        const WRITE_TOOLS = /* @__PURE__ */ new Set(["memory_store", "memory_update", "memory_forget", "memory_delete_all"]);
        const messages = event.messages ?? [];
        const lastAssistant = [...messages].reverse().find((m) => m.role === "assistant");
        const writeToolUsed = lastAssistant && Array.isArray(lastAssistant.content) ? lastAssistant.content.some(
          (block) => block.type === "tool_use" && WRITE_TOOLS.has(block.name)
        ) : false;
        if (writeToolUsed) {
          releaseDreamLock(stateDir);
          recordDreamCompletion(stateDir);
          api.logger.info("openclaw-mem0: auto-dream completed (verified write tool usage), lock released");
        } else {
          releaseDreamLock(stateDir);
          api.logger.warn("openclaw-mem0: auto-dream injected but no write tools executed. Lock released, will retry.");
        }
        return;
      }
      if (!event.success) return;
      if (stateDir && sessionId && !isNonInteractiveTrigger(trigger, sessionId)) {
        incrementSessionCount(stateDir, sessionId);
      }
      api.logger.info("openclaw-mem0: skills-mode agent_end (no auto-capture)");
    });
    return;
  }
  if (cfg.autoRecall) {
    api.on("before_agent_start", async (event, ctx) => {
      if (!event.prompt || event.prompt.length < 5) return;
      const trigger = ctx?.trigger ?? void 0;
      const sessionId = ctx?.sessionKey ?? void 0;
      if (isNonInteractiveTrigger(trigger, sessionId)) {
        api.logger.info("openclaw-mem0: skipping recall for non-interactive trigger");
        return;
      }
      if (sessionId) session.setCurrentSessionId(sessionId);
      const isNewSession = true;
      const isSubagent = isSubagentSession(sessionId);
      const recallSessionKey = isSubagent ? void 0 : sessionId;
      try {
        const recallTopK = Math.max((cfg.topK ?? 5) * 2, 10);
        let longTermResults = await provider.search(
          event.prompt,
          buildSearchOptions(void 0, recallTopK, void 0, recallSessionKey)
        );
        const recallThreshold = Math.max(cfg.searchThreshold, 0.6);
        longTermResults = longTermResults.filter(
          (r) => (r.score ?? 0) >= recallThreshold
        );
        if (longTermResults.length > 1) {
          const topScore = longTermResults[0]?.score ?? 0;
          if (topScore > 0) {
            longTermResults = longTermResults.filter(
              (r) => (r.score ?? 0) >= topScore * 0.5
            );
          }
        }
        if (event.prompt.length < 100 || isNewSession) {
          const broadOpts = buildSearchOptions(void 0, 5, void 0, recallSessionKey);
          broadOpts.threshold = 0.5;
          const broadResults = await provider.search(
            "recent decisions, preferences, active projects, and configuration",
            broadOpts
          );
          const existingIds = new Set(longTermResults.map((r) => r.id));
          for (const r of broadResults) {
            if (!existingIds.has(r.id)) {
              longTermResults.push(r);
            }
          }
        }
        longTermResults = longTermResults.slice(0, cfg.topK);
        let sessionResults = [];
        if (sessionId) {
          sessionResults = await provider.search(
            event.prompt,
            buildSearchOptions(void 0, void 0, sessionId, recallSessionKey)
          );
          sessionResults = sessionResults.filter(
            (r) => (r.score ?? 0) >= cfg.searchThreshold
          );
        }
        const longTermIds = new Set(longTermResults.map((r) => r.id));
        const uniqueSessionResults = sessionResults.filter(
          (r) => !longTermIds.has(r.id)
        );
        if (longTermResults.length === 0 && uniqueSessionResults.length === 0) return;
        let memoryContext = "";
        if (longTermResults.length > 0) {
          memoryContext += longTermResults.map(
            (r) => `- ${r.memory}${r.categories?.length ? ` [${r.categories.join(", ")}]` : ""}`
          ).join("\n");
        }
        if (uniqueSessionResults.length > 0) {
          if (memoryContext) memoryContext += "\n";
          memoryContext += "\nSession memories:\n";
          memoryContext += uniqueSessionResults.map((r) => `- ${r.memory}`).join("\n");
        }
        const totalCount = longTermResults.length + uniqueSessionResults.length;
        api.logger.info(
          `openclaw-mem0: injecting ${totalCount} memories into context (${longTermResults.length} long-term, ${uniqueSessionResults.length} session)`
        );
        const preamble = isSubagent ? `The following are stored memories for user "${cfg.userId}". You are a subagent \u2014 use these memories for context but do not assume you are this user.` : `The following are stored memories for user "${cfg.userId}". Use them to personalize your response:`;
        return {
          prependContext: `<relevant-memories>
${preamble}
${memoryContext}
</relevant-memories>`
        };
      } catch (err) {
        api.logger.warn(`openclaw-mem0: recall failed: ${String(err)}`);
      }
    });
  }
  if (cfg.autoCapture) {
    api.on("agent_end", async (event, ctx) => {
      if (!event.success || !event.messages || event.messages.length === 0) {
        return;
      }
      const trigger = ctx?.trigger ?? void 0;
      const sessionId = ctx?.sessionKey ?? void 0;
      if (isNonInteractiveTrigger(trigger, sessionId)) {
        api.logger.info("openclaw-mem0: skipping capture for non-interactive trigger");
        return;
      }
      if (isSubagentSession(sessionId)) {
        api.logger.info("openclaw-mem0: skipping capture for subagent (main agent captures consolidated result)");
        return;
      }
      if (sessionId) session.setCurrentSessionId(sessionId);
      try {
        const SUMMARY_PATTERNS = [
          /## What I (Accomplished|Built|Updated)/i,
          /✅\s*(Done|Complete|All done)/i,
          /Here's (what I updated|the recap|a summary)/i,
          /### Changes Made/i,
          /Implementation Status/i,
          /All locked in\. Quick summary/i
        ];
        const allParsed = [];
        for (let i = 0; i < event.messages.length; i++) {
          const msg = event.messages[i];
          if (!msg || typeof msg !== "object") continue;
          const msgObj = msg;
          const role = msgObj.role;
          if (role !== "user" && role !== "assistant") continue;
          let textContent = "";
          const content = msgObj.content;
          if (typeof content === "string") {
            textContent = content;
          } else if (Array.isArray(content)) {
            for (const block of content) {
              if (block && typeof block === "object" && "text" in block && typeof block.text === "string") {
                textContent += (textContent ? "\n" : "") + block.text;
              }
            }
          }
          if (!textContent) continue;
          if (textContent.includes("<relevant-memories>")) {
            textContent = textContent.replace(/<relevant-memories>[\s\S]*?<\/relevant-memories>\s*/g, "").trim();
            if (!textContent) continue;
          }
          const isSummary = role === "assistant" && SUMMARY_PATTERNS.some((p) => p.test(textContent));
          allParsed.push({
            role,
            content: textContent,
            index: i,
            isSummary
          });
        }
        if (allParsed.length === 0) return;
        const recentWindow = 20;
        const recentCutoff = allParsed.length - recentWindow;
        const candidates = [];
        for (const msg of allParsed) {
          if (msg.isSummary && msg.index < recentCutoff) {
            candidates.push(msg);
          }
        }
        const seenIndices = new Set(candidates.map((m) => m.index));
        for (const msg of allParsed) {
          if (msg.index >= recentCutoff && !seenIndices.has(msg.index)) {
            candidates.push(msg);
          }
        }
        candidates.sort((a, b) => a.index - b.index);
        const selected = candidates.map((m) => ({
          role: m.role,
          content: m.content
        }));
        const formattedMessages = filterMessagesForExtraction(selected);
        if (formattedMessages.length === 0) return;
        if (!formattedMessages.some((m) => m.role === "user")) return;
        const timestamp = (/* @__PURE__ */ new Date()).toISOString().split("T")[0];
        formattedMessages.unshift({
          role: "system",
          content: `Current date: ${timestamp}. The user is identified as "${cfg.userId}". Extract durable facts from this conversation. Include this date when storing time-sensitive information.`
        });
        const addOpts = buildAddOptions(void 0, sessionId, sessionId);
        const result = await provider.add(
          formattedMessages,
          addOpts
        );
        const capturedCount = result.results?.length ?? 0;
        if (capturedCount > 0) {
          api.logger.info(
            `openclaw-mem0: auto-captured ${capturedCount} memories`
          );
        }
      } catch (err) {
        api.logger.warn(`openclaw-mem0: capture failed: ${String(err)}`);
      }
    });
  }
}
var index_default = memoryPlugin;
export {
  agentUserId,
  createProvider,
  index_default as default,
  effectiveUserId,
  extractAgentId,
  filterMessagesForExtraction,
  isGenericAssistantMessage,
  isNoiseMessage,
  isNonInteractiveTrigger,
  isSubagentSession,
  mem0ConfigSchema,
  resolveUserId,
  stripNoiseFromContent
};
//# sourceMappingURL=index.js.map
