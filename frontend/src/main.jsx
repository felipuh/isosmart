import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { ThemeProvider } from './context/ThemeContext'
import { I18nProvider } from './context/I18nContext'
import { FontSizeProvider } from './context/FontSizeContext'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <ThemeProvider>
        <FontSizeProvider>
          <I18nProvider>
            <AuthProvider>
              <App />
            </AuthProvider>
          </I18nProvider>
        </FontSizeProvider>
      </ThemeProvider>
    </BrowserRouter>
  </React.StrictMode>,
)
