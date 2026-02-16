import { useEffect } from "react";
import { useOffline } from "./useOffline";
import { getDrafts, deleteDraft, DraftReport } from "../utils/offline";
import { createReport } from "../services/api";

export const useAutoUpload = () => {
  const isOffline = useOffline();

  useEffect(() => {
    if (!isOffline) {
      const uploadDrafts = async () => {
        const drafts: DraftReport[] = await getDrafts();
        for (const draft of drafts) {
          try {
            const formData = new FormData();
            formData.append("latitude", draft.location[0].toString());
            formData.append("longitude", draft.location[1].toString());
            formData.append("user_override_category", draft.category);
            if (draft.photo) formData.append("photo", draft.photo);

            await createReport(formData);
            if (draft.id) await deleteDraft(draft.id);
          } catch (err) {
            console.error("Failed to upload draft", err);
          }
        }
      };
      uploadDrafts();
    }
  }, [isOffline]);
};
