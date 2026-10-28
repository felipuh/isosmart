/* eslint-disable react-refresh/only-export-components */
import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';

const STORAGE_KEY = 'isosmart_font_size';
const LEVELS = ['small', 'normal', 'large', 'xlarge'];
const DEFAULT_LEVEL = 'normal';

const FontSizeContext = createContext(null);

export const FontSizeProvider = ({ children }) => {
  const [fontSizeLevel, setFontSizeLevel] = useState(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    return LEVELS.includes(saved) ? saved : DEFAULT_LEVEL;
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-font-size', fontSizeLevel);
    localStorage.setItem(STORAGE_KEY, fontSizeLevel);
  }, [fontSizeLevel]);

  const increaseFontSize = useCallback(() => {
    setFontSizeLevel((current) => {
      const idx = LEVELS.indexOf(current);
      return idx < LEVELS.length - 1 ? LEVELS[idx + 1] : current;
    });
  }, []);

  const decreaseFontSize = useCallback(() => {
    setFontSizeLevel((current) => {
      const idx = LEVELS.indexOf(current);
      return idx > 0 ? LEVELS[idx - 1] : current;
    });
  }, []);

  const resetFontSize = useCallback(() => setFontSizeLevel(DEFAULT_LEVEL), []);

  const isMinLevel = fontSizeLevel === LEVELS[0];
  const isMaxLevel = fontSizeLevel === LEVELS[LEVELS.length - 1];

  return (
    <FontSizeContext.Provider value={{ fontSizeLevel, increaseFontSize, decreaseFontSize, resetFontSize, isMinLevel, isMaxLevel }}>
      {children}
    </FontSizeContext.Provider>
  );
};

export const useFontSize = () => {
  const ctx = useContext(FontSizeContext);
  if (!ctx) throw new Error('useFontSize must be used inside FontSizeProvider');
  return ctx;
};
