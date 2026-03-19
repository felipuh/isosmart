import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../context/I18nContext';

const ForgotPasswordPage = () => {
  const { t } = useI18n();
  const { requestPasswordReset } = useAuth();
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setMessage('');
    setError('');
    setLoading(true);

    const result = await requestPasswordReset(email);
    if (result.success) {
      setMessage(result.message);
    } else {
      setError(result.error);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyan-500/20 rounded-full blur-3xl"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl"></div>
      </div>

      <div className="relative w-full max-w-md bg-slate-800/80 backdrop-blur-xl border border-slate-700 rounded-2xl shadow-2xl p-8">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-white mb-2">{t('auth.passwordReset.request.title')}</h1>
          <p className="text-slate-400">{t('auth.passwordReset.request.subtitle')}</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-slate-300 mb-2">
              {t('common.forms.email')}
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="w-full px-4 py-3 rounded-lg bg-slate-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500"
              placeholder={t('auth.passwordReset.request.placeholders.email')}
              autoComplete="email"
              required
            />
          </div>

          {message ? <div className="text-sm text-emerald-300">{message}</div> : null}
          {error ? <div className="text-sm text-red-300">{error}</div> : null}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 px-4 bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 text-white font-semibold rounded-lg shadow-lg shadow-cyan-500/25 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? t('common.messages.loading') : t('auth.passwordReset.request.submit')}
          </button>
        </form>

        <div className="mt-6 text-center text-sm">
          <Link to="/login" className="text-cyan-400 hover:text-cyan-300 transition-colors">
            {t('auth.passwordReset.backToLogin')}
          </Link>
        </div>
      </div>
    </div>
  );
};

export default ForgotPasswordPage;