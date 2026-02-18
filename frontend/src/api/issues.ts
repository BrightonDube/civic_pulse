import { http } from "./http";
import type { Issue, IssueCreate } from "../types/issue";

export async function fetchIssues() {
  const response = await http.get<Issue[]>("/issues");
  return response.data;
}

export async function createIssue(payload: IssueCreate) {
  const response = await http.post<Issue>("/issues", payload);
  return response.data;
}
