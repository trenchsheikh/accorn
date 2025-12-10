import { Sidebar } from "@/components/sidebar";

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="flex h-screen w-full overflow-hidden bg-slate-50 relative font-sans">
            {/* Global Background Gradients */}
            <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-blue-200/40 rounded-full blur-[120px] pointer-events-none" />
            <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-purple-200/40 rounded-full blur-[120px] pointer-events-none" />
            <div className="absolute top-[40%] left-[40%] w-[30%] h-[30%] bg-indigo-200/30 rounded-full blur-[100px] pointer-events-none" />

            {/* Sidebar */}
            <Sidebar />

            {/* Main Content Area */}
            <main className="flex-1 h-full overflow-hidden relative z-10">
                {children}
            </main>
        </div>
    );
}
