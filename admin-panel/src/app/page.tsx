"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowRight, Loader2, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { useAuth } from "@/contexts/auth-context";

export default function Onboarding() {
  const [step, setStep] = useState(0);
  const [formData, setFormData] = useState({
    name: "",
    url: "",
  });
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const { user, token, isLoading } = useAuth();

  useEffect(() => {
    // Focus input on step change
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, [step]);

  const questions = [
    {
      key: "name",
      question: "What is the name of your business?",
      placeholder: "Acorn Inc.",
      type: "text",
    },
    {
      key: "url",
      question: "What is your website URL?",
      placeholder: "https://example.com",
      type: "url",
    },
  ];

  const handleNext = async () => {
    if (step < questions.length - 1) {
      setStep(step + 1);
    } else {
      await handleSubmit();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && formData[questions[step].key as keyof typeof formData]) {
      handleNext();
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      let formattedUrl = formData.url.trim();
      if (!/^https?:\/\//i.test(formattedUrl)) {
        formattedUrl = `https://${formattedUrl}`;
      }

      const response = await axios.post(
        "http://127.0.0.1:8000/v1/onboard",
        {
          root_url: formattedUrl,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      const agentId = response.data.id;
      router.push(`/dashboard/${agentId}`);
    } catch (error: any) {
      console.error("Error onboarding agent:", error);
      alert(`Failed to create agent: ${error.message || "Unknown error"}`);
      setLoading(false);
    }
  };

  const currentQ = questions[step];
  const progress = ((step + 1) / questions.length) * 100;

  // Show loading while auth is being checked
  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-white">
        <Loader2 className="h-12 w-12 animate-spin text-zinc-400" />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-white font-sans selection:bg-black selection:text-white">
      {/* Progress Bar */}
      <div className="fixed top-0 left-0 h-1 bg-zinc-100 w-full">
        <motion.div
          className="h-full bg-black"
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.5, ease: "easeInOut" }}
        />
      </div>

      <main className="flex-1 flex flex-col items-center justify-center p-8">
        <div className="w-full max-w-2xl">
          <AnimatePresence mode="wait">
            {loading ? (
              <motion.div
                key="loading"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="text-center space-y-6"
              >
                <Loader2 className="h-16 w-16 animate-spin mx-auto text-zinc-400" />
                <h2 className="text-3xl font-light tracking-tight">Creating your agent...</h2>
                <p className="text-zinc-500">This will just take a moment.</p>
              </motion.div>
            ) : (
              <motion.div
                key={step}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3, ease: "easeOut" }}
                className="space-y-8"
              >
                <div className="space-y-2">
                  <span className="text-sm font-medium text-zinc-400 uppercase tracking-wider">
                    Step {step + 1} of {questions.length}
                  </span>
                  <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-black leading-tight">
                    {currentQ.question}
                  </h1>
                </div>

                <div className="relative group">
                  <input
                    ref={inputRef}
                    type={currentQ.type}
                    value={formData[currentQ.key as keyof typeof formData]}
                    onChange={(e) => setFormData({ ...formData, [currentQ.key]: e.target.value })}
                    onKeyDown={handleKeyDown}
                    placeholder={currentQ.placeholder}
                    className="w-full bg-transparent text-3xl md:text-4xl pb-4 border-b-2 border-zinc-200 focus:border-black outline-none transition-colors placeholder:text-zinc-300"
                    autoFocus
                  />
                  <div className="absolute right-0 bottom-4">
                    <Button
                      size="lg"
                      className={cn(
                        "rounded-full h-12 w-12 p-0 transition-all duration-300",
                        formData[currentQ.key as keyof typeof formData]
                          ? "opacity-100 translate-x-0"
                          : "opacity-0 translate-x-4 pointer-events-none"
                      )}
                      onClick={handleNext}
                    >
                      {step === questions.length - 1 ? (
                        <Check className="h-6 w-6" />
                      ) : (
                        <ArrowRight className="h-6 w-6" />
                      )}
                    </Button>
                  </div>
                </div>

                <div className="flex items-center gap-2 text-sm text-zinc-400">
                  <span className="bg-zinc-100 px-2 py-1 rounded text-xs font-mono">Enter</span>
                  <span>to continue</span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}
