import { useEffect, useState } from "react";
import { fetchIssues } from "../api/issues";
import type { Issue } from "../types/issue";
import Loading from "../components/Loading";

export default function Home() {
  const [issues, setIssues] = useState<Issue[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    fetchIssues()
      .then((data) => {
        if (active) {
          setIssues(data);
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <section>
      <h1>CivicPulse</h1>
      <p>Welcome to CivicPulse - Infrastructure Issue Reporting Platform</p>
      {loading ? (
        <Loading />
      ) : (
        <ul>
          {issues.map((issue) => (
            <li key={issue.id}>
              <strong>{issue.title}</strong>
              <div>{issue.description}</div>
              <small>Status: {issue.status}</small>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
