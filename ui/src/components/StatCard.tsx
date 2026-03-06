import React from 'react'
import { motion } from 'framer-motion'

export function StatCard({ title, value, icon, subtitle }: { title: string, value: string | number, icon: React.ReactNode, subtitle?: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="bg-white/60 dark:bg-neutral-900/40 backdrop-blur-xl rounded-xl border border-white/20 dark:border-neutral-700/30 shadow-lg p-5 flex flex-col justify-between"
    >
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-sm font-medium text-neutral-500 dark:text-neutral-400">{title}</h3>
        <div className="p-2 bg-neutral-50 dark:bg-neutral-950 rounded-md">
          {icon}
        </div>
      </div>
      <div>
        <div className="text-2xl font-bold">{value}</div>
        {subtitle && (
          <div className="text-xs text-neutral-400 mt-1">{subtitle}</div>
        )}
      </div>
    </motion.div>
  )
}
