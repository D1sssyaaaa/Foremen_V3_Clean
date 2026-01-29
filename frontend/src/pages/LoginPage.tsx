import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login({ username, password });
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка входа. Проверьте логин и пароль.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      minHeight: '100vh',
      backgroundColor: '#ecf0f1'
    }}>
      <div style={{ 
        backgroundColor: 'white', 
        padding: '40px', 
        borderRadius: '8px',
        boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
        width: '100%',
        maxWidth: '400px'
      }}>
        <h1 style={{ marginTop: 0, marginBottom: '10px', textAlign: 'center' }}>Снаб</h1>
        <p style={{ textAlign: 'center', color: '#7f8c8d', marginBottom: '30px' }}>
          Система учета затрат
        </p>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
              Логин
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoFocus
              style={{
                width: '100%',
                padding: '12px',
                border: '1px solid #ddd',
                borderRadius: '6px',
                fontSize: '14px',
                boxSizing: 'border-box'
              }}
            />
          </div>

          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
              Пароль
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={{
                width: '100%',
                padding: '12px',
                border: '1px solid #ddd',
                borderRadius: '6px',
                fontSize: '14px',
                boxSizing: 'border-box'
              }}
            />
          </div>

          {error && (
            <div style={{ 
              padding: '12px', 
              backgroundColor: '#fee', 
              color: '#c33',
              borderRadius: '6px',
              marginBottom: '20px',
              fontSize: '14px'
            }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: '12px',
              backgroundColor: '#3498db',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              fontSize: '16px',
              fontWeight: '500',
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.6 : 1
            }}
          >
            {loading ? 'Вход...' : 'Войти'}
          </button>

          <div style={{ 
            marginTop: '20px', 
            textAlign: 'center',
            fontSize: '14px',
            color: '#7f8c8d'
          }}>
            Нет аккаунта?{' '}
            <Link 
              to="/register" 
              style={{ 
                color: '#3498db', 
                textDecoration: 'none',
                fontWeight: '500'
              }}
            >
              Зарегистрироваться
            </Link>
          </div>
        </form>

        <div style={{ marginTop: '20px', padding: '12px', backgroundColor: '#f8f9fa', borderRadius: '6px' }}>
          <div style={{ fontSize: '12px', fontWeight: '600', marginBottom: '8px', color: '#2c3e50' }}>
            Тестовые пользователи:
          </div>
          <table style={{ width: '100%', fontSize: '11px', color: '#7f8c8d' }}>
            <tbody>
              <tr>
                <td style={{ padding: '2px 0' }}>admin</td>
                <td style={{ padding: '2px 0', textAlign: 'right' }}>admin123</td>
              </tr>
              <tr>
                <td style={{ padding: '2px 0' }}>accountant</td>
                <td style={{ padding: '2px 0', textAlign: 'right' }}>acc123</td>
              </tr>
              <tr>
                <td style={{ padding: '2px 0' }}>hr_manager</td>
                <td style={{ padding: '2px 0', textAlign: 'right' }}>hr123</td>
              </tr>
              <tr>
                <td style={{ padding: '2px 0' }}>materials_manager</td>
                <td style={{ padding: '2px 0', textAlign: 'right' }}>mat123</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
