import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { Report } from "../types";
import { set, get, del, keys } from "idb-keyval"; // npm install idb-keyval

interface ReportContextType {
  reports: Report[];
  addReport: (report: Report) => void;
  updateReport: (updated: Report) => void;
  offlineDrafts: Report[];
  syncOfflineDrafts: () => void;
}

const ReportContext = createContext<ReportContextType | undefined>(undefined);

export const ReportProvider = ({ children }: { children: ReactNode }) => {
  const [reports, setReports] = useState<Report[]>([]);
  const [offlineDrafts, setOfflineDrafts] = useState<Report[]>([]);

  // Load offline drafts from IndexedDB on mount
  useEffect(() => {
    const loadDrafts = async () => {
      const draftKeys = await keys();
      const drafts: Report[] = [];
      for (const k of draftKeys) {
        const draft = await get<Report>(k);
        if (draft) drafts.push(draft);
      }
      setOfflineDrafts(drafts);
    };
    loadDrafts();
  }, []);

  // Add a report
  const addReport = async (report: Report) => {
    if (navigator.onLine) {
      // If online, add directly
      setReports(prev => [...prev, report]);
    } else {
      // Offline: save to IndexedDB
      await set(`draft-${report.id}`, report);
      setOfflineDrafts(prev => [...prev, report]);
    }
  };

  // Update report
  const updateReport = async (updated: Report) => {
    setReports(prev => prev.map(r => (r.id === updated.id ? updated : r)));
    // If draft exists offline, remove it from IndexedDB
    await del(`draft-${updated.id}`);
    setOfflineDrafts(prev => prev.filter(d => d.id !== updated.id));
  };

  // Sync offline drafts when back online
  const syncOfflineDrafts = async () => {
    if (!navigator.onLine) return;
    for (const draft of offlineDrafts) {
      setReports(prev => [...prev, draft]);
      await del(`draft-${draft.id}`);
    }
    setOfflineDrafts([]);
  };

  // Listen for online event to auto-sync
  useEffect(() => {
    const handleOnline = () => syncOfflineDrafts();
    window.addEventListener("online", handleOnline);
    return () => window.removeEventListener("online", handleOnline);
  }, [offlineDrafts]);

  return (
    <ReportContext.Provider
      value={{ reports, addReport, updateReport, offlineDrafts, syncOfflineDrafts }}
    >
      {children}
    </ReportContext.Provider>
  );
};

export const useReports = () => {
  const context = useContext(ReportContext);
  if (!context) throw new Error("useReports must be used inside ReportProvider");
  return context;
};
