import { openDB } from "idb";

export interface DraftReport {
  id?: number;
  title: string;
  description: string;
  category: string;
  location: [number, number];
  photo?: File | null;
  timestamp: number;
}

// Initialize IndexedDB
export const getDB = async () => {
  return openDB("CivicPulse", 1, {
    upgrade(db) {
      if (!db.objectStoreNames.contains("drafts")) {
        db.createObjectStore("drafts", { keyPath: "id", autoIncrement: true });
      }
    },
  });
};

// Save a draft
export const saveDraft = async (draft: DraftReport) => {
  const db = await getDB();
  await db.put("drafts", draft);
};

// Get all drafts
export const getDrafts = async (): Promise<DraftReport[]> => {
  const db = await getDB();
  return db.getAll("drafts");
};

// Delete a draft after upload
export const deleteDraft = async (id: number) => {
  const db = await getDB();
  await db.delete("drafts", id);
};
