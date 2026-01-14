import { motion } from 'framer-motion';
import { Activity, ShoppingBag, Package, AlertCircle, TrendingUp, Plus, ArrowRight } from 'lucide-react';
import AdminLayout from '../../components/AdminLayout';

const AdminDashboard = ({ onLogout, user }) => {
    const stats = [
        { label: "Today's Sales", value: 'रु 12,450', icon: <ShoppingBag />, color: 'bg-emerald-500', trend: '+8%' },
        { label: 'Low Stock', value: '14', icon: <AlertCircle />, color: 'bg-amber-500', trend: 'Critical' },
        { label: 'Total Stock', value: '842', icon: <Package />, color: 'bg-blue-500', trend: '+2%' },
        { label: 'Footfall', value: '86', icon: <Activity />, color: 'bg-indigo-500', trend: '+15%' },
    ];

    return (
        <AdminLayout onLogout={onLogout} pharmacyName={user?.pharmacy_name}>
            <div className="space-y-12">
                {/* Welcome Section */}
                <div className="flex items-end justify-between">
                    <div>
                        <h1 className="text-4xl font-black text-slate-800 tracking-tight">System Core</h1>
                        <p className="text-slate-500 font-medium mt-1">Real-time snapshots of your pharmacy operations.</p>
                    </div>
                    <button className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-[20px] font-black shadow-xl shadow-blue-600/20 active:scale-95 transition-all flex items-center gap-3">
                        <Plus size={20} /> New Billing Entry
                    </button>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                    {stats.map((stat, i) => (
                        <motion.div
                            key={i}
                            whileHover={{ y: -8 }}
                            className="bg-white p-8 rounded-[40px] shadow-premium border border-slate-100 group cursor-pointer overflow-hidden relative"
                        >
                            <div className="absolute top-0 right-0 w-24 h-24 bg-slate-50 rounded-full -mr-12 -mt-12 group-hover:bg-blue-50 transition-colors"></div>

                            <div className={`w-14 h-14 ${stat.color} rounded-2xl flex items-center justify-center text-white shadow-lg mb-6 relative z-10`}>
                                {stat.icon}
                            </div>

                            <div className="relative z-10">
                                <div className="flex items-center justify-between mb-1">
                                    <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{stat.label}</p>
                                    <span className={`text-[10px] font-bold px-2 py-1 rounded-full ${stat.trend.includes('+') ? 'bg-emerald-50 text-emerald-600' : 'bg-amber-50 text-amber-600'}`}>
                                        {stat.trend}
                                    </span>
                                </div>
                                <h3 className="text-3xl font-black text-slate-800">{stat.value}</h3>
                            </div>
                        </motion.div>
                    ))}
                </div>

                {/* Main Workspace */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
                    {/* Detailed Transactions */}
                    <div className="lg:col-span-2 bg-white rounded-[48px] shadow-premium border border-slate-100 p-10 overflow-hidden">
                        <div className="flex items-center justify-between mb-10">
                            <div className="flex items-center gap-4">
                                <div className="w-12 h-12 bg-blue-50 rounded-2xl flex items-center justify-center text-blue-600 shadow-sm border border-blue-100">
                                    <TrendingUp size={24} />
                                </div>
                                <h3 className="text-2xl font-black text-slate-800 tracking-tight">Recent Activity Stream</h3>
                            </div>
                            <button className="text-sm font-black text-blue-600 hover:underline">Audits (2026)</button>
                        </div>

                        <div className="space-y-6">
                            {[1, 2, 3, 4].map((_, i) => (
                                <div key={i} className="flex items-center justify-between p-6 rounded-[32px] border border-slate-50 hover:border-blue-100 hover:bg-blue-50/20 transition-all group">
                                    <div className="flex items-center gap-5">
                                        <div className="w-14 h-14 bg-white rounded-2xl flex flex-col items-center justify-center border border-slate-100 shadow-sm font-black text-slate-400 group-hover:bg-blue-600 group-hover:text-white transition-all">
                                            <span className="text-[10px] leading-none mb-1">JAN</span>
                                            <span className="text-lg leading-none">{0 + i + 8}</span>
                                        </div>
                                        <div>
                                            <p className="font-black text-slate-700">ORD-{(10293 + i).toString()}</p>
                                            <p className="text-xs font-bold text-slate-400 mt-1 uppercase tracking-widest">Cash Terminal • 12:{(15 + i * 10).toString()} PM</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-8 text-right">
                                        <div className="hidden sm:block">
                                            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-none mb-1">Payment</p>
                                            <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full uppercase">Verified</span>
                                        </div>
                                        <div>
                                            <p className="text-xl font-black text-slate-800 tracking-tight">रु {(450 + i * 120).toFixed(2)}</p>
                                            <button className="text-[10px] font-bold text-blue-500 hover:underline flex items-center gap-1 justify-end mt-1 uppercase">Print Copy <ArrowRight size={10} /></button>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Stock Warning Widget */}
                    <div className="bg-[#0f172a] rounded-[48px] shadow-2xl p-10 relative overflow-hidden group">
                        <div className="absolute top-0 left-0 w-32 h-32 bg-blue-500/10 blur-3xl -ml-16 -mt-16"></div>
                        <h3 className="text-2xl font-black text-white mb-10 tracking-tight">Vitals & Warnings</h3>

                        <div className="space-y-6">
                            {[1, 2, 3].map((_, i) => (
                                <div key={i} className="p-6 bg-white/[0.03] border border-white/5 rounded-[32px] hover:bg-white/[0.05] transition-all">
                                    <div className="flex justify-between items-start mb-4">
                                        <div className="w-10 h-10 bg-amber-500/10 rounded-xl flex items-center justify-center text-amber-500">
                                            <AlertCircle size={20} />
                                        </div>
                                        <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Only 0{i + 2} Left</span>
                                    </div>
                                    <h4 className="text-lg font-black text-white leading-tight">Augmentin Duo 625mg</h4>
                                    <p className="text-xs font-bold text-slate-500 mt-1 uppercase tracking-widest">Batch: BNV-10293X</p>
                                    <div className="h-1 w-full bg-white/5 rounded-full mt-4 overflow-hidden">
                                        <div className={`h-full bg-amber-500 w-${(2 + i) * 10}`}></div>
                                    </div>
                                </div>
                            ))}
                        </div>

                        <button className="w-full mt-10 py-5 bg-white text-[#0f172a] rounded-[24px] font-black shadow-xl hover:scale-105 active:scale-95 transition-all">
                            Generate Inventory Order
                        </button>
                    </div>
                </div>
            </div>
        </AdminLayout>
    );
};

export default AdminDashboard;
