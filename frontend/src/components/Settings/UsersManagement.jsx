import React, { useState, useEffect } from 'react';
import { 
  Users, UserPlus, Search, MoreVertical, Shield, Mail, 
  Phone, Building, Edit2, Trash2, Key, UserCheck, UserX,
  ChevronDown, X, Loader2, Check, AlertCircle
} from 'lucide-react';
import settingsService from '../../services/settingsService';

const UsersManagement = ({ organizationId }) => {
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

  const roleLabels = {
    org_admin: { label: 'Administrador', color: 'bg-purple-100 text-purple-700 dark:bg-purple-900/50 dark:text-purple-300' },
    iso_manager: { label: 'Gestor ISO', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300' },
    auditor: { label: 'Auditor', color: 'bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-300' },
    user: { label: 'Usuario', color: 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300' },
    viewer: { label: 'Solo Lectura', color: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400' },
  };

  useEffect(() => {
    loadUsers();
  }, [organizationId]);

  const loadUsers = async () => {
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
  };

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
    if (!confirm('¿Estás seguro de eliminar este usuario?')) return;
    
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
              Gestión de Usuarios
            </h2>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Administra usuarios y permisos del sistema
            </p>
          </div>
        </div>
        
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2.5 bg-gradient-to-r from-violet-500 to-fuchsia-500 hover:from-violet-600 hover:to-fuchsia-600 text-white rounded-xl font-medium shadow-lg shadow-violet-500/25 transition-all flex items-center gap-2"
        >
          <UserPlus className="w-5 h-5" />
          Nuevo Usuario
        </button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="p-4 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-xl border border-blue-100 dark:border-blue-800/50">
            <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{stats.total_users}</p>
            <p className="text-sm text-blue-600/70 dark:text-blue-400/70">Total Usuarios</p>
          </div>
          <div className="p-4 bg-gradient-to-br from-emerald-50 to-teal-50 dark:from-emerald-900/20 dark:to-teal-900/20 rounded-xl border border-emerald-100 dark:border-emerald-800/50">
            <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">{stats.active_users}</p>
            <p className="text-sm text-emerald-600/70 dark:text-emerald-400/70">Activos</p>
          </div>
          <div className="p-4 bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/20 rounded-xl border border-amber-100 dark:border-amber-800/50">
            <p className="text-2xl font-bold text-amber-600 dark:text-amber-400">{stats.by_role?.org_admin || 0}</p>
            <p className="text-sm text-amber-600/70 dark:text-amber-400/70">Administradores</p>
          </div>
          <div className="p-4 bg-gradient-to-br from-rose-50 to-pink-50 dark:from-rose-900/20 dark:to-pink-900/20 rounded-xl border border-rose-100 dark:border-rose-800/50">
            <p className="text-2xl font-bold text-rose-600 dark:text-rose-400">{stats.inactive_users}</p>
            <p className="text-sm text-rose-600/70 dark:text-rose-400/70">Inactivos</p>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="flex-1 relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
          <input
            type="text"
            placeholder="Buscar usuarios..."
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
            <option value="all">Todos los roles</option>
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
          <p className="text-slate-500 dark:text-slate-400">No se encontraron usuarios</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-700">
                <th className="text-left py-4 px-4 text-sm font-semibold text-slate-600 dark:text-slate-300">Usuario</th>
                <th className="text-left py-4 px-4 text-sm font-semibold text-slate-600 dark:text-slate-300">Rol</th>
                <th className="text-left py-4 px-4 text-sm font-semibold text-slate-600 dark:text-slate-300 hidden md:table-cell">Departamento</th>
                <th className="text-left py-4 px-4 text-sm font-semibold text-slate-600 dark:text-slate-300">Estado</th>
                <th className="text-right py-4 px-4 text-sm font-semibold text-slate-600 dark:text-slate-300">Acciones</th>
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
                        Activo
                      </span>
                    ) : (
                      <span className="flex items-center gap-1.5 text-slate-400">
                        <span className="w-2 h-2 bg-slate-400 rounded-full"></span>
                        Inactivo
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
                            Editar
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
                            Cambiar Contraseña
                          </button>
                          <button
                            onClick={() => handleToggleActive(user.id)}
                            className="w-full px-4 py-2 text-left text-sm text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700 flex items-center gap-2"
                          >
                            {user.is_active ? (
                              <>
                                <UserX className="w-4 h-4" />
                                Desactivar
                              </>
                            ) : (
                              <>
                                <UserCheck className="w-4 h-4" />
                                Activar
                              </>
                            )}
                          </button>
                          <hr className="my-2 border-slate-200 dark:border-slate-700" />
                          <button
                            onClick={() => handleDeleteUser(user.id)}
                            className="w-full px-4 py-2 text-left text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/30 flex items-center gap-2"
                          >
                            <Trash2 className="w-4 h-4" />
                            Eliminar
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
      setError(err.response?.data?.message || 'Error al crear usuario');
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
            Nuevo Usuario
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
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Nombre</label>
              <input
                type="text"
                value={formData.first_name}
                onChange={(e) => setFormData({...formData, first_name: e.target.value})}
                className="w-full px-4 py-2.5 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-violet-500 text-slate-800 dark:text-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Apellido</label>
              <input
                type="text"
                value={formData.last_name}
                onChange={(e) => setFormData({...formData, last_name: e.target.value})}
                className="w-full px-4 py-2.5 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-violet-500 text-slate-800 dark:text-white"
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Nombre de usuario *</label>
            <input
              type="text"
              required
              value={formData.username}
              onChange={(e) => setFormData({...formData, username: e.target.value})}
              className="w-full px-4 py-2.5 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-violet-500 text-slate-800 dark:text-white"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Email *</label>
            <input
              type="email"
              required
              value={formData.email}
              onChange={(e) => setFormData({...formData, email: e.target.value})}
              className="w-full px-4 py-2.5 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-violet-500 text-slate-800 dark:text-white"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Contraseña *</label>
            <input
              type="password"
              required
              minLength={8}
              value={formData.password}
              onChange={(e) => setFormData({...formData, password: e.target.value})}
              className="w-full px-4 py-2.5 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-violet-500 text-slate-800 dark:text-white"
              placeholder="Mínimo 8 caracteres"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Rol *</label>
            <select
              value={formData.role}
              onChange={(e) => setFormData({...formData, role: e.target.value})}
              className="w-full px-4 py-2.5 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-violet-500 text-slate-800 dark:text-white"
            >
              <option value="user">Usuario</option>
              <option value="viewer">Solo Lectura</option>
              <option value="auditor">Auditor</option>
              <option value="iso_manager">Gestor ISO</option>
              <option value="org_admin">Administrador</option>
            </select>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Cargo</label>
              <input
                type="text"
                value={formData.job_title}
                onChange={(e) => setFormData({...formData, job_title: e.target.value})}
                className="w-full px-4 py-2.5 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-violet-500 text-slate-800 dark:text-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Departamento</label>
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
              Cancelar
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-4 py-2.5 bg-gradient-to-r from-violet-500 to-fuchsia-500 text-white rounded-xl font-medium flex items-center gap-2 disabled:opacity-50"
            >
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
              Crear Usuario
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Modal para editar usuario
const EditUserModal = ({ user, onClose, onSuccess }) => {
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
            Editar Usuario
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
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Rol</label>
            <select
              value={formData.role}
              onChange={(e) => setFormData({...formData, role: e.target.value})}
              className="w-full px-4 py-2.5 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-800 dark:text-white"
            >
              <option value="user">Usuario</option>
              <option value="viewer">Solo Lectura</option>
              <option value="auditor">Auditor</option>
              <option value="iso_manager">Gestor ISO</option>
              <option value="org_admin">Administrador</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Cargo</label>
            <input
              type="text"
              value={formData.job_title}
              onChange={(e) => setFormData({...formData, job_title: e.target.value})}
              className="w-full px-4 py-2.5 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-800 dark:text-white"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Departamento</label>
            <input
              type="text"
              value={formData.department}
              onChange={(e) => setFormData({...formData, department: e.target.value})}
              className="w-full px-4 py-2.5 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-800 dark:text-white"
            />
          </div>
          
          <div className="flex justify-end gap-3 pt-4">
            <button type="button" onClick={onClose} className="px-4 py-2.5 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-xl">
              Cancelar
            </button>
            <button type="submit" disabled={saving} className="px-4 py-2.5 bg-gradient-to-r from-violet-500 to-fuchsia-500 text-white rounded-xl font-medium flex items-center gap-2 disabled:opacity-50">
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
              Guardar Cambios
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Modal para resetear contraseña
const PasswordResetModal = ({ user, onClose, onSuccess }) => {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (password !== confirmPassword) {
      setError('Las contraseñas no coinciden');
      return;
    }
    
    try {
      setSaving(true);
      setError(null);
      await settingsService.resetPassword(user.id, password);
      onSuccess();
    } catch (err) {
      setError('Error al cambiar contraseña');
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
            Cambiar Contraseña
          </h3>
          <button onClick={onClose} className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg">
            <X className="w-5 h-5 text-slate-400" />
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Establecer nueva contraseña para <strong>{user.full_name}</strong>
          </p>
          
          {error && (
            <div className="p-3 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg text-red-600 dark:text-red-300 text-sm">
              {error}
            </div>
          )}
          
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Nueva Contraseña</label>
            <input
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2.5 bg-white dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-800 dark:text-white"
              placeholder="Mínimo 8 caracteres"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Confirmar Contraseña</label>
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
              Cancelar
            </button>
            <button type="submit" disabled={saving} className="px-4 py-2.5 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-xl font-medium flex items-center gap-2 disabled:opacity-50">
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Key className="w-4 h-4" />}
              Cambiar Contraseña
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default UsersManagement;
