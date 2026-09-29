const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export async function fetchVideoInfo(url: string) {
  const res = await fetch(`${API_BASE}/video/info`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to fetch metadata" }));
    throw new Error(err.detail || "Failed to fetch video metadata");
  }
  return res.json();
}

export async function startProcessingPipeline(url: string, target_languages: string[], generate_video_file: boolean = false) {
  const res = await fetch(`${API_BASE}/video/process`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, target_languages, generate_video_file }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to start pipeline" }));
    throw new Error(err.detail || "Failed to start pipeline");
  }
  return res.json();
}

export async function checkJobStatus(job_id: string) {
  const res = await fetch(`${API_BASE}/jobs/${job_id}`);
  if (!res.ok) return null;
  return res.json();
}

export async function fetchTranscript(video_id: string, lang: string = "en") {
  const res = await fetch(`${API_BASE}/transcript/${video_id}?lang=${lang}`);
  if (!res.ok) {
    return null;
  }
  return res.json();
}

export async function translateTranscript(video_id: string, target_language: string, source_language: string = "en") {
  const res = await fetch(`${API_BASE}/translation`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ video_id, target_language, source_language }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Translation failed" }));
    throw new Error(err.detail || "Translation failed");
  }
  return res.json();
}

export async function fetchDatabaseStatus() {
  try {
    const res = await fetch(`${API_BASE}/db/status`);
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function fetchRecentVideos() {
  try {
    const res = await fetch(`${API_BASE}/videos?limit=10`);
    if (!res.ok) return [];
    const data = await res.json();
    return data.videos || [];
  } catch {
    return [];
  }
}

export function getDownloadUrl(video_id: string, file_type: string, lang: string = "en") {
  return `${API_BASE}/download/${video_id}/${file_type}?lang=${lang}`;
}
