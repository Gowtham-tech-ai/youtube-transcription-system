"use client";

import React from "react";
import {
  CheckCircle2,
  Clock,
  Loader2,
  AlertCircle,
  Cpu,
  Layers,
  Sparkles,
  Database,
  ArrowRight
} from "lucide-react";
import { JobStatusData } from "@/types";

interface PipelineMonitorProps {
  job: JobStatusData | null;
  isOpen: boolean;
  onClose: () => void;
}

const PIPELINE_STAGES = [
  {
    id: "downloading",
    title: "1. YouTube Downloader",
    engine: "yt-dlp",
    desc: "Fetch video metadata & high quality audio stream",
  },
  {
    id: "extracting_audio",
    title: "2. Audio Extraction",
    engine: "FFmpeg",
    desc: "De-multiplex and convert audio to 16kHz WAV format",
  },
  {
    id: "preprocessing",
    title: "3. Audio Preprocessing",
    engine: "FFmpeg Filters",
    desc: "Loudness normalization & FFT noise suppression",
  },
  {
    id: "transcribing",
    title: "4. Speech to Text",
    engine: "OpenAI Whisper",
    desc: "Deep learning acoustic model & automatic transcription",
  },
  {
    id: "text_processing",
    title: "5. Text Processing",
    engine: "NLP Timestamping",
    desc: "Sentence chunking & word-level timestamp alignment",
  },
  {
    id: "translating",
    title: "6. Translation",
    engine: "Multilingual Engine",
    desc: "Multi-language target translation (Telugu, Hindi, Spanish)",
  },
];

export default function PipelineMonitor({ job, isOpen, onClose }: PipelineMonitorProps) {
  if (!isOpen) return null;

  // Determine stage status
  const getStageState = (stageIndex: number) => {
    if (!job) return "idle";
    if (job.status === "completed") return "completed";
    if (job.status === "failed") return "failed";

    const currentStageKey = job.stage;
    const currentStageIdx = PIPELINE_STAGES.findIndex((s) => s.id === currentStageKey);

    if (currentStageIdx === -1) {
      if (job.progress > (stageIndex + 1) * 16) return "completed";
      if (job.progress >= stageIndex * 16) return "active";
      return "idle";
    }

    if (stageIndex < currentStageIdx) return "completed";
    if (stageIndex === currentStageIdx) return "active";
    return "idle";
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-3xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-4 sm:p-5 border-b border-slate-800 bg-slate-950 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="h-9 w-9 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm sm:text-base font-bold text-white flex items-center gap-2">
                Processing Pipeline (Asynchronous Workers)
              </h3>
              <p className="text-xs text-slate-400">
                End-to-end task queue orchestration matching architecture diagram
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
          >
            ✕
          </button>
        </div>

        {/* Progress Overview Bar */}
        <div className="p-4 bg-slate-900/60 border-b border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-300 font-medium flex items-center gap-2">
              Status:{" "}
              <span
                className={`font-semibold capitalize px-2 py-0.5 rounded text-[11px] ${
                  job?.status === "completed"
                    ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                    : job?.status === "processing"
                    ? "bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 animate-pulse"
                    : "bg-slate-800 text-slate-400"
                }`}
              >
                {job?.status || "Idle"}
              </span>
            </span>
            <span className="font-mono text-indigo-400 font-bold">
              {job?.progress || 0}% Complete
            </span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
            <div
              className="bg-gradient-to-r from-indigo-500 via-purple-500 to-emerald-500 h-2 transition-all duration-300 rounded-full"
              style={{ width: `${job?.progress || 0}%` }}
            />
          </div>
          {job?.message && (
            <p className="text-xs text-slate-400 font-mono italic">
              &gt; {job.message}
            </p>
          )}
        </div>

        {/* 6 Pipeline Stages */}
        <div className="p-4 sm:p-5 overflow-y-auto space-y-3">
          {PIPELINE_STAGES.map((stage, idx) => {
            const state = getStageState(idx);

            return (
              <div
                key={stage.id}
                className={`p-3 rounded-xl border flex items-center justify-between gap-3 transition-all ${
                  state === "completed"
                    ? "bg-emerald-950/20 border-emerald-500/30 text-emerald-300"
                    : state === "active"
                    ? "bg-indigo-950/30 border-indigo-500/50 shadow-md shadow-indigo-500/10 text-white"
                    : "bg-slate-950/40 border-slate-800 text-slate-400"
                }`}
              >
                <div className="flex items-center space-x-3">
                  <div className="shrink-0">
                    {state === "completed" && (
                      <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                    )}
                    {state === "active" && (
                      <Loader2 className="w-5 h-5 text-indigo-400 animate-spin" />
                    )}
                    {state === "idle" && (
                      <Clock className="w-5 h-5 text-slate-600" />
                    )}
                    {state === "failed" && (
                      <AlertCircle className="w-5 h-5 text-rose-400" />
                    )}
                  </div>
                  <div>
                    <h4 className="text-xs font-semibold text-white flex items-center gap-2">
                      {stage.title}
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                        {stage.engine}
                      </span>
                    </h4>
                    <p className="text-[11px] text-slate-400 mt-0.5">{stage.desc}</p>
                  </div>
                </div>

                <div className="text-[11px] font-mono font-medium shrink-0">
                  {state === "completed" && (
                    <span className="text-emerald-400">DONE</span>
                  )}
                  {state === "active" && (
                    <span className="text-indigo-400 animate-pulse">RUNNING</span>
                  )}
                  {state === "idle" && (
                    <span className="text-slate-600">QUEUED</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer info */}
        <div className="p-4 bg-slate-950 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <span className="flex items-center gap-1.5">
            <Database className="w-3.5 h-3.5 text-emerald-400" />
            MongoDB Collections: <code className="text-slate-300 font-mono">videos</code>, <code className="text-slate-300 font-mono">transcripts</code>, <code className="text-slate-300 font-mono">translations</code>
          </span>
          <button
            onClick={onClose}
            className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-xs"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
