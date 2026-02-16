import { openDB } from "idb";
import { Report } from "../types";

const DB_NAME = "civic-pulse-db";
const STORE = "drafts";

export const dbPromise = openDB(DB_NAME, 1, {
  upgrade(db) {
    if (!db.objectStoreNames.contains(STORE)) {
      db.createObjectStore(STORE, { keyPath: "id" });
    }
  },
});

// Save draft
export async function saveDraft(report: Report) {
  const db = await dbPromise;
  await db.put(STORE, report);
}

// Get all drafts
export async function getDrafts(): Promise<Report[]> {
  const db = await dbPromise;
  return db.getAll(STORE);
}

// Delete draft
export async function deleteDraft(id: string) {
  const db = await dbPromise;
  await db.delete(STORE, id);
}
