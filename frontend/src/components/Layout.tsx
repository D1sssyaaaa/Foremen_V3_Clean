import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { NotificationBell } from './NotificationBell';

export function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const menuItems = [
    { path: '/', label: 'Главная', icon: '🏠', roles: [] },
    { path: '/objects', label: 'Объекты', icon: 'building', roles: [] },
    { path: '/timesheets', label: 'Табели РТБ', icon: '📅', roles: ['HR_MANAGER', 'MANAGER', 'ADMIN'] },
    { path: '/material-requests', label: 'Заявки материалы', icon: '📦', roles: ['MATERIALS_MANAGER', 'PROCUREMENT_MANAGER', 'MANAGER', 'ADMIN'] },
    { path: '/equipment-orders', label: 'Аренда техники', icon: '🚜', roles: ['EQUIPMENT_MANAGER', 'MANAGER', 'ADMIN'] },
    { path: '/upd', label: 'УПД', icon: '📄', roles: ['ACCOUNTANT', 'MATERIALS_MANAGER', 'MANAGER', 'ADMIN'] },
    { path: '/analytics', label: 'Аналитика', icon: '📊', roles: ['MANAGER', 'ADMIN', 'ACCOUNTANT'] },
    { path: '/admin', label: 'Настройки', icon: '⚙️', roles: ['ADMIN'] },
  ];

  const availableMenuItems = menuItems.filter(item => {
    if (item.roles.length === 0) return true;
    return user?.roles.some(role => item.roles.includes(role));
  });

  return (
    <div className="flex flex-col min-h-screen bg-[var(--bg-ios)] text-[var(--text-primary)] font-primary">
      {/* Header */}
      <div className="bg-[var(--bg-card)] border-b border-[var(--separator)] px-6 py-4 flex justify-between items-center sticky top-0 z-50">
        <h1 className="m-0 text-xl font-semibold tracking-tight">Снаб</h1>
        <div className="flex gap-4 items-center">
          <NotificationBell />
          <button
            onClick={() => navigate('/profile')}
            className="px-4 py-2 bg-[var(--bg-ios)] hover:bg-[var(--bg-pressed)] text-[var(--text-primary)] rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
          >
            <span>👤</span>
            <span>Профиль</span>
          </button>
          <button
            onClick={handleLogout}
            className="px-4 py-2 text-red-500 hover:bg-red-50 rounded-lg text-sm font-medium transition-colors"
          >
            Выход
          </button>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <div className="w-64 bg-[var(--bg-card)] border-r border-[var(--separator)] hidden md:block overflow-y-auto">
          <nav className="p-4 space-y-1">
            {availableMenuItems.map(item => {
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`
                    flex items-center gap-3 px-4 py-3 rounded-xl text-[15px] font-medium transition-all
                    ${isActive
                      ? 'bg-[var(--blue-ios)] text-white shadow-sm'
                      : 'text-[var(--text-secondary)] hover:bg-[var(--bg-ios)] hover:text-[var(--text-primary)]'
                    }
                  `}
                >
                  <span className={isActive ? 'text-white' : 'grayscale'}>{item.icon}</span>
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Main content */}
        <div className="flex-1 overflow-y-auto bg-[var(--bg-ios)] p-6 md:p-8">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </div>
      </div>
    </div>
  );
}
