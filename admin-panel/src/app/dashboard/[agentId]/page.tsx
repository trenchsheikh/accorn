"use client";

import { useState, useEffect, useRef } from "react";
import { useParams } from "next/navigation";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import { Loader2, Send, Copy, Check, Bot, User, Globe, Code } from "lucide-react";

interface ScrapeStatus {
    status: "pending" | "scraping" | "ready" | "failed";
    pages_scraped: number;
    total_pages: number;
    logs?: any[];
}

interface Message {
    role: "user" | "agent";
    content: string;
}

export default function Dashboard() {
    const params = useParams();
    const agentId = params.agentId as string;

    const [status, setStatus] = useState<ScrapeStatus | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [chatLoading, setChatLoading] = useState(false);
    const [copied, setCopied] = useState(false);

    const scrollAreaRef = useRef<HTMLDivElement>(null);

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

    // Scroll to bottom of chat
    useEffect(() => {
        if (scrollAreaRef.current) {
            const scrollContainer = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]');
            if (scrollContainer) {
                scrollContainer.scrollTop = scrollContainer.scrollHeight;
            }
        }
    }, [messages]);

    const handleSendMessage = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim()) return;

        const userMsg = input;
        setMessages(prev => [...prev, { role: "user", content: userMsg }]);
        setInput("");
        setChatLoading(true);

        try {
            // Use fetch for streaming response if possible, but for now simple POST
            // The backend supports streaming but axios is easier for simple text first
            // Let's use fetch to handle the stream properly if we want, or just wait for full response
            // The backend returns NDJSON stream. Let's try to handle it or just use a simple non-streaming approach if backend supports it?
            // The backend code shows it returns StreamingResponse. 
            // Let's implement a simple reader for the stream.

            const response = await fetch(`http://127.0.0.1:8000/v1/agents/${agentId}/query`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query: userMsg }),
            });

            if (!response.body) throw new Error("No response body");

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let agentMsg = "";

            // Add empty agent message to start
            setMessages(prev => [...prev, { role: "agent", content: "" }]);

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split("\n");

                for (const line of lines) {
                    if (!line.trim()) continue;
                    try {
                        const data = JSON.parse(line);
                        if (data.type === "text") {
                            agentMsg += data.content;
                            setMessages(prev => {
                                const newMsgs = [...prev];
                                newMsgs[newMsgs.length - 1].content = agentMsg;
                                return newMsgs;
                            });
                        }
                    } catch (e) {
                        console.error("Error parsing chunk:", e);
                    }
                }
            }

        } catch (error) {
            console.error("Error sending message:", error);
            setMessages(prev => [...prev, { role: "agent", content: "Error: Could not get response from agent." }]);
        } finally {
            setChatLoading(false);
        }
    };

    const copyEmbedCode = () => {
        const code = `<script src="http://127.0.0.1:8000/widget.js" data-agent="${agentId}" async></script>`;
        navigator.clipboard.writeText(code);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const getStatusColor = (s: string) => {
        switch (s) {
            case "ready": return "bg-green-500";
            case "scraping": return "bg-yellow-500";
            case "failed": return "bg-red-500";
            default: return "bg-gray-500";
        }
    };

    return (
        <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950 p-8">
            <div className="max-w-5xl mx-auto space-y-8">
                <div className="flex justify-between items-center">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight">Agent Dashboard</h1>
                        <p className="text-muted-foreground">Manage and test your AI agent</p>
                    </div>
                    <div className="flex items-center gap-2">
                        <Badge variant="outline" className="text-sm py-1 px-3">
                            ID: {agentId.slice(0, 8)}...
                        </Badge>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Status Card */}
                    <Card className="md:col-span-1 h-fit">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Globe className="h-5 w-5" />
                                Status
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="flex items-center justify-between">
                                <span className="font-medium capitalize">{status?.status || "Loading..."}</span>
                                <div className={`h-3 w-3 rounded-full ${getStatusColor(status?.status || "")}`} />
                            </div>

                            {status?.status === "scraping" && (
                                <div className="space-y-2">
                                    <div className="flex justify-between text-xs text-muted-foreground">
                                        <span>Scraping pages...</span>
                                        <span>{status.pages_scraped} / {status.total_pages || "?"}</span>
                                    </div>
                                    <Progress value={status.total_pages ? (status.pages_scraped / status.total_pages) * 100 : 0} />
                                </div>
                            )}

                            {status?.status === "ready" && (
                                <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-md text-sm text-green-700 dark:text-green-300">
                                    Agent is ready to answer questions!
                                </div>
                            )}

                            <Separator />

                            <div className="space-y-2">
                                <h3 className="text-sm font-medium">Live Scraping Logs</h3>
                                <ScrollArea className="h-[300px] w-full rounded-md border p-2 bg-black text-xs font-mono text-green-400">
                                    {status?.logs && status.logs.length > 0 ? (
                                        <div className="space-y-1">
                                            {status.logs.map((log: any, i: number) => (
                                                <div key={i} className="flex gap-2">
                                                    <span className="text-zinc-500">[{new Date(log.timestamp).toLocaleTimeString()}]</span>
                                                    <span className={log.type === "error" ? "text-red-400" : log.type === "success" ? "text-green-400" : "text-zinc-300"}>
                                                        {log.message}
                                                    </span>
                                                </div>
                                            ))}
                                        </div>
                                    ) : (
                                        <div className="text-zinc-500 italic">Waiting for logs...</div>
                                    )}
                                </ScrollArea>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Main Content Tabs */}
                    <div className="md:col-span-2">
                        <Tabs defaultValue="test" className="w-full">
                            <TabsList className="grid w-full grid-cols-2">
                                <TabsTrigger value="test">Test Agent</TabsTrigger>
                                <TabsTrigger value="embed">Embed</TabsTrigger>
                            </TabsList>

                            <TabsContent value="test" className="mt-4">
                                <Card className="h-[600px] flex flex-col">
                                    <CardHeader>
                                        <CardTitle className="flex items-center gap-2">
                                            <Bot className="h-5 w-5" />
                                            Test Playground
                                        </CardTitle>
                                        <CardDescription>
                                            Chat with your agent to verify its knowledge base.
                                        </CardDescription>
                                    </CardHeader>
                                    <CardContent className="flex-1 overflow-hidden p-0">
                                        <ScrollArea className="h-full p-4" ref={scrollAreaRef}>
                                            <div className="space-y-4">
                                                {messages.length === 0 && (
                                                    <div className="text-center text-muted-foreground py-10">
                                                        <Bot className="h-12 w-12 mx-auto mb-4 opacity-20" />
                                                        <p>Start a conversation to test your agent.</p>
                                                    </div>
                                                )}
                                                {messages.map((msg, i) => (
                                                    <div
                                                        key={i}
                                                        className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                                                    >
                                                        <div
                                                            className={`flex gap-2 max-w-[80%] ${msg.role === "user" ? "flex-row-reverse" : "flex-row"
                                                                }`}
                                                        >
                                                            <Avatar className="h-8 w-8">
                                                                <AvatarFallback className={msg.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"}>
                                                                    {msg.role === "user" ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                                                                </AvatarFallback>
                                                            </Avatar>
                                                            <div
                                                                className={`rounded-lg p-3 text-sm ${msg.role === "user"
                                                                    ? "bg-primary text-primary-foreground"
                                                                    : "bg-muted"
                                                                    }`}
                                                            >
                                                                {msg.content}
                                                            </div>
                                                        </div>
                                                    </div>
                                                ))}
                                                {chatLoading && (
                                                    <div className="flex justify-start">
                                                        <div className="flex gap-2 max-w-[80%]">
                                                            <Avatar className="h-8 w-8">
                                                                <AvatarFallback className="bg-muted">
                                                                    <Bot className="h-4 w-4" />
                                                                </AvatarFallback>
                                                            </Avatar>
                                                            <div className="bg-muted rounded-lg p-3 flex items-center">
                                                                <Loader2 className="h-4 w-4 animate-spin" />
                                                            </div>
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        </ScrollArea>
                                    </CardContent>
                                    <Separator />
                                    <CardFooter className="p-4">
                                        <form onSubmit={handleSendMessage} className="flex w-full gap-2">
                                            <Input
                                                placeholder="Ask a question..."
                                                value={input}
                                                onChange={(e) => setInput(e.target.value)}
                                                disabled={chatLoading}
                                            />
                                            <Button type="submit" size="icon" disabled={chatLoading || !input.trim()}>
                                                <Send className="h-4 w-4" />
                                            </Button>
                                        </form>
                                    </CardFooter>
                                </Card>
                            </TabsContent>

                            <TabsContent value="embed" className="mt-4">
                                <Card>
                                    <CardHeader>
                                        <CardTitle className="flex items-center gap-2">
                                            <Code className="h-5 w-5" />
                                            Embed Code
                                        </CardTitle>
                                        <CardDescription>
                                            Copy and paste this code into your website's HTML to add the agent widget.
                                        </CardDescription>
                                    </CardHeader>
                                    <CardContent className="space-y-4">
                                        <div className="relative rounded-md bg-muted p-4 font-mono text-sm">
                                            <code className="break-all">
                                                {`<script src="http://127.0.0.1:8000/widget.js" data-agent="${agentId}" async></script>`}
                                            </code>
                                            <Button
                                                size="icon"
                                                variant="ghost"
                                                className="absolute right-2 top-2 h-8 w-8"
                                                onClick={copyEmbedCode}
                                            >
                                                {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                                            </Button>
                                        </div>
                                        <div className="rounded-md bg-blue-50 dark:bg-blue-900/20 p-4 text-sm text-blue-700 dark:text-blue-300">
                                            <p className="font-semibold mb-1">Installation Instructions:</p>
                                            <ol className="list-decimal list-inside space-y-1">
                                                <li>Copy the code snippet above.</li>
                                                <li>Paste it before the closing <code>&lt;/body&gt;</code> tag of your website.</li>
                                                <li>The widget will appear in the bottom right corner.</li>
                                            </ol>
                                        </div>
                                    </CardContent>
                                </Card>
                            </TabsContent>
                        </Tabs>
                    </div>
                </div>
            </div>
        </div>
    );
}
