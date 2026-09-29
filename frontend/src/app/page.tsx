"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Play,
  Sparkles,
  ArrowRight,
  Clock,
  User,
  Eye,
  Layers,
  Settings,
  AlertCircle,
  CheckCircle,
  RefreshCw,
  Search,
  Subtitles,
  Flame,
  Check
} from "lucide-react";
import { YoutubeIcon } from "@/components/Icons";
import Header from "@/components/Header";
import VideoPlayer, { VideoPlayerRef } from "@/components/VideoPlayer";
import TranscriptViewer from "@/components/TranscriptViewer";
import DownloadSection from "@/components/DownloadSection";
import PipelineMonitor from "@/components/PipelineMonitor";
import {
  fetchVideoInfo,
  startProcessingPipeline,
  checkJobStatus,
  fetchTranscript,
  translateTranscript,
  fetchDatabaseStatus,
  fetchRecentVideos
} from "@/lib/api";
import { VideoMetadata, TranscriptSegment, JobStatusData, DatabaseStatus } from "@/types";

const INITIAL_VIDEO_ID = "x7X9w_GIm1s"; // Python in 100 Seconds

const DEFAULT_LANGUAGES: Record<string, string> = {
  en: "English (Original)",
  hi: "Hindi (हिन्दी)",
  es: "Spanish (Español)",
  fr: "French (Français)",
  de: "German (Deutsch)"
};

export default function HomePage() {
  const [urlInput, setUrlInput] = useState<string>(`https://www.youtube.com/watch?v=${INITIAL_VIDEO_ID}`);
  const [activeVideoId, setActiveVideoId] = useState<string>(INITIAL_VIDEO_ID);
  const [videoMeta, setVideoMeta] = useState<VideoMetadata | null>(null);

  const [segments, setSegments] = useState<TranscriptSegment[]>([]);
  const [currentLanguage, setCurrentLanguage] = useState<string>("en");
  const [currentTime, setCurrentTime] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isTranslating, setIsTranslating] = useState<boolean>(false);
  const [job, setJob] = useState<JobStatusData | null>(null);
  const [showPipelineModal, setShowPipelineModal] = useState<boolean>(false);
  const [dbStatus, setDbStatus] = useState<DatabaseStatus | null>(null);
  const [recentVideos, setRecentVideos] = useState<any[]>([]);
  const [pipelineOptions, setPipelineOptions] = useState({
    downloadVideo: false,
    autoTranslate: true
  });

  const playerRef = useRef<VideoPlayerRef | null>(null);

  // Load database status & recent history
  useEffect(() => {
    fetchDatabaseStatus().then((status) => setDbStatus(status));
    fetchRecentVideos().then((vids) => setRecentVideos(vids));
    // Load real metadata and transcript for the initial video.
    const loadInitialVideo = async () => {
      try {
        const infoRes = await fetchVideoInfo(`https://www.youtube.com/watch?v=${INITIAL_VIDEO_ID}`);
        setVideoMeta(infoRes.metadata);
        await loadVideoTranscript(INITIAL_VIDEO_ID, "en");
      } catch (err) {
        console.error("Initial video load failed:", err);
        setSegments([]);
      }
    };

    loadInitialVideo();
  }, []);

  // Poll for background job progress
  useEffect(() => {
    if (!job || job.status === "completed" || job.status === "failed") return;

    const interval = setInterval(async () => {
      try {
        const updated = await checkJobStatus(job.job_id);
        if (updated) {
          setJob(updated);
          if (updated.status === "completed") {
            clearInterval(interval);
            setIsLoading(false);
            setActiveVideoId(updated.video_id);
            setCurrentLanguage("en");
            await loadVideoTranscript(updated.video_id, "en");
            fetchDatabaseStatus().then((status) => setDbStatus(status));
            fetchRecentVideos().then((vids) => setRecentVideos(vids));
          } else if (updated.status === "failed") {
            clearInterval(interval);
            setIsLoading(false);
          }
        }
      } catch (err) {
        console.error("Job poll error:", err);
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [job, currentLanguage]);

  // Load only real transcript data from the backend.
  // No demo/sample transcript is inserted when the server has no data.
  const loadVideoTranscript = async (videoId: string, lang: string) => {
    try {
      const data = await fetchTranscript(videoId, lang);

      if (data?.segments?.length) {
        setSegments(data.segments);
        return data;
      }

      setSegments([]);
      return null;
    } catch (e) {
      console.error(`Error fetching ${lang} transcript for ${videoId}:`, e);
      setSegments([]);
      return null;
    }
  };

  // Handle URL Submission & Pipeline Launch
  const handleProcessVideo = async (targetUrl?: string) => {
    const url = targetUrl || urlInput;
    if (!url.trim()) return;

    setIsLoading(true);
    try {
      // 1. Fetch metadata
      const infoRes = await fetchVideoInfo(url);
      const meta = infoRes.metadata;
      setVideoMeta(meta);
      setActiveVideoId(meta.video_id);
      setCurrentLanguage("en");
      setSegments([]);

      // 2. Start asynchronous pipeline.
      // Argos Translate is currently installed with these real language models.
      const targetLangs = pipelineOptions.autoTranslate
        ? ["hi", "es", "fr", "de"]
        : [];
      const pipelineRes = await startProcessingPipeline(
        url,
        targetLangs,
        pipelineOptions.downloadVideo
      );
      
      setJob({
        job_id: pipelineRes.job_id,
        video_id: pipelineRes.video_id,
        status: "processing",
        stage: "downloading",
        progress: 15,
        message: "Asynchronous processing pipeline started..."
      });
      setShowPipelineModal(true);
    } catch (err: any) {
      console.error("Processing failed:", err);
      setIsLoading(false);
      alert(err.message || "Failed to process video");
    }
  };

  // Handle multi-language switch only after confirming the real source transcript exists.
  const handleLanguageChange = async (targetLang: string) => {
    if (isTranslating || !activeVideoId) return;

    setIsTranslating(true);
    try {
      const sourceTranscript = await fetchTranscript(activeVideoId, "en");

      if (!sourceTranscript?.segments?.length) {
        throw new Error("Transcript is not ready. Please wait for transcription to complete.");
      }

      if (targetLang === "en") {
        setCurrentLanguage("en");
        setSegments(sourceTranscript.segments);
        return;
      }

      const res = await translateTranscript(activeVideoId, targetLang, "en");

      if (!res?.translation?.segments?.length) {
        throw new Error(`No ${targetLang} translation was returned.`);
      }

      setCurrentLanguage(targetLang);
      setSegments(res.translation.segments);
    } catch (err: any) {
      console.error("Translation error:", err);
      setCurrentLanguage("en");
      await loadVideoTranscript(activeVideoId, "en");
      alert(err?.message || "Translation failed. Please try again after transcription completes.");
    } finally {
      setIsTranslating(false);
    }
  };

  // Jump to timestamp handler
  const handleJumpTo = (seconds: number) => {
    if (playerRef.current) {
      playerRef.current.seekTo(seconds);
    }
  };

  // Select the real transcript segment that matches the YouTube playback time.
  const activeCaption = segments.find(
    (segment) => currentTime >= segment.start && currentTime <= segment.end
  )?.text || "";

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col font-sans">
      {/* Header */}
      <Header
        dbStatus={dbStatus}
        onSelectSample={(sampleUrl) => {
          setUrlInput(sampleUrl);
          handleProcessVideo(sampleUrl);
        }}
        onOpenDashboard={() => setShowPipelineModal(true)}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Input Bar & Config Controls */}
        <section className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 sm:p-5 shadow-xl">
          <div className="flex flex-col sm:flex-row items-center gap-3">
            <div className="relative flex-1 w-full">
              <YoutubeIcon className="w-5 h-5 absolute left-3.5 top-3 text-rose-500" />
              <input
                type="text"
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
                placeholder="Paste YouTube Video URL (e.g., https://www.youtube.com/watch?v=...)"
                className="w-full bg-slate-950 border border-slate-700/80 rounded-xl pl-11 pr-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all font-mono"
              />
            </div>

            <button
              onClick={() => handleProcessVideo()}
              disabled={isLoading}
              className="w-full sm:w-auto px-6 py-2.5 rounded-xl bg-gradient-to-r from-rose-600 via-indigo-600 to-indigo-700 hover:from-rose-500 hover:to-indigo-600 text-white text-sm font-semibold shadow-lg shadow-indigo-600/30 flex items-center justify-center space-x-2 transition-all disabled:opacity-50 shrink-0"
            >
              {isLoading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Processing...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Transcribe & Highlight</span>
                </>
              )}
            </button>
          </div>

          {/* Quick Options Bar */}
          <div className="mt-3 pt-3 border-t border-slate-800/80 flex flex-wrap items-center justify-between text-xs text-slate-400 gap-2">
            <div className="flex items-center space-x-4">
              <label className="flex items-center space-x-1.5 cursor-pointer hover:text-slate-300">
                <input
                  type="checkbox"
                  checked={pipelineOptions.autoTranslate}
                  onChange={(e) =>
                    setPipelineOptions({ ...pipelineOptions, autoTranslate: e.target.checked })
                  }
                  className="rounded bg-slate-800 border-slate-700 text-indigo-600 focus:ring-indigo-500"
                />
                <span>Auto-generate Multilingual Translations (Hindi, Spanish, French, German)</span>
              </label>

              <label className="flex items-center space-x-1.5 cursor-pointer hover:text-slate-300">
                <input
                  type="checkbox"
                  checked={pipelineOptions.downloadVideo}
                  onChange={(e) =>
                    setPipelineOptions({ ...pipelineOptions, downloadVideo: e.target.checked })
                  }
                  className="rounded bg-slate-800 border-slate-700 text-indigo-600 focus:ring-indigo-500"
                />
                <span>Store Local MP4 Copy</span>
              </label>
            </div>

            {videoMeta?.title && (
              <span className="text-slate-500 truncate max-w-xs hidden md:inline">
                Active: <strong className="text-slate-300">{videoMeta.title}</strong>
              </span>
            )}
          </div>
        </section>

        {/* Core Dual-Column Workspace */}
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column (Video Player + Metadata + Downloads) - 5 Columns */}
          <div className="lg:col-span-5 space-y-4">
            {/* Video Player */}
            <VideoPlayer
              ref={playerRef}
              videoId={activeVideoId}
              captionText={activeCaption}
              onTimeUpdate={(time) => setCurrentTime(time)}
            />

            {/* Video Info Card */}
            {videoMeta && (
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 space-y-3">
                <h2 className="text-sm font-bold text-white line-clamp-2">
                  {videoMeta.title}
                </h2>
                <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400">
                  <span className="flex items-center gap-1">
                    <User className="w-3.5 h-3.5 text-indigo-400" />
                    {videoMeta.channel || "YouTube Channel"}
                  </span>
                  {videoMeta.duration ? (
                    <span className="flex items-center gap-1 font-mono">
                      <Clock className="w-3.5 h-3.5 text-amber-400" />
                      {Math.floor(videoMeta.duration / 60)}m {Math.floor(videoMeta.duration % 60)}s
                    </span>
                  ) : null}
                  {videoMeta.view_count ? (
                    <span className="flex items-center gap-1">
                      <Eye className="w-3.5 h-3.5 text-emerald-400" />
                      {videoMeta.view_count.toLocaleString()} views
                    </span>
                  ) : null}
                </div>
              </div>
            )}

            {/* Downloads Bar */}
            <DownloadSection
              videoId={activeVideoId}
              currentLanguage={currentLanguage}
            />
          </div>

          {/* Right Column (Synchronized Transcript Viewer) - 7 Columns */}
          <div className="lg:col-span-7 h-[680px]">
            <TranscriptViewer
              segments={segments}
              currentTime={currentTime}
              currentLanguage={currentLanguage}
              availableLanguages={DEFAULT_LANGUAGES}
              isTranslating={isTranslating}
              onLanguageChange={handleLanguageChange}
              onJumpTo={handleJumpTo}
            />
          </div>
        </section>

        {/* Recent Videos & MongoDB Atlas Indexed Library */}
        {recentVideos.length > 0 && (
          <section className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 space-y-3">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
              <Flame className="w-4 h-4 text-rose-500" />
              Indexed in MongoDB Database
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {recentVideos.slice(0, 4).map((vid, idx) => (
                <div
                  key={idx}
                  onClick={() => {
                    setActiveVideoId(vid.video_id);
                    setVideoMeta(vid);
                    setCurrentLanguage("en");
                    setSegments([]);
                    loadVideoTranscript(vid.video_id, "en");
                  }}
                  className="p-2.5 rounded-xl border border-slate-800 bg-slate-950/60 hover:bg-slate-800/80 cursor-pointer transition-all flex items-center space-x-3 group"
                >
                  <img
                    src={vid.thumbnail || `https://img.youtube.com/vi/${vid.video_id}/hqdefault.jpg`}
                    alt={vid.title}
                    className="w-14 h-10 object-cover rounded-lg shrink-0 border border-slate-700"
                  />
                  <div className="overflow-hidden">
                    <p className="text-xs font-medium text-slate-200 line-clamp-1 group-hover:text-indigo-400 transition-colors">
                      {vid.title}
                    </p>
                    <p className="text-[10px] text-slate-500 line-clamp-1">{vid.channel}</p>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}
      </main>

      {/* Asynchronous Pipeline Worker Monitor Modal */}
      <PipelineMonitor
        job={job}
        isOpen={showPipelineModal}
        onClose={() => setShowPipelineModal(false)}
      />
    </div>
  );
}
