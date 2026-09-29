"use client";

import React, { useState, useEffect, useRef, useMemo } from "react";
import {
  Search,
  Globe,
  Volume2,
  Copy,
  Check,
  ArrowDownCircle,
  Clock,
  Sparkles,
  ChevronRight,
  ExternalLink
} from "lucide-react";
import { TranscriptSegment } from "@/types";

interface TranscriptViewerProps {
  segments: TranscriptSegment[];
  currentTime: number;
  currentLanguage: string;
  availableLanguages: Record<string, string>;
  isTranslating: boolean;
  onLanguageChange: (lang: string) => void;
  onJumpTo: (seconds: number) => void;
}

export default function TranscriptViewer({
  segments,
  currentTime,
  currentLanguage,
  availableLanguages,
  isTranslating,
  onLanguageChange,
  onJumpTo,
}: TranscriptViewerProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [autoScroll, setAutoScroll] = useState(true);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [activeSegmentIndex, setActiveSegmentIndex] = useState<number>(-1);
  const activeItemRef = useRef<HTMLDivElement | null>(null);
  const scrollContainerRef = useRef<HTMLDivElement | null>(null);

  // Compute active segment based on current playback time
  useEffect(() => {
    const idx = segments.findIndex(
      (seg) => currentTime >= seg.start && currentTime <= seg.end
    );
    if (idx !== -1) {
      setActiveSegmentIndex(idx);
    }
  }, [currentTime, segments]);

  // Smooth auto-scroll to active sentence if enabled
  useEffect(() => {
    if (autoScroll && activeItemRef.current && scrollContainerRef.current) {
      activeItemRef.current.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
      });
    }
  }, [activeSegmentIndex, autoScroll]);

  // Format seconds to mm:ss
  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s < 10 ? "0" : ""}${s}`;
  };

  // Filter and search matching segments
  const filteredSegments = useMemo(() => {
    if (!searchQuery.trim()) {
      return segments.map((seg, originalIndex) => ({
        ...seg,
        originalIndex,
        isMatch: false,
      }));
    }
    const q = searchQuery.toLowerCase();
    return segments.map((seg, originalIndex) => ({
      ...seg,
      originalIndex,
      isMatch: seg.text.toLowerCase().includes(q),
    }));
  }, [segments, searchQuery]);

  const matchCount = useMemo(() => {
    if (!searchQuery.trim()) return 0;
    return filteredSegments.filter((s) => s.isMatch).length;
  }, [filteredSegments, searchQuery]);

  // Copy segment text
  const handleCopy = (text: string, idx: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 1800);
  };

  // Text to Speech playback for translation or segment
  const handleSpeak = (text: string, lang: string) => {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = lang === "te" ? "te-IN" : lang === "hi" ? "hi-IN" : lang === "es" ? "es-ES" : "en-US";
      window.speechSynthesis.speak(utterance);
    }
  };

  // Helper to render text with word-level highlight or search highlight
  const renderSegmentContent = (seg: TranscriptSegment, isActiveSegment: boolean) => {
    // If word-level timestamps exist and this segment is currently active, highlight words in real-time
    if (isActiveSegment && seg.words && seg.words.length > 0) {
      return (
        <span className="leading-relaxed">
          {seg.words.map((w, wIdx) => {
            const isWordActive = currentTime >= w.start && currentTime <= w.end;
            return (
              <span
                key={wIdx}
                onClick={(e) => {
                  e.stopPropagation();
                  onJumpTo(w.start);
                }}
                className={`inline-block mx-0.5 px-1 py-0.5 rounded cursor-pointer transition-all duration-150 ${
                  isWordActive
                    ? "bg-indigo-500 text-white font-semibold scale-105 shadow-sm shadow-indigo-500/50"
                    : "hover:bg-slate-800 text-slate-200"
                }`}
                title={`Jump to ${formatTime(w.start)}`}
              >
                {w.word}
              </span>
            );
          })}
        </span>
      );
    }

    // Search query highlighting if active search
    if (searchQuery.trim() && seg.text.toLowerCase().includes(searchQuery.toLowerCase())) {
      const parts = seg.text.split(new RegExp(`(${searchQuery})`, "gi"));
      return (
        <span className="leading-relaxed">
          {parts.map((part, i) =>
            part.toLowerCase() === searchQuery.toLowerCase() ? (
              <mark
                key={i}
                className="bg-amber-400/30 text-amber-200 px-1 py-0.5 rounded font-medium border border-amber-400/40"
              >
                {part}
              </mark>
            ) : (
              part
            )
          )}
        </span>
      );
    }

    return <span className="leading-relaxed text-slate-300">{seg.text}</span>;
  };

  return (
    <div className="flex flex-col h-full bg-slate-900 rounded-2xl border border-slate-800 shadow-xl overflow-hidden">
      {/* Top Controls: Language Selector & Search Bar */}
      <div className="p-4 border-b border-slate-800 bg-slate-900/90 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          {/* Language Selector */}
          <div className="flex items-center space-x-2">
            <Globe className="w-4 h-4 text-indigo-400" />
            <span className="text-xs font-semibold text-slate-300">Language:</span>
            <select
              value={currentLanguage}
              onChange={(e) => onLanguageChange(e.target.value)}
              disabled={isTranslating}
              className="bg-slate-800 border border-slate-700 text-xs text-white rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-500 cursor-pointer"
            >
              {Object.entries(availableLanguages).map(([code, name]) => (
                <option key={code} value={code}>
                  {name}
                </option>
              ))}
            </select>
            {isTranslating && (
              <span className="flex items-center gap-1 text-[11px] text-amber-400 animate-pulse">
                <Sparkles className="w-3 h-3" /> Translating...
              </span>
            )}
          </div>

          {/* Auto-scroll toggle */}
          <button
            onClick={() => setAutoScroll(!autoScroll)}
            className={`flex items-center space-x-1.5 text-xs px-2.5 py-1 rounded-md border transition-colors ${
              autoScroll
                ? "bg-indigo-500/10 text-indigo-400 border-indigo-500/30"
                : "bg-slate-800 text-slate-400 border-slate-700 hover:text-slate-200"
            }`}
          >
            <ArrowDownCircle className="w-3.5 h-3.5" />
            <span>Auto-scroll</span>
          </button>
        </div>

        {/* Search Bar */}
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search words or phrases in transcript..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-950/70 border border-slate-800 rounded-xl pl-9 pr-24 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
          />
          {searchQuery.trim() && (
            <div className="absolute right-2.5 top-2 flex items-center space-x-1.5">
              <span className="text-[11px] px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-mono">
                {matchCount} match{matchCount === 1 ? "" : "es"}
              </span>
              <button
                onClick={() => setSearchQuery("")}
                className="text-xs text-slate-400 hover:text-white px-1"
              >
                ✕
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Segments Transcript Body */}
      <div
        ref={scrollContainerRef}
        className="flex-1 overflow-y-auto p-4 space-y-2.5 divide-y divide-slate-800/40"
      >
        {filteredSegments.length === 0 ? (
          <div className="text-center py-16 text-slate-500 text-xs">
            No transcript segments available. Load a YouTube video to begin.
          </div>
        ) : (
          filteredSegments.map((seg) => {
            const isActive = seg.originalIndex === activeSegmentIndex;
            return (
              <div
                key={seg.originalIndex}
                ref={isActive ? activeItemRef : null}
                onClick={() => onJumpTo(seg.start)}
                className={`pt-2.5 p-3 rounded-xl cursor-pointer transition-all duration-200 group border ${
                  isActive
                    ? "bg-indigo-950/40 border-indigo-500/60 shadow-lg shadow-indigo-500/10 ring-1 ring-indigo-500/40"
                    : seg.isMatch
                    ? "bg-amber-950/20 border-amber-500/40"
                    : "bg-slate-950/30 border-transparent hover:bg-slate-800/50 hover:border-slate-800"
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  {/* Timestamp Badge */}
                  <div className="flex items-center space-x-1.5 shrink-0 pt-0.5">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onJumpTo(seg.start);
                      }}
                      className={`flex items-center space-x-1 px-2 py-0.5 rounded-md font-mono text-[11px] font-medium transition-colors ${
                        isActive
                          ? "bg-indigo-500 text-white shadow-sm"
                          : "bg-slate-800 text-slate-400 group-hover:text-indigo-400 group-hover:bg-slate-700"
                      }`}
                      title="Jump to video position"
                    >
                      <Clock className="w-3 h-3" />
                      <span>{formatTime(seg.start)}</span>
                    </button>
                  </div>

                  {/* Spoken Text with Word Highlights */}
                  <div className="flex-1 text-xs leading-relaxed">
                    {renderSegmentContent(seg, isActive)}
                  </div>

                  {/* Actions: Listen / Copy */}
                  <div className="flex items-center space-x-1 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleSpeak(seg.text, currentLanguage);
                      }}
                      className="p-1 rounded hover:bg-slate-700 text-slate-400 hover:text-white"
                      title="Listen sentence"
                    >
                      <Volume2 className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleCopy(seg.text, seg.originalIndex);
                      }}
                      className="p-1 rounded hover:bg-slate-700 text-slate-400 hover:text-white"
                      title="Copy text"
                    >
                      {copiedIndex === seg.originalIndex ? (
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Footer Info */}
      <div className="p-3 bg-slate-900 border-t border-slate-800 flex items-center justify-between text-[11px] text-slate-400">
        <span>
          {segments.length} segments • Click any word/timestamp to jump
        </span>
        <span className="font-mono text-indigo-400">
          Sync: {formatTime(currentTime)}
        </span>
      </div>
    </div>
  );
}
