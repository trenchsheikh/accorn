"use client";

import { useState, useEffect, useRef } from "react";
import { useParams } from "next/navigation";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Loader2, Mic, Send, Sparkles, Check, X, ArrowRight, Bot, User, MicOff, Code, Copy } from "lucide-react";

interface ScrapeStatus {
    status: "pending" | "scraping" | "ready" | "failed";
    pages_scraped: number;
    total_pages: number;
    logs?: any[];
}

interface Voice {
    id: string;
    name: string;
}

interface ProposedChanges {
    voice_id?: string;
    personality?: string;
}

interface AdminResponse {
    reply: string;
    audio_base64?: string;
    proposed_changes?: ProposedChanges;
    voice_options?: Voice[];
}

const VOICES = [
    { id: "21m00Tcm4TlvDq8ikWAM", name: "Bella (American, Soft)" },
    { id: "AZnzlk1XvdvUeBnXmlld", name: "Domi (American, Strong)" },
    { id: "EXAVITQu4vr4xnSDxMaL", name: "Bella (British, Professional)" },
    { id: "ErXwobaYiN019PkySvjV", "name": "Antoni (American, Deep)" },
    { id: "MF3mGyEYCl7XYWbV9V6O", "name": "Elli (American, Young)" },
    { id: "TxGEqnHWrfWFTfGW9XjX", "name": "Josh (American, Deep)" },
    { id: "VR6AewLTigWg4xSOukaG", "name": "Arnold (American, Crisp)" },
    { id: "pNInz6obpgDQGcFmaJgB", "name": "Adam (American, Deep)" },
    { id: "yoZ06aMxZJJ28mfd3POQ", "name": "Sam (American, Raspy)" },
];

export default function Dashboard() {
    const params = useParams();
    const agentId = params.agentId as string;

    const [status, setStatus] = useState<ScrapeStatus | null>(null);
    const [input, setInput] = useState("");
    const [isListening, setIsListening] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);

    // Admin Agent State
    const [adminReply, setAdminReply] = useState<string>("Hi! I'm your Agent Configurator. How can I help you today?");
    const [proposedChanges, setProposedChanges] = useState<ProposedChanges | null>(null);
    const [voiceOptions, setVoiceOptions] = useState<Voice[] | null>(null);
    const [isPlayingAudio, setIsPlayingAudio] = useState(false);
    const [playingPreviewId, setPlayingPreviewId] = useState<string | null>(null);

    // Audio Context
    const audioContextRef = useRef<AudioContext | null>(null);
    const recognitionRef = useRef<any>(null);

    // Poll status
    useEffect(() => {
        const fetchStatus = async () => {
            try {
                const res = await axios.get(`http://127.0.0.1:8000/v1/agents/${agentId}/status`);
                setStatus(res.data);
            } catch (error) {
                console.error("Error fetching status:", error);
            }
        };
        fetchStatus();
        const interval = setInterval(fetchStatus, 5000);
        return () => clearInterval(interval);
    }, [agentId]);

    // Setup Speech Recognition
    useEffect(() => {
        if (typeof window !== "undefined" && 'webkitSpeechRecognition' in window) {
            const recognition = new (window as any).webkitSpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;

            recognition.onstart = () => setIsListening(true);
            recognition.onend = () => setIsListening(false);
            recognition.onresult = (event: any) => {
                const transcript = event.results[0][0].transcript;
                setInput(transcript);
                handleSendIntent(transcript);
            };

            recognitionRef.current = recognition;
        }
    }, []);

    const toggleListening = () => {
        if (isListening) {
            recognitionRef.current?.stop();
        } else {
            recognitionRef.current?.start();
        }
    };

    const playAudio = async (base64: string, isPreview = false) => {
        if (!audioContextRef.current) {
            audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
        }

        try {
            const binaryString = window.atob(base64);
            const len = binaryString.length;
            const bytes = new Uint8Array(len);
            for (let i = 0; i < len; i++) bytes[i] = binaryString.charCodeAt(i);

            const buffer = await audioContextRef.current.decodeAudioData(bytes.buffer);
            const source = audioContextRef.current.createBufferSource();
            source.buffer = buffer;
            source.connect(audioContextRef.current.destination);

            if (!isPreview) setIsPlayingAudio(true);
            source.onended = () => {
                if (!isPreview) setIsPlayingAudio(false);
                if (isPreview) setPlayingPreviewId(null);
            };
            source.start(0);
        } catch (e) {
            console.error("Error playing audio", e);
            setPlayingPreviewId(null);
        }
    };

    const handleSendIntent = async (text: string = input) => {
        if (!text.trim()) return;

        setIsProcessing(true);
        setProposedChanges(null); // Reset previous proposals
        setVoiceOptions(null); // Reset voice options

        try {
            const res = await axios.post<AdminResponse>(`http://127.0.0.1:8000/v1/admin/intent`, {
                text: text,
                agent_id: agentId
            });

            setAdminReply(res.data.reply);
            if (res.data.proposed_changes && Object.keys(res.data.proposed_changes).length > 0) {
                setProposedChanges(res.data.proposed_changes);
            }
            if (res.data.voice_options) {
                setVoiceOptions(res.data.voice_options);
            }

            if (res.data.audio_base64) {
                playAudio(res.data.audio_base64);
            }

            setInput("");
        } catch (error) {
            console.error("Error sending intent:", error);
            setAdminReply("Sorry, I had trouble processing that request.");
        } finally {
            setIsProcessing(false);
        }
    };

    const handlePlayPreview = async (voiceId: string, voiceName: string) => {
        if (playingPreviewId) return; // Prevent multiple plays
        setPlayingPreviewId(voiceId);
        try {
            const res = await axios.post(`http://127.0.0.1:8000/v1/admin/speak`, {
                text: `Hello, I am ${voiceName}.`,
                voice_id: voiceId
            });
            if (res.data.audio_base64) {
                playAudio(res.data.audio_base64, true);
            }
        } catch (error) {
            console.error("Error playing preview:", error);
            setPlayingPreviewId(null);
        }
    };

    const handleConfirmChanges = async () => {
        if (!proposedChanges) return;

        try {
            await axios.patch(`http://127.0.0.1:8000/v1/agents/${agentId}/config`, proposedChanges);
            setAdminReply("Great! I've updated your agent's configuration.");
            setProposedChanges(null);
            // Optionally play a success sound or TTS
        } catch (error) {
            console.error("Error saving config:", error);
            setAdminReply("I encountered an error saving the changes.");
        }
    };

    const getVoiceName = (id: string) => VOICES.find(v => v.id === id)?.name || id;

    return (
        <div className="h-full w-full flex flex-col items-center justify-center p-6 relative overflow-y-auto">
            {/* Main Content: The Orb & Interaction */}
            <div className="flex-1 flex flex-col items-center justify-center w-full max-w-4xl z-10 space-y-12">

                {/* Admin Agent Reply */}
                <div className="text-center space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-700">
                    <h2 className="text-3xl md:text-4xl font-medium text-slate-900 leading-tight tracking-tight drop-shadow-sm">
                        "{adminReply}"
                    </h2>
                </div>

                {/* The Orb (Hidden if showing voice options to save space) */}
                {!voiceOptions && (
                    <div className={`orb-container transition-transform duration-500 ${isPlayingAudio ? 'scale-110' : 'scale-100'}`}>
                        <div className="orb-glow" />
                        <div className={`orb-core ${isPlayingAudio ? 'animate-pulse' : ''}`} />
                    </div>
                )}

                {/* Voice Options Grid */}
                {voiceOptions && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 w-full animate-in zoom-in-95 duration-300">
                        {voiceOptions.map((voice) => (
                            <Card key={voice.id} className="bg-white/40 backdrop-blur-xl border-white/40 shadow-lg hover:shadow-xl hover:bg-white/60 transition-all cursor-pointer group"
                                onClick={() => handleSendIntent(`Change voice to ${voice.name}`)}
                            >
                                <CardContent className="p-4 flex items-center justify-between">
                                    <div className="flex flex-col">
                                        <span className="font-medium text-slate-900">{voice.name}</span>
                                        <span className="text-xs text-slate-600">Click to select</span>
                                    </div>
                                    <Button
                                        size="icon"
                                        variant="ghost"
                                        className="rounded-full hover:bg-white/50 text-blue-600"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            handlePlayPreview(voice.id, voice.name);
                                        }}
                                    >
                                        {playingPreviewId === voice.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                                    </Button>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                )}


                {/* Proposed Changes Bubble */}
                {proposedChanges && (
                    <div className="w-full max-w-md animate-in zoom-in-95 duration-300">
                        <Card className="bg-white/50 backdrop-blur-2xl border-white/50 shadow-2xl overflow-hidden p-0">
                            <div className="bg-gradient-to-r from-purple-500/5 to-blue-500/5 border-b border-white/30 p-4">
                                <div className="flex items-center gap-2.5">
                                    <div className="p-2 bg-purple-500/10 rounded-lg">
                                        <Sparkles className="w-4 h-4 text-purple-600" />
                                    </div>
                                    <h3 className="text-base font-semibold text-slate-900">Proposed Changes</h3>
                                </div>
                            </div>
                            <CardContent className="space-y-3 p-5">
                                {proposedChanges.voice_id && (
                                    <div className="flex items-center justify-between p-3 rounded-lg bg-white/60 border border-white/40">
                                        <span className="text-sm font-medium text-slate-600">Voice</span>
                                        <span className="text-sm font-bold text-slate-900">{getVoiceName(proposedChanges.voice_id)}</span>
                                    </div>
                                )}
                                {proposedChanges.personality && (
                                    <div className="space-y-2">
                                        <span className="text-sm font-medium text-slate-600">Personality</span>
                                        <div className="p-3 rounded-lg bg-white/60 border border-white/40 text-sm text-slate-800 italic">
                                            "{proposedChanges.personality}"
                                        </div>
                                    </div>
                                )}
                            </CardContent>
                            <div className="flex gap-3 p-5 pt-2 border-t border-white/20 bg-white/20">
                                <Button
                                    variant="outline"
                                    className="flex-1 bg-white/60 border-white/50 hover:bg-white/90 text-slate-700"
                                    onClick={() => setProposedChanges(null)}
                                >
                                    <X className="w-4 h-4 mr-2" />
                                    Cancel
                                </Button>
                                <Button
                                    className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white shadow-lg border-0"
                                    onClick={handleConfirmChanges}
                                >
                                    <Check className="w-4 h-4 mr-2" />
                                    Confirm
                                </Button>
                            </div>
                        </Card>
                    </div>
                )}

                {/* Input Area */}
                <div className="w-full max-w-xl relative group">
                    <div className="absolute inset-0 bg-gradient-to-r from-blue-200 to-purple-200 rounded-full blur-xl opacity-20 group-hover:opacity-40 transition-opacity duration-500" />
                    <div className="relative flex items-center gap-2 bg-white/60 backdrop-blur-2xl border border-white/40 rounded-full p-2 shadow-xl hover:shadow-2xl transition-all duration-300">
                        <Input
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => e.key === "Enter" && handleSendIntent()}
                            placeholder="Type a command or say 'Change voice to...'"
                            className="flex-1 border-none bg-transparent shadow-none focus-visible:ring-0 text-slate-800 placeholder:text-slate-500 px-4 h-12 text-lg"
                            disabled={isProcessing}
                        />
                        <Button
                            size="icon"
                            className={`h-12 w-12 rounded-full transition-all duration-300 ${isListening
                                ? "bg-red-500 hover:bg-red-600 shadow-red-200 animate-pulse"
                                : "bg-slate-900 hover:bg-slate-800 text-white shadow-lg"
                                }`}
                            onClick={toggleListening}
                            disabled={isProcessing}
                        >
                            {isListening ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
                        </Button>
                    </div>
                    <div className="text-center mt-3 text-xs text-slate-400 font-medium tracking-wide uppercase">
                        {isProcessing ? "Processing..." : isListening ? "Listening..." : "Ready for command"}
                    </div>
                </div>
            </div>
        </div>
    );
}
