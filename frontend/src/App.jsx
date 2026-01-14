import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import SuperAdminDashboard from './pages/SuperAdmin/Dashboard';
import Clients from './pages/SuperAdmin/Clients';
import AdminDashboard from './pages/Admin/Dashboard';
import Billing from './pages/Cashier/Billing';
import { useState, useEffect } from 'react';

function App() {
    const [user, setUser] = useState(JSON.parse(localStorage.getItem('user')) || null);

    const handleLogin = (userData) => {
        setUser(userData);
        localStorage.setItem('user', JSON.stringify(userData));
    };

    const handleLogout = () => {
        setUser(null);
        localStorage.removeItem('user');
        localStorage.removeItem('token');
    };

    return (
        <Router>
            <Routes>
                <Route path="/login" element={!user ? <Login onLogin={handleLogin} /> : <Navigate to="/" />} />

                <Route path="/" element={
                    user?.role === 'SUPER_ADMIN' ? <SuperAdminDashboard onLogout={handleLogout} /> :
                        user?.role === 'ADMIN' ? <AdminDashboard onLogout={handleLogout} user={user} /> :
                            user?.role === 'CASHIER' ? <Billing onLogout={handleLogout} user={user} /> :
                                <Navigate to="/login" />
                } />

                <Route path="/super/clients" element={
                    user?.role === 'SUPER_ADMIN' ? <Clients onLogout={handleLogout} /> : <Navigate to="/login" />
                } />

                {/* Add more routes here */}
            </Routes>
        </Router>
    );
}

export default App;
