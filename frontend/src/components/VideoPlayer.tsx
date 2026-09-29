"use client";

import React, { useEffect, useRef, useState, useImperativeHandle, forwardRef } from "react";
import { Play, Pause, RotateCcw, Volume2, FastForward } from "lucide-react";

export interface VideoPlayerRef {
  seekTo: (seconds: number) => void;
  play: () => void;
  pause: () => void;
}

interface VideoPlayerProps {
  videoId: string;
  captionText?: string;
  onTimeUpdate: (currentTime: number) => void;
}

declare global {
  interface Window {
    YT: any;
    onYouTubeIframeAPIReady: () => void;
  }
}

const VideoPlayer = forwardRef<VideoPlayerRef, VideoPlayerProps>(
  ({ videoId, captionText = "", onTimeUpdate }, ref) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const playerRef = useRef<any>(null);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [currentTime, setCurrentTime] = useState<number>(0);
  const [duration, setDuration] = useState<number>(0);
  const [playbackRate, setPlaybackRate] = useState<number>(1);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Expose seekTo and play controls to parent
  useImperativeHandle(ref, () => ({
    seekTo: (seconds: number) => {
      if (playerRef.current && typeof playerRef.current.seekTo === "function") {
        playerRef.current.seekTo(seconds, true);
        playerRef.current.playVideo();
        setIsPlaying(true);
        setCurrentTime(seconds);
        onTimeUpdate(seconds);
      }
    },
    play: () => {
      if (playerRef.current && typeof playerRef.current.playVideo === "function") {
        playerRef.current.playVideo();
        setIsPlaying(true);
      }
    },
    pause: () => {
      if (playerRef.current && typeof playerRef.current.pauseVideo === "function") {
        playerRef.current.pauseVideo();
        setIsPlaying(false);
      }
    }
  }));

  // Load YouTube IFrame API script
  useEffect(() => {
    if (!window.YT) {
      const tag = document.createElement("script");
      tag.src = "https://www.youtube.com/iframe_api";
      const firstScriptTag = document.getElementsByTagName("script")[0];
      firstScriptTag.parentNode?.insertBefore(tag, firstScriptTag);
    }

    const initPlayer = () => {
      if (!window.YT || !window.YT.Player) return;
      if (playerRef.current) {
        playerRef.current.destroy();
      }

      playerRef.current = new window.YT.Player("youtube-player-element", {
        videoId: videoId,
        playerVars: {
          autoplay: 0,
          controls: 1,
          rel: 0,
          modestbranding: 1,
          playsinline: 1,
          enablejsapi: 1,
          origin: typeof window !== "undefined" ? window.location.origin : ""
        },
        events: {
          onReady: (event: any) => {
            const dur = event.target.getDuration();
            setDuration(dur || 0);
          },
          onStateChange: (event: any) => {
            // YT.PlayerState.PLAYING is 1
            if (event.data === 1) {
              setIsPlaying(true);
              startTracking();
            } else {
              setIsPlaying(false);
              stopTracking();
            }
          }
        }
      });
    };

    if (window.YT && window.YT.Player) {
      initPlayer();
    } else {
      window.onYouTubeIframeAPIReady = initPlayer;
    }

    return () => {
      stopTracking();
      if (playerRef.current) {
        try {
          playerRef.current.destroy();
        } catch {
          // ignore
        }
      }
    };
  }, [videoId]);

  const startTracking = () => {
    stopTracking();
    timerRef.current = setInterval(() => {
      if (playerRef.current && typeof playerRef.current.getCurrentTime === "function") {
        const time = playerRef.current.getCurrentTime();
        if (time !== undefined && !isNaN(time)) {
          setCurrentTime(time);
          onTimeUpdate(time);
        }
      }
    }, 200); // 5 updates per second for smooth word highlighting
  };

  const stopTracking = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  const handleTogglePlay = () => {
    if (!playerRef.current) return;
    if (isPlaying) {
      playerRef.current.pauseVideo();
    } else {
      playerRef.current.playVideo();
    }
  };

  const handleRewind = (seconds: number) => {
    if (playerRef.current && typeof playerRef.current.getCurrentTime === "function") {
      const nextTime = Math.max(0, playerRef.current.getCurrentTime() - seconds);
      playerRef.current.seekTo(nextTime, true);
    }
  };

  const handleChangeRate = (rate: number) => {
    if (playerRef.current && typeof playerRef.current.setPlaybackRate === "function") {
      playerRef.current.setPlaybackRate(rate);
      setPlaybackRate(rate);
    }
  };

  const formatSeconds = (sec: number) => {
    const mins = Math.floor(sec / 60);
    const secs = Math.floor(sec % 60);
    return `${mins}:${secs < 10 ? "0" : ""}${secs}`;
  };

  return (
    <div className="flex flex-col rounded-2xl overflow-hidden bg-slate-900 border border-slate-800 shadow-xl">
      {/* Video Viewport */}
      <div className="relative aspect-video w-full bg-black">
        <div id="youtube-player-element" className="w-full h-full" />

        {/* Real synchronized transcript caption overlay. The parent supplies the
            segment whose start/end timestamps contain the current playback time. */}
        {captionText.trim() && (
          <div className="pointer-events-none absolute inset-x-0 bottom-14 z-20 flex justify-center px-4 sm:px-8">
            <div className="max-w-[82%] rounded-md bg-black/75 px-2.5 py-1 text-center text-xs font-medium leading-snug text-white shadow-md backdrop-blur-sm sm:text-sm">
              {captionText}
            </div>
          </div>
        )}
      </div>

      {/* Sync Controls Bar */}
      <div className="p-3 bg-slate-900/90 border-t border-slate-800 flex items-center justify-between text-xs text-slate-300">
        <div className="flex items-center space-x-2">
          <button
            onClick={handleTogglePlay}
            className="p-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white transition-colors"
            title={isPlaying ? "Pause" : "Play"}
          >
            {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 fill-white" />}
          </button>
          <button
            onClick={() => handleRewind(5)}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
            title="Rewind 5s"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
          <span className="font-mono text-xs text-slate-400 pl-1">
            {formatSeconds(currentTime)} / {formatSeconds(duration)}
          </span>
        </div>

        {/* Speed Selector */}
        <div className="flex items-center space-x-1.5">
          <span className="text-slate-500 text-[11px] hidden sm:inline">Speed:</span>
          {[0.75, 1, 1.25, 1.5].map((rate) => (
            <button
              key={rate}
              onClick={() => handleChangeRate(rate)}
              className={`px-2 py-0.5 rounded text-[11px] font-mono transition-colors ${
                playbackRate === rate
                  ? "bg-indigo-500/20 text-indigo-400 border border-indigo-500/40"
                  : "bg-slate-800 text-slate-400 hover:bg-slate-700"
              }`}
            >
              {rate}x
            </button>
          ))}
        </div>
      </div>
    </div>
  );
  }
);

VideoPlayer.displayName = "VideoPlayer";
export default VideoPlayer;
