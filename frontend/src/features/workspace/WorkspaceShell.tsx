import { LogOut, RefreshCw } from "lucide-react";
import type { ReactNode } from "react";
import type { UserRole, WorkspaceModule } from "./types";

export function WorkspaceShell({
  role,
  modules,
  activeModule,
  title,
  subtitle,
  children,
  onModuleChange,
  onRefresh,
  onLogout
}: {
  role: UserRole;
  modules: WorkspaceModule[];
  activeModule: string;
  title: string;
  subtitle: string;
  children: ReactNode;
  onModuleChange: (key: string) => void;
  onRefresh: () => void;
  onLogout: () => void;
}) {
  return (
    <main className="workspace-shell">
      <aside className="workspace-sidebar">
        <div className="workspace-brand">
          <div className="brand-mark">AI</div>
          <div>
            <strong>雪花识别 Agent</strong>
            <span>{role === "admin" ? "管理员控制台" : "业务员工作台"}</span>
          </div>
        </div>
        <nav className="workspace-nav" aria-label="功能模块">
          {modules.map((module) => {
            const Icon = module.icon;
            const active = module.key === activeModule;
            return (
              <button
                className={active ? "module-nav-button active" : "module-nav-button"}
                key={module.key}
                type="button"
                onClick={() => onModuleChange(module.key)}
                title={module.description}
              >
                <Icon size={18} />
                <span>{module.label}</span>
              </button>
            );
          })}
        </nav>
        <div className="workspace-sidebar-footer">
          <button className="module-nav-button" type="button" onClick={onRefresh}>
            <RefreshCw size={18} />
            <span>刷新状态</span>
          </button>
          <button className="module-nav-button" type="button" onClick={onLogout}>
            <LogOut size={18} />
            <span>退出登录</span>
          </button>
        </div>
      </aside>

      <section className="workspace-main">
        <header className="workspace-header">
          <div>
            <p className="eyebrow">CR Snow · AI Recognition</p>
            <h1>{title}</h1>
            <p>{subtitle}</p>
          </div>
          <span className="role-pill">{role === "admin" ? "管理员" : "业务员"}</span>
        </header>
        {children}
      </section>
    </main>
  );
}
