export type Issue = {
  id: number;
  title: string;
  description: string;
  category?: string | null;
  location?: string | null;
  status: string;
  is_resolved: boolean;
  created_at: string;
};

export type IssueCreate = {
  title: string;
  description: string;
  category?: string | null;
  location?: string | null;
};
