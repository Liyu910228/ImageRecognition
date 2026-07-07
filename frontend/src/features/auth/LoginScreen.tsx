import { useState } from "react";
import { LockKeyhole, ShieldCheck, UserRound } from "lucide-react";

export function LoginScreen({
  error,
  onLogin
}: {
  error: string;
  onLogin: (username: string, password: string) => void;
}) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  return (
    <main className="login-page">
      <section className="login-hero">
        <div className="brand-lockup">
          <div className="brand-mark">
            <ShieldCheck size={34} />
          </div>
          <div>
            <p>CR SNOW</p>
            <h1>产品图片 AI 识别系统</h1>
          </div>
        </div>
        <div className="hero-copy">
          <h2>统一管理模板库、模型配置与门店图片识别。</h2>
          <p>管理员维护模型和模板，业务员专注上传识别，让产品编码匹配更快、更稳。</p>
        </div>
        <div className="login-feature-grid">
          <div><strong>AI</strong><span>多模态识别</span></div>
          <div><strong>API</strong><span>模型可配置</span></div>
          <div><strong>DATA</strong><span>模板库管理</span></div>
        </div>
      </section>

      <section className="login-panel">
        <p className="login-kicker">ACCOUNT LOGIN</p>
        <h2>欢迎回来</h2>
        <p className="login-subtitle">请选择角色账号登录系统。</p>
        <label>
          <span>账号</span>
          <div className="login-input">
            <UserRound size={18} />
            <input value={username} onChange={(event) => setUsername(event.target.value)} placeholder="请输入账号" />
          </div>
        </label>
        <label>
          <span>密码</span>
          <div className="login-input">
            <LockKeyhole size={18} />
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="请输入密码"
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  onLogin(username, password);
                }
              }}
            />
          </div>
        </label>
        {error && <div className="login-error">{error}</div>}
        <button className="login-button" type="button" onClick={() => onLogin(username, password)}>
          登录系统
          <span>→</span>
        </button>
        <div className="demo-accounts">
          <div><span>管理员</span><strong>admin / admin</strong></div>
          <div><span>业务员</span><strong>root / 2345</strong></div>
        </div>
      </section>
    </main>
  );
}
