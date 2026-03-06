import React from 'react'
import { AlertCircle, CheckCircle2, MinusCircle, Youtube, MessageCircle, Star, Hash } from "lucide-react"
import { motion } from 'framer-motion'

export interface SentimentOutput {
  event_id: string
  label: "positive" | "neutral" | "negative" | string
  score: number
  confidence: number
  model_version: string
  scored_at_utc: string
  source?: string
}

export function LiveEventFeed({ events }: { events: SentimentOutput[] }) {
  const getSourceIcon = (source?: string) => {
    switch (source?.toLowerCase()) {
      case 'youtube': return <Youtube className="w-4 h-4 text-red-500" />;
      case 'reddit': return <MessageCircle className="w-4 h-4 text-orange-500" />;
      case 'reviews': return <Star className="w-4 h-4 text-yellow-500" />;
      default: return <Hash className="w-4 h-4 text-neutral-400" />;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
      className="bg-white/60 dark:bg-neutral-900/40 backdrop-blur-xl rounded-xl border border-white/20 dark:border-neutral-700/30 shadow-lg p-5 flex flex-col h-[400px]"
    >
      <h2 className="text-lg font-semibold mb-4">Latest Ingested Events</h2>
      <div className="flex-1 overflow-y-auto pr-2 space-y-3">
        {events.length === 0 ? (
          <div className="flex h-full items-center justify-center text-sm text-neutral-400">
            No events yet
          </div>
        ) : (
          events.map((ev, idx) => (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              key={`${ev.event_id}-${idx}`}
              className="flex items-start gap-3 p-3 rounded-lg bg-white/40 dark:bg-neutral-800/40 border border-white/30 dark:border-neutral-700/30 text-sm shadow-sm"
            >
              <div className="mt-0.5 flex flex-col items-center gap-2">
                {ev.label === 'positive' && <CheckCircle2 className="w-4 h-4 text-emerald-500" />}
                {ev.label === 'negative' && <AlertCircle className="w-4 h-4 text-rose-500" />}
                {ev.label === 'neutral' && <MinusCircle className="w-4 h-4 text-neutral-500" />}
                {getSourceIcon(ev.source)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex justify-between items-center mb-1">
                  <span className="font-medium text-xs capitalize text-neutral-500 dark:text-neutral-400 flex items-center gap-1">
                    {ev.label} {ev.source && <span className="text-[10px] text-neutral-400 lowercase">({ev.source})</span>}
                  </span>
                  <span className="text-[10px] text-neutral-400">
                    {new Date(ev.scored_at_utc).toLocaleTimeString()}
                  </span>
                </div>
                <div className="font-mono text-xs text-neutral-600 dark:text-neutral-300 truncate">
                  Score: {ev.score.toFixed(3)}
                </div>
                <div className="text-xs text-neutral-400 truncate mt-1">
                  ID: {ev.event_id}
                </div>
              </div>
            </motion.div>
          ))
        )}
      </div>
    </motion.div>
  )
}
