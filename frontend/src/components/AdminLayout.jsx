import { motion } from 'framer-motion';
import { Pill, LayoutDashboard, ShoppingCart, Package, Users, BarChart2, Bell, LogOut, Search } from 'lucide-react';
import { useLocation, Link } from 'react-router-dom';

const AdminLayout = ({ children, onLogout, pharmacyName }) => {
    const location = useLocation();

    const navItems = [
        { icon: <LayoutDashboard size={22} />, label: 'Dashboard', path: '/' },
        { icon: <ShoppingCart size={22} />, label: 'Billing Terminal', path: '/billing' },
        { icon: <Package size={22} />, label: 'Inventory', path: '/inventory' },
        { icon: <Users size={22} />, label: 'Staff & Roles', path: '/staff' },
        { icon: <BarChart2 size={22} />, label: 'Analytics', path: '/reports' },
    ];

    return (
        <div className="flex h-screen bg-[#fcfdfe] overflow-hidden">
            {/* Sleek Admin Sidebar */}
            <aside className="w-80 bg-white border-r border-slate-100 flex flex-col z-20">
                <div className="p-8">
                    <div className="flex items-center gap-3">
                        <div className="w-12 h-12 bg-blue-600 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-600/20">
                            <Pill className="text-white animate-pulse" size={24} />
                        </div>
                        <div>
                            <h2 className="text-xl font-black text-slate-800 tracking-tight">AARAMBHA</h2>
                            <p className="text-[10px] font-bold text-blue-500 uppercase tracking-widest leading-none mt-1">Pharmacy Admin</p>
                        </div>
                    </div>
                </div>

                <nav className="flex-1 px-4 space-y-2 mt-4">
                    {navItems.map((item) => {
                        const isActive = location.pathname === item.path;
                        return (
                            <Link key={item.path} to={item.path}>
                                <div className={`flex items-center gap-4 px-6 py-4 rounded-3xl transition-all duration-300 group ${isActive ? 'bg-blue-600 text-white shadow-xl shadow-blue-600/20' : 'text-slate-500 hover:bg-slate-50 hover:text-blue-600'
                                    }`}>
                                    <span className={isActive ? 'text-white' : 'group-hover:scale-110 transition-transform'}>{item.icon}</span>
                                    <span className="font-bold text-sm">{item.label}</span>
                                </div>
                            </Link>
                        );
                    })}
                </nav>

                <div className="p-4 bg-slate-50/50 m-6 rounded-[32px] border border-slate-100 text-center">
                    <Bell size={24} className="mx-auto text-amber-500 mb-2" />
                    <p className="text-xs font-black text-slate-800 uppercase tracking-wider">Stock Alert</p>
                    <p className="text-[10px] font-medium text-slate-500 mt-1">5 items expiring soon</p>
                    <button className="mt-3 text-[10px] font-black text-blue-600 uppercase underline decoration-blue-200">Review</button>
                </div>

                <div className="p-6 border-t border-slate-100">
                    <button onClick={onLogout} className="w-full flex items-center gap-4 px-6 py-4 rounded-2xl text-slate-400 hover:bg-red-50 hover:text-red-500 transition-all font-bold">
                        <LogOut size={20} /> Sign Out
                    </button>
                </div>
            </aside>

            <div className="flex-1 flex flex-col overflow-hidden">
                {/* Modern Header */}
                <header className="h-24 bg-white/50 backdrop-blur-md border-b border-slate-100 flex items-center justify-between px-12 z-10">
                    <div className="flex items-center gap-4 bg-slate-100/50 px-6 py-3 rounded-2xl w-[450px] border border-slate-200/50">
                        <Search size={18} className="text-slate-400" />
                        <input type="text" placeholder="Search medicines by name or batch..." className="bg-transparent border-none focus:outline-none text-sm w-full font-medium" />
                    </div>

                    <div className="flex items-center gap-6">
                        <div className="text-right">
                            <p className="text-sm font-black text-slate-800 leading-none">{pharmacyName || 'Life Care Pharmacy'}</p>
                            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-1">Licensed Branch</p>
                        </div>
                        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 p-[2px] shadow-lg shadow-blue-500/20">
                            <div className="w-full h-full bg-white rounded-[14px]"></div>
                        </div>
                    </div>
                </header>

                <main className="flex-1 overflow-y-auto p-12 custom-scrollbar">
                    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
                        {children}
                    </motion.div>
                </main>
            </div>
        </div>
    );
};

export default AdminLayout;
