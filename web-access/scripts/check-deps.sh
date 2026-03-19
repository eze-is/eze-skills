#!/usr/bin/env bash
# 环境检查：Node.js、Chrome 调试端口、CDP Proxy

# Node.js
if command -v node &>/dev/null; then
  NODE_VER=$(node --version 2>/dev/null)
  NODE_MAJOR=$(echo "$NODE_VER" | sed 's/v//' | cut -d. -f1)
  if [ "$NODE_MAJOR" -ge 22 ] 2>/dev/null; then
    echo "node: ok ($NODE_VER)"
  else
    echo "node: warn ($NODE_VER, 建议升级到 22+)"
  fi
else
  echo "node: missing"
fi

# Chrome 调试端口（9222）— 用 WebSocket 探测，与 proxy 一致
# chrome://inspect 方式开启调试时只有 WebSocket，没有 HTTP API
if node -e "const ws=new WebSocket('ws://127.0.0.1:9222/devtools/browser');ws.onopen=()=>{console.log('ok');process.exit(0)};ws.onerror=()=>process.exit(1);setTimeout(()=>process.exit(1),2000)" 2>/dev/null; then
  echo "chrome: ok (port 9222)"
else
  echo "chrome: not connected — 请打开 chrome://inspect/#remote-debugging 并勾选 Allow remote debugging"
fi

# CDP Proxy
HEALTH=$(curl -s --connect-timeout 2 "http://127.0.0.1:3456/health" 2>/dev/null)
if echo "$HEALTH" | grep -q '"ok"'; then
  if echo "$HEALTH" | grep -q '"connected":true'; then
    echo "proxy: running (chrome connected)"
  else
    echo "proxy: running (chrome disconnected)"
  fi
else
  echo "proxy: not running"
fi
