#!/usr/bin/env bash
set -e

BASE_URL="${BASE_URL:-https://deepl.micosoft.icu/api}"
CARD_KEY="${CARD_KEY:-}"
PAGE_SIZE="${PAGE_SIZE:-10}"
PAGE="${PAGE:-1}"

if [ -z "$CARD_KEY" ]; then
  echo "ERR: CARD_KEY is required" >&2
  exit 2
fi

# 1) login (do not echo key)
# Key is a plain activation code (UUID-like). No need for special escaping.
login_json=$(printf '{"card":"%s","agent":"main"}' "$CARD_KEY")
login_resp=$(curl -sS -m 20 "$BASE_URL/users/card-login" \
  -H 'content-type: application/json' \
  --data "$login_json")

# Extract token & basic fields
TOKEN=$(node -e "const r=JSON.parse(process.argv[1]); if(r.code) process.exit(3); console.log(r.data && r.data.token || '')" "$login_resp" 2>/dev/null || true)
if [ -z "$TOKEN" ]; then
  echo "ERR: login failed or token missing" >&2
  echo "login_resp_prefix: ${login_resp:0:200}" >&2
  exit 3
fi

# 2) whoami
whoami_resp=$(curl -sS -m 20 "$BASE_URL/users/whoami" -H "x-auth-token: $TOKEN")

# 3) chatlog (optional)
chatlog_body=$(node -e "console.log(JSON.stringify({page:+process.env.PAGE||1,pageSize:+process.env.PAGE_SIZE||10,sortBy:'create_at',desc:1}))")
chatlog_resp=$(curl -sS -m 20 "$BASE_URL/chatgpt/chatlog" \
  -H 'content-type: application/json' \
  -H "x-auth-token: $TOKEN" \
  --data "$chatlog_body" || true)

# Normalize output
node - "$whoami_resp" "$chatlog_resp" <<'JS'
const whoami = JSON.parse(process.argv[2]);
const chatlog = (()=>{ try { return JSON.parse(process.argv[3]); } catch { return null; } })();
function die(msg,obj){
  console.error('ERR:', msg);
  if(obj) console.error(String(obj).slice(0,200));
  process.exit(4);
}
if (whoami.code) die('whoami failed', whoami.msg||JSON.stringify(whoami));
const u = whoami.data||{};
const dayTotal = Number(u?.vip?.day_score ?? 0);
const dayUsed = Number(u?.day_score_used ?? 0);
const dayLeft = (isFinite(dayTotal)&&isFinite(dayUsed)) ? (dayTotal - dayUsed) : null;
const expireAt = u?.vip?.expire_at ?? null;
const out = {
  userId: u?.id ?? null,
  account: u?.account ?? null,
  dayTotal,
  dayUsed,
  dayLeft,
  expireAt,
};
if (chatlog && !chatlog.code) {
  out.recent = (chatlog.data?.list||[]).slice(0,5).map(x=>({
    id:x.id, model:x.model, channel:x.channel, role:x.role,
    create_at:x.create_at, prompt_tokens:x.prompt_tokens,
    completion_tokens:x.completion_tokens, cached_tokens:x.cached_tokens,
    score:x.score, score_used:x.score_used,
  }));
}
process.stdout.write(JSON.stringify(out,null,2));
JS