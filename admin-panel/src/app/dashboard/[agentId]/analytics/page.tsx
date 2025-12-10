"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { ArrowUpRight, ArrowDownRight, Users, MessageSquare, Clock, Activity } from "lucide-react";

const data = [
    { name: "Mon", conversations: 40 },
    { name: "Tue", conversations: 30 },
    { name: "Wed", conversations: 20 },
    { name: "Thu", conversations: 27 },
    { name: "Fri", conversations: 18 },
    { name: "Sat", conversations: 23 },
    { name: "Sun", conversations: 34 },
];

export default function AnalyticsPage() {
    return (
        <div className="p-8 space-y-8 h-full overflow-y-auto">
            <div className="flex items-center justify-between">
                <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Analytics</h1>
                <div className="text-sm text-slate-500">Last 7 Days</div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {[
                    { title: "Total Conversations", value: "1,234", change: "+12%", icon: MessageSquare, trend: "up" },
                    { title: "Avg Duration", value: "2m 14s", change: "-5%", icon: Clock, trend: "down" },
                    { title: "Active Visitors", value: "892", change: "+8%", icon: Users, trend: "up" },
                    { title: "Resolution Rate", value: "98.5%", change: "+1%", icon: Activity, trend: "up" },
                ].map((stat, i) => (
                    <Card key={i} className="bg-white/40 backdrop-blur-xl border-white/40 shadow-lg hover:shadow-xl transition-all">
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium text-slate-600">
                                {stat.title}
                            </CardTitle>
                            <stat.icon className="h-4 w-4 text-slate-400" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-slate-900">{stat.value}</div>
                            <p className={`text-xs flex items-center mt-1 ${stat.trend === 'up' ? 'text-green-600' : 'text-red-600'}`}>
                                {stat.trend === 'up' ? <ArrowUpRight className="h-3 w-3 mr-1" /> : <ArrowDownRight className="h-3 w-3 mr-1" />}
                                {stat.change} from last week
                            </p>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {/* Charts Area */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <Card className="bg-white/40 backdrop-blur-xl border-white/40 shadow-lg col-span-1 lg:col-span-2">
                    <CardHeader>
                        <CardTitle className="text-slate-800">Conversation Volume</CardTitle>
                    </CardHeader>
                    <CardContent className="pl-2">
                        <div className="h-[300px] w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={data}>
                                    <XAxis
                                        dataKey="name"
                                        stroke="#888888"
                                        fontSize={12}
                                        tickLine={false}
                                        axisLine={false}
                                    />
                                    <YAxis
                                        stroke="#888888"
                                        fontSize={12}
                                        tickLine={false}
                                        axisLine={false}
                                        tickFormatter={(value) => `${value}`}
                                    />
                                    <Tooltip
                                        cursor={{ fill: 'transparent' }}
                                        contentStyle={{ backgroundColor: 'rgba(255, 255, 255, 0.8)', borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                    />
                                    <Bar dataKey="conversations" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
