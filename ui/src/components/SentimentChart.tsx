import React from 'react'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer } from "recharts"
import { motion } from 'framer-motion'

export function SentimentChart({ chartData }: { chartData: { name: string, score: number }[] }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.1 }}
      className="lg:col-span-2 bg-white/60 dark:bg-neutral-900/40 backdrop-blur-xl rounded-xl border border-white/20 dark:border-neutral-700/30 shadow-lg p-5"
    >
      <div className="mb-4">
        <h2 className="text-lg font-semibold">Live Sentiment Trend</h2>
        <p className="text-xs text-neutral-500">Score ranges from -1.0 (negative) to +1.0 (positive)</p>
      </div>
      <div className="h-[300px] w-full">
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#525252" opacity={0.2} />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} tickMargin={8} opacity={0.5} />
              <YAxis domain={[-1, 1]} tick={{ fontSize: 12 }} opacity={0.5} />
              <RechartsTooltip
                contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                labelStyle={{ fontWeight: 'bold', color: '#171717' }}
              />
              <Area
                type="monotone"
                dataKey="score"
                stroke="#3b82f6"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#colorScore)"
                isAnimationActive={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-neutral-400">
            Waiting for data...
          </div>
        )}
      </div>
    </motion.div>
  )
}
