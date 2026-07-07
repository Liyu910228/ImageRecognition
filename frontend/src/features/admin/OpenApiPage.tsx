import { OpenApiPanel } from "../settings/OpenApiPanel";
import type { useOpenApiTokens } from "../settings/useOpenApiTokens";

type OpenApiState = ReturnType<typeof useOpenApiTokens>;

export function OpenApiPage({ openApi }: { openApi: OpenApiState }) {
  return (
    <div className="module-page">
      <div className="module-header">
        <div>
          <h2>开放接口</h2>
          <p>生成业务系统调用识别接口所需的 Bearer Token。</p>
        </div>
      </div>
      <OpenApiPanel
        status={openApi.openApiStatus}
        generatedToken={openApi.generatedOpenApiToken}
        message={openApi.openApiMessage}
        onGenerate={() => void openApi.handleGenerateOpenApiToken()}
      />
    </div>
  );
}
