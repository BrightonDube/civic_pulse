import { getDrafts, deleteDraft } from "./db";
import { uploadReport } from "./api";

export async function syncDrafts() {
  const drafts = await getDrafts();

  for (const draft of drafts) {
    const success = await uploadReport(draft);

    if (success) {
      await deleteDraft(draft.id);
    }
  }
}
