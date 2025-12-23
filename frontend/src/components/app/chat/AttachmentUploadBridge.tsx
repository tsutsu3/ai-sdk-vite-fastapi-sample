import { useEffect, useRef } from "react";
import { usePromptInputAttachments } from "@/components/ai-elements/prompt-input";

export type AttachmentUploadBridgeProps = {
  onUploaded: (attachmentId: string, fileId: string) => void;
  onRemoved: (attachmentIds: string[]) => void;
  onUploadCountChange: (count: number) => void;
};

export const AttachmentUploadBridge = ({
  onUploaded,
  onRemoved,
  onUploadCountChange,
}: AttachmentUploadBridgeProps) => {
  const attachments = usePromptInputAttachments();
  const uploadingIds = useRef<Set<string>>(new Set());
  const uploadedIds = useRef<Set<string>>(new Set());
  const knownIds = useRef<Set<string>>(new Set());

  useEffect(() => {
    const currentIds = new Set(attachments.files.map((file) => file.id));
    const removed: string[] = [];
    for (const id of knownIds.current) {
      if (!currentIds.has(id)) {
        removed.push(id);
        uploadedIds.current.delete(id);
        uploadingIds.current.delete(id);
      }
    }
    if (removed.length) {
      onRemoved(removed);
    }
    knownIds.current = currentIds;
  }, [attachments.files, onRemoved]);

  useEffect(() => {
    let cancelled = false;
    const uploadNew = async () => {
      const pending = attachments.files.filter(
        (file) =>
          !uploadingIds.current.has(file.id) &&
          !uploadedIds.current.has(file.id)
      );
      if (!pending.length) {
        onUploadCountChange(0);
        return;
      }
      onUploadCountChange(pending.length);
      for (const file of pending) {
        uploadingIds.current.add(file.id);
        onUploadCountChange(uploadingIds.current.size);
        try {
          const response = await fetch(file.url);
          const blob = await response.blob();
          const formData = new FormData();
          formData.append("file", blob, file.filename || "upload.bin");
          const uploadResponse = await fetch("/api/file", {
            method: "POST",
            body: formData,
          });
          if (!uploadResponse.ok) {
            throw new Error("File upload failed");
          }
          const payload = await uploadResponse.json();
          if (!cancelled && payload?.fileId) {
            onUploaded(file.id, payload.fileId as string);
            uploadedIds.current.add(file.id);
          }
        } catch {
          if (!cancelled) {
            onRemoved([file.id]);
          }
        } finally {
          uploadingIds.current.delete(file.id);
          onUploadCountChange(uploadingIds.current.size);
        }
      }
    };
    uploadNew();
    return () => {
      cancelled = true;
    };
  }, [attachments.files, onRemoved, onUploadCountChange, onUploaded]);

  return null;
};
