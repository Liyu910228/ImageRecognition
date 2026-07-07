import { useEffect, useMemo, useState } from "react";
import {
  BarChart3,
  Boxes,
  ClipboardCheck,
  Database,
  KeyRound,
  ScrollText,
  Settings2,
  ShieldCheck,
  UploadCloud,
  WandSparkles
} from "lucide-react";
import { LoginScreen } from "./features/auth/LoginScreen";
import { OverviewPage } from "./features/admin/OverviewPage";
import { ModelManagementPage } from "./features/admin/ModelManagementPage";
import { TemplateLibraryPage } from "./features/admin/TemplateLibraryPage";
import { BrandRulesPage } from "./features/admin/BrandRulesPage";
import { LogsPage } from "./features/admin/LogsPage";
import { OpenApiPage } from "./features/admin/OpenApiPage";
import { UploadRecognitionPage } from "./features/business/UploadRecognitionPage";
import { BatchResultsPage } from "./features/business/BatchResultsPage";
import { ReviewPage } from "./features/business/ReviewPage";
import { useRecognitionWorkflow } from "./features/recognition/hooks/useRecognitionWorkflow";
import { useTemplateLibrary } from "./features/templates/useTemplateLibrary";
import { useModelSettings } from "./features/settings/useModelSettings";
import { useRecognitionLogs } from "./features/settings/useRecognitionLogs";
import { useOpenApiTokens } from "./features/settings/useOpenApiTokens";
import { WorkspaceShell } from "./features/workspace/WorkspaceShell";
import type { UserRole, WorkspaceModule } from "./features/workspace/types";
import { fetchSystemStatus, type SystemStatus } from "./shared/api/client";

type LoadState = "loading" | "ready" | "error";
type AdminModuleKey = "overview" | "business-test" | "models" | "templates" | "brand-rules" | "logs" | "open-api";
type BusinessModuleKey = "upload" | "batch-results" | "review";

const adminModules: WorkspaceModule[] = [
  { key: "overview", label: "工作概览", description: "系统状态和关键指标", icon: BarChart3 },
  { key: "business-test", label: "业务测试", description: "用当前模型和规则测试图片识别效果", icon: WandSparkles },
  { key: "models", label: "模型管理", description: "平台模型独立配置", icon: Settings2 },
  { key: "templates", label: "模板库", description: "上传、构建和删除模板文件", icon: Database },
  { key: "brand-rules", label: "品牌规则", description: "品牌词、提示词、Top 候选和权重", icon: ShieldCheck },
  { key: "logs", label: "日志管理", description: "查看匹配过程和门禁原因", icon: ScrollText },
  { key: "open-api", label: "开放接口", description: "生成接口调用 Token", icon: KeyRound }
];

const businessModules: WorkspaceModule[] = [
  { key: "upload", label: "上传识别", description: "图片、文件夹、表格链接识别", icon: UploadCloud },
  { key: "batch-results", label: "批量结果", description: "导出、重试和查看候选", icon: Boxes },
  { key: "review", label: "人工审核", description: "原图和模板图审核统计", icon: ClipboardCheck }
];

export function App() {
  const [role, setRole] = useState<UserRole | null>(() => {
    const saved = sessionStorage.getItem("userRole");
    return saved === "admin" || saved === "business" ? saved : null;
  });
  const [activeAdminModule, setActiveAdminModule] = useState<AdminModuleKey>(() => getSavedModule("adminActiveModule", "overview", adminModules) as AdminModuleKey);
  const [activeBusinessModule, setActiveBusinessModule] = useState<BusinessModuleKey>(() => getSavedModule("businessActiveModule", "upload", businessModules) as BusinessModuleKey);
  const [loginError, setLoginError] = useState("");
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [error, setError] = useState("");

  async function loadStatus() {
    setLoadState("loading");
    setError("");
    try {
      setStatus(await fetchSystemStatus());
      setLoadState("ready");
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "状态接口请求失败");
      setLoadState("error");
    }
  }

  const models = useModelSettings(loadStatus);
  const templates = useTemplateLibrary(loadStatus);
  const logs = useRecognitionLogs();
  const openApi = useOpenApiTokens();
  const workflow = useRecognitionWorkflow(models.frontendApiKey);

  useEffect(() => {
    void loadStatus();
    void models.loadModelSettings();
    void templates.loadTemplateSources();
    void openApi.loadOpenApiStatus();
    void logs.loadRecognitionLogs();
  }, []);

  function handleLogin(username: string, password: string) {
    if (username === "admin" && password === "admin") {
      sessionStorage.setItem("userRole", "admin");
      setRole("admin");
      setLoginError("");
      return;
    }
    if (username === "root" && password === "2345") {
      sessionStorage.setItem("userRole", "business");
      setRole("business");
      setLoginError("");
      return;
    }
    setLoginError("账号或密码错误");
  }

  function handleLogout() {
    sessionStorage.removeItem("userRole");
    setRole(null);
  }

  function handleModuleChange(key: string) {
    if (role === "admin" && isModuleKey(key, adminModules)) {
      setActiveAdminModule(key as AdminModuleKey);
      sessionStorage.setItem("adminActiveModule", key);
    }
    if (role === "business" && isModuleKey(key, businessModules)) {
      setActiveBusinessModule(key as BusinessModuleKey);
      sessionStorage.setItem("businessActiveModule", key);
    }
  }

  const activeModule = role === "admin" ? activeAdminModule : activeBusinessModule;
  const modules = role === "admin" ? adminModules : businessModules;
  const activeModuleInfo = useMemo(
    () => modules.find((module) => module.key === activeModule) ?? modules[0],
    [activeModule, modules]
  );

  if (!role) {
    return <LoginScreen error={loginError} onLogin={handleLogin} />;
  }

  return (
    <WorkspaceShell
      role={role}
      modules={modules}
      activeModule={activeModule}
      title={role === "admin" ? "图片识别管理工作台" : "图片识别业务工作台"}
      subtitle={activeModuleInfo.description}
      onModuleChange={handleModuleChange}
      onRefresh={() => void refreshAll(loadStatus, models.loadModelSettings, templates.loadTemplateSources, openApi.loadOpenApiStatus, logs.loadRecognitionLogs)}
      onLogout={handleLogout}
    >
      {loadState === "error" && <div className="error-banner">{error}</div>}
      {loadState === "loading" && <div className="model-note module-loading">正在同步系统状态...</div>}
      {role === "admin" ? renderAdminModule(activeAdminModule, { status, templates, models, logs, openApi, workflow }) : renderBusinessModule(activeBusinessModule, workflow)}
    </WorkspaceShell>
  );
}

function renderAdminModule(
  activeModule: AdminModuleKey,
  state: {
    status: SystemStatus | null;
    templates: ReturnType<typeof useTemplateLibrary>;
    models: ReturnType<typeof useModelSettings>;
    logs: ReturnType<typeof useRecognitionLogs>;
    openApi: ReturnType<typeof useOpenApiTokens>;
    workflow: ReturnType<typeof useRecognitionWorkflow>;
  }
) {
  switch (activeModule) {
    case "overview":
      return (
        <OverviewPage
          status={state.status}
          templateSources={state.templates.templateSources}
          logs={state.logs.recognitionLogs}
          openApiStatus={state.openApi.openApiStatus}
        />
      );
    case "business-test":
      return (
        <BusinessTestPage
          workflow={state.workflow}
        />
      );
    case "models":
      return <ModelManagementPage settings={state.models} />;
    case "templates":
      return <TemplateLibraryPage templates={state.templates} />;
    case "brand-rules":
      return <BrandRulesPage settings={state.models} />;
    case "logs":
      return <LogsPage logs={state.logs} />;
    case "open-api":
      return <OpenApiPage openApi={state.openApi} />;
    default:
      return null;
  }
}

function BusinessTestPage({ workflow }: { workflow: ReturnType<typeof useRecognitionWorkflow> }) {
  return (
    <div className="business-test-stack">
      <UploadRecognitionPage workflow={workflow} />
      <BatchResultsPage workflow={workflow} />
      <ReviewPage workflow={workflow} />
    </div>
  );
}

function renderBusinessModule(activeModule: BusinessModuleKey, workflow: ReturnType<typeof useRecognitionWorkflow>) {
  switch (activeModule) {
    case "upload":
      return <UploadRecognitionPage workflow={workflow} />;
    case "batch-results":
      return <BatchResultsPage workflow={workflow} />;
    case "review":
      return <ReviewPage workflow={workflow} />;
    default:
      return null;
  }
}

async function refreshAll(...loaders: Array<() => Promise<void>>) {
  await Promise.all(loaders.map((loader) => loader()));
}

function getSavedModule(storageKey: string, fallback: string, modules: WorkspaceModule[]) {
  const saved = sessionStorage.getItem(storageKey);
  return saved && modules.some((module) => module.key === saved) ? saved : fallback;
}

function isModuleKey(key: string, modules: WorkspaceModule[]) {
  return modules.some((module) => module.key === key);
}
