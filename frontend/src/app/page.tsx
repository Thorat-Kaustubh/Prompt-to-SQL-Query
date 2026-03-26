"use client";

import React, { useState, useEffect } from 'react';
import { NavigationSidebar } from '@/components/studio/NavigationSidebar';
import { AnalystDashboard } from '@/components/studio/AnalystDashboard';
import { useAppStore } from '@/store/useAppStore';

export default function Home() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [mounted, setMounted] = useState(false);
  const { setTheme } = useAppStore();

  useEffect(() => {
    setMounted(true);
    const savedTheme = localStorage.getItem('theme') as 'dark' | 'light' | null;
    if (savedTheme) {
      setTheme(savedTheme);
    } else {
      setTheme('light'); // Standard layout defaults to light or system
    }
  }, [setTheme]);

  if (!mounted) {
    return <div className="h-screen bg-[var(--bg-primary)]" />;
  }

  return (
    <main suppressHydrationWarning className="flex h-screen w-full bg-[var(--bg-primary)] overflow-hidden text-[var(--text-primary)] noise">
      
      {/* 1. LEFT SIDEBAR */}
      <NavigationSidebar 
        isOpen={isSidebarOpen} 
        toggleSidebarAction={() => setIsSidebarOpen(!isSidebarOpen)} 
      />

      {/* 2. MAIN CHAT AREA + 3. TOP RIGHT PROFILE CONTROL (inside AnalystDashboard) */}
      <AnalystDashboard />

    </main>
  );
}


