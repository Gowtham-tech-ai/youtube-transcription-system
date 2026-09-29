"use client";

import React from "react";
import { Download, FileText, Music, Video, Subtitles, Globe, ArrowDownToLine } from "lucide-react";
import { getDownloadUrl } from "@/lib/api";

interface DownloadSectionProps {
  videoId: string;
  currentLanguage: string;
}

export default function DownloadSection({ videoId, currentLanguage }: DownloadSectionProps) {
  const downloadItems = [
    {
      label: "Download Audio (MP3)",
      type: "mp3",
      icon: Music,
      desc: "Preprocessed 192kbps audio",
      color: "from-emerald-500/20 to-teal-500/10 text-emerald-400 border-emerald-500/30",
    },
    {
      label: "Subtitles (SRT)",
      type: "srt",
      icon: Subtitles,
      desc: `SubRip format (${currentLanguage.toUpperCase()})`,
      color: "from-blue-500/20 to-cyan-500/10 text-blue-400 border-blue-500/30",
    },
    {
      label: "Web Subtitles (VTT)",
      type: "vtt",
      icon: Subtitles,
      desc: `WebVTT standard captions`,
      color: "from-indigo-500/20 to-violet-500/10 text-indigo-400 border-indigo-500/30",
    },
    {
      label: "Transcript (TXT)",
      type: "txt",
      icon: FileText,
      desc: `Full clean text transcription`,
      color: "from-amber-500/20 to-orange-500/10 text-amber-400 border-amber-500/30",
    },
    {
      label: "Video (MP4)",
      type: "mp4",
      icon: Video,
      desc: "Downloaded HD video file",
      color: "from-purple-500/20 to-pink-500/10 text-purple-400 border-purple-500/30",
    },
  ];

  return (
    <div className="bg-slate-900 rounded-2xl border border-slate-800 p-5 shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <ArrowDownToLine className="w-4 h-4 text-indigo-400" />
          Export & Download Center
        </h3>
        <span className="text-xs text-slate-400">
          Selected Lang: <span className="font-mono text-indigo-400 font-semibold">{currentLanguage.toUpperCase()}</span>
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {downloadItems.map((item, idx) => {
          const Icon = item.icon;
          const url = getDownloadUrl(videoId, item.type, currentLanguage);

          return (
            <a
              key={idx}
              href={url}
              target="_blank"
              rel="noreferrer"
              download
              className={`p-3 rounded-xl border bg-gradient-to-b ${item.color} hover:scale-[1.02] transition-all flex flex-col justify-between group`}
            >
              <div className="flex items-center justify-between mb-2">
                <Icon className="w-5 h-5" />
                <Download className="w-3.5 h-3.5 opacity-60 group-hover:opacity-100 transition-opacity" />
              </div>
              <div>
                <p className="text-xs font-semibold text-white group-hover:text-indigo-300 transition-colors">
                  {item.label}
                </p>
                <p className="text-[10px] text-slate-400 mt-0.5">{item.desc}</p>
              </div>
            </a>
          );
        })}
      </div>
    </div>
  );
}
