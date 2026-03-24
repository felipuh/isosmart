import { useState } from 'react';
import { Building2, KeyRound, Mail, Shield, UserRound } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../context/I18nContext';

const ProfilePage = () => {
  const { user, profile, currentOrganization, changePassword, mustChangePassword, securityAlert } = useAuth();
  const { t } = useI18n();

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setSuccess('');

    if (!currentPassword || !newPassword || !confirmPassword) {
      setError(t('profilePage.messages.requiredFields'));
      return;
    }

    if (newPassword !== confirmPassword) {
      setError(t('profilePage.messages.mismatch'));
      return;
    }

    setSaving(true);
    const result = await changePassword(currentPassword, newPassword, confirmPassword);
    setSaving(false);

    if (result.success) {
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setSuccess(t('profilePage.messages.passwordUpdated'));
      return;
    }

    setError(result.error || t('auth.errors.changePasswordFailed'));
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/60 to-cyan-50/40 dark:from-slate-900 dark:via-slate-900 dark:to-slate-800 p-6">
      <div className="max-w-5xl mx-auto space-y-6">
        <section className="rounded-2xl border border-slate-200/80 dark:border-slate-700 bg-white/90 dark:bg-slate-900/80 shadow-xl p-6 md:p-8">
          <h1 className="text-2xl md:text-3xl font-bold text-slate-900 dark:text-slate-100">{t('auth.userMenu.profile')}</h1>
          <p className="text-sm md:text-base text-slate-600 dark:text-slate-300 mt-2">{t('profilePage.subtitle')}</p>
        </section>

        <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <article className="rounded-2xl border border-slate-200/80 dark:border-slate-700 bg-white/90 dark:bg-slate-900/80 shadow-lg p-6">
            <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-5 flex items-center gap-2">
              <UserRound className="w-5 h-5 text-blue-600 dark:text-blue-300" />
              {t('profilePage.accountData')}
            </h2>

            <div className="space-y-4 text-sm">
              <div className="flex items-start gap-3">
                <Mail className="w-4 h-4 text-slate-400 mt-0.5" />
                <div>
                  <p className="text-slate-500 dark:text-slate-400">{t('common.forms.email')}</p>
                  <p className="text-slate-900 dark:text-slate-100 font-medium break-all">{user?.email || '-'}</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <Shield className="w-4 h-4 text-slate-400 mt-0.5" />
                <div>
                  <p className="text-slate-500 dark:text-slate-400">{t('profilePage.role')}</p>
                  <p className="text-slate-900 dark:text-slate-100 font-medium">{profile?.role_display || '-'}</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <Building2 className="w-4 h-4 text-slate-400 mt-0.5" />
                <div>
                  <p className="text-slate-500 dark:text-slate-400">{t('profilePage.organization')}</p>
                  <p className="text-slate-900 dark:text-slate-100 font-medium">{currentOrganization?.name || t('auth.userMenu.noOrganization')}</p>
                </div>
              </div>
            </div>
          </article>

          <article id="password" className="rounded-2xl border border-slate-200/80 dark:border-slate-700 bg-white/90 dark:bg-slate-900/80 shadow-lg p-6">
            <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-2 flex items-center gap-2">
              <KeyRound className="w-5 h-5 text-emerald-600 dark:text-emerald-300" />
              {t('settings.users.password.title')}
            </h2>
            {mustChangePassword && (
              <div className="mb-5 rounded-xl border border-amber-200 dark:border-amber-900/50 bg-amber-50 dark:bg-amber-900/20 px-4 py-3 text-sm text-amber-800 dark:text-amber-200">
                Debes cambiar tu contrasena inicial antes de continuar. Usa una frase o contrasena de al menos 12 caracteres y evita datos predecibles.
              </div>
            )}
            {mustChangePassword && securityAlert?.reason_code === 'TEMP_PASSWORD_EXPIRING' && (
              <div className="mb-5 rounded-xl border border-orange-200 dark:border-orange-900/50 bg-orange-50 dark:bg-orange-900/20 px-4 py-3 text-sm text-orange-800 dark:text-orange-200">
                Tu contrasena temporal vence en {securityAlert.days_left} dia(s). Cambiala ahora para evitar bloqueo de acceso.
              </div>
            )}
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-5">{t('profilePage.passwordHint')}</p>

            <form onSubmit={handleSubmit} className="space-y-4">
              <label className="block">
                <span className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">{t('profilePage.currentPassword')}</span>
                <input
                  type="password"
                  value={currentPassword}
                  onChange={(event) => setCurrentPassword(event.target.value)}
                  autoComplete="current-password"
                  className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-4 py-2.5 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                />
              </label>

              <label className="block">
                <span className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">{t('auth.passwordReset.confirm.newPassword')}</span>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(event) => setNewPassword(event.target.value)}
                  autoComplete="new-password"
                  className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-4 py-2.5 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                />
              </label>

              <label className="block">
                <span className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">{t('common.forms.confirmPassword')}</span>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                  autoComplete="new-password"
                  className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-4 py-2.5 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                />
              </label>

              {error && (
                <div className="rounded-lg border border-red-200 dark:border-red-900/50 bg-red-50 dark:bg-red-900/20 px-3 py-2 text-sm text-red-700 dark:text-red-300">
                  {error}
                </div>
              )}

              {success && (
                <div className="rounded-lg border border-emerald-200 dark:border-emerald-900/50 bg-emerald-50 dark:bg-emerald-900/20 px-3 py-2 text-sm text-emerald-700 dark:text-emerald-300">
                  {success}
                </div>
              )}

              <button
                type="submit"
                disabled={saving}
                className="inline-flex items-center justify-center rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white px-5 py-2.5 text-sm font-semibold transition-colors"
              >
                {saving ? t('common.messages.saving') : t('settings.users.password.submit')}
              </button>
            </form>
          </article>
        </section>
      </div>
    </div>
  );
};

export default ProfilePage;
