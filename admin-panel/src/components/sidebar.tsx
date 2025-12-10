"use client";

import Link from "next/link";
import { useParams, usePathname } from "next/navigation";
import { Bot, BarChart2, Settings, FileText, LogOut, User } from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

export function Sidebar() {
    const pathname = usePathname();
    const params = useParams();
    const agentId = params.agentId as string;

    const links = [
        { href: `/dashboard/${agentId}`, label: "Agent", icon: Bot, active: pathname === `/dashboard/${agentId}` },
        { href: `/dashboard/${agentId}/analytics`, label: "Analytics", icon: BarChart2, active: pathname === `/dashboard/${agentId}/analytics` },
        { href: `/dashboard/${agentId}/logs`, label: "Logs", icon: FileText, active: pathname === `/dashboard/${agentId}/logs` },
        { href: `/dashboard/${agentId}/settings`, label: "Settings", icon: Settings, active: pathname === `/dashboard/${agentId}/settings` },
    ];

    return (
        <div className="h-full w-64 flex flex-col border-r border-white/20 bg-white/10 backdrop-blur-xl text-slate-900 shadow-xl z-20">
            {/* Logo */}
            <div className="p-6 flex items-center gap-3">
                <div className="h-8 w-8 rounded-full bg-black text-white flex items-center justify-center font-bold shadow-lg">
                    A
                </div>
                <span className="font-bold text-lg tracking-tight">Acorn</span>
            </div>

            {/* Navigation */}
            <nav className="flex-1 px-4 space-y-2 mt-4">
                {links.map((link) => (
                    <Link
                        key={link.label}
                        href={link.href}
                        className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group ${link.active
                            ? "bg-white/40 shadow-sm font-medium text-slate-900"
                            : "text-slate-600 hover:bg-white/20 hover:text-slate-900"
                            }`}
                    >
                        <link.icon className={`w-5 h-5 ${link.active ? "text-blue-600" : "text-slate-500 group-hover:text-slate-700"}`} />
                        {link.label}
                    </Link>
                ))}
            </nav>

            {/* User Profile */}
            <div className="p-4 border-t border-white/20 bg-white/5">
                <div className="flex items-center gap-3 p-2 rounded-xl hover:bg-white/20 cursor-pointer transition-colors">
                    <Avatar className="h-9 w-9 border border-white/30 shadow-sm">
                        <AvatarFallback className="bg-gradient-to-br from-blue-500 to-purple-500 text-white">
                            <User className="w-4 h-4" />
                        </AvatarFallback>
                    </Avatar>
                    <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-slate-900 truncate">Admin User</p>
                        <p className="text-xs text-slate-500 truncate">admin@acorn.ai</p>
                    </div>
                    <LogOut className="w-4 h-4 text-slate-400 hover:text-red-500 transition-colors" />
                </div>
            </div>
        </div>
    );
}
