import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { ThemeProvider } from './context/ThemeContext'
import { I18nProvider } from './context/I18nContext'
import { FontSizeProvider } from './context/FontSizeContext'
import App from './App.jsx'
import './index.css'

// I18n integration note: I18nProvider must be initialized before useI18n can be used
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <I18nProvider>
        <ThemeProvider>
          <FontSizeProvider>
            <AuthProvider>
              <App />
            </AuthProvider>
          </FontSizeProvider>
        </ThemeProvider>
      </I18nProvider>
    </BrowserRouter>
  </React.StrictMode>,
)
