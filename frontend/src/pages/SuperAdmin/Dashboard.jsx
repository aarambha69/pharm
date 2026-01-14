import { motion } from 'framer-motion';
import { Users, ShieldCheck, CreditCard, Activity, TrendingUp, Package, AlertTriangle, ArrowUpRight } from 'lucide-react';
import SuperAdminLayout from '../../components/SuperAdminLayout';

const SuperAdminDashboard = ({ onLogout }) => {
    const stats = [
        { label: 'Total Clients', value: '128', icon: <Users />, color: 'from-blue-500 to-blue-600', trend: '+12%' },
        { label: 'Active Licenses', value: '114', icon: <ShieldCheck />, color: 'from-emerald-500 to-emerald-600', trend: '+5%' },
        { label: 'Total Revenue', value: 'रु 425k', icon: <CreditCard />, color: 'from-indigo-500 to-indigo-600', trend: '+18%' },
        { label: 'System Uptime', value: '99.9%', icon: <Activity />, color: 'from-amber-500 to-amber-600', trend: 'Stable' },
    ];

    return (
        <SuperAdminLayout onLogout={onLogout}>
            <div className="space-y-10">
                {/* Hero Section */}
                <section className="relative rounded-[40px] bg-indigo-600 p-12 overflow-hidden group">
                    <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-white/10 rounded-full -mr-48 -mt-48 blur-3xl group-hover:bg-white/15 transition-all duration-1000"></div>
                    <div className="relative z-10 flex items-center justify-between">
                        <div className="max-w-2xl">
                            <h2 className="text-4xl font-black text-white mb-4 leading-tight">Welcome back, Chief!</h2>
                            <p className="text-indigo-100 text-lg opacity-80 leading-relaxed font-medium">
                                Your pharmacy ecosystem is thriving. You have <span className="text-white font-bold underline decoration-indigo-400">3 new activation requests</span> waiting for your approval today. Keep scaling!
                            </p>
                            <button className="mt-8 bg-white text-indigo-600 px-8 py-4 rounded-2xl font-bold flex items-center gap-2 hover:shadow-2xl hover:shadow-white/20 transition-all active:scale-95">
                                Review Pending Requests <ArrowUpRight size={20} />
                            </button>
                        </div>
                        <div className="hidden xl:block">
                            <div className="w-64 h-64 bg-white/10 backdrop-blur-2xl rounded-full flex items-center justify-center border border-white/20 animate-float">
                                <TrendingUp size={100} className="text-white" />
                            </div>
                        </div>
                    </div>
                </section>

                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                    {stats.map((stat, i) => (
                        <motion.div
                            key={i}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.1 }}
                            className="bg-white p-8 rounded-[32px] shadow-premium hover:shadow-premium-xl transition-all duration-300 group border border-slate-100"
                        >
                            <div className="flex justify-between items-start mb-6">
                                <div className={`w-14 h-14 bg-gradient-to-br ${stat.color} rounded-2xl flex items-center justify-center text-white shadow-lg group-hover:scale-110 transition-transform`}>
                                    {stat.icon}
                                </div>
                                <span className={`text-xs font-black px-3 py-1.5 rounded-full ${stat.trend.includes('+') ? 'bg-emerald-50 text-emerald-600' : 'bg-slate-50 text-slate-500'}`}>
                                    {stat.trend}
                                </span>
                            </div>
                            <p className="text-slate-500 font-bold text-sm uppercase tracking-widest">{stat.label}</p>
                            <h3 className="text-3xl font-black text-slate-800 mt-2">{stat.value}</h3>
                        </motion.div>
                    ))}
                </div>

                {/* Lower Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
                    {/* Recent Clients */}
                    <div className="lg:col-span-2 bg-white p-10 rounded-[40px] shadow-premium border border-slate-100">
                        <div className="flex items-center justify-between mb-8">
                            <h3 className="text-2xl font-black text-slate-800">Recent Activations</h3>
                            <button className="text-indigo-600 font-bold text-sm hover:underline">Download Report</button>
                        </div>
                        <div className="space-y-6">
                            {[1, 2, 3].map((_, i) => (
                                <div key={i} className="flex items-center justify-between p-6 bg-slate-50 rounded-3xl border border-transparent hover:border-indigo-100 hover:bg-white transition-all cursor-pointer group">
                                    <div className="flex items-center gap-6">
                                        <div className="w-14 h-14 bg-white rounded-2xl shadow-sm flex items-center justify-center group-hover:shadow-md transition-all">
                                            <div className="w-8 h-8 rounded-full bg-indigo-500/10 flex items-center justify-center text-indigo-600 font-black">
                                                {String.fromCharCode(65 + i)}
                                            </div>
                                        </div>
                                        <div>
                                            <p className="font-black text-slate-800 text-lg">Himalayan Biotech Pharma</p>
                                            <p className="text-sm font-medium text-slate-500 mt-1 flex items-center gap-2">
                                                <Package size={14} className="text-indigo-400" />
                                                Premium Corporate • 24 Users
                                            </p>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <p className="font-black text-slate-800">रु 25,000</p>
                                        <p className="text-[10px] font-bold text-emerald-600 uppercase mt-1 tracking-widest">Active License</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                        <button className="w-full mt-8 py-5 border-2 border-dashed border-slate-200 rounded-3xl text-slate-400 font-bold hover:border-indigo-300 hover:text-indigo-600 transition-all">
                            Explore All Clients
                        </button>
                    </div>

                    {/* System Health / Alerts */}
                    <div className="bg-[#0f172a] p-10 rounded-[40px] shadow-2xl relative overflow-hidden">
                        <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/20 blur-3xl"></div>
                        <h3 className="text-2xl font-black text-white mb-8">System Health</h3>
                        <div className="space-y-8">
                            <HealthItem label="Database Gateway" status="Operational" percentage={98} />
                            <HealthItem label="License Server" status="Operational" percentage={100} />
                            <HealthItem label="Billing API" status="Congested" percentage={75} />
                            <HealthItem label="Backup Engine" status="Operational" percentage={100} />
                        </div>

                        <div className="mt-12 bg-amber-500/10 border border-amber-500/20 p-6 rounded-3xl">
                            <div className="flex items-start gap-4">
                                <AlertTriangle className="text-amber-500 shrink-0" size={24} />
                                <div>
                                    <p className="text-amber-200 font-bold text-sm">Action Required</p>
                                    <p className="text-xs text-amber-500/70 mt-1 font-medium leading-relaxed">
                                        Server memory usage exceeded 85% in last 1 hour. Consider scaling the cluster.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </SuperAdminLayout>
    );
};

const HealthItem = ({ label, status, percentage }) => (
    <div className="space-y-2">
        <div className="flex justify-between items-end">
            <div>
                <p className="text-slate-400 text-xs font-bold uppercase tracking-widest">{label}</p>
                <p className={`text-xs font-bold mt-1 ${status === 'Operational' ? 'text-emerald-400' : 'text-amber-400'}`}>
                    {status}
                </p>
            </div>
            <p className="text-white font-black text-sm">{percentage}%</p>
        </div>
        <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
            <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${percentage}%` }}
                transition={{ duration: 1, delay: 0.5 }}
                className={`h-full ${status === 'Operational' ? 'bg-emerald-500' : 'bg-amber-500'}`}
            ></motion.div>
        </div>
    </div>
);

export default SuperAdminDashboard;
