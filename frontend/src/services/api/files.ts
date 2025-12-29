import { requestJson } from "@/lib/http/client";

export type FileUploadResponse = {
  fileId?: string;
  contentType?: string;
  size?: number;
};

export async function uploadFile(
  blob: Blob,
  filename?: string,
): Promise<FileUploadResponse | null> {
  const formData = new FormData();
  formData.append("file", blob, filename || "upload.bin");

  const result = await requestJson<FileUploadResponse>("/api/file", {
    method: "POST",
    body: formData,
  });
  if (!result.ok) {
    return null;
  }
  return result.data;
}
