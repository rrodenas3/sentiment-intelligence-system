"use client"

import React, { useEffect, useState, useCallback } from "react"
import { useRouter } from "next/navigation"
import { fetchEventSource } from "@microsoft/fetch-event-source"
import { StatCard } from "../components/StatCard"
import { SentimentChart } from "../components/SentimentChart"
import { LiveEventFeed, SentimentOutput } from "../components/LiveEventFeed"
import { AlertCircle, CheckCircle2, MinusCircle, Activity, Loader2, LogOut } from "lucide-react"
import { motion } from "framer-motion"

export default function Dashboard() {
  const [events, setEvents] = useState<SentimentOutput[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const [userEmail, setUserEmail] = useState<string | null>(null)
  const [selectedSource, setSelectedSource] = useState<string>("All")
  const [timeRange, setTimeRange] = useState<string>("live")
  const [historicalData, setHistoricalData] = useState<{ name: string, score: number }[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [fetchError, setFetchError] = useState<string | null>(null)
  const [summary, setSummary] = useState({
    count: 0,
    by_label: { positive: 0, neutral: 0, negative: 0 }
  })

  const router = useRouter()
  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000"

  const handleLogout = useCallback(() => {
    localStorage.removeItem("token")
    router.push("/login")
  }, [router])

  // Connect to SSE stream with Auth
  useEffect(() => {
    const token = localStorage.getItem("token")
    if (!token) {
      router.push("/login")
      return
    }

    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      // eslint-disable-next-line react-hooks/set-state-in-effect
      if (payload.sub) setUserEmail(payload.sub)
    } catch (e) {
      console.error("Invalid token format", e)
    }

    const ctrl = new AbortController()
    let reconnectAttempts = 0

    fetchEventSource(`${apiBase}/stream/sentiment`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: "text/event-stream"
      },
      signal: ctrl.signal,
      onopen(response) {
        if (response.ok && response.status === 200) {
          setIsConnected(true)
          reconnectAttempts = 0
          setFetchError(null)
        } else if (response.status === 401) {
          handleLogout()
        }
        return Promise.resolve()
      },
      onmessage(event) {
        try {
          const data: SentimentOutput = JSON.parse(event.data)
          if (selectedSource !== "All" && data.source && data.source.toLowerCase() !== selectedSource.toLowerCase()) {
            return;
          }
          setEvents(prev => [data, ...prev].slice(0, 100))
          setSummary(prev => ({
            count: prev.count + 1,
            by_label: { ...prev.by_label, [data.label]: prev.by_label[data.label as keyof typeof prev.by_label] + 1 }
          }))
        } catch (err) {
          console.error("Failed to parse SSE event", err)
        }
      },
      onerror(err) {
        console.error("SSE connection error", err)
        setIsConnected(false)
        setFetchError("Live stream interrupted. Attempting to reconnect...")
        reconnectAttempts++
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000)
        return delay // return delay to auto-retry
      }
    })

    return () => ctrl.abort()
  }, [apiBase, router, selectedSource, handleLogout])

  // Fetch historical aggregates when timeRange changes
  useEffect(() => {
    const token = localStorage.getItem("token")
    if (!token) return

    if (timeRange === "live") {
      setHistoricalData([])
      setIsLoading(true)
      setFetchError(null)
      // Fetch initial summary from GET /sentiment/summary
      const sourceParam = selectedSource !== "All" ? `?source=${selectedSource.toLowerCase()}` : ""
      fetch(`${apiBase}/sentiment/summary${sourceParam}`, {
        headers: { Authorization: `Bearer ${token}` }
      })
        .then(async res => {
          if (!res.ok) throw new Error("Failed to load summary")
          return res.json()
        })
        .then(data => {
          setSummary({
            count: data.count || 0,
            by_label: data.by_label || { positive: 0, neutral: 0, negative: 0 }
          })
        })
        .finally(() => setIsLoading(false))
      return
    }

    setIsLoading(true)
    setFetchError(null)
    let windowSize = "1h"
    let limit = 24
    if (timeRange === "1h") { windowSize = "1m"; limit = 60 }
    else if (timeRange === "6h") { windowSize = "5m"; limit = 72 }
    else if (timeRange === "24h") { windowSize = "1h"; limit = 24 }
    else if (timeRange === "7d") { windowSize = "1h"; limit = 168 }

    let url = `${apiBase}/sentiment/aggregates?window=${windowSize}&limit=${limit}`
    if (selectedSource !== "All") {
      url += `&source=${selectedSource.toLowerCase()}`
    }

    fetch(url, { headers: { Authorization: `Bearer ${token}` } })
      .then(res => res.ok ? res.json() : [])
      .then((data: any[]) => {
        // Map aggregate row to a generic score between -1 and 1
        let sumTotal = 0, sumPos = 0, sumNeu = 0, sumNeg = 0;
        const mapped = data.reverse().map(row => {
          const total = row.count_total || 1
          sumTotal += row.count_total || 0
          sumPos += row.count_positive || 0
          sumNeu += row.count_neutral || 0
          sumNeg += row.count_negative || 0
          const score = (row.count_positive - row.count_negative) / total
          return {
            name: new Date(row.bucket_start).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit' }),
            score: score
          }
        })
        setHistoricalData(mapped)
        setSummary({
          count: sumTotal,
          by_label: { positive: sumPos, neutral: sumNeu, negative: sumNeg }
        })
      })
      .catch(err => setFetchError("Failed to fetch historical data: " + err.message))
      .finally(() => setIsLoading(false))

  }, [timeRange, selectedSource, apiBase])

  // Calculate stats
  const total = summary.count || 1 // prevent div by zero
  const posPercent = ((summary.by_label.positive / total) * 100).toFixed(1)
  const negPercent = ((summary.by_label.negative / total) * 100).toFixed(1)
  const neuPercent = ((summary.by_label.neutral / total) * 100).toFixed(1)

  // Chart data: Use historicalData if not live, otherwise live rolling events
  const chartData = timeRange === "live"
    ? [...events].reverse().map((ev) => ({
      name: new Date(ev.scored_at_utc).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      score: ev.score,
    }))
    : historicalData

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  }

  return (
    <div className="min-h-screen bg-transparent p-6 md:p-8 font-sans text-neutral-900 dark:text-neutral-100">
      <div className="max-w-6xl mx-auto space-y-6">

        {fetchError && (
          <div className="max-w-7xl mx-auto mt-4 px-4 py-3 rounded-lg bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/50 flex items-start gap-3 text-rose-600 dark:text-rose-400 text-sm">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <p>{fetchError}</p>
          </div>
        )}

        {/* Header */}
        <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-neutral-200 dark:border-neutral-800 pb-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Sentiment Intelligence</h1>
            <div className="flex items-center gap-3 mt-1">
              <p className="text-sm text-neutral-500 dark:text-neutral-400">Real-time multi-source monitoring dashboard</p>
              <select
                value={selectedSource}
                onChange={(e) => {
                  setSelectedSource(e.target.value)
                  setEvents([]) // clear events when source changes
                }}
                className="text-xs bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-md py-1 px-2 focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer"
              >
                <option value="All">All Sources</option>
                <option value="youtube">YouTube</option>
                <option value="reddit">Reddit</option>
                <option value="reviews">Reviews</option>
              </select>
            </div>
          </div>
          <div className="flex flex-col sm:flex-row items-center gap-4 mt-4 md:mt-0">
            <div className="flex items-center gap-2 bg-neutral-100 dark:bg-neutral-800/50 p-1 pl-2 rounded-lg text-sm border border-neutral-200 dark:border-neutral-800">
              <span className="text-neutral-500 text-xs font-medium uppercase tracking-wider">Time</span>
              <div className="flex items-center gap-1 bg-white dark:bg-neutral-900 rounded-md p-1 border shadow-sm border-neutral-200 dark:border-neutral-800">
                {(['live', '1h', '6h', '24h', '7d'] as const).map(tr => (
                  <button
                    key={tr}
                    onClick={() => setTimeRange(tr)}
                    className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${timeRange === tr ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-400' : 'text-neutral-600 hover:bg-neutral-100 dark:text-neutral-400 dark:hover:bg-neutral-800'}`}
                  >
                    {tr === 'live' ? 'Live' : tr}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex items-center gap-2 text-sm font-medium px-3 py-1.5 rounded-full bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 shadow-sm">
              {isConnected && timeRange === "live" ? (
                <>
                  <div className="relative flex h-2.5 w-2.5">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
                  </div>
                  <span className="text-neutral-700 dark:text-neutral-300">Live</span>
                </>
              ) : (
                <>
                  <div className="w-2.5 h-2.5 rounded-full bg-neutral-400 dark:bg-neutral-600"></div>
                  <span className="text-neutral-500 dark:text-neutral-400">{timeRange !== 'live' ? 'Historical' : 'Offline'}</span>
                </>
              )}
            </div>
            {userEmail && (
              <span className="text-sm font-medium text-neutral-600 dark:text-neutral-300 hidden sm:inline-block">
                {userEmail}
              </span>
            )}
            <button
              onClick={handleLogout}
              title="Sign out"
              className="p-2 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-full text-neutral-500 hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-colors shadow-sm"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </header>

        {/* Top Stats Cards */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="show"
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"
        >
          <StatCard
            title="Total Events Scored"
            value={summary.count.toLocaleString()}
            icon={<Activity className="w-5 h-5 text-blue-500" />}
          />
          <StatCard
            title="Positive Sentiment"
            value={`${posPercent}%`}
            subtitle={`${summary.by_label.positive.toLocaleString()} events`}
            icon={<CheckCircle2 className="w-5 h-5 text-emerald-500" />}
          />
          <StatCard
            title="Neutral Sentiment"
            value={`${neuPercent}%`}
            subtitle={`${summary.by_label.neutral.toLocaleString()} events`}
            icon={<MinusCircle className="w-5 h-5 text-neutral-500" />}
          />
          <StatCard
            title="Negative Sentiment"
            value={`${negPercent}%`}
            subtitle={`${summary.by_label.negative.toLocaleString()} events`}
            icon={<AlertCircle className="w-5 h-5 text-rose-500" />}
          />
        </motion.div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 relative">

          {isLoading && (
            <div className="absolute inset-0 z-10 bg-white/50 dark:bg-neutral-950/50 flex items-center justify-center backdrop-blur-[1px] rounded-xl border border-neutral-200/50 dark:border-neutral-800/50">
              <div className="flex flex-col items-center gap-2 text-neutral-500 dark:text-neutral-400">
                <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
                <span className="text-sm font-medium">Loading data...</span>
              </div>
            </div>
          )}

          {/* Chart Section */}
          <SentimentChart chartData={chartData} />

          {/* Live Feed Section */}
          <LiveEventFeed events={events} />

        </div>
      </div>
    </div>
  )
}
