import { useState } from 'react';
import axios from 'axios';
import { Pill, Phone, Lock, ArrowRight, ShieldCheck, Zap, Activity } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const Login = ({ onLogin }) => {
    const [phone, setPhone] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            const response = await axios.post('/api/login', { phone, password });
            localStorage.setItem('token', response.data.token);
            onLogin(response.data.user);
        } catch (err) {
            setError(err.response?.data?.message || 'Authentication failed. Please check your credentials.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-[#050810] overflow-hidden relative">
            {/* Animated Background Elements */}
            <motion.div
                animate={{
                    scale: [1, 1.2, 1],
                    opacity: [0.3, 0.2, 0.3],
                    x: [0, 50, 0],
                    y: [0, 30, 0]
                }}
                transition={{ duration: 15, repeat: Infinity, ease: "linear" }}
                className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] bg-indigo-600/20 rounded-full blur-[150px]"
            />
            <motion.div
                animate={{
                    scale: [1, 1.3, 1],
                    opacity: [0.2, 0.1, 0.2],
                    x: [0, -40, 0],
                    y: [0, -20, 0]
                }}
                transition={{ duration: 18, repeat: Infinity, ease: "linear" }}
                className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-blue-600/20 rounded-full blur-[150px]"
            />

            <div className="max-w-6xl w-full grid grid-cols-1 lg:grid-cols-2 gap-12 p-6 items-center z-10">
                {/* Left Side: Brand & Visual */}
                <motion.div
                    initial={{ opacity: 0, x: -50 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.8 }}
                    className="hidden lg:block space-y-8"
                >
                    <div className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-500/10 border border-indigo-500/20 rounded-full text-indigo-400 text-sm font-semibold">
                        <Zap size={16} /> Version 2.0 Now Live
                    </div>
                    <h1 className="text-6xl font-extrabold text-white leading-[1.1]">
                        Next-Gen <span className="text-gradient">Pharmacy</span> Management Solution.
                    </h1>
                    <p className="text-xl text-slate-400 max-w-lg leading-relaxed">
                        Experience the most powerful, secure, and intuitive platform designed for modern healthcare businesses.
                    </p>

                    <div className="grid grid-cols-2 gap-6 pt-8">
                        <FeatureBox icon={<ShieldCheck className="text-emerald-400" />} title="Secure License" desc="Machine-bound security" />
                        <FeatureBox icon={<Activity className="text-blue-400" />} title="Live Insights" desc="Real-time data tracking" />
                    </div>
                </motion.div>

                {/* Right Side: Login Form */}
                <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.6 }}
                    className="relative"
                >
                    <div className="bg-white/[0.03] backdrop-blur-xl border border-white/10 p-10 lg:p-14 rounded-[32px] shadow-2xl relative overflow-hidden group">
                        {/* Form Glow Effect */}
                        <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/10 blur-3xl -mr-16 -mt-16 group-hover:bg-indigo-500/20 transition-all duration-700"></div>

                        <div className="text-center mb-10">
                            <div className="bg-gradient-to-br from-indigo-500 to-blue-600 w-20 h-20 rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-2xl shadow-indigo-500/20 rotate-12 group-hover:rotate-0 transition-transform duration-500">
                                <Pill className="text-white w-10 h-10" />
                            </div>
                            <h2 className="text-3xl font-bold text-white mb-2">Welcome Back</h2>
                            <p className="text-slate-500">Sign in to manage your pharmacy ecosystem</p>
                        </div>

                        <form onSubmit={handleSubmit} className="space-y-6">
                            <div className="space-y-2">
                                <label className="text-xs font-bold text-slate-500 uppercase tracking-widest ml-1">Login ID / Phone</label>
                                <div className="relative group">
                                    <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-indigo-500 transition-colors">
                                        <Phone size={20} />
                                    </div>
                                    <input
                                        type="text"
                                        value={phone}
                                        onChange={(e) => setPhone(e.target.value)}
                                        className="w-full bg-white/[0.05] border border-white/10 text-white pl-12 pr-4 py-4 rounded-2xl focus:outline-none focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 transition-all text-lg"
                                        placeholder="Enter phone number"
                                        required
                                    />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <label className="text-xs font-bold text-slate-500 uppercase tracking-widest ml-1">Secure Password</label>
                                <div className="relative group">
                                    <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-indigo-500 transition-colors">
                                        <Lock size={20} />
                                    </div>
                                    <input
                                        type="password"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        className="w-full bg-white/[0.05] border border-white/10 text-white pl-12 pr-4 py-4 rounded-2xl focus:outline-none focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 transition-all text-lg"
                                        placeholder="••••••••"
                                        required
                                    />
                                </div>
                            </div>

                            <AnimatePresence>
                                {error && (
                                    <motion.div
                                        initial={{ opacity: 0, height: 0 }}
                                        animate={{ opacity: 1, height: 'auto' }}
                                        exit={{ opacity: 0, height: 0 }}
                                        className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-2xl text-sm font-medium flex items-center gap-3"
                                    >
                                        <div className="w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse"></div>
                                        {error}
                                    </motion.div>
                                )}
                            </AnimatePresence>

                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 text-white py-4 rounded-2xl font-bold shadow-[0_10px_30px_-10px_rgba(79,70,229,0.5)] flex items-center justify-center gap-3 transition-all active:scale-[0.98] disabled:opacity-70 group"
                            >
                                {loading ? (
                                    <div className="w-6 h-6 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                                ) : (
                                    <>
                                        Initialize Session <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                                    </>
                                )}
                            </button>
                        </form>

                        <div className="mt-10 pt-8 border-t border-white/10 text-center">
                            <p className="text-slate-500 text-sm font-medium">
                                Protected by <span className="text-slate-300">Aarambha Shield™</span> Technology
                            </p>
                        </div>
                    </div>
                </motion.div>
            </div>

            {/* Footer Branding */}
            <div className="absolute bottom-8 left-1/2 -translate-x-1/2 text-slate-700 text-xs font-bold uppercase tracking-[0.3em] pointer-events-none">
                Aarambha Softwares &copy; 2026
            </div>
        </div>
    );
};

const FeatureBox = ({ icon, title, desc }) => (
    <div className="p-4 bg-white/[0.03] border border-white/5 rounded-2xl flex items-start gap-4">
        <div className="mt-1">{icon}</div>
        <div>
            <h4 className="text-white font-bold text-sm">{title}</h4>
            <p className="text-slate-500 text-xs mt-0.5">{desc}</p>
        </div>
    </div>
);

export default Login;
