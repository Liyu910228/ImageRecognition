import { Database, Download } from "lucide-react";
import type { useTemplateLibrary } from "../templates/useTemplateLibrary";

type TemplateLibraryState = ReturnType<typeof useTemplateLibrary>;

export function TemplateLibraryPage({ templates }: { templates: TemplateLibraryState }) {
  return (
    <div className="module-page">
      <div className="module-header">
        <div>
          <h2>模板库</h2>
          <p>上传多个 Excel 模板文件，构建完成后可按单个文件下载或删除。</p>
        </div>
        <label className="secondary-action">
          <Database size={18} />
          {templates.templateUploadState === "uploading" ? "处理中" : "上传模板库"}
          <input
            type="file"
            accept=".xlsx"
            multiple
            disabled={templates.templateUploadState === "uploading"}
            onChange={(event) => void templates.handleTemplateUpload(event.target.files)}
          />
        </label>
      </div>
      <div className="panel template-admin">
        {templates.templateUploadMessage && (
          <div className={templates.templateUploadState === "error" ? "inline-error template-message" : "model-note template-message"}>
            {templates.templateUploadMessage}
          </div>
        )}
        <div className="template-source-list">
          {templates.templateSources.length ? (
            templates.templateSources.map((source) => (
              <div className="template-source-row" key={source.filename}>
                <div>
                  <strong>{source.filename}</strong>
                  <span>{formatBytes(source.size)} · 已构建完成</span>
                </div>
                <div className="template-source-actions">
                  <button
                    className="secondary-action compact-action"
                    type="button"
                    disabled={templates.templateUploadState === "uploading"}
                    onClick={() => templates.handleDownloadTemplateSource(source.filename)}
                  >
                    <Download size={16} />
                    下载源文件
                  </button>
                  <button
                    className="danger-action"
                    type="button"
                    disabled={templates.templateUploadState === "uploading"}
                    onClick={() => void templates.handleDeleteTemplateSource(source.filename)}
                  >
                    删除
                  </button>
                </div>
              </div>
            ))
          ) : (
            <div className="empty-source">暂无已构建模板文件</div>
          )}
        </div>
      </div>
    </div>
  );
}

function formatBytes(bytes: number) {
  if (bytes < 1024 * 1024) {
    return `${Math.round(bytes / 1024)} KB`;
  }
  return `${Math.round((bytes / 1024 / 1024) * 10) / 10} MB`;
}
