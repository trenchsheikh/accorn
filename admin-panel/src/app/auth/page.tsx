"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import { motion, AnimatePresence } from "framer-motion";
import { Mail, Lock, User, ArrowRight, Loader2, Github, Chrome } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

export default function AuthPage() {
    const [mode, setMode] = useState<"login" | "signup">("signup");
    const [formData, setFormData] = useState({
        email: "",
        password: "",
        name: "",
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const router = useRouter();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setLoading(true);

        try {
            const endpoint = mode === "signup" ? "/v1/auth/signup" : "/v1/auth/login";
            const payload = mode === "signup"
                ? { email: formData.email, password: formData.password, name: formData.name }
                : { email: formData.email, password: formData.password };

            const response = await axios.post(`http://127.0.0.1:8000${endpoint}`, payload);

            // Store token and user data
            localStorage.setItem("auth_token", response.data.access_token);
            localStorage.setItem("user", JSON.stringify(response.data.user));

            // Redirect to onboarding
            router.push("/");
        } catch (err: any) {
            console.error("Auth error:", err);
            setError(err.response?.data?.detail || "Authentication failed. Please try again.");
            setLoading(false);
        }
    };

    const handleSocialAuth = (provider: string) => {
        // Placeholder for social auth
        alert(`${provider} authentication coming soon!`);
    };

    const isFormValid = () => {
        if (mode === "signup") {
            return formData.email && formData.password && formData.name && formData.password.length >= 6;
        }
        return formData.email && formData.password;
    };

    return (
        <div className="flex min-h-screen bg-gradient-to-br from-zinc-50 via-white to-zinc-100">
            {/* Left side - Simple & Sleek */}
            <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-gradient-to-br from-slate-900 to-slate-800 text-white p-12 flex-col justify-between">
                {/* Subtle grid pattern */}
                <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAxMCAwIEwgMCAwIDAgMTAiIGZpbGw9Im5vbmUiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS1vcGFjaXR5PSIwLjAzIiBzdHJva2Utd2lkdGg9IjEiLz48L3BhdHRlcm4+PC9kZWZzPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InVybCgjZ3JpZCkiLz48L3N2Zz4=')] opacity-50" />

                {/* Header */}
                <div className="relative z-10">
                    <h1 className="text-6xl font-bold tracking-tight mb-4">Acorn</h1>
                    <p className="text-lg text-white/60 max-w-md">
                        AI-powered customer support for your business
                    </p>
                </div>

                {/* Simple feature list */}
                <div className="relative z-10 space-y-4">
                    <div className="flex items-center gap-3 text-white/80">
                        <div className="w-1.5 h-1.5 rounded-full bg-white/60" />
                        <span>Deploy in minutes</span>
                    </div>
                    <div className="flex items-center gap-3 text-white/80">
                        <div className="w-1.5 h-1.5 rounded-full bg-white/60" />
                        <span>Trained on your content</span>
                    </div>
                    <div className="flex items-center gap-3 text-white/80">
                        <div className="w-1.5 h-1.5 rounded-full bg-white/60" />
                        <span>24/7 availability</span>
                    </div>
                </div>
            </div>

            {/* Right side - Auth Form */}
            <div className="flex-1 flex items-center justify-center p-8">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="w-full max-w-md"
                >
                    <div className="text-center mb-8">
                        <h2 className="text-3xl font-bold tracking-tight mb-2">
                            {mode === "signup" ? "Create your account" : "Welcome back"}
                        </h2>
                        <p className="text-zinc-600">
                            {mode === "signup"
                                ? "Start building your AI agent today"
                                : "Sign in to continue to your dashboard"}
                        </p>
                    </div>

                    {/* Social Auth Buttons */}
                    <div className="space-y-3 mb-6">
                        <Button
                            type="button"
                            variant="outline"
                            className="w-full h-12 text-base"
                            onClick={() => handleSocialAuth("Google")}
                        >
                            <Chrome className="mr-2 h-5 w-5" />
                            Continue with Google
                        </Button>
                        <Button
                            type="button"
                            variant="outline"
                            className="w-full h-12 text-base"
                            onClick={() => handleSocialAuth("GitHub")}
                        >
                            <Github className="mr-2 h-5 w-5" />
                            Continue with GitHub
                        </Button>
                    </div>

                    <div className="relative mb-6">
                        <div className="absolute inset-0 flex items-center">
                            <div className="w-full border-t border-zinc-200" />
                        </div>
                        <div className="relative flex justify-center text-sm">
                            <span className="px-4 bg-white text-zinc-500">Or continue with email</span>
                        </div>
                    </div>

                    {/* Auth Form */}
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <AnimatePresence mode="wait">
                            {error && (
                                <motion.div
                                    initial={{ opacity: 0, height: 0 }}
                                    animate={{ opacity: 1, height: "auto" }}
                                    exit={{ opacity: 0, height: 0 }}
                                    className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg text-sm"
                                >
                                    {error}
                                </motion.div>
                            )}
                        </AnimatePresence>

                        {mode === "signup" && (
                            <div className="space-y-2">
                                <label className="text-sm font-medium text-zinc-700">
                                    Full Name
                                </label>
                                <div className="relative">
                                    <User className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-zinc-400" />
                                    <Input
                                        type="text"
                                        placeholder="John Doe"
                                        value={formData.name}
                                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                        className="pl-10 h-12 text-base"
                                        required
                                    />
                                </div>
                            </div>
                        )}

                        <div className="space-y-2">
                            <label className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
                                Email
                            </label>
                            <div className="relative">
                                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-zinc-400" />
                                <Input
                                    type="email"
                                    placeholder="you@example.com"
                                    value={formData.email}
                                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                    className="pl-10 h-12 text-base"
                                    required
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
                                Password
                            </label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-zinc-400" />
                                <Input
                                    type="password"
                                    placeholder={mode === "signup" ? "At least 6 characters" : "Enter your password"}
                                    value={formData.password}
                                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                                    className="pl-10 h-12 text-base"
                                    required
                                    minLength={mode === "signup" ? 6 : undefined}
                                />
                            </div>
                        </div>

                        <Button
                            type="submit"
                            className="w-full h-12 text-base font-medium"
                            disabled={!isFormValid() || loading}
                        >
                            {loading ? (
                                <>
                                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                                    {mode === "signup" ? "Creating account..." : "Signing in..."}
                                </>
                            ) : (
                                <>
                                    {mode === "signup" ? "Create account" : "Sign in"}
                                    <ArrowRight className="ml-2 h-5 w-5" />
                                </>
                            )}
                        </Button>
                    </form>

                    {/* Toggle Mode */}
                    <div className="mt-6 text-center">
                        <button
                            type="button"
                            onClick={() => {
                                setMode(mode === "signup" ? "login" : "signup");
                                setError("");
                            }}
                            className="text-sm text-zinc-600 hover:text-black transition-colors"
                        >
                            {mode === "signup" ? (
                                <>
                                    Already have an account?{" "}
                                    <span className="font-semibold underline">Sign in</span>
                                </>
                            ) : (
                                <>
                                    Don't have an account?{" "}
                                    <span className="font-semibold underline">Sign up</span>
                                </>
                            )}
                        </button>
                    </div>
                </motion.div>
            </div>
        </div>
    );
}
