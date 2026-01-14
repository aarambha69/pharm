import { motion } from 'framer-motion';
import { Shield, LayoutDashboard, Users, Package, Bell, Settings, LogOut, ChevronRight } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';

const SuperAdminLayout = ({ children, onLogout }) => {
    const location = useLocation();

    const navItems = [
        { icon: <LayoutDashboard size={22} />, label: 'Dashboard', path: '/' },
        { icon: <Users size={22} />, label: 'Client Accounts', path: '/super/clients' },
        { icon: <Package size={22} />, label: 'Package Builder', path: '/package-builder' },
        { icon: <Bell size={22} />, label: 'Global Alerts', path: '/alerts' },
        { icon: <Settings size={22} />, label: 'System Settings', path: '/settings' },
    ];

    return (
        <div className="flex h-screen bg-slate-50 overflow-hidden">
            {/* Premium Sidebar */}
            <aside className="w-80 bg-[#0f172a] text-slate-400 flex flex-col relative z-20 shadow-2xl">
                <div className="p-8">
                    <div className="flex items-center gap-3 group cursor-pointer">
                        <div className="w-12 h-12 bg-indigo-600 rounded-2xl flex items-center justify-center shadow-lg shadow-indigo-600/30 group-hover:scale-110 transition-transform duration-300">
                            <Shield className="text-white" size={28} />
                        </div>
                        <div>
                            <h2 className="text-2xl font-black text-white tracking-tight">AARAMBHA</h2>
                            <p className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest leading-none mt-1">Super Admin Console</p>
                        </div>
                    </div>
                </div>

                <nav className="flex-1 px-4 mt-4 space-y-2">
                    {navItems.map((item) => {
                        const isActive = location.pathname === item.path;
                        return (
                            <Link key={item.path} to={item.path}>
                                <motion.div
                                    whileHover={{ x: 5 }}
                                    className={`flex items-center justify-between px-6 py-4 rounded-2xl transition-all duration-300 group ${isActive
                                            ? 'bg-indigo-600 text-white shadow-xl shadow-indigo-600/20'
                                            : 'hover:bg-white/[0.03] hover:text-slate-200'
                                        }`}
                                >
                                    <div className="flex items-center gap-4">
                                        <span className={isActive ? 'text-white' : 'text-slate-500 group-hover:text-indigo-400 transition-colors'}>
                                            {item.icon}
                                        </span>
                                        <span className="font-bold text-sm tracking-wide">{item.label}</span>
                                    </div>
                                    {isActive && <ChevronRight size={18} />}
                                </motion.div>
                            </Link>
                        );
                    })}
                </nav>

                <div className="p-6">
                    <button
                        onClick={onLogout}
                        className="w-full flex items-center gap-4 px-6 py-4 rounded-2xl bg-red-500/5 text-red-400 hover:bg-red-500 hover:text-white transition-all duration-300 group shadow-sm hover:shadow-red-500/30"
                    >
                        <LogOut size={20} className="group-hover:-translate-x-1 transition-transform" />
                        <span className="font-bold text-sm">Sign Out System</span>
                    </button>
                </div>
            </aside>

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col relative overflow-hidden">
                {/* Sleek Top Header */}
                <header className="h-24 bg-white/80 backdrop-blur-md border-b border-slate-200/60 flex items-center justify-between px-12 z-10">
                    <div>
                        <h1 className="text-2xl font-black text-slate-800 tracking-tight">
                            {navItems.find(n => n.path === location.pathname)?.label || 'System Overview'}
                        </h1>
                        <p className="text-sm text-slate-500 font-medium">Manage your pharmaceutical business ecosystem</p>
                    </div>

                    <div className="flex items-center gap-6">
                        <div className="flex flex-col text-right">
                            <span className="text-sm font-black text-slate-800">Aarambha Aryal</span>
                            <span className="text-[10px] font-bold text-indigo-500 uppercase tracking-widest">Master Authority</span>
                        </div>
                        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500 to-blue-600 p-[3px] shadow-lg shadow-indigo-500/20">
                            <div className="w-full h-full bg-white rounded-[13px] flex items-center justify-center font-black text-indigo-600 text-lg">
                                AA
                            </div>
                        </div>
                    </div>
                </header>

                {/* Dynamic content with motion transition */}
                <main className="flex-1 overflow-y-auto p-12 custom-scrollbar">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5 }}
                    >
                        {children}
                    </motion.div>
                </main>
            </div>
        </div>
    );
};

export default SuperAdminLayout;
