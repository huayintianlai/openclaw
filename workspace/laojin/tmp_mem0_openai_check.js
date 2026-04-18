const OpenAI = require('/Volumes/KenDisk/Coding/openclaw-runtime/extensions/openclaw-mem0/node_modules/openai');

async function main() {
  const apiKey = process.env.MEM0_OPENAI_API_KEY;
  const model = process.env.MEM0_EMBEDDER_MODEL || 'text-embedding-3-small';
  const baseURL = 'https://api.openai.com/v1';
  console.log(JSON.stringify({
    hasKey: !!apiKey,
    keyLen: apiKey ? apiKey.length : 0,
    model,
    baseURL
  }));

  const client = new OpenAI({ apiKey, baseURL, timeout: 20000 });
  try {
    const res = await client.embeddings.create({
      model,
      input: 'OpenClaw memory health check'
    });
    console.log(JSON.stringify({ ok: true, dims: res?.data?.[0]?.embedding?.length || null }));
  } catch (err) {
    console.error(JSON.stringify({
      ok: false,
      name: err?.name,
      message: err?.message,
      status: err?.status || null,
      code: err?.code || null,
      type: err?.type || null,
      cause: err?.cause ? {
        name: err.cause.name,
        message: err.cause.message,
        code: err.cause.code,
        errno: err.cause.errno,
        syscall: err.cause.syscall,
        type: err.cause.type
      } : null
    }, null, 2));
    process.exit(1);
  }
}

main();
