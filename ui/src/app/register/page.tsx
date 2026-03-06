"use client"

import React, { useState } from "react"
import { useRouter } from "next/navigation"
import { Lock, Mail, Loader2, UserPlus } from "lucide-react"

export default function RegisterPage() {
    const [email, setEmail] = useState("")
    const [password, setPassword] = useState("")
    const [error, setError] = useState("")
    const [loading, setLoading] = useState(false)

    const router = useRouter()
    const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000"

    const handleRegister = async (e: React.FormEvent) => {
        e.preventDefault()
        setError("")
        setLoading(true)

        try {
            const res = await fetch(`${apiBase}/auth/register`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password, role: "user" }),
            })

            if (!res.ok) {
                let errMessage = "Registration failed"
                try {
                    const data = await res.json()
                    errMessage = Array.isArray(data.detail) ? data.detail[0]?.msg : data.detail || errMessage
                } catch { /* ignore non-json errors */ }
                throw new Error(errMessage)
            }

            const data = await res.json()
            if (data.access_token) {
                localStorage.setItem("token", data.access_token)
                router.push("/")
            } else {
                throw new Error("No token received")
            }
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : String(err))
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-neutral-50 dark:bg-neutral-950 p-6 text-neutral-900 dark:text-neutral-100 font-sans">
            <div className="max-w-md w-full bg-white dark:bg-neutral-900 rounded-xl border border-neutral-200 dark:border-neutral-800 shadow-sm p-8">
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 mb-4">
                        <UserPlus className="w-6 h-6" />
                    </div>
                    <h1 className="text-2xl font-bold">Create an Account</h1>
                    <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-2">
                        Register to access the live Sentiment Dashboard
                    </p>
                </div>

                {error && (
                    <div className="mb-6 p-3 rounded-md bg-rose-50 border border-rose-200 text-rose-600 text-sm dark:bg-rose-950/30 dark:border-rose-900/50 dark:text-rose-400">
                        {error}
                    </div>
                )}

                <form onSubmit={handleRegister} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium mb-1">Email</label>
                        <div className="relative">
                            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-400" />
                            <input
                                type="email"
                                required
                                className="w-full pl-10 pr-4 py-2 bg-neutral-50 dark:bg-neutral-950 border border-neutral-200 dark:border-neutral-800 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 transition-shadow"
                                placeholder="you@example.com"
                                value={email}
                                onChange={e => setEmail(e.target.value)}
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium mb-1">Password</label>
                        <div className="relative">
                            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-400" />
                            <input
                                type="password"
                                required
                                minLength={8}
                                className="w-full pl-10 pr-4 py-2 bg-neutral-50 dark:bg-neutral-950 border border-neutral-200 dark:border-neutral-800 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 transition-shadow"
                                placeholder="••••••••"
                                value={password}
                                onChange={e => setPassword(e.target.value)}
                            />
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full py-2.5 px-4 bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded-md transition-colors disabled:opacity-70 flex items-center justify-center gap-2 mt-2"
                    >
                        {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Sign Up"}
                    </button>
                </form>

                <div className="mt-6 text-center text-sm text-neutral-500">
                    Already have an account?{" "}
                    <button onClick={() => router.push("/login")} className="text-blue-500 hover:underline">
                        Sign in
                    </button>
                </div>
            </div>
        </div>
    )
}
