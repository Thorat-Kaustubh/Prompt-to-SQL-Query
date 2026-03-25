import { Sun, Moon } from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';

export const ThemeToggle = () => {
  const { theme, toggleTheme } = useAppStore();

  return (
    <button
      onClick={toggleTheme}
      className="p-2 rounded-full bg-surface border border-border/40 hover:bg-border/20 transition-all active:scale-95"
      aria-label="Toggle Theme"
    >
      {theme === 'dark' ? (
        <Sun className="w-5 h-5 text-accent" />
      ) : (
        <Moon className="w-5 h-5 text-accent" />
      )}
    </button>
  );
};
