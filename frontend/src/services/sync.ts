import { getDrafts, deleteDraft } from "./db";
import { createReport } from "./api";

export async function syncDrafts() {
  const drafts = await getDrafts();

  for (const draft of drafts) {
    try {
      const formData = new FormData();
      if (draft.photo_url) formData.append("photo_url", draft.photo_url);
      formData.append("latitude", String(draft.latitude));
      formData.append("longitude", String(draft.longitude));
      if (draft.category) formData.append("user_override_category", draft.category);

      await createReport(formData);
      await deleteDraft(draft.id);
    } catch {
      // Will retry on next sync
    }
  }
}
