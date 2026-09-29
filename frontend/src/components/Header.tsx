"use client";

import { Database, Sparkles, CheckCircle2, Cloud } from "lucide-react";
import { YoutubeIcon } from "@/components/Icons";
import { DatabaseStatus } from "@/types";

interface HeaderProps {
  dbStatus: DatabaseStatus | null;
  onSelectSample: (url: string) => void;
  onOpenDashboard: () => void;
}

export const SAMPLE_VIDEOS = [
  {
    title: "TED: How Language Shapes Thought",
    url: "https://www.youtube.com/watch?v=RKK7wGAYP6k",
    tag: "Cognition & Speech"
  },
  {
    title: "Python in 100 Seconds",
    url: "https://www.youtube.com/watch?v=x7X9w_GIm1s",
    tag: "Fast Code Tutorial"
  },
  {
    title: "Steve Jobs Stanford Speech",
    url: "https://www.youtube.com/watch?v=UF8uR6Z6KLc",
    tag: "Inspirational"
  }
];

export default function Header({ dbStatus, onSelectSample, onOpenDashboard }: HeaderProps) {
  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center space-x-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-rose-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-rose-500/20">
            <YoutubeIcon className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-base sm:text-lg font-bold bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent flex items-center gap-2">
              YouTube Multilingual Transcriber
              <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
                v1.0
              </span>
            </h1>
            <p className="text-xs text-slate-400 hidden sm:block">
              Speech-to-Text • Word-Level Timestamps • AI Translation
            </p>
          </div>
        </div>

        {/* Center: Quick Samples */}
        <div className="hidden md:flex items-center space-x-2">
          <span className="text-xs text-slate-400 flex items-center gap-1">
            <Sparkles className="w-3.5 h-3.5 text-amber-400" /> Samples:
          </span>
          {SAMPLE_VIDEOS.map((sample, idx) => (
            <button
              key={idx}
              onClick={() => onSelectSample(sample.url)}
              className="text-xs px-2.5 py-1 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700/60 transition-colors"
            >
              {sample.title.split(":")[0]}
            </button>
          ))}
        </div>

        {/* Right: MongoDB Atlas Status & Dashboard */}
        <div className="flex items-center space-x-3">
          <div
            className={`flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-medium border ${
              dbStatus?.is_atlas_connected
                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                : "bg-cyan-500/10 text-cyan-400 border-cyan-500/30"
            }`}
            title={dbStatus?.mode || "Database connected"}
          >
            {dbStatus?.is_atlas_connected ? (
              <Cloud className="w-3.5 h-3.5 text-emerald-400" />
            ) : (
              <Database className="w-3.5 h-3.5 text-cyan-400" />
            )}
            <span className="hidden sm:inline">
              {dbStatus?.is_atlas_connected ? "MongoDB Atlas" : "MongoDB (Local)"}
            </span>
            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
          </div>

          <button
            onClick={onOpenDashboard}
            className="text-xs px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium shadow-md shadow-indigo-600/20 transition-all"
          >
            Pipeline Monitor
          </button>
        </div>
      </div>
    </header>
  );
}
