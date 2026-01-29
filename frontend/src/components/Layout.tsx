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
    { path: '/', label: 'Главная', roles: [] },
    { path: '/objects', label: 'Объекты', roles: [] },
    { path: '/timesheets', label: 'Табели РТБ', roles: ['HR_MANAGER', 'MANAGER', 'ADMIN'] },
    { path: '/material-requests', label: 'Заявки материалы', roles: ['MATERIALS_MANAGER', 'PROCUREMENT_MANAGER', 'MANAGER', 'ADMIN'] },
    { path: '/equipment-orders', label: 'Аренда техники', roles: ['EQUIPMENT_MANAGER', 'MANAGER', 'ADMIN'] },
    { path: '/upd', label: 'УПД', roles: ['ACCOUNTANT', 'MATERIALS_MANAGER', 'MANAGER', 'ADMIN'] },
    { path: '/analytics', label: 'Аналитика', roles: ['MANAGER', 'ADMIN', 'ACCOUNTANT'] },
    { path: '/admin', label: '⚙️ Администрирование', roles: ['ADMIN'] },
  ];

  const availableMenuItems = menuItems.filter(item => {
    if (item.roles.length === 0) return true;
    return user?.roles.some(role => item.roles.includes(role));
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', fontFamily: 'system-ui, -apple-system, sans-serif' }}>
      {/* Header */}
      <div style={{
        backgroundColor: '#2c3e50',
        color: 'white',
        padding: '15px 30px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}>
        <h1 style={{ margin: 0, fontSize: '24px' }}>Снаб</h1>
        <div style={{ display: 'flex', gap: '15px', alignItems: 'center' }}>
          <NotificationBell />
          <button
            onClick={() => navigate('/profile')}
            style={{
              padding: '8px 16px',
              backgroundColor: '#3498db',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            <span>👤</span>
            <span>Профиль</span>
          </button>
          <button
            onClick={handleLogout}
            style={{
              padding: '8px 16px',
              backgroundColor: '#e74c3c',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            Выход
          </button>
        </div>
      </div>

      <div style={{ display: 'flex', flex: 1 }}>
        {/* Sidebar */}
        <div style={{ 
          width: '250px', 
          backgroundColor: '#2c3e50', 
          color: 'white',
          padding: '20px',
          boxSizing: 'border-box'
        }}>
        
        <nav>
          {availableMenuItems.map(item => (
            <Link
              key={item.path}
              to={item.path}
              style={{
                display: 'block',
                padding: '12px 16px',
                marginBottom: '5px',
                borderRadius: '6px',
                textDecoration: 'none',
                color: 'white',
                backgroundColor: location.pathname === item.path ? '#34495e' : 'transparent',
                transition: 'background-color 0.2s'
              }}
              onMouseEnter={(e) => {
                if (location.pathname !== item.path) {
                  e.currentTarget.style.backgroundColor = '#34495e80';
                }
              }}
              onMouseLeave={(e) => {
                if (location.pathname !== item.path) {
                  e.currentTarget.style.backgroundColor = 'transparent';
                }
              }}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        </div>

        {/* Main content */}
        <div style={{ 
          flex: 1, 
          backgroundColor: '#ecf0f1',
          padding: '30px',
          overflowY: 'auto'
        }}>
          {children}
        </div>
      </div>
    </div>
  );
}
