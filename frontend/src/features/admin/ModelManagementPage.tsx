import { ModelSettingsPanel } from "../settings/ModelSettingsPanel";
import type { useModelSettings } from "../settings/useModelSettings";

type ModelSettingsState = ReturnType<typeof useModelSettings>;

export function ModelManagementPage({ settings }: { settings: ModelSettingsState }) {
  return (
    <div className="module-page">
      <div className="module-header">
        <div>
          <h2>模型管理</h2>
          <p>每个平台模型独立配置、启用、测试和删除。</p>
        </div>
      </div>
      <ModelSettingsPanel
        modelSettings={settings.modelSettings}
        modelMessage={settings.modelMessage}
        frontendApiKey={settings.frontendApiKey}
        backendApiKeyInput={settings.backendApiKeyInput}
        backendVolcApiKeyInput={settings.backendVolcApiKeyInput}
        setFrontendApiKey={settings.setFrontendApiKey}
        setBackendApiKeyInput={settings.setBackendApiKeyInput}
        setBackendVolcApiKeyInput={settings.setBackendVolcApiKeyInput}
        setModelMessage={settings.setModelMessage}
        handleModelChange={settings.handleModelChange}
        handleSaveModels={settings.handleSaveModels}
        handleResetModels={settings.handleResetModels}
      />
    </div>
  );
}
