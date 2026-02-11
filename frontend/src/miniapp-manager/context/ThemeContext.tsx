import React, { createContext, useContext, useEffect, useState } from 'react';
import WebApp from '@twa-dev/sdk';

interface Theme {
  isDark: boolean;
  toggleTheme: () => void;
  colors: {
    bg_primary: string;
    bg_secondary: string;
    text_primary: string;
    text_secondary: string;
    card_bg: string;
    card_border: string;
    // Status colors
    success: string;
    danger: string;
    warning: string;
    // Chart colors
    chart_primary: string;
    chart_secondary: string;
    chart_tertiary: string;
  };
}

const lightTheme: Omit<Theme, 'toggleTheme'> = {
  isDark: false,
  colors: {
    bg_primary: '#F2F2F7', // iOS System Gray 6
    bg_secondary: '#FFFFFF',
    text_primary: '#000000', // Pure Black
    text_secondary: '#3C3C43', // Darker Gray for legibility
    card_bg: 'rgba(255, 255, 255, 0.95)', // Almost opaque for contrast
    card_border: 'rgba(0, 0, 0, 0.05)', // Subtle dark border
    success: '#34C759',
    danger: '#FF3B30',
    warning: '#FFCC00',
    chart_primary: '#007AFF',
    chart_secondary: '#AF52DE',
    chart_tertiary: '#FF9500',
  }
};

const darkTheme: Omit<Theme, 'toggleTheme'> = {
  isDark: true,
  colors: {
    bg_primary: '#000000',
    bg_secondary: '#1C1C1E',
    text_primary: '#FFFFFF',
    text_secondary: '#8E8E93',
    card_bg: 'rgba(28, 28, 30, 0.6)', // Glassy dark
    card_border: 'rgba(255, 255, 255, 0.1)',
    success: '#30D158',
    danger: '#FF453A',
    warning: '#FFD60A',
    chart_primary: '#0A84FF',
    chart_secondary: '#BF5AF2',
    chart_tertiary: '#FF9F0A',
  }
};

const ThemeContext = createContext<Theme>({ ...darkTheme, toggleTheme: () => { } });

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Initialize with passed props or default logic
  const [themeData, setThemeData] = useState<Omit<Theme, 'toggleTheme'>>(() => {
    // Check local storage first
    try {
      const saved = localStorage.getItem('theme_preference');
      if (saved) {
        return saved === 'dark' ? darkTheme : lightTheme;
      }
    } catch (e) {
      console.warn('Failed to read theme preference', e);
    }
    return darkTheme;
  });

  const toggleTheme = () => {
    setThemeData(prev => {
      const nextTheme = prev.isDark ? lightTheme : darkTheme;
      // Persist
      try {
        localStorage.setItem('theme_preference', nextTheme.isDark ? 'dark' : 'light');
      } catch (e) {
        console.warn('Failed to save theme preference', e);
      }

      if (nextTheme.isDark) {
        document.documentElement.classList.add('dark');
        if (WebApp.isVersionAtLeast('6.1')) {
          WebApp.setHeaderColor('#000000');
          WebApp.setBackgroundColor('#000000');
        }
      } else {
        document.documentElement.classList.remove('dark');
        if (WebApp.isVersionAtLeast('6.1')) {
          WebApp.setHeaderColor('#ffffff');
          WebApp.setBackgroundColor('#F2F2F7');
        }
      }
      return nextTheme;
    });
  };

  useEffect(() => {
    // Sync class on mount/change
    if (themeData.isDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [themeData.isDark]);

  useEffect(() => {
    // Detect Telegram Theme ONLY if no user preference is saved
    const saved = localStorage.getItem('theme_preference');
    if (saved) return; // Skip auto-detection if user manually set preference

    try {
      const isTelegram = !!(window as any).Telegram?.WebApp;
      if (isTelegram && WebApp.colorScheme) {
        console.log("Telegram Theme Detected:", WebApp.colorScheme);
        if (WebApp.colorScheme === 'light') {
          setThemeData(lightTheme);
        } else {
          setThemeData(darkTheme);
        }
        WebApp.expand();
        if (WebApp.isVersionAtLeast('6.1')) {
          WebApp.setHeaderColor(WebApp.colorScheme === 'light' ? '#F2F2F7' : '#000000');
          WebApp.setBackgroundColor(WebApp.colorScheme === 'light' ? '#F2F2F7' : '#000000');
        }
      } else {
        // Default to dark if not Telegram and no preference
        setThemeData(darkTheme);
      }
    } catch (e) {
      console.warn('Telegram WebApp SDK Error, defaulting to dark theme', e);
      setThemeData(darkTheme);
    }
  }, []);

  const value: Theme = {
    ...themeData,
    toggleTheme
  };

  return (
    <ThemeContext.Provider value={value}>
      <div
        style={{
          backgroundColor: themeData.colors.bg_primary,
          color: themeData.colors.text_primary,
          minHeight: '100vh',
          transition: 'background-color 0.3s ease'
        }}
      >
        {children}
      </div>
    </ThemeContext.Provider>
  );
};

export const useTheme = () => useContext(ThemeContext);
