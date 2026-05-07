const PASSWORD_HASH = "3fc1ce90629e0e4f0976ed8aa37ddcf89cd2ee6cb6853fbdde030b877700571e";
const COOKIE_NAME = "aig_auth";

async function sha256(message) {
  const msgBuffer = new TextEncoder().encode(message);
  const hashBuffer = await crypto.subtle.digest("SHA-256", msgBuffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, "0")).join("");
}

function getAuthCookie(request) {
  const cookies = request.headers.get("Cookie") || "";
  const match = cookies.match(new RegExp(`${COOKIE_NAME}=([^;]+)`));
  return match ? match[1] : null;
}

const LOGIN_PAGE = `<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Google Ads 管理后台 - 登录</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .card {
      background: white;
      border-radius: 16px;
      padding: 48px 40px;
      width: 100%;
      max-width: 400px;
      box-shadow: 0 25px 50px rgba(0,0,0,0.3);
    }
    .logo {
      text-align: center;
      margin-bottom: 32px;
    }
    .logo h1 {
      font-size: 20px;
      font-weight: 700;
      color: #111827;
      margin-top: 8px;
    }
    .logo p { font-size: 13px; color: #6b7280; margin-top: 4px; }
    .icon {
      width: 56px; height: 56px;
      background: linear-gradient(135deg, #667eea, #764ba2);
      border-radius: 14px;
      display: flex; align-items: center; justify-content: center;
      margin: 0 auto;
      font-size: 24px;
    }
    label { display: block; font-size: 14px; font-weight: 500; color: #374151; margin-bottom: 6px; }
    input[type=password] {
      width: 100%;
      padding: 12px 16px;
      border: 1.5px solid #e5e7eb;
      border-radius: 10px;
      font-size: 15px;
      outline: none;
      transition: border-color 0.2s;
    }
    input[type=password]:focus { border-color: #667eea; }
    button {
      width: 100%;
      padding: 13px;
      background: linear-gradient(135deg, #667eea, #764ba2);
      color: white;
      border: none;
      border-radius: 10px;
      font-size: 15px;
      font-weight: 600;
      cursor: pointer;
      margin-top: 20px;
      transition: opacity 0.2s;
    }
    button:hover { opacity: 0.9; }
    .error {
      background: #fef2f2;
      color: #dc2626;
      border: 1px solid #fecaca;
      border-radius: 8px;
      padding: 10px 14px;
      font-size: 13px;
      margin-bottom: 16px;
    }
  </style>
</head>
<body>
  <div class="card">
    <div class="logo">
      <div class="icon">📊</div>
      <h1>AI Google Ads</h1>
      <p>全托管投放系统 · 管理后台</p>
    </div>
    {{ERROR}}
    <form method="POST" action="/_auth/login">
      <label>访问密码</label>
      <input type="password" name="password" placeholder="请输入访问密码" autofocus required>
      <button type="submit">进入系统 →</button>
    </form>
  </div>
</body>
</html>`;

export async function onRequest(context) {
  const { request, next } = context;
  const url = new URL(request.url);

  // Handle login POST
  if (request.method === "POST" && url.pathname === "/_auth/login") {
    const formData = await request.formData();
    const password = formData.get("password") || "";
    const hash = await sha256(password);

    if (hash === PASSWORD_HASH) {
      return new Response(null, {
        status: 302,
        headers: {
          "Location": "/",
          "Set-Cookie": `${COOKIE_NAME}=${PASSWORD_HASH}; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=86400`,
        },
      });
    }

    return new Response(
      LOGIN_PAGE.replace("{{ERROR}}", '<div class="error">❌ 密码错误，请重试</div>'),
      { status: 401, headers: { "Content-Type": "text/html; charset=utf-8" } }
    );
  }

  // Check auth cookie
  const cookie = getAuthCookie(request);
  if (cookie === PASSWORD_HASH) {
    return next();
  }

  // Show login page
  return new Response(
    LOGIN_PAGE.replace("{{ERROR}}", ""),
    { status: 200, headers: { "Content-Type": "text/html; charset=utf-8" } }
  );
}