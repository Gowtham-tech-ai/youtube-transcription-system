export interface WordTimestamp {
  word: string;
  start: number;
  end: number;
}

export interface TranscriptSegment {
  start: number;
  end: number;
  text: string;
  words?: WordTimestamp[];
}

export interface VideoMetadata {
  video_id: string;
  url: string;
  title: string;
  channel?: string;
  duration?: number;
  thumbnail?: string;
  view_count?: number;
  description?: string;
  audio_path?: string;
  video_path?: string;
  source_language?: string;
  created_at?: string;
}

export interface TranscriptData {
  video_id: string;
  language: string;
  is_source: boolean;
  full_text: string;
  segments: TranscriptSegment[];
}

export interface JobStatusData {
  job_id: string;
  video_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  stage: string;
  progress: number;
  message: string;
  error?: string;
}

export interface DatabaseStatus {
  is_atlas_connected: boolean;
  db_name: string;
  videos_count: number;
  mode: string;
}
