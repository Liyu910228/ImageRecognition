import { FileImage, FileSpreadsheet, FolderUp, ImageUp, RefreshCw } from "lucide-react";
import { RecognitionResultPanel } from "../recognition/components/RecognitionResultPanel";
import type { useRecognitionWorkflow } from "../recognition/hooks/useRecognitionWorkflow";
import { folderPickerProps } from "../recognition/workflowHelpers";

type Workflow = ReturnType<typeof useRecognitionWorkflow>;

export function UploadRecognitionPage({ workflow }: { workflow: Workflow }) {
  return (
    <div className="module-page">
      <div className="module-header">
        <div>
          <h2>上传识别</h2>
          <p>支持单张图片、文件夹批量、表格批量链接和图片链接识别。</p>
        </div>
      </div>
      <section className="workspace-grid">
        <div className="panel upload-panel">
          <div className="panel-heading">
            <div>
              <h2>图片来源</h2>
              <p>业务员只需要上传图片，模型策略由管理员统一配置。</p>
            </div>
          </div>
          <div className="upload-actions">
            <label className="primary-action">
              <ImageUp size={18} />
              选择图片
              <input
                type="file"
                accept="image/jpeg,image/png,image/webp"
                onChange={(event) => void workflow.handleFileChange(event.target.files?.[0])}
              />
            </label>
            <label className={`secondary-action ${workflow.recognitionState === "recognizing" ? "is-disabled" : ""}`}>
              <FolderUp size={18} />
              选择文件夹
              <input
                type="file"
                accept="image/jpeg,image/png,image/webp"
                multiple
                disabled={workflow.recognitionState === "recognizing"}
                onChange={(event) => {
                  void workflow.handleFolderChange(event.target.files);
                  event.currentTarget.value = "";
                }}
                {...folderPickerProps}
              />
            </label>
            <button
              className="secondary-action"
              type="button"
              onClick={() => void workflow.handleRecognize()}
              disabled={workflow.recognitionState === "recognizing"}
            >
              <RefreshCw size={18} />
              {recognizeButtonText(workflow)}
            </button>
          </div>
          <div className="workbook-link-upload">
            <label className={`secondary-action ${workflow.recognitionState === "recognizing" ? "is-disabled" : ""}`}>
              <FileSpreadsheet size={18} />
              表格批量上传链接
              <input
                type="file"
                accept=".xlsx"
                disabled={workflow.recognitionState === "recognizing"}
                onChange={(event) => {
                  void workflow.handleWorkbookLinkUpload(event.target.files?.[0]);
                  event.currentTarget.value = "";
                }}
              />
            </label>
            <span>
              {workflow.workbookLinks.length
                ? `${workflow.workbookName} · 已读取 ${workflow.workbookLinks.length} 条照片链接`
                : "读取表格中的“照片链接”字段"}
            </span>
          </div>
          <div className="url-recognition">
            <input
              value={workflow.imageUrl}
              onChange={(event) => workflow.setImageUrl(event.target.value)}
              placeholder="粘贴图片链接：https://..."
            />
            <button
              className="secondary-action"
              type="button"
              onClick={() => void workflow.handleRecognizeUrl()}
              disabled={workflow.recognitionState === "recognizing"}
            >
              链接识别
            </button>
          </div>
          <div className="hint-recognition">
            <input
              value={workflow.manualHints}
              onChange={(event) => workflow.setManualHints(event.target.value)}
              placeholder="辅助关键词，可选：雪花 纯生 箱 500ml"
            />
          </div>
          <div className={`drop-zone ${workflow.previewUrl ? "has-preview" : ""}`}>
            {workflow.previewUrl ? (
              <img src={workflow.previewUrl} alt="上传图片预览" />
            ) : (
              <>
                <FileImage size={34} />
                <span>选择 JPG、PNG 或 WebP 图片</span>
              </>
            )}
          </div>
          {workflow.selectedFile && (
            <p className="file-note">
              {workflow.folderFiles.length
                ? `文件夹已选择 ${workflow.folderFiles.length} 张图片，当前：${workflow.selectedFile.webkitRelativePath || workflow.selectedFile.name}`
                : workflow.selectedFile.name}
            </p>
          )}
          {workflow.workbookLinks.length > 0 && (
            <p className="file-note">表格链接队列：{workflow.workbookName}，共 {workflow.workbookLinks.length} 条</p>
          )}
          {workflow.batchProgress.total > 0 && (
            <div className="batch-progress">
              <span>批量进度</span>
              <strong>{workflow.batchProgress.current}/{workflow.batchProgress.total}</strong>
            </div>
          )}
          {workflow.recognitionState === "error" && <div className="inline-error">{workflow.recognitionError}</div>}
        </div>
        <RecognitionResultPanel recognition={workflow.recognition} />
      </section>
    </div>
  );
}

function recognizeButtonText(workflow: Workflow) {
  if (workflow.recognitionState === "recognizing") {
    return "识别中";
  }
  if (workflow.workbookLinks.length) {
    return `开始识别 ${workflow.workbookLinks.length} 条链接`;
  }
  if (workflow.folderFiles.length) {
    return `开始识别 ${workflow.folderFiles.length} 张`;
  }
  return "开始识别";
}
