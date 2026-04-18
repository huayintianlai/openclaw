import { promises as fs } from 'node:fs';
import { existsSync, readFileSync, statSync } from 'node:fs';
import { basename, dirname, isAbsolute, join, resolve as resolvePath } from 'node:path';
import { pathToFileURL } from 'node:url';
import { Type } from '@sinclair/typebox';
import {
  sendMessageTelegram,
  type OpenClawPluginApi,
  type OpenClawPluginToolContext,
} from 'openclaw/plugin-sdk';

type SearchResult = {
  file_id?: string;
  filename?: string;
  source_file?: string;
  source_type?: string;
  area?: string;
  owner_type?: string;
  owner_id?: string;
  page_no?: number | null;
  slide_no?: number | null;
  chunk_no?: number | null;
  excerpt?: string;
  text?: string;
  score?: number;
  storage_path?: string;
};

type SearchResponse = {
  status: 'success' | 'error';
  query?: string;
  results?: SearchResult[];
  error?: string;
};

type IngestResponse = {
  status: 'success' | 'error';
  file_id?: string;
  filename?: string;
  type?: string;
  chunks?: number;
  duplicate?: boolean;
  meta?: Record<string, unknown>;
  error?: string;
};

type FileMeta = {
  file_id: string;
  filename: string;
  mime_type?: string;
  source_type?: string;
  area?: string;
  access_level?: string;
  owner_type?: string;
  owner_id?: string;
  storage_path?: string;
  parse_status?: string;
  chunk_count?: number;
  tags?: string[];
  created_at?: string;
  updated_at?: string;
};

type FileMetaResponse = {
  status: 'success' | 'error';
  file?: FileMeta;
  hits?: SearchResult[];
  error?: string;
};

type SessionEntry = {
  deliveryContext?: {
    channel?: string;
    to?: string;
    accountId?: string;
  };
  lastChannel?: string;
  lastTo?: string;
  lastAccountId?: string;
  origin?: {
    provider?: string;
    surface?: string;
    to?: string;
    accountId?: string;
  };
};

type ConversationTarget = {
  channel: string;
  to: string;
  accountId?: string;
};

type OfficialFeishuSendModule = {
  sendMediaFeishu: (params: {
    cfg: OpenClawPluginApi['config'];
    to: string;
    mediaBuffer?: Buffer;
    fileName?: string;
    accountId?: string;
  }) => Promise<unknown>;
};

const DEFAULT_API_URL = 'http://47.108.68.217:8000';
const DEFAULT_SEARCH_THRESHOLD = 0.35;
const DEFAULT_LIMIT = 5;
const sessionStoreCache = new Map<
  string,
  { mtimeMs: number; store: Record<string, SessionEntry> }
>();
const OFFICIAL_FEISHU_MODULE_CANDIDATES = [
  '/opt/homebrew/lib/node_modules/openclaw/dist/extensions/feishu/index.js',
  '/usr/local/lib/node_modules/openclaw/dist/extensions/feishu/index.js',
];
let officialFeishuSendModulePromise: Promise<OfficialFeishuSendModule> | null = null;
const TEXT_LIKE_EXTENSIONS = new Set(['.txt', '.md', '.markdown', '.log', '.text']);

function readPluginString(
  pluginConfig: Record<string, unknown> | undefined,
  key: string,
): string | undefined {
  const value = pluginConfig?.[key];
  return typeof value === 'string' && value ? value : undefined;
}

function readPluginNumber(
  pluginConfig: Record<string, unknown> | undefined,
  key: string,
): number | undefined {
  const value = pluginConfig?.[key];
  return typeof value === 'number' && Number.isFinite(value) ? value : undefined;
}

function asArrayOfStrings(value: unknown): string[] | undefined {
  if (!Array.isArray(value)) {
    return undefined;
  }
  const items = value
    .map((item) => (typeof item === 'string' ? item.trim() : ''))
    .filter(Boolean);
  return items.length > 0 ? items : undefined;
}

function authHeaders(apiToken: string): Record<string, string> {
  return apiToken ? { Authorization: `Bearer ${apiToken}` } : {};
}

function buildApiUrl(apiUrl: string, path: string): string {
  return `${apiUrl.replace(/\/+$/, '')}${path}`;
}

async function readJson<T>(response: Response): Promise<T> {
  const text = await response.text();
  if (!response.ok) {
    throw new Error(text || `API error: ${response.status}`);
  }
  try {
    return JSON.parse(text) as T;
  } catch (error) {
    throw new Error(`Invalid JSON response: ${String(error)}`);
  }
}

function formatHitLocation(result: SearchResult): string {
  if (typeof result.page_no === 'number') {
    return `第 ${result.page_no} 页`;
  }
  if (typeof result.slide_no === 'number') {
    return `第 ${result.slide_no} 页幻灯片`;
  }
  return '';
}

function formatSearchResult(result: SearchResult, index: number): string {
  const label = result.filename || result.source_file || '未命名材料';
  const sourceType = result.source_type || 'document';
  const location = formatHitLocation(result);
  const excerpt = (result.excerpt || result.text || '').trim().replace(/\s+/g, ' ');
  const detailParts = [
    result.area ? `area=${result.area}` : '',
    result.file_id ? `file_id=${result.file_id}` : '',
    location,
    typeof result.score === 'number' ? `相似度 ${(result.score * 100).toFixed(1)}%` : '',
  ].filter(Boolean);

  return [
    `${index + 1}. [${sourceType}] ${label}`,
    detailParts.length > 0 ? `   ${detailParts.join(' | ')}` : '',
    excerpt ? `   ${excerpt.slice(0, 220)}${excerpt.length > 220 ? '...' : ''}` : '',
  ].filter(Boolean).join('\n');
}

function resolveSessionStorePath(ctx: OpenClawPluginToolContext): string | undefined {
  if (!ctx.workspaceDir || !ctx.agentId) {
    return undefined;
  }
  const openclawHome = dirname(dirname(ctx.workspaceDir));
  return join(openclawHome, 'agents', ctx.agentId, 'sessions', 'sessions.json');
}

function loadSessionStore(storePath: string | undefined): Record<string, SessionEntry> | undefined {
  if (!storePath) {
    return undefined;
  }

  try {
    const stats = statSync(storePath);
    const cached = sessionStoreCache.get(storePath);
    if (cached && cached.mtimeMs === stats.mtimeMs) {
      return cached.store;
    }

    const parsed = JSON.parse(readFileSync(storePath, 'utf8')) as Record<string, SessionEntry>;
    sessionStoreCache.set(storePath, { mtimeMs: stats.mtimeMs, store: parsed });
    return parsed;
  } catch {
    return undefined;
  }
}

function resolveConversationTarget(ctx: OpenClawPluginToolContext): ConversationTarget | undefined {
  if (!ctx.sessionKey) {
    return undefined;
  }

  const store = loadSessionStore(resolveSessionStorePath(ctx));
  const entry = store?.[ctx.sessionKey];
  if (!entry) {
    return undefined;
  }

  const channel =
    entry.deliveryContext?.channel ||
    entry.origin?.surface ||
    entry.origin?.provider ||
    ctx.messageChannel;
  const to = entry.deliveryContext?.to || entry.lastTo || entry.origin?.to;
  const accountId =
    entry.deliveryContext?.accountId || entry.lastAccountId || entry.origin?.accountId || ctx.agentAccountId;

  if (!channel || !to) {
    return undefined;
  }

  return { channel, to, accountId };
}

function resolveCandidatePaths(api: OpenClawPluginApi, ctx: OpenClawPluginToolContext, inputPath: string): string[] {
  const trimmed = inputPath.trim();
  const candidates = new Set<string>();

  if (isAbsolute(trimmed)) {
    candidates.add(resolvePath(trimmed));
  }
  if (ctx.workspaceDir) {
    candidates.add(resolvePath(ctx.workspaceDir, trimmed));
  }
  if (ctx.agentDir) {
    candidates.add(resolvePath(ctx.agentDir, trimmed));
  }

  try {
    candidates.add(resolvePath(api.resolvePath(trimmed)));
  } catch {
    // Ignore bad path resolution attempts and fall back to the explicit candidates.
  }

  candidates.add(resolvePath(trimmed));
  return Array.from(candidates);
}

async function resolveExistingFilePath(
  api: OpenClawPluginApi,
  ctx: OpenClawPluginToolContext,
  inputPath: string,
): Promise<string> {
  for (const candidate of resolveCandidatePaths(api, ctx, inputPath)) {
    try {
      const stats = await fs.stat(candidate);
      if (stats.isFile()) {
        return candidate;
      }
    } catch {
      // Keep scanning candidates.
    }
  }

  throw new Error(`找不到文件: ${inputPath}`);
}

function openclawHomeFromWorkspace(workspaceDir?: string): string {
  return workspaceDir ? dirname(dirname(workspaceDir)) : process.cwd();
}

async function ensureDownloadPath(
  ctx: OpenClawPluginToolContext,
  fileId: string,
  filename: string,
): Promise<string> {
  const openclawHome = openclawHomeFromWorkspace(ctx.workspaceDir);
  const dirPath = join(openclawHome, 'tmp', 'knowledge-files', fileId);
  await fs.mkdir(dirPath, { recursive: true });
  return join(dirPath, filename);
}

function escapePdfText(value: string): string {
  return value.replace(/\\/g, '\\\\').replace(/\(/g, '\\(').replace(/\)/g, '\\)');
}

function buildSimplePdfBuffer(text: string): Buffer {
  const normalized = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
  const lines = normalized.split('\n').slice(0, 200);
  const body = [
    'BT',
    '/F1 12 Tf',
    '50 780 Td',
    '14 TL',
    ...lines.flatMap((line, index) => {
      const escaped = escapePdfText(line.slice(0, 160));
      return index === 0 ? [`(${escaped}) Tj`] : ['T*', `(${escaped}) Tj`];
    }),
    'ET',
  ].join('\n');

  const objects = [
    '1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n',
    '2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n',
    '3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj\n',
    '4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n',
    `5 0 obj\n<< /Length ${Buffer.byteLength(body, 'utf8')} >>\nstream\n${body}\nendstream\nendobj\n`,
  ];

  let pdf = '%PDF-1.4\n';
  const offsets = [0];
  for (const object of objects) {
    offsets.push(Buffer.byteLength(pdf, 'utf8'));
    pdf += object;
  }
  const xrefOffset = Buffer.byteLength(pdf, 'utf8');
  pdf += `xref\n0 ${objects.length + 1}\n`;
  pdf += '0000000000 65535 f \n';
  for (let i = 1; i < offsets.length; i += 1) {
    pdf += `${String(offsets[i]).padStart(10, '0')} 00000 n \n`;
  }
  pdf += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xrefOffset}\n%%EOF\n`;
  return Buffer.from(pdf, 'utf8');
}

async function prepareIngestSourcePath(
  ctx: OpenClawPluginToolContext,
  originalPath: string,
): Promise<{ filePath: string; uploadFileName: string }> {
  const lowerPath = originalPath.toLowerCase();
  const ext = lowerPath.slice(lowerPath.lastIndexOf('.'));
  if (!TEXT_LIKE_EXTENSIONS.has(ext)) {
    return {
      filePath: originalPath,
      uploadFileName: basename(originalPath),
    };
  }

  const text = await fs.readFile(originalPath, 'utf8');
  const openclawHome = openclawHomeFromWorkspace(ctx.workspaceDir);
  const dirPath = join(openclawHome, 'tmp', 'knowledge-text-pdf');
  await fs.mkdir(dirPath, { recursive: true });
  const uploadFileName = `${basename(originalPath)}.pdf`;
  const filePath = join(dirPath, uploadFileName);
  await fs.writeFile(filePath, buildSimplePdfBuffer(text));
  return { filePath, uploadFileName };
}

async function fetchSearch(
  apiUrl: string,
  apiToken: string,
  params: {
    query: string;
    area?: string;
    accessLevel?: string;
    limit?: number;
    minScore?: number;
    ownerType?: string;
    ownerId?: string;
  },
): Promise<SearchResponse> {
  const formData = new FormData();
  formData.append('query', params.query);
  formData.append('limit', String(params.limit ?? DEFAULT_LIMIT));
  formData.append('access_level', params.accessLevel || 'global');
  formData.append('min_score', String(params.minScore ?? DEFAULT_SEARCH_THRESHOLD));
  if (params.area) {
    formData.append('area', params.area);
  }
  if (params.ownerType) {
    formData.append('owner_type', params.ownerType);
  }
  if (params.ownerId) {
    formData.append('owner_id', params.ownerId);
  }

  const response = await fetch(buildApiUrl(apiUrl, '/search'), {
    method: 'POST',
    headers: authHeaders(apiToken),
    body: formData,
  });
  return readJson<SearchResponse>(response);
}

async function fetchIngest(
  apiUrl: string,
  apiToken: string,
  params: {
    filePath: string;
    uploadFileName?: string;
    area: string;
    accessLevel: string;
    ownerType: string;
    ownerId: string;
    tags?: string[];
    forceReindex?: boolean;
  },
): Promise<IngestResponse> {
  const fileBuffer = await fs.readFile(params.filePath);
  const formData = new FormData();
  formData.append('file', new Blob([fileBuffer]), params.uploadFileName || basename(params.filePath));
  formData.append('area', params.area);
  formData.append('access_level', params.accessLevel);
  formData.append('owner_type', params.ownerType);
  formData.append('owner_id', params.ownerId);
  formData.append('force_reindex', params.forceReindex ? 'true' : 'false');
  for (const tag of params.tags ?? []) {
    formData.append('tags', tag);
  }

  const response = await fetch(buildApiUrl(apiUrl, '/ingest/file'), {
    method: 'POST',
    headers: authHeaders(apiToken),
    body: formData,
  });
  return readJson<IngestResponse>(response);
}

async function fetchFileMeta(apiUrl: string, apiToken: string, fileId: string): Promise<FileMetaResponse> {
  const response = await fetch(buildApiUrl(apiUrl, `/files/${encodeURIComponent(fileId)}/meta`), {
    method: 'GET',
    headers: authHeaders(apiToken),
  });
  return readJson<FileMetaResponse>(response);
}

async function downloadKnowledgeFile(
  apiUrl: string,
  apiToken: string,
  fileId: string,
  destinationPath: string,
): Promise<void> {
  const response = await fetch(buildApiUrl(apiUrl, `/files/${encodeURIComponent(fileId)}`), {
    method: 'GET',
    headers: authHeaders(apiToken),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `文件下载失败: ${response.status}`);
  }

  const arrayBuffer = await response.arrayBuffer();
  await fs.writeFile(destinationPath, Buffer.from(arrayBuffer));
}

async function getOfficialFeishuSendModule(): Promise<OfficialFeishuSendModule> {
  if (!officialFeishuSendModulePromise) {
    officialFeishuSendModulePromise = (async () => {
      for (const candidate of OFFICIAL_FEISHU_MODULE_CANDIDATES) {
        try {
          const module = (await import(pathToFileURL(candidate).href)) as Partial<OfficialFeishuSendModule>;
          if (typeof module.sendMediaFeishu === 'function') {
            return module as OfficialFeishuSendModule;
          }
        } catch {
          // Try the next official install path candidate.
        }
      }
      throw new Error('Official Feishu send runtime not found');
    })();
  }
  return officialFeishuSendModulePromise;
}

async function returnFileToConversation(
  api: OpenClawPluginApi,
  ctx: OpenClawPluginToolContext,
  target: ConversationTarget,
  localPath: string,
  fileMeta: FileMeta,
): Promise<string> {
  if (target.channel === 'feishu') {
    const feishuSend = await getOfficialFeishuSendModule();
    await feishuSend.sendMediaFeishu({
      cfg: api.config,
      to: target.to,
      mediaBuffer: await fs.readFile(localPath),
      fileName: fileMeta.filename,
      accountId: target.accountId,
    });
    return 'feishu';
  }

  if (target.channel === 'telegram') {
    await sendMessageTelegram(target.to, '', {
      mediaUrl: pathToFileURL(localPath).toString(),
      accountId: target.accountId || undefined,
    });
    return 'telegram';
  }

  throw new Error(`当前只支持飞书和 Telegram 直接回传附件，当前会话渠道为 ${target.channel}`);
}

function normalizeExplicitTarget(params: {
  channel?: string;
  target?: string;
  accountId?: string;
}): ConversationTarget | undefined {
  if (!params.channel || !params.target) {
    return undefined;
  }
  return {
    channel: params.channel,
    to: params.target,
    accountId: params.accountId,
  };
}

export default {
  id: 'knowledge-search-plugin',
  name: 'Knowledge Search',
  description: 'Search, ingest, fetch, and return documents from the knowledge base',

  register(api: OpenClawPluginApi) {
    const apiUrl =
      readPluginString(api.pluginConfig, 'apiUrl') ||
      process.env.KNOWLEDGE_API_URL ||
      DEFAULT_API_URL;
    const apiToken =
      readPluginString(api.pluginConfig, 'apiToken') ||
      process.env.KNOWLEDGE_API_TOKEN ||
      '';
    const defaultSearchThreshold =
      readPluginNumber(api.pluginConfig, 'searchThreshold') ||
      DEFAULT_SEARCH_THRESHOLD;

    api.logger.info('knowledge-search-plugin: registered');

    api.registerTool(
      (toolCtx) => ({
        name: 'knowledge_search',
        label: 'Knowledge Search',
        description:
          '向量语义搜索知识库。用于搜索 PDF、PPT、图片等已入库材料，并返回 file_id、命中片段和材料定位信息。',
        parameters: Type.Object({
          query: Type.String({ description: '搜索关键词或自然语言问题' }),
          area: Type.Optional(Type.String({ description: '限定搜索范围' })),
          accessLevel: Type.Optional(
            Type.String({ description: '访问级别，默认 global' }),
          ),
          ownerType: Type.Optional(
            Type.String({ description: '限定上传归属类型，如 agent、user、global' }),
          ),
          ownerId: Type.Optional(Type.String({ description: '限定上传归属 ID' })),
          limit: Type.Optional(Type.Number({ description: '返回结果数量，默认 5' })),
          minScore: Type.Optional(
            Type.Number({ description: '最小相似度阈值，默认 0.35' }),
          ),
        }),
        async execute(_toolCallId, params) {
          const {
            query,
            area,
            accessLevel,
            ownerType,
            ownerId,
            limit = DEFAULT_LIMIT,
            minScore = defaultSearchThreshold,
          } = params as {
            query: string;
            area?: string;
            accessLevel?: string;
            ownerType?: string;
            ownerId?: string;
            limit?: number;
            minScore?: number;
          };

          try {
            const result = await fetchSearch(apiUrl, apiToken, {
              query,
              area,
              accessLevel,
              ownerType,
              ownerId,
              limit,
              minScore,
            });

            const hits = (result.results ?? []).filter(
              (entry) => typeof entry.score !== 'number' || entry.score >= minScore,
            );
            if (result.status !== 'success' || hits.length === 0) {
              return {
                content: [{ type: 'text', text: '没有找到相关材料。' }],
                details: { count: 0, results: [] },
              };
            }

            const formatted = hits.map((entry, index) => formatSearchResult(entry, index)).join('\n\n');
            return {
              content: [
                {
                  type: 'text',
                  text: `找到 ${hits.length} 条相关材料：\n\n${formatted}`,
                },
              ],
              details: { count: hits.length, results: hits },
            };
          } catch (error) {
            return {
              content: [{ type: 'text', text: `知识库搜索失败: ${String(error)}` }],
              details: { error: String(error) },
            };
          }
        },
      }),
      { name: 'knowledge_search' },
    );

    api.registerTool(
      (toolCtx) => ({
        name: 'knowledge_ingest_file',
        label: 'Knowledge Ingest File',
        description:
          '将本地文件上传到知识库并完成解析入库。支持 PDF、PPTX、图片，返回 file_id 供后续检索和回传。',
        parameters: Type.Object({
          path: Type.String({ description: '待入库文件路径，可为绝对路径或相对 workspace 路径' }),
          area: Type.String({ description: '知识库分类，如 工作文档、培训资料、日记' }),
          accessLevel: Type.Optional(
            Type.String({ description: '访问级别，默认 global' }),
          ),
          ownerType: Type.Optional(
            Type.String({ description: '归属类型，默认 agent' }),
          ),
          ownerId: Type.Optional(
            Type.String({ description: '归属 ID，默认当前 agentId' }),
          ),
          tags: Type.Optional(
            Type.Array(Type.String({ description: '标签' }), { description: '可选标签列表' }),
          ),
          forceReindex: Type.Optional(
            Type.Boolean({ description: '是否强制重建索引，默认 false' }),
          ),
        }),
        async execute(_toolCallId, params) {
          const {
            path,
            area,
            accessLevel = 'global',
            ownerType = 'agent',
            ownerId,
            forceReindex = false,
          } = params as {
            path: string;
            area: string;
            accessLevel?: string;
            ownerType?: string;
            ownerId?: string;
            forceReindex?: boolean;
          };

          try {
            const resolvedPath = await resolveExistingFilePath(api, toolCtx, path);
            const preparedSource = await prepareIngestSourcePath(toolCtx, resolvedPath);
            const ingestResult = await fetchIngest(apiUrl, apiToken, {
              filePath: preparedSource.filePath,
              uploadFileName: preparedSource.uploadFileName,
              area,
              accessLevel,
              ownerType,
              ownerId: ownerId || toolCtx.agentId || 'default',
              tags: asArrayOfStrings((params as { tags?: unknown }).tags),
              forceReindex,
            });

            if (ingestResult.status !== 'success' || !ingestResult.file_id) {
              throw new Error(ingestResult.error || '未知入库错误');
            }

            const lines = [
              `入库成功：${ingestResult.filename || preparedSource.uploadFileName}`,
              `file_id: ${ingestResult.file_id}`,
              ingestResult.type ? `type: ${ingestResult.type}` : '',
              typeof ingestResult.chunks === 'number' ? `chunks: ${ingestResult.chunks}` : '',
              ingestResult.duplicate ? '本次命中去重，复用了已有索引。' : '',
            ].filter(Boolean);

            return {
              content: [{ type: 'text', text: lines.join('\n') }],
              details: ingestResult,
            };
          } catch (error) {
            return {
              content: [{ type: 'text', text: `文件入库失败: ${String(error)}` }],
              details: { error: String(error) },
            };
          }
        },
      }),
      { name: 'knowledge_ingest_file' },
    );

    api.registerTool(
      (toolCtx) => ({
        name: 'knowledge_get_file',
        label: 'Knowledge Get File',
        description: '获取已入库附件的元数据、命中片段和本地缓存路径。',
        parameters: Type.Object({
          fileId: Type.String({ description: '知识库 file_id' }),
        }),
        async execute(_toolCallId, params) {
          const { fileId } = params as { fileId: string };

          try {
            const metaResult = await fetchFileMeta(apiUrl, apiToken, fileId);
            if (metaResult.status !== 'success' || !metaResult.file) {
              throw new Error(metaResult.error || '材料不存在');
            }

            const fileMeta = metaResult.file;
            const destinationPath = await ensureDownloadPath(toolCtx, fileMeta.file_id, fileMeta.filename);
            if (!existsSync(destinationPath)) {
              await downloadKnowledgeFile(apiUrl, apiToken, fileId, destinationPath);
            }

            const hits = (metaResult.hits ?? []).slice(0, 3);
            const summary = [
              `材料：${fileMeta.filename}`,
              `file_id: ${fileMeta.file_id}`,
              fileMeta.source_type ? `type: ${fileMeta.source_type}` : '',
              fileMeta.area ? `area: ${fileMeta.area}` : '',
              typeof fileMeta.chunk_count === 'number' ? `chunks: ${fileMeta.chunk_count}` : '',
              `local_path: ${destinationPath}`,
              hits.length > 0 ? '' : '',
              ...hits.map((hit, index) => formatSearchResult(hit, index)),
            ].filter(Boolean).join('\n');

            return {
              content: [{ type: 'text', text: summary }],
              details: {
                file: fileMeta,
                hits,
                localPath: destinationPath,
              },
            };
          } catch (error) {
            return {
              content: [{ type: 'text', text: `获取材料失败: ${String(error)}` }],
              details: { error: String(error) },
            };
          }
        },
      }),
      { name: 'knowledge_get_file' },
    );

    api.registerTool(
      (toolCtx) => ({
        name: 'knowledge_return_file',
        label: 'Knowledge Return File',
        description:
          '将已入库的原始附件直接重新发回当前会话。当前支持飞书和 Telegram，会自动定位当前会话目标。',
        parameters: Type.Object({
          fileId: Type.String({ description: '知识库 file_id' }),
          channel: Type.Optional(
            Type.String({ description: '显式指定回传渠道，如 feishu / telegram' }),
          ),
          target: Type.Optional(
            Type.String({ description: '显式指定回传目标，如 user:ou_xxx 或 chat_id' }),
          ),
          accountId: Type.Optional(
            Type.String({ description: '显式指定发送所用账号 ID' }),
          ),
        }),
        async execute(_toolCallId, params) {
          const { fileId, channel, target, accountId } = params as {
            fileId: string;
            channel?: string;
            target?: string;
            accountId?: string;
          };

          try {
            const conversationTarget =
              normalizeExplicitTarget({ channel, target, accountId }) ||
              resolveConversationTarget(toolCtx);
            if (!conversationTarget) {
              throw new Error('当前会话缺少回传目标，无法定位 channel/to/accountId');
            }

            const metaResult = await fetchFileMeta(apiUrl, apiToken, fileId);
            if (metaResult.status !== 'success' || !metaResult.file) {
              throw new Error(metaResult.error || '材料不存在');
            }

            const fileMeta = metaResult.file;
            const destinationPath = await ensureDownloadPath(toolCtx, fileMeta.file_id, fileMeta.filename);
            await downloadKnowledgeFile(apiUrl, apiToken, fileId, destinationPath);

            const deliveredVia = await returnFileToConversation(
              api,
              toolCtx,
              conversationTarget,
              destinationPath,
              fileMeta,
            );
            const topHit = metaResult.hits?.[0];
            const location = topHit ? formatHitLocation(topHit) : '';

            return {
              content: [
                {
                  type: 'text',
                  text: [
                    `已回传附件：${fileMeta.filename}`,
                    `file_id: ${fileMeta.file_id}`,
                    `channel: ${deliveredVia}`,
                    location ? `命中位置：${location}` : '',
                  ].filter(Boolean).join('\n'),
                },
              ],
              details: {
                file: fileMeta,
                deliveredVia,
                target: conversationTarget,
                localPath: destinationPath,
              },
            };
          } catch (error) {
            return {
              content: [{ type: 'text', text: `回传附件失败: ${String(error)}` }],
              details: { error: String(error) },
            };
          }
        },
      }),
      { name: 'knowledge_return_file' },
    );
  },
};
