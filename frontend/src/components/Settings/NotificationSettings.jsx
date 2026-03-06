import React, { useState } from 'react';
import { 
  Bell, AlertTriangle, Target, FileText, Users, Mail,
  Save, Loader2, Check, AlertCircle, Info, ToggleLeft, ToggleRight
} from 'lucide-react';
import settingsService from '../../services/settingsService';
import { useI18n } from '../../context/I18nContext';

const NotificationSettings = ({ settings, onUpdate, organizationId }) => {
  const { t } = useI18n();
  const [formData, setFormData] = useState({
    notify_risk_critical: settings?.notify_risk_critical ?? true,
    notify_risk_high: settings?.notify_risk_high ?? true,
    notify_objective_deadline: settings?.notify_objective_deadline ?? true,
    notify_document_upload: settings?.notify_document_upload ?? false,
    notify_stakeholder_change: settings?.notify_stakeholder_change ?? true,
    notification_email: settings?.notification_email ?? '',
  });
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(null);

  const notifications = [
    {
      key: 'notify_risk_critical',
      title: 'Riesgos Críticos',
      description: 'Recibir alertas cuando se detecten riesgos de nivel crítico',
      icon: AlertTriangle,
      color: 'text-red-500',
      bgColor: 'bg-red-100 dark:bg-red-900/30',
      priority: 'Alta'
    },
    {
      key: 'notify_risk_high',
      title: 'Riesgos Altos',
      description: 'Recibir alertas cuando se detecten riesgos de nivel alto',
      icon: AlertTriangle,
      color: 'text-amber-500',
      bgColor: 'bg-amber-100 dark:bg-amber-900/30',
      priority: 'Media'
    },
    {
      key: 'notify_objective_deadline',
      title: 'Vencimiento de Objetivos',
      description: 'Alertas cuando un objetivo de calidad está próximo a vencer',
      icon: Target,
      color: 'text-blue-500',
      bgColor: 'bg-blue-100 dark:bg-blue-900/30',
      priority: 'Media'
    },
    {
      key: 'notify_document_upload',
      title: 'Nuevos Documentos',
      description: 'Notificar cuando se suban nuevos documentos al sistema',
      icon: FileText,
      color: 'text-emerald-500',
      bgColor: 'bg-emerald-100 dark:bg-emerald-900/30',
      priority: 'Baja'
    },
    {
      key: 'notify_stakeholder_change',
      title: 'Cambios en Stakeholders',
      description: 'Alertas cuando cambien las expectativas de partes interesadas',
      icon: Users,
      color: 'text-violet-500',
      bgColor: 'bg-violet-100 dark:bg-violet-900/30',
      priority: 'Media'
    },
  ];

  const handleToggle = (key) => {
    setFormData(prev => ({ ...prev, [key]: !prev[key] }));
    setSuccess(false);
  };

  const handleSubmit = async () => {
    try {
      setSaving(true);
      setError(null);
      
      const result = await settingsService.updateNotifications(formData, organizationId);
      onUpdate(result);
      setSuccess(true);
      
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError('Error al guardar la configuración');
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const enabledCount = notifications.filter(n => formData[n.key]).length;

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <div className="p-3 bg-gradient-to-br from-amber-500 to-orange-500 rounded-xl shadow-lg shadow-amber-500/25">
          <Bell className="w-6 h-6 text-white" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-slate-800 dark:text-white">
            Configuración de Notificaciones
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Configura qué alertas deseas recibir del sistema
          </p>
        </div>
      </div>

      {/* Alerts */}
      {success && (
        <div className="mb-6 p-4 bg-emerald-50 dark:bg-emerald-900/30 border border-emerald-200 dark:border-emerald-800 rounded-xl flex items-center gap-3">
          <Check className="w-5 h-5 text-emerald-500" />
          <span className="text-emerald-700 dark:text-emerald-300">{t('common.messages.success')}</span>
        </div>
      )}

      {error && (
        <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-xl flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-500" />
          <span className="text-red-700 dark:text-red-300">{error}</span>
        </div>
      )}

      {/* Status */}
      <div className="mb-8 p-4 bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/20 rounded-xl border border-amber-100 dark:border-amber-800/50">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-white dark:bg-slate-800 rounded-lg shadow-sm">
            <Bell className="w-5 h-5 text-amber-500" />
          </div>
          <div>
            <p className="font-semibold text-slate-800 dark:text-white">
              {enabledCount} de {notifications.length} notificaciones activas
            </p>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              {enabledCount === 0 ? 'No recibirás ninguna alerta' : 'Recibirás alertas según tu configuración'}
            </p>
          </div>
        </div>
      </div>

      {/* Email Configuration */}
      <div className="mb-8 p-6 bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-700/30 dark:to-slate-800/30 rounded-2xl border border-slate-200 dark:border-slate-700">
        <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-4 flex items-center gap-2">
          <Mail className="w-5 h-5 text-indigo-500" />
          Email para Notificaciones
        </h3>
        
        <div className="space-y-2">
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
            Dirección de correo electrónico
          </label>
          <div className="relative">
            <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              type="email"
              value={formData.notification_email}
              onChange={(e) => setFormData(prev => ({ ...prev, notification_email: e.target.value }))}
              placeholder="alertas@miempresa.com"
              className="w-full pl-12 pr-4 py-3 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all text-slate-800 dark:text-white placeholder-slate-400"
            />
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Las notificaciones se enviarán a esta dirección. Deja vacío para no recibir emails.
          </p>
        </div>
      </div>

      {/* Notification List */}
      <div className="space-y-4 mb-8">
        <h3 className="text-lg font-bold text-slate-800 dark:text-white">
          Tipos de Notificaciones
        </h3>
        
        {notifications.map((notification) => {
          const Icon = notification.icon;
          const isEnabled = formData[notification.key];
          
          return (
            <div 
              key={notification.key}
              className={`
                p-4 rounded-xl border-2 transition-all duration-200
                ${isEnabled 
                  ? 'bg-white dark:bg-slate-800/50 border-slate-200 dark:border-slate-600' 
                  : 'bg-slate-50 dark:bg-slate-800/30 border-slate-100 dark:border-slate-700 opacity-60'
                }
              `}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className={`p-2.5 rounded-xl ${notification.bgColor}`}>
                    <Icon className={`w-5 h-5 ${notification.color}`} />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="font-semibold text-slate-800 dark:text-white">
                        {notification.title}
                      </h4>
                      <span className={`
                        px-2 py-0.5 rounded text-xs font-medium
                        ${notification.priority === 'Alta' ? 'bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-300' :
                          notification.priority === 'Media' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-300' :
                          'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300'}
                      `}>
                        {notification.priority}
                      </span>
                    </div>
                    <p className="text-sm text-slate-500 dark:text-slate-400">
                      {notification.description}
                    </p>
                  </div>
                </div>
                
                <button
                  onClick={() => handleToggle(notification.key)}
                  className="flex-shrink-0 ml-4"
                >
                  {isEnabled ? (
                    <ToggleRight className="w-12 h-7 text-amber-500" />
                  ) : (
                    <ToggleLeft className="w-12 h-7 text-slate-400" />
                  )}
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Info Box */}
      <div className="mb-8 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl flex items-start gap-3">
        <Info className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
        <div className="text-sm text-blue-700 dark:text-blue-300">
          <p className="font-medium mb-1">{t('settings.notifications.howItWorks')}</p>
          <p>
            Las notificaciones se envían por correo electrónico cuando se detectan eventos importantes en tu sistema. 
            También verás las alertas en el dashboard principal y en la campana de notificaciones.
          </p>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          onClick={handleSubmit}
          disabled={saving}
          className="px-6 py-3 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white rounded-xl font-medium shadow-lg shadow-amber-500/25 hover:shadow-amber-500/40 transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saving ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Guardando...
            </>
          ) : (
            <>
              <Save className="w-5 h-5" />
              Guardar Configuración
            </>
          )}
        </button>
      </div>
    </div>
  );
};

export default NotificationSettings;