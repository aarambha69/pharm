import { useState, useEffect } from 'react';
import axios from 'axios';
import { Plus, Search, Edit3, ShieldAlert, Key, MapPin, Phone, Hash, MoreVertical, Filter, Download } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import SuperAdminLayout from '../../components/SuperAdminLayout';

const Clients = ({ onLogout }) => {
    const [clients, setClients] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [formData, setFormData] = useState({
        pharmacy_name: '',
        address: '',
        pan_number: '',
        contact_number: '',
        package_id: '1',
        duration_days: '365'
    });

    useEffect(() => {
        fetchClients();
    }, []);

    const fetchClients = async () => {
        try {
            const response = await axios.get('/api/super/clients', {
                headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
            });
            setClients(response.data);
        } catch (err) {
            console.error('Failed to fetch clients', err);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await axios.post('/api/super/clients', formData, {
                headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
            });
            setShowModal(false);
            fetchClients();
            setFormData({ pharmacy_name: '', address: '', pan_number: '', contact_number: '', package_id: '1', duration_days: '365' });
        } catch (err) {
            alert('Failed to register client');
        }
    };

    return (
        <SuperAdminLayout onLogout={onLogout}>
            <div className="space-y-8">
                {/* Actions Bar */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                    <div className="relative group max-w-lg w-full">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-indigo-600 transition-colors" size={20} />
                        <input
                            type="text"
                            placeholder="Search pharmacies, PAN, or System ID..."
                            className="w-full pl-12 pr-4 py-4 bg-white border border-slate-200 rounded-[20px] shadow-sm focus:outline-none focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 transition-all font-medium"
                        />
                    </div>

                    <div className="flex items-center gap-3">
                        <button className="p-4 bg-white border border-slate-200 rounded-[20px] text-slate-600 hover:bg-slate-50 transition-all shadow-sm">
                            <Filter size={20} />
                        </button>
                        <button className="p-4 bg-white border border-slate-200 rounded-[20px] text-slate-600 hover:bg-slate-50 transition-all shadow-sm">
                            <Download size={20} />
                        </button>
                        <button
                            onClick={() => setShowModal(true)}
                            className="bg-indigo-600 hover:bg-indigo-700 text-white px-8 py-4 rounded-[20px] font-bold flex items-center gap-3 transition-all shadow-lg shadow-indigo-600/20 active:scale-95"
                        >
                            <Plus size={20} /> <span className="hidden sm:inline">Register Client</span>
                        </button>
                    </div>
                </div>

                {/* Clients Table */}
                <div className="bg-white rounded-[40px] shadow-premium border border-slate-100 overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="bg-slate-50/50 text-slate-500 text-[11px] font-black uppercase tracking-[0.2em]">
                                    <th className="px-10 py-6">Pharmacy Identity</th>
                                    <th className="px-10 py-6">Control Data</th>
                                    <th className="px-10 py-6">License Package</th>
                                    <th className="px-10 py-6">Status</th>
                                    <th className="px-10 py-6 text-right">Operations</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-50">
                                {clients.map((client) => (
                                    <tr key={client.id} className="hover:bg-indigo-50/30 transition-all duration-300 group">
                                        <td className="px-10 py-8">
                                            <div className="flex items-center gap-5">
                                                <div className="w-14 h-14 bg-white rounded-2xl shadow-sm border border-slate-100 flex items-center justify-center font-black text-indigo-600 text-xl group-hover:scale-110 transition-transform">
                                                    {client.pharmacy_name.charAt(0)}
                                                </div>
                                                <div>
                                                    <p className="font-black text-slate-800 text-lg leading-tight">{client.pharmacy_name}</p>
                                                    <div className="flex items-center gap-4 mt-2">
                                                        <div className="flex items-center gap-1.5 text-xs font-bold text-slate-400">
                                                            <MapPin size={12} className="text-indigo-400" /> {client.address}
                                                        </div>
                                                        <div className="flex items-center gap-1.5 text-xs font-bold text-slate-400">
                                                            <Phone size={12} className="text-emerald-400" /> {client.contact_number}
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-10 py-8">
                                            <div className="space-y-1.5">
                                                <div className="flex items-center gap-2">
                                                    <Hash size={12} className="text-slate-400" />
                                                    <span className="text-xs font-bold text-slate-600 uppercase tracking-wider">{client.client_id_code}</span>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <ShieldAlert size={12} className="text-slate-400" />
                                                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">PAN: {client.pan_number || 'N/A'}</span>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-10 py-8">
                                            <div className="inline-flex flex-col">
                                                <span className={`px-4 py-2 rounded-xl text-xs font-black uppercase tracking-widest inline-block ${client.package_name === 'Premium' ? 'bg-amber-100 text-amber-600' : 'bg-indigo-50 text-indigo-600'
                                                    }`}>
                                                    {client.package_name} Plan
                                                </span>
                                                <div className="flex items-center gap-2 mt-2 text-[10px] font-bold text-slate-400 px-1 uppercase">
                                                    Exp: {new Date(client.license_expiry).toLocaleDateString()}
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-10 py-8">
                                            <div className="flex items-center gap-2.5">
                                                <div className={`w-2 h-2 rounded-full animate-pulse ${client.status === 'active' ? 'bg-emerald-500' : 'bg-red-500'}`}></div>
                                                <span className={`text-[11px] font-black uppercase tracking-widest ${client.status === 'active' ? 'text-emerald-600' : 'text-red-500'}`}>
                                                    {client.status}
                                                </span>
                                            </div>
                                        </td>
                                        <td className="px-10 py-8 text-right">
                                            <div className="flex justify-end gap-3 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                                                <OperationBtn icon={<Edit3 size={18} />} color="text-indigo-600 bg-indigo-50" />
                                                <OperationBtn icon={<Key size={18} />} color="text-amber-600 bg-amber-50" />
                                                <button className="p-3 bg-red-50 text-red-600 rounded-[14px] hover:bg-red-600 hover:text-white transition-all">
                                                    <MoreVertical size={18} />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {loading && (
                        <div className="p-20 flex flex-col items-center justify-center gap-4">
                            <div className="w-10 h-10 border-4 border-indigo-100 border-t-indigo-600 rounded-full animate-spin"></div>
                            <p className="text-xs font-black text-slate-400 uppercase tracking-[0.2em]">Synchronizing Cloud Data...</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Modern Modal */}
            <AnimatePresence>
                {showModal && (
                    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xl z-50 flex items-center justify-center p-6">
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0, y: 20 }}
                            animate={{ scale: 1, opacity: 1, y: 0 }}
                            exit={{ scale: 0.9, opacity: 0, y: 20 }}
                            className="bg-white rounded-[48px] shadow-2xl w-full max-w-2xl overflow-hidden border border-white/20"
                        >
                            <div className="p-12 pb-8 flex justify-between items-start">
                                <div>
                                    <h3 className="text-4xl font-black text-slate-800 tracking-tight">Register <span className="text-indigo-600">Client</span></h3>
                                    <p className="text-slate-500 font-medium mt-2 text-lg">Initialize a new pharmacy entity in the ecosystem.</p>
                                </div>
                                <button onClick={() => setShowModal(false)} className="w-12 h-12 rounded-full border border-slate-100 flex items-center justify-center text-slate-400 hover:bg-slate-50 transition-all">
                                    ✕
                                </button>
                            </div>

                            <form onSubmit={handleSubmit} className="p-12 pt-0 space-y-8">
                                <div className="grid grid-cols-2 gap-8">
                                    <div className="col-span-2 space-y-2">
                                        <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Entity Official Name</label>
                                        <input required value={formData.pharmacy_name} onChange={(e) => setFormData({ ...formData, pharmacy_name: e.target.value })} className="premium-input text-lg font-bold" placeholder="e.g. Life Care Pharmacy Nepal" />
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Geographic Location</label>
                                        <input required value={formData.address} onChange={(e) => setFormData({ ...formData, address: e.target.value })} className="premium-input" placeholder="City, Ward No." />
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Govt. PAN Number</label>
                                        <input value={formData.pan_number} onChange={(e) => setFormData({ ...formData, pan_number: e.target.value })} className="premium-input" placeholder="9 Digit TIN/PAN" />
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Primary Communication</label>
                                        <input required value={formData.contact_number} onChange={(e) => setFormData({ ...formData, contact_number: e.target.value })} className="premium-input" placeholder="Office Phone" />
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Target Package</label>
                                        <select value={formData.package_id} onChange={(e) => setFormData({ ...formData, package_id: e.target.value })} className="premium-input appearance-none">
                                            <option value="1">Enterprise Basic</option>
                                            <option value="2">Business Standard</option>
                                            <option value="3">Premium Corporate</option>
                                        </select>
                                    </div>
                                </div>

                                <div className="flex gap-4 pt-4">
                                    <button type="button" onClick={() => setShowModal(false)} className="flex-1 py-5 rounded-[24px] font-black text-slate-500 hover:bg-slate-50 transition-all border border-transparent">
                                        Abort Request
                                    </button>
                                    <button type="submit" className="flex-[1.5] py-5 bg-indigo-600 text-white rounded-[24px] font-black text-lg shadow-xl shadow-indigo-600/30 hover:bg-indigo-700 transition-all active:scale-[0.98]">
                                        Finalize Registration
                                    </button>
                                </div>
                            </form>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>
        </SuperAdminLayout>
    );
};

const OperationBtn = ({ icon, color }) => (
    <button className={`p-3 rounded-[14px] transition-all hover:scale-110 active:scale-95 shadow-sm ${color}`}>
        {icon}
    </button>
);

export default Clients;
