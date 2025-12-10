"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Search, Filter, Download } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

const logs = [
    { id: "CONV-001", date: "2024-03-10 14:30", visitor: "User #4567", duration: "3m 12s", status: "resolved", sentiment: "positive" },
    { id: "CONV-002", date: "2024-03-10 13:15", visitor: "User #6543", duration: "1m 45s", status: "resolved", sentiment: "neutral" },
    { id: "CONV-003", date: "2024-03-10 11:20", visitor: "User #7890", duration: "0m 30s", status: "abandoned", sentiment: "n/a" },
    { id: "CONV-004", date: "2024-03-09 16:45", visitor: "User #5678", duration: "5m 10s", status: "resolved", sentiment: "positive" },
    { id: "CONV-005", date: "2024-03-09 09:10", visitor: "User #5432", duration: "2m 05s", status: "resolved", sentiment: "negative" },
];

export default function LogsPage() {
    return (
        <div className="p-8 space-y-8 h-full overflow-y-auto">
            <div className="flex items-center justify-between">
                <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Conversation Logs</h1>
                <div className="flex gap-2">
                    <Button variant="outline" className="bg-white/40 border-white/40 hover:bg-white/60">
                        <Download className="w-4 h-4 mr-2" />
                        Export
                    </Button>
                </div>
            </div>

            {/* Filters */}
            <div className="flex gap-4">
                <div className="relative flex-1 max-w-sm">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                    <Input
                        placeholder="Search logs..."
                        className="pl-9 bg-white/40 border-white/40 focus-visible:ring-blue-500/50"
                    />
                </div>
                <Button variant="outline" className="bg-white/40 border-white/40 hover:bg-white/60">
                    <Filter className="w-4 h-4 mr-2" />
                    Filter
                </Button>
            </div>

            {/* Logs Table */}
            <Card className="bg-white/40 backdrop-blur-xl border-white/40 shadow-lg overflow-hidden">
                <CardContent className="p-0">
                    <div className="w-full overflow-auto">
                        <table className="w-full text-sm text-left">
                            <thead className="text-xs text-slate-500 uppercase bg-white/20 border-b border-white/20">
                                <tr>
                                    <th className="px-6 py-4 font-medium">Conversation ID</th>
                                    <th className="px-6 py-4 font-medium">Date & Time</th>
                                    <th className="px-6 py-4 font-medium">Visitor</th>
                                    <th className="px-6 py-4 font-medium">Duration</th>
                                    <th className="px-6 py-4 font-medium">Status</th>
                                    <th className="px-6 py-4 font-medium">Sentiment</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-white/20">
                                {logs.map((log) => (
                                    <tr key={log.id} className="hover:bg-white/20 transition-colors">
                                        <td className="px-6 py-4 font-medium text-slate-900">{log.id}</td>
                                        <td className="px-6 py-4 text-slate-600">{log.date}</td>
                                        <td className="px-6 py-4 text-slate-600">{log.visitor}</td>
                                        <td className="px-6 py-4 text-slate-600">{log.duration}</td>
                                        <td className="px-6 py-4">
                                            <Badge variant="outline" className={`
                                        ${log.status === 'resolved' ? 'bg-green-100 text-green-700 border-green-200' : ''}
                                        ${log.status === 'abandoned' ? 'bg-red-100 text-red-700 border-red-200' : ''}
                                    `}>
                                                {log.status}
                                            </Badge>
                                        </td>
                                        <td className="px-6 py-4">
                                            {log.sentiment !== 'n/a' && (
                                                <div className={`flex items-center gap-1 font-medium
                                            ${log.sentiment === 'positive' ? 'text-green-600' : ''}
                                            ${log.sentiment === 'neutral' ? 'text-slate-600' : ''}
                                            ${log.sentiment === 'negative' ? 'text-red-600' : ''}
                                        `}>
                                                    {log.sentiment === 'positive' && '😊'}
                                                    {log.sentiment === 'neutral' && '😐'}
                                                    {log.sentiment === 'negative' && 'jq'}
                                                    <span className="capitalize">{log.sentiment}</span>
                                                </div>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
