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
  const [themeData, setThemeData] = useState<Omit<Theme, 'toggleTheme'>>(darkTheme);

  const toggleTheme = () => {
    setThemeData(prev => prev.isDark ? lightTheme : darkTheme);
  };

  useEffect(() => {
    // Detect Telegram Theme
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
        WebApp.setHeaderColor(WebApp.colorScheme === 'light' ? '#F2F2F7' : '#000000');
      } else {
        console.log("Not in Telegram, defaulting to Dark Theme");
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
