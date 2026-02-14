import { useEffect } from "react";
import { useOffline } from "./useOffline";
import { getDrafts, deleteDraft, DraftReport } from "../utils/offline";
import axios from "axios";

export const useAutoUpload = () => {
  const isOffline = useOffline();

  useEffect(() => {
    if (!isOffline) {
      const uploadDrafts = async () => {
        const drafts: DraftReport[] = await getDrafts();
        for (const draft of drafts) {
          try {
            const formData = new FormData();
            formData.append("title", draft.title);
            formData.append("description", draft.description);
            formData.append("category", draft.category);
            formData.append("lat", draft.location[0].toString());
            formData.append("lng", draft.location[1].toString());
            if (draft.photo) formData.append("photo", draft.photo);

            await axios.post("/api/reports", formData, {
              headers: { "Content-Type": "multipart/form-data" },
            });

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
