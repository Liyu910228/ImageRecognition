import { KeyRound, RefreshCw } from "lucide-react";
import type { OpenApiStatus } from "../../shared/api/client";

export function OpenApiPanel({
  status,
  generatedToken,
  message,
  onGenerate
}: {
  status: OpenApiStatus | null;
  generatedToken: string;
  message: string;
  onGenerate: () => void;
}) {
  const firstKey = status?.keys[0];

  return (
    <div className="panel">
      <div className="panel-heading inline-heading">
        <div>
          <h2>开放接口</h2>
          <p>给业务系统调用识别接口使用</p>
        </div>
        <KeyRound size={18} />
      </div>
      <div className="open-api-box">
        <div className="open-api-status">
          <span>Token 状态</span>
          <strong>{status?.configured ? "已配置" : "未配置"}</strong>
        </div>
        <div className="open-api-status">
          <span>当前 Token</span>
          <strong>{firstKey?.maskedKey ?? "--"}</strong>
        </div>
        <button className="secondary-action" type="button" onClick={onGenerate}>
          <RefreshCw size={16} />
          生成/轮换 Token
        </button>
        {generatedToken && (
          <label className="open-api-token">
            <span>新 Token 仅本次显示</span>
            <input readOnly value={generatedToken} onFocus={(event) => event.currentTarget.select()} />
          </label>
        )}
        <div className="model-note">
          调用方式：请求头添加 <code>Authorization: Bearer &lt;OPEN_API_TOKEN&gt;</code>
        </div>
        {message && <p className="model-note">{message}</p>}
      </div>
    </div>
  );
}
