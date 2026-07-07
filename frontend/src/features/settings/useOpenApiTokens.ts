import { useState } from "react";
import {
  fetchOpenApiStatus,
  generateOpenApiToken,
  type OpenApiStatus
} from "../../shared/api/client";

export function useOpenApiTokens() {
  const [openApiStatus, setOpenApiStatus] = useState<OpenApiStatus | null>(null);
  const [openApiMessage, setOpenApiMessage] = useState("");
  const [generatedOpenApiToken, setGeneratedOpenApiToken] = useState("");

  async function loadOpenApiStatus() {
    try {
      setOpenApiStatus(await fetchOpenApiStatus());
    } catch (error) {
      setOpenApiMessage(error instanceof Error ? error.message : "开放接口状态请求失败");
    }
  }

  async function handleGenerateOpenApiToken() {
    setOpenApiMessage("正在生成开放接口 Token...");
    setGeneratedOpenApiToken("");
    try {
      const result = await generateOpenApiToken("default");
      setGeneratedOpenApiToken(result.key);
      setOpenApiMessage("新 Token 已生成，请提供给业务系统保存；离开页面后只显示脱敏值。");
      await loadOpenApiStatus();
    } catch (error) {
      setOpenApiMessage(error instanceof Error ? error.message : "开放接口 Token 生成失败");
    }
  }

  return {
    openApiStatus,
    openApiMessage,
    generatedOpenApiToken,
    loadOpenApiStatus,
    handleGenerateOpenApiToken
  };
}
