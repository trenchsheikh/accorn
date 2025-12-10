"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { useRouter, usePathname } from "next/navigation";
import axios from "axios";

interface User {
    id: string;
    email: string;
    name: string;
    created_at: string;
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    login: (email: string, password: string) => Promise<void>;
    signup: (email: string, password: string, name: string) => Promise<void>;
    logout: () => void;
    isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const router = useRouter();
    const pathname = usePathname();

    useEffect(() => {
        // Load user from localStorage on mount
        const storedToken = localStorage.getItem("auth_token");
        const storedUser = localStorage.getItem("user");

        if (storedToken && storedUser) {
            setToken(storedToken);
            setUser(JSON.parse(storedUser));
        }
        setIsLoading(false);
    }, []);

    const login = async (email: string, password: string) => {
        const response = await axios.post("http://127.0.0.1:8000/v1/auth/login", {
            email,
            password,
        });

        const { access_token, user: userData } = response.data;
        localStorage.setItem("auth_token", access_token);
        localStorage.setItem("user", JSON.stringify(userData));
        setToken(access_token);
        setUser(userData);
    };

    const signup = async (email: string, password: string, name: string) => {
        const response = await axios.post("http://127.0.0.1:8000/v1/auth/signup", {
            email,
            password,
            name,
        });

        const { access_token, user: userData } = response.data;
        localStorage.setItem("auth_token", access_token);
        localStorage.setItem("user", JSON.stringify(userData));
        setToken(access_token);
        setUser(userData);
    };

    const logout = () => {
        localStorage.removeItem("auth_token");
        localStorage.removeItem("user");
        setToken(null);
        setUser(null);
        router.push("/auth");
    };

    return (
        <AuthContext.Provider value={{ user, token, login, signup, logout, isLoading }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
}
