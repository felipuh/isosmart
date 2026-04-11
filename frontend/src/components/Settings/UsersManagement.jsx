import React, { useState, useEffect, useCallback } from 'react';
import { 
  Users, UserPlus, Search, MoreVertical, Shield, Mail, 
  Phone, Building, Edit2, Trash2, Key, UserCheck, UserX,
  ChevronDown, X, Loader2, Check, AlertCircle
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useI18n } from '../../context/I18nContext';
import settingsService from '../../services/settingsService';
import { showAlert, showConfirm } from '../../services/dialogs';

const UsersManagement = () => {
  const { t } = useI18n();
  const { currentOrganization, hasRole } = useAuth();
  const organizationId = currentOrganization?.id;
  const [users, setUsers] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [actionMenu, setActionMenu] = useState(null);
  const canManageUsers = hasRole(['org_admin', 'iso_manager']);

  const roleLabels = {
    org_admin: { label: t('settings.users.roles.org_admin'), color: 'bg-purple-100 text-purple-700 dark:bg-purple-900/50 dark:text-purple-300' },
    iso_manager: { label: t('settings.users.roles.iso_manager'), color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300' },
    auditor: { label: t('settings.users.roles.auditor'), color: 'bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-300' },
    user: { label: t('settings.users.roles.user'), color: 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300' },
    viewer: { label: t('settings.users.roles.viewer'), color: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400' },
  };

  const loadUsers = useCallback(async () => {
    try {
      setLoading(true);
      const [usersData, statsData] = await Promise.all([
        settingsService.getUsers(organizationId),
        settingsService.getUserStats(organizationId)
      ]);
      setUsers(usersData);
      setStats(statsData);
    } catch (err) {
      console.error('Error cargando usuarios:', err);
    } finally {
      setLoading(false);
    }
  }, [organizationId]);

  useEffect(() => {
    if (organizationId) {
      loadUsers();
    }
  }, [organizationId, loadUsers]);

  const filteredUsers = users.filter(user => {
    const matchesSearch = 
      user.user?.username?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.user?.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.full_name?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesRole = roleFilter === 'all' || user.role === roleFilter;
    
    return matchesSearch && matchesRole;
  });

  const handleToggleActive = async (userId) => {
    try {
      await settingsService.toggleUserActive(userId);
      loadUsers();
    } catch (err) {
      console.error('Error:', err);
    }
    setActionMenu(null);
  };

  const handleDeleteUser = async (userId) => {
    if (!canManageUsers) {
      await showAlert(t('settings.users.messages.noPermissionDelete'), { icon: 'warning' });
      return;
    }
    
    const confirmed = await showConfirm(t('settings.users.messages.confirmDelete'));
    if (!confirmed) return;
    
    try {
      await settingsService.deleteUser(userId);
      loadUsers();
    } catch (err) {
      console.error('Error:', err);
    }
    setActionMenu(null);
  };

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-gradient-to-br from-violet-500 to-fuchsia-500 rounded-xl shadow-lg shadow-violet-500/25">
            <Users className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-800 dark:text-white">
              {t('settings.users.title')}
            </h2>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              {t('settings.users.subtitle')}
            </p>
          </div>
        </div>
        
        <button
          onClick={() => setShowCreateModal(true)}
          disabled={!canManageUsers}
          className="px-4 py-2.5 bg-gradient-to-r from-violet-500 to-fuchsia-500 hover:from-violet-600 hover:to-fuchsia-600 text-white rounded-xl font-medium shadow-lg shadow-violet-500/25 transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          title={!canManageUsers ? t('settings.users.messages.noPermissionCreate') : ''}
        >
          <UserPlus className="w-5 h-5" />
          {t('settings.users.actions.newUser')}
        </button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="p-4 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-xl border border-blue-100 dark:border-blue-800/50">
            <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{stats.total_users}</p>
            <p className="text-sm text-blue-600/70 dark:text-blue-400/70">{t('settings.users.stats.totalUsers')}</p>
          </div>
          <div className="p-4 bg-gradient-to-br from-emerald-50 to-teal-50 dark:from-emerald-900/20 dark:to-teal-900/20 rounded-xl border border-emerald-100 dark:border-emerald-800/50">
            <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">{stats.active_users}</p>
            <p className="text-sm text-emerald-600/70 dark:text-emerald-400/70">{t('settings.users.stats.active')}</p>
          </div>
          <div className="p-4 bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/20 rounded-xl border border-amber-100 dark:border-amber-800/50">
            <p className="text-2xl font-bold text-amber-600 dark:text-amber-400">{stats.by_role?.org_admin || 0}</p>
            <p className="text-sm text-amber-600/70 dark:text-amber-400/70">{t('settings.users.stats.admins')}</p>
          </div>
          <div className="p-4 bg-gradient-to-br from-rose-50 to-pink-50 dark:from-rose-900/20 dark:to-pink-900/20 rounded-xl border border-rose-100 dark:border-rose-800/50">
            <p className="text-2xl font-bold text-rose-600 dark:text-rose-400">{stats.inactive_users}</p>
            <p className="text-sm text-rose-600/70 dark:text-rose-400/70">{t('settings.users.stats.inactive')}</p>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="flex-1 relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
          <input
            type="text"
            placeholder={t('settings.users.filters.searchPlaceholder')}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-12 pr-4 py-3 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-violet-500 focus:border-transparent transition-all text-slate-800 dark:text-white"
          />
        </div>
        
        <div className="relative">
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            className="appearance-none pl-4 pr-10 py-3 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-violet-500 focus:border-transparent transition-all text-slate-800 dark:text-white cursor-pointer min-w-[180px]"
          >
            <option value="all">{t('settings.users.filters.allRoles')}</option>
            {Object.entries(roleLabels).map(([value, { label }]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
          <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 pointer-events-none" />
        </div>
      </div>

      {/* Users Table */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 text-violet-500 animate-spin" />
        </div>
      ) : filteredUsers.length === 0 ? (
        <div className="text-center py-12">
          <Users className="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
          <p className="text-slate-500 dark:text-slate-400">{t('settings.users.empty.noUsers')}</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-700">
                <th className="text-left py-4 px-4 text-sm font-semibold text-slate-600 dark:text-slate-300">{t('settings.users.table.user')}</th>
                <th className="text-left py-4 px-4 text-sm font-semibold text-slate-600 dark:text-slate-300">{t('settings.users.table.role')}</th>
                <th className="text-left py-4 px-4 text-sm font-semibold text-slate-600 dark:text-slate-300 hidden md:table-cell">{t('settings.users.table.department')}</th>
                <th className="text-left py-4 px-4 text-sm font-semibold text-slate-600 dark:text-slate-300">{t('common.forms.status')}</th>
                <th className="text-right py-4 px-4 text-sm font-semibold text-slate-600 dark:text-slate-300">{t('settings.users.table.actions')}</th>
              </tr>
            </thead>
            <tbody>
              {filteredUsers.map((user) => (
                <tr 
                  key={user.id} 
                  className="border-b border-slate-100 dark:border-slate-700/50 hover:bg-slate-50 dark:hover:bg-slate-700/30 transition-colors"
                >
                  <td className="py-4 px-4">
                    <div className="flex items-center gap-3">
                      {user.avatar ? (
                        <img 
                          src={user.avatar} 
                          alt={user.full_name}
                          className="w-10 h-10 rounded-full object-cover"
                        />
                      ) : (
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-violet-400 to-fuchsia-500 flex items-center justify-center text-white font-semibold">
                          {user.user?.first_name?.[0] || user.user?.username?.[0] || '?'}
                        </div>
                      )}
                      <div>
                        <p className="font-medium text-slate-800 dark:text-white">
                          {user.full_name || user.user?.username}
                        </p>
                        <p className="text-sm text-slate-500 dark:text-slate-400">
                          {user.user?.email}
                        </p>
                      </div>
                    </div>
                  </td>
                  <td className="py-4 px-4">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${roleLabels[user.role]?.color || 'bg-slate-100 text-slate-600'}`}>
                      {roleLabels[user.role]?.label || user.role}
                    </span>
                  </td>
                  <td className="py-4 px-4 hidden md:table-cell">
                    <span className="text-slate-600 dark:text-slate-300">
                      {user.department || '-'}
                    </span>
                  </td>
                  <td className="py-4 px-4">
                    {user.is_active ? (
                      <span className="flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400">
                        <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span>
                        {t('common.labels.active')}
                      </span>
                    ) : (
                      <span className="flex items-center gap-1.5 text-slate-400">
                        <span className="w-2 h-2 bg-slate-400 rounded-full"></span>
                        {t('common.labels.inactive')}
                      </span>
                    )}
                  </td>
                  <td className="py-4 px-4 text-right">
                    <div className="relative">
                      <button
                        onClick={() => setActionMenu(actionMenu === user.id ? null : user.id)}
                        className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
                      >
                        <MoreVertical className="w-5 h-5 text-slate-400" />
                      </button>
                      
                      {actionMenu === user.id && (
                        <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-slate-800 rounded-xl shadow-xl border border-slate-200 dark:border-slate-700 py-2 z-10">
                          <button
                            onClick={() => {
                              setSelectedUser(user);
                              setShowEditModal(true);
                              setActionMenu(null);
                            }}
                            className="w-full px-4 py-2 text-left text-sm text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700 flex items-center gap-2"
                          >
                            <Edit2 className="w-4 h-4" />
                            {t('common.buttons.edit')}
                          </button>
                          <button
                            onClick={() => {
                              setSelectedUser(user);
                              setShowPasswordModal(true);
                              setActionMenu(null);
                            }}
                            className="w-full px-4 py-2 text-left text-sm text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700 flex items-center gap-2"
                          >
                            <Key className="w-4 h-4" />
                            {t('settings.users.actions.changePassword')}
                          </button>
                          <button
                            onClick={() => handleToggleActive(user.id)}
                            className="w-full px-4 py-2 text-left text-sm text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700 flex items-center gap-2"
                          >
                            {user.is_active ? (
                              <>
                                <UserX className="w-4 h-4" />
                                {t('settings.users.actions.deactivate')}
                              </>
                            ) : (
                              <>
                                <UserCheck className="w-4 h-4" />
                                {t('settings.users.actions.activate')}
                              </>
                            )}
                          </button>
                          <hr className="my-2 border-slate-200 dark:border-slate-700" />
                          <button
                            onClick={() => handleDeleteUser(user.id)}
                            className="w-full px-4 py-2 text-left text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/30 flex items-center gap-2"
                          >
                            <Trash2 className="w-4 h-4" />
                            {t('common.buttons.delete')}
                          </button>
                        </div>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create User Modal */}
      {showCreateModal && (
        <CreateUserModal 
          organizationId={organizationId}
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false);
            loadUsers();
          }}
        />
      )}

      {/* Edit User Modal */}
      {showEditModal && selectedUser && (
        <EditUserModal 
          user={selectedUser}
          onClose={() => {
            setShowEditModal(false);
            setSelectedUser(null);
          }}
          onSuccess={() => {
            setShowEditModal(false);
            setSelectedUser(null);
            loadUsers();
          }}
        />
      )}

      {/* Password Reset Modal */}
      {showPasswordModal && selectedUser && (
        <PasswordResetModal 
          user={selectedUser}
          onClose={() => {
            setShowPasswordModal(false);
            setSelectedUser(null);
          }}
          onSuccess={() => {
            setShowPasswordModal(false);
            setSelectedUser(null);
          }}
        />
      )}
    </div>
  );
};

// Modal para crear usuario
const CreateUserModal = ({ organizationId, onClose, onSuccess }) => {
  const { t } = useI18n();
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    role: 'user',
    job_title: '',
    department: '',
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      setSaving(true);
      setError(null);
      await settingsService.createUser({
        ...formData,
        organization_id: organizationId
      });
      onSuccess();
    } catch (err) {
      setError(err.response?.data?.message || t('settings.users.messages.createError'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between">
          <h3 className="text-lg font-bold text-slate-800 dark:text-white flex items-center gap-2">
            <UserPlus className="w-5 h-5 text-violet-500" />
            {t('settings.users.create.title')}
          </h3>
          <button onClick={onClose} className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg">
            <X className="w-5 h-5 text-slate-400" />
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg text-red-600 dark:text-red-300 text-sm flex items-center gap-2">
              <AlertCircle className="w-4 h-4" />
              {error}
            </div>
          )}
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">{t('common.forms.name')}</label>
              <input
                type="text"
                value={formData.first_name}
                onChange={(e) => setFormData({...formData, first_name: e.target.value})}
                className="w-full px-4 py-2.5 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-violet-500 text-slate-800 dark:text-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">{t('settings.users.fields.lastName')}</label>
              <input
                type="text"
                value={formData.last_name}
                onChange={(e) => setFormData({...formData, last_name: e.target.value})}
                className="w-full px-4 py-2.5 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-violet-500 text-slate-800 dark:text-white"
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">{t('settings.users.fields.usernameRequired')}</label>
            <input
              type="text"
              required
              value={formData.username}
              onChange={(e) => setFormData({...formData, username: e.target.value})}
              className="w-full px-4 py-2.5 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-violet-500 text-slate-800 dark:text-white"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">{t('settings.users.fields.emailRequired')}</label>
            <input
              type="email"
              required
              value={formData.email}
              onChange={(e) => setFormData({...formData, email: e.target.value})}
              className="w-full px-4 py-2.5 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-violet-500 text-slate-800 dark:text-white"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">{t('settings.users.fields.passwordRequired')}</label>
            <input
              type="password"
              required
              minLength={8}
              value={formData.password}
              onChange={(e) => setFormData({...formData, password: e.target.value})}
              className="w-full px-4 py-2.5 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-violet-500 text-slate-800 dark:text-white"
              placeholder={t('settings.users.placeholders.min8Chars')}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">{t('settings.users.fields.roleRequired')}</label>
            <select
              value={formData.role}
              onChange={(e) => setFormData({...formData, role: e.target.value})}
              className="w-full px-4 py-2.5 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-violet-500 text-slate-800 dark:text-white"
            >
              <option value="user">{t('settings.users.roles.user')}</option>
              <option value="viewer">{t('settings.users.roles.viewer')}</option>
              <option value="auditor">{t('settings.users.roles.auditor')}</option>
              <option value="iso_manager">{t('settings.users.roles.iso_manager')}</option>
              <option value="org_admin">{t('settings.users.roles.org_admin')}</option>
            </select>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">{t('settings.users.fields.position')}</label>
              <input
                type="text"
                value={formData.job_title}
                onChange={(e) => setFormData({...formData, job_title: e.target.value})}
                className="w-full px-4 py-2.5 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-violet-500 text-slate-800 dark:text-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">{t('settings.users.fields.department')}</label>
              <input
                type="text"
                value={formData.department}
                onChange={(e) => setFormData({...formData, department: e.target.value})}
                className="w-full px-4 py-2.5 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-violet-500 text-slate-800 dark:text-white"
              />
            </div>
          </div>
          
          <div className="flex justify-end gap-3 pt-4">
            <button type="button" onClick={onClose} className="px-4 py-2.5 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-xl">
              {t('common.buttons.cancel')}
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-4 py-2.5 bg-gradient-to-r from-violet-500 to-fuchsia-500 text-white rounded-xl font-medium flex items-center gap-2 disabled:opacity-50"
            >
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
              {t('settings.users.create.submit')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Modal para editar usuario
const EditUserModal = ({ user, onClose, onSuccess }) => {
  const { t } = useI18n();
  const [formData, setFormData] = useState({
    role: user.role,
    job_title: user.job_title || '',
    department: user.department || '',
  });
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      await settingsService.updateUser(user.id, formData);
      onSuccess();
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl max-w-md w-full">
        <div className="p-6 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between">
          <h3 className="text-lg font-bold text-slate-800 dark:text-white flex items-center gap-2">
            <Edit2 className="w-5 h-5 text-violet-500" />
            {t('settings.users.edit.title')}
          </h3>
          <button onClick={onClose} className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg">
            <X className="w-5 h-5 text-slate-400" />
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="flex items-center gap-3 p-4 bg-slate-50 dark:bg-slate-700/50 rounded-xl">
            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-violet-400 to-fuchsia-500 flex items-center justify-center text-white font-semibold text-lg">
              {user.user?.first_name?.[0] || user.user?.username?.[0]}
            </div>
            <div>
              <p className="font-semibold text-slate-800 dark:text-white">{user.full_name}</p>
              <p className="text-sm text-slate-500 dark:text-slate-400">{user.user?.email}</p>
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">{t('settings.users.fields.role')}</label>
            <select
              value={formData.role}
              onChange={(e) => setFormData({...formData, role: e.target.value})}
              className="w-full px-4 py-2.5 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-800 dark:text-white"
            >
              <option value="user">{t('settings.users.roles.user')}</option>
              <option value="viewer">{t('settings.users.roles.viewer')}</option>
              <option value="auditor">{t('settings.users.roles.auditor')}</option>
              <option value="iso_manager">{t('settings.users.roles.iso_manager')}</option>
              <option value="org_admin">{t('settings.users.roles.org_admin')}</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">{t('settings.users.fields.position')}</label>
            <input
              type="text"
              value={formData.job_title}
              onChange={(e) => setFormData({...formData, job_title: e.target.value})}
              className="w-full px-4 py-2.5 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-800 dark:text-white"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">{t('settings.users.fields.department')}</label>
            <input
              type="text"
              value={formData.department}
              onChange={(e) => setFormData({...formData, department: e.target.value})}
              className="w-full px-4 py-2.5 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-800 dark:text-white"
            />
          </div>
          
          <div className="flex justify-end gap-3 pt-4">
            <button type="button" onClick={onClose} className="px-4 py-2.5 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-xl">
              {t('common.buttons.cancel')}
            </button>
            <button type="submit" disabled={saving} className="px-4 py-2.5 bg-gradient-to-r from-violet-500 to-fuchsia-500 text-white rounded-xl font-medium flex items-center gap-2 disabled:opacity-50">
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
              {t('settings.users.edit.submit')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Modal para resetear contraseña
const PasswordResetModal = ({ user, onClose, onSuccess }) => {
  const { t } = useI18n();
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (password !== confirmPassword) {
      setError(t('common.messages.passwordMismatch'));
      return;
    }
    
    try {
      setSaving(true);
      setError(null);
      await settingsService.resetPassword(user.id, password);
      onSuccess();
    } catch (error) {
      console.error('Error al cambiar contraseña:', error);
      setError(t('settings.users.messages.changePasswordError'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl max-w-md w-full">
        <div className="p-6 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between">
          <h3 className="text-lg font-bold text-slate-800 dark:text-white flex items-center gap-2">
            <Key className="w-5 h-5 text-amber-500" />
            {t('settings.users.password.title')}
          </h3>
          <button onClick={onClose} className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg">
            <X className="w-5 h-5 text-slate-400" />
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <p className="text-sm text-slate-600 dark:text-slate-400">
            {t('settings.users.password.subtitle')} <strong>{user.full_name}</strong>
          </p>
          
          {error && (
            <div className="p-3 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg text-red-600 dark:text-red-300 text-sm">
              {error}
            </div>
          )}
          
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">{t('settings.users.fields.newPassword')}</label>
            <input
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2.5 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-800 dark:text-white"
              placeholder={t('settings.users.placeholders.min8Chars')}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">{t('common.forms.confirmPassword')}</label>
            <input
              type="password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full px-4 py-2.5 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-800 dark:text-white"
            />
          </div>
          
          <div className="flex justify-end gap-3 pt-4">
            <button type="button" onClick={onClose} className="px-4 py-2.5 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-xl">
              {t('common.buttons.cancel')}
            </button>
            <button type="submit" disabled={saving} className="px-4 py-2.5 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-xl font-medium flex items-center gap-2 disabled:opacity-50">
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Key className="w-4 h-4" />}
              {t('settings.users.password.submit')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default UsersManagement;