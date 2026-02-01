export async function submitReport(data: FormData) {
  const res = await fetch('/api/reports', {
    method: 'POST',
    body: data,
  });
  return res.json();
}
