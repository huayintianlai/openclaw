#!/usr/bin/env node

const path = require("node:path");

const plugin = require("../extensions/mobile-runtime-plugin/index.js");

async function main() {
  const repoRoot = path.resolve(__dirname, "..");
  const runtime = new plugin.__internal.MobileRuntime(
    plugin.__internal.resolveConfig(
      {
        repoRoot,
        registryPath: path.join(repoRoot, "devices", "mobile.registry.json"),
        stateDir: path.join(repoRoot, "state", "mobile-runtime"),
        flowDir: path.join(repoRoot, "flows", "mobile"),
        adbPath: "/opt/homebrew/bin/adb",
        autoGlmDir: "/Users/xiaojiujiu2/Documents/coding/AutoGLM"
      },
      console
    ),
    console
  );

  await runtime.init();

  const devices = await runtime.describeDevices();
  console.log(JSON.stringify({ phase: "list_devices", count: devices.length, devices }, null, 2));

  if (devices.length === 0) {
    process.exit(1);
  }

  const primary = devices.find((item) => item.alias === "xiaodong-main") || devices[0];
  const observeDevice = runtime.loadRegistry().devices.find((item) => item.alias === primary.alias) || primary;
  const backend = runtime.getBackend(primary.backend);
  const observation = await backend.observe(observeDevice, {
    include_screenshot: true,
    include_ui_tree: true
  });

  console.log(JSON.stringify({
    phase: "observe",
    alias: primary.alias,
    backend: primary.backend,
    observation: observation.observation,
    fallback_used: observation.fallback_used
  }, null, 2));

  const safeAction = await runtime.executeMacProxyAction(observeDevice, {
    kind: "open_app",
    app: "settings"
  });

  console.log(JSON.stringify({
    phase: "safe_action",
    result: safeAction
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
