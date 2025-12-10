"use client";

import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Save, Trash2, Code, Copy, CheckCircle2, AlertTriangle } from "lucide-react";
import { useState } from "react";

export default function SettingsPage() {
    const params = useParams();
    const agentId = params.agentId as string;
    const [copied, setCopied] = useState(false);

    const handleCopy = () => {
        navigator.clipboard.writeText(
            `<script src="http://127.0.0.1:8000/widget.js" data-agent-id="${agentId}" data-base-url="http://127.0.0.1:8000"></script>`
        );
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="h-full overflow-y-auto">
            <div className="max-w-7xl mx-auto p-8 space-y-6">
                {/* Header */}
                <div className="space-y-1">
                    <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Settings</h1>
                    <p className="text-slate-500">Manage your agent configuration and integration</p>
                </div>

                {/* Grid Layout */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Embed Script */}
                    <Card className="bg-white/50 backdrop-blur-xl border-white/50 shadow-xl overflow-hidden lg:col-span-2 p-0">
                        <div className="bg-gradient-to-r from-blue-500/5 to-purple-500/5 border-b border-white/30 p-4">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-blue-500/10 rounded-lg">
                                        <Code className="w-5 h-5 text-blue-600" />
                                    </div>
                                    <div>
                                        <h3 className="text-base font-semibold text-slate-900">Widget Embed Code</h3>
                                        <p className="text-xs text-slate-500 mt-0.5">
                                            Add this script to your website to enable the chat widget
                                        </p>
                                    </div>
                                </div>
                                <Button
                                    className={`transition-all ${copied
                                        ? "bg-green-500 hover:bg-green-600"
                                        : "bg-blue-600 hover:bg-blue-700"
                                        } text-white shadow-lg`}
                                    onClick={handleCopy}
                                >
                                    {copied ? (
                                        <>
                                            <CheckCircle2 className="h-4 w-4 mr-2" />
                                            Copied!
                                        </>
                                    ) : (
                                        <>
                                            <Copy className="h-4 w-4 mr-2" />
                                            Copy Code
                                        </>
                                    )}
                                </Button>
                            </div>
                        </div>
                        <CardContent className="p-6">
                            <pre className="bg-slate-900 text-slate-100 p-4 rounded-lg text-sm overflow-x-auto border border-slate-700 shadow-inner font-mono">
                                {`<script 
  src="http://127.0.0.1:8000/widget.js" 
  data-agent-id="${agentId}" 
  data-base-url="http://127.0.0.1:8000">
</script>`}
                            </pre>
                            <p className="text-xs text-slate-600 mt-3">
                                Paste this code before the closing <code className="bg-slate-100 px-1.5 py-0.5 rounded text-xs font-mono border border-slate-200">&lt;/body&gt;</code> tag on your website.
                            </p>
                        </CardContent>
                    </Card>

                    {/* Agent Configuration */}
                    <Card className="bg-white/50 backdrop-blur-xl border-white/50 shadow-xl overflow-hidden p-0">
                        <div className="bg-slate-50/50 border-b border-white/30 p-4">
                            <h3 className="text-base font-semibold text-slate-900">Agent Configuration</h3>
                            <p className="text-xs text-slate-500 mt-0.5">
                                Manage your agent's basic information
                            </p>
                        </div>
                        <CardContent className="p-6 space-y-5">
                            <div className="space-y-2.5">
                                <Label htmlFor="agentName" className="text-sm font-medium text-slate-700">
                                    Agent Name
                                </Label>
                                <Input
                                    id="agentName"
                                    defaultValue="Acorn Receptionist"
                                    className="h-10 bg-white/60 border-white/60 focus:border-blue-400 focus:ring-blue-400/20"
                                />
                            </div>
                            <div className="space-y-2.5">
                                <Label htmlFor="agentId" className="text-sm font-medium text-slate-700">
                                    Agent ID
                                </Label>
                                <Input
                                    id="agentId"
                                    value={agentId}
                                    disabled
                                    className="h-10 bg-slate-100/50 border-white/60 text-slate-500 cursor-not-allowed font-mono text-sm"
                                />
                            </div>

                            <Separator className="bg-white/40" />

                            <div className="flex justify-end">
                                <Button className="bg-blue-600 hover:bg-blue-700 text-white shadow-lg">
                                    <Save className="w-4 h-4 mr-2" />
                                    Save Changes
                                </Button>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Danger Zone */}
                    <Card className="bg-red-50/60 backdrop-blur-xl border-red-200/60 shadow-xl overflow-hidden p-0">
                        <div className="bg-red-100/40 border-b border-red-200/60 p-4">
                            <div className="flex items-center gap-2">
                                <div className="p-2 bg-red-500/10 rounded-lg">
                                    <AlertTriangle className="w-4 h-4 text-red-600" />
                                </div>
                                <div>
                                    <h3 className="text-base font-semibold text-red-700">Danger Zone</h3>
                                    <p className="text-xs text-red-600/80 mt-0.5">
                                        Irreversible and destructive actions
                                    </p>
                                </div>
                            </div>
                        </div>
                        <CardContent className="p-6">
                            <div className="space-y-3">
                                <div>
                                    <p className="font-semibold text-slate-900">Delete Agent</p>
                                    <p className="text-sm text-slate-600 mt-1">
                                        Permanently delete this agent and all its data. This action cannot be undone.
                                    </p>
                                </div>
                                <Button
                                    variant="destructive"
                                    className="w-full bg-red-600 hover:bg-red-700 shadow-lg"
                                >
                                    <Trash2 className="w-4 h-4 mr-2" />
                                    Delete Agent
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
