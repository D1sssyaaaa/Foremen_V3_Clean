import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './hooks/useAuth';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Layout } from './components/Layout';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { DashboardPage } from './pages/DashboardPage';
import { ProfilePage } from './pages/ProfilePage';
import { ObjectsPage } from './pages/ObjectsPage';
import { ObjectDetailPage } from './pages/ObjectDetailPage';
import { UPDPage } from './pages/UPDPage';
import { MaterialRequestsPage } from './pages/MaterialRequestsPage';
import { EquipmentOrdersPage } from './pages/EquipmentOrdersPage';
import { TimeSheetsPage } from './pages/TimeSheetsPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { NotificationsPage } from './pages/NotificationsPage';
import { AdminPage } from './pages/AdminPage';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout>
                  <DashboardPage />
                </Layout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <Layout>
                  <ProfilePage />
                </Layout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/objects"
            element={
              <ProtectedRoute>
                <Layout>
                  <ObjectsPage />
                </Layout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/objects/:id"
            element={
              <ProtectedRoute>
                <Layout>
                  <ObjectDetailPage />
                </Layout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/upd"
            element={
              <ProtectedRoute roles={['ACCOUNTANT', 'MATERIALS_MANAGER', 'MANAGER', 'ADMIN']}>
                <Layout>
                  <UPDPage />
                </Layout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/timesheets"
            element={
              <ProtectedRoute roles={['HR_MANAGER', 'MANAGER', 'ADMIN']}>
                <Layout>
                  <TimeSheetsPage />
                </Layout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/material-requests"
            element={
              <ProtectedRoute roles={['MATERIALS_MANAGER', 'PROCUREMENT_MANAGER', 'MANAGER', 'ADMIN']}>
                <Layout>
                  <MaterialRequestsPage />
                </Layout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/equipment-orders"
            element={
              <ProtectedRoute roles={['EQUIPMENT_MANAGER', 'MANAGER', 'ADMIN']}>
                <Layout>
                  <EquipmentOrdersPage />
                </Layout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/analytics"
            element={
              <ProtectedRoute roles={['MANAGER', 'ADMIN', 'ACCOUNTANT']}>
                <Layout>
                  <AnalyticsPage />
                </Layout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/notifications"
            element={
              <ProtectedRoute>
                <Layout>
                  <NotificationsPage />
                </Layout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/admin"
            element={
              <ProtectedRoute roles={['ADMIN']}>
                <Layout>
                  <AdminPage />
                </Layout>
              </ProtectedRoute>
            }
          />

          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
