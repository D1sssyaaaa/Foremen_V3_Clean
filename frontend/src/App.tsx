import { BrowserRouter as Router, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { AuthProvider } from './hooks/useAuth';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Layout } from './components/Layout';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { DashboardPage } from './pages/DashboardPage';
import { ProfilePage } from './pages/ProfilePage';
// Mini App Import
import { TimeSheetFlow } from "./miniapp/pages/TimeSheetFlow";
import { ObjectsPage } from './pages/ObjectsPage';
import { ObjectDetailPage } from './pages/ObjectDetailPage';
import { UPDPage } from './pages/UPDPage';
import { MaterialRequestsPage } from './pages/MaterialRequestsPage';
import { EquipmentOrdersPage } from './pages/EquipmentOrdersPage';

import { AnalyticsPage } from './pages/AnalyticsPage';
import { NotificationsPage } from './pages/NotificationsPage';
import { AdminPage } from './pages/AdminPage';
import { ManagerDashboardPage } from './pages/ManagerDashboardPage';

import { ManagerPortfolioPage } from './miniapp-manager/pages/ManagerPortfolioPage';
import { EstimateSelectionPage } from './miniapp/pages/EstimateSelectionPage';
import { MaterialRequestPage } from './miniapp/pages/MaterialRequestPage';
import { ManagerObjectDetailPage } from './miniapp-manager/pages/ManagerObjectDetailPage';
import { ObjectSelectPage } from './miniapp/pages/ObjectSelectPage';
import { EstimateViewPage } from './miniapp/pages/EstimateViewPage';
import { MyRequestsPage } from './miniapp/pages/MyRequestsPage';
import { ThemeProvider } from './miniapp-manager/context/ThemeContext';


function App() {
  return (
    <AuthProvider>
      <ThemeProvider>
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

            <Route
              path="/manager-dashboard"
              element={
                <ProtectedRoute roles={['MANAGER', 'ADMIN']}>
                  <Layout>
                    <ManagerDashboardPage />
                  </Layout>
                </ProtectedRoute>
              }
            />


            {/* Mini App Routes */}
            <Route path="/miniapp/timesheets" element={<TimeSheetFlow />} />
            <Route path="/miniapp/estimates" element={<EstimateSelectionPage />} />
            <Route path="/miniapp/estimate/:id/materials" element={<MaterialRequestPage />} />
            <Route path="/miniapp/manager" element={<ManagerPortfolioPage />} />
            <Route path="/miniapp/manager/object/:id" element={<ManagerObjectDetailPage />} />

            {/* New Mini App Routes for Foremen */}
            <Route path="/miniapp/objects" element={<ObjectSelectPage />} />
            <Route path="/miniapp/estimate/:objectId" element={<EstimateViewPage />} />
            <Route path="/miniapp/material-request/:objectId" element={<MaterialRequestPage />} />
            <Route path="/miniapp/my-requests" element={<MyRequestsPage />} />

            {/* Main App Routes */}
            <Route path="/" element={<Navigate to="/" />} />
          </Routes>
        </Router>
      </ThemeProvider>
    </AuthProvider>
  );
}

export default App;
