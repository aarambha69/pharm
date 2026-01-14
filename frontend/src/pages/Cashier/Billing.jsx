import { useState, useEffect } from 'react';
import axios from 'axios';
import { ShoppingCart, Plus, Trash2, Printer, Search, User, CreditCard, Calculator, FileText, Pill, ChevronDown, Monitor } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const Billing = ({ onLogout, user }) => {
    const [items, setItems] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [inventory, setInventory] = useState([
        { id: 1, name: 'Paracetamol 500mg', batch: 'BNX-1029', expiry: '2026-12', price: 5, stock: 100, category: 'Analgesic' },
        { id: 2, name: 'Amoxicillin 250mg', batch: 'AMX-2041', expiry: '2026-10', price: 15, stock: 50, category: 'Antibiotic' },
        { id: 3, name: 'Ibuprofen 400mg', batch: 'IBU-3091', expiry: '2027-01', price: 10, stock: 80, category: 'Nsaid' },
        { id: 4, name: 'Cetirizine 10mg', batch: 'CET-4055', expiry: '2026-08', price: 8, stock: 120, category: 'Antihistamine' }
    ]);
    const [cart, setCart] = useState([]);
    const [customer, setCustomer] = useState({ name: '', contact: '' });
    const [discount, setDiscount] = useState(0);
    const [vat, setVat] = useState(13);

    const calculateTotal = () => cart.reduce((acc, item) => acc + (item.price * item.quantity), 0);
    const subTotal = calculateTotal();
    const discAmt = (subTotal * discount) / 100;
    const taxable = subTotal - discAmt;
    const vatAmt = (taxable * vat) / 100;
    const grandTotal = taxable + vatAmt;

    const addToCart = (med) => {
        const existing = cart.find(c => c.id === med.id);
        if (existing) {
            setCart(cart.map(c => c.id === med.id ? { ...c, quantity: c.quantity + 1 } : c));
        } else {
            setCart([...cart, { ...med, quantity: 1 }]);
        }
    };

    const removeFromCart = (id) => setCart(cart.filter(c => c.id !== id));

    return (
        <div className="flex h-screen bg-[#0f172a] text-slate-300 overflow-hidden">
            {/* Left side: Search & Inventory Grid */}
            <div className="flex-1 flex flex-col p-8 overflow-hidden h-full">
                <header className="flex items-center justify-between mb-8 shrink-0">
                    <div>
                        <h1 className="text-3xl font-black text-white tracking-tight">Billing Terminal</h1>
                        <div className="flex items-center gap-2 mt-1">
                            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
                            <p className="text-xs font-bold text-slate-500 uppercase tracking-widest leading-none">Terminal ID: {user?.id || 'POS-01'} • Online</p>
                        </div>
                    </div>

                    <div className="relative group w-full max-w-xl">
                        <Search className="absolute left-5 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-blue-400 transition-colors" size={24} />
                        <input
                            type="text"
                            placeholder="Search by Medicine Name, Molecular formula or Batch..."
                            className="w-full bg-white/5 border border-white/10 rounded-[28px] pl-16 pr-6 py-5 text-white placeholder:text-slate-600 focus:outline-none focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 transition-all text-lg font-medium"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                </header>

                {/* Categories / Filters Quick Access */}
                <div className="flex items-center gap-3 mb-8 shrink-0 overflow-x-auto pb-2 no-scrollbar">
                    {['All Items', 'Analgesic', 'Antibiotic', 'Nsaid', 'Cardiac', 'Gastric', 'Syrups'].map((cat, i) => (
                        <button key={i} className={`px-6 py-3 rounded-full text-xs font-black uppercase tracking-widest transition-all whitespace-nowrap ${i === 0 ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/20' : 'bg-white/5 text-slate-500 hover:bg-white/10 hover:text-slate-300 border border-white/5'}`}>
                            {cat}
                        </button>
                    ))}
                </div>

                {/* Inventory Grid */}
                <div className="flex-1 overflow-y-auto custom-scrollbar pr-2 pb-8">
                    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                        {inventory.filter(m => m.name.toLowerCase().includes(searchTerm.toLowerCase())).map((med) => (
                            <motion.div
                                layout
                                key={med.id}
                                whileHover={{ y: -5, scale: 1.02 }}
                                className="bg-white/[0.03] border border-white/5 p-6 rounded-[32px] hover:bg-white/[0.05] hover:border-blue-500/30 transition-all cursor-pointer group relative overflow-hidden"
                                onClick={() => addToCart(med)}
                            >
                                <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-100 transition-opacity">
                                    <Plus size={24} className="text-blue-500" />
                                </div>

                                <div className="flex gap-4 mb-6">
                                    <div className="w-14 h-14 bg-white/5 rounded-2xl flex items-center justify-center border border-white/10 text-white font-black group-hover:bg-blue-600 transition-colors">
                                        <Pill size={28} />
                                    </div>
                                    <div>
                                        <h3 className="font-black text-white text-lg leading-tight group-hover:text-blue-400 transition-colors">{med.name}</h3>
                                        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-1 inline-block">{med.category}</span>
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-4 pt-6 border-t border-white/5">
                                    <div>
                                        <p className="text-[10px] font-black text-slate-600 uppercase tracking-widest">Pricing</p>
                                        <p className="text-xl font-black text-white">रु {med.price.toFixed(2)}</p>
                                    </div>
                                    <div className="text-right">
                                        <p className="text-[10px] font-black text-slate-600 uppercase tracking-widest">Inventory</p>
                                        <p className={`text-xl font-black ${med.stock < 10 ? 'text-red-500' : 'text-slate-200'}`}>{med.stock} <span className="text-xs">PC</span></p>
                                    </div>
                                </div>

                                <div className="mt-4 flex items-center gap-2">
                                    <span className="w-1 h-1 rounded-full bg-slate-700"></span>
                                    <p className="text-[10px] font-bold text-slate-600 uppercase tracking-widest">Batch: {med.batch} • Exp: {med.expiry}</p>
                                </div>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Right side: Modern Cart / POS Interface */}
            <div className="w-[500px] bg-white flex flex-col shadow-[-20px_0_50px_rgba(0,0,0,0.2)] z-20">
                <div className="p-8 border-b border-slate-100 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center text-blue-600">
                            <Monitor size={20} />
                        </div>
                        <div>
                            <h2 className="text-xl font-black text-slate-800 tracking-tight">Active Invoice</h2>
                            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-[0.2em] mt-0.5">Counter POS #01</p>
                        </div>
                    </div>
                    <button onClick={onLogout} className="p-4 bg-slate-50 text-slate-400 hover:text-red-500 rounded-2xl transition-all">
                        <Trash2 size={20} />
                    </button>
                </div>

                {/* Customer Information Panel */}
                <div className="p-8 bg-slate-50/50 border-b border-slate-100">
                    <div className="grid grid-cols-2 gap-6">
                        <div className="space-y-1.5">
                            <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">Customer Name</label>
                            <div className="relative">
                                <User size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                                <input type="text" className="w-full bg-white border border-slate-200 rounded-xl pl-10 pr-4 py-3 text-sm font-bold text-slate-700 focus:outline-none focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 transition-all" placeholder="Anonymous Walk-in" />
                            </div>
                        </div>
                        <div className="space-y-1.5">
                            <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">Contact No.</label>
                            <input type="text" className="w-full bg-white border border-slate-200 rounded-xl px-4 py-3 text-sm font-bold text-slate-700 focus:outline-none focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 transition-all" placeholder="+977-98..." />
                        </div>
                    </div>
                </div>

                {/* Cart Items List */}
                <div className="flex-1 overflow-y-auto p-8 space-y-4 custom-scrollbar-light">
                    <AnimatePresence mode="popLayout">
                        {cart.length === 0 ? (
                            <div className="h-full flex flex-col items-center justify-center text-center opacity-30 select-none pt-20">
                                <ShoppingCart size={80} className="text-slate-300 mb-6" />
                                <p className="text-lg font-black text-slate-400 uppercase tracking-widest leading-tight">Terminal Empty<br /><span className="text-xs font-bold">Waiting for input...</span></p>
                            </div>
                        ) : (
                            cart.map((item) => (
                                <motion.div
                                    key={item.id}
                                    initial={{ opacity: 0, x: 20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    exit={{ opacity: 0, x: -20, scale: 0.95 }}
                                    className="p-6 bg-slate-50 rounded-[32px] border border-slate-100 relative group"
                                >
                                    <div className="flex items-start justify-between">
                                        <div className="flex gap-4">
                                            <div className="w-12 h-12 bg-white rounded-2xl flex items-center justify-center font-black text-blue-600 shadow-sm border border-slate-100">
                                                {item.quantity}
                                            </div>
                                            <div>
                                                <h4 className="font-black text-slate-800 text-lg leading-tight">{item.name}</h4>
                                                <p className="text-[10px] font-bold text-slate-400 mt-1 uppercase tracking-widest">Batch: {item.batch} • Unit रु {item.price.toFixed(2)}</p>
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <p className="text-lg font-black text-slate-800 tracking-tight">रु {(item.price * item.quantity).toFixed(2)}</p>
                                            <button onClick={() => removeFromCart(item.id)} className="text-[10px] font-black text-red-400 hover:text-red-600 uppercase tracking-widest mt-1">Remove</button>
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-2 mt-4 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <button onClick={() => {
                                            if (item.quantity > 1) setCart(cart.map(c => c.id === item.id ? { ...c, quantity: c.quantity - 1 } : c))
                                        }} className="w-8 h-8 rounded-full bg-white border border-slate-200 flex items-center justify-center text-slate-600 hover:bg-slate-50 transition-all font-black">-</button>
                                        <button onClick={() => {
                                            setCart(cart.map(c => c.id === item.id ? { ...c, quantity: c.quantity + 1 } : c))
                                        }} className="w-8 h-8 rounded-full bg-white border border-slate-200 flex items-center justify-center text-slate-600 hover:bg-slate-50 transition-all font-black">+</button>
                                    </div>
                                </motion.div>
                            ))
                        )}
                    </AnimatePresence>
                </div>

                {/* Calculator / Payment Summary */}
                <div className="p-10 bg-[#0f172a] rounded-t-[50px] shadow-[0_-20px_50px_rgba(0,0,0,0.3)]">
                    <div className="space-y-4 mb-8">
                        <div className="flex justify-between items-center text-slate-500">
                            <span className="text-[11px] font-black uppercase tracking-[0.2em]">Merchandise Subtotal</span>
                            <span className="text-lg font-black text-white">रु {subTotal.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between items-center text-slate-500">
                            <div className="flex items-center gap-2">
                                <span className="text-[11px] font-black uppercase tracking-[0.2em]">Discounts</span>
                                <div className="flex items-center gap-1 bg-white/5 px-2 py-0.5 rounded-lg border border-white/5">
                                    <input type="number" className="bg-transparent w-8 text-xs font-black text-blue-400 focus:outline-none text-center" value={discount} onChange={(e) => setDiscount(e.target.value)} />
                                    <span className="text-[10px]">%</span>
                                </div>
                            </div>
                            <span className="text-lg font-black text-red-400">- रु {discAmt.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between items-center text-slate-500">
                            <span className="text-[11px] font-black uppercase tracking-[0.2em]">Govt Taxes (VAT {vat}%)</span>
                            <span className="text-lg font-black text-amber-500">+ रु {vatAmt.toFixed(2)}</span>
                        </div>
                    </div>

                    <div className="flex items-end justify-between py-8 border-t border-white/5 mb-8">
                        <div>
                            <p className="text-[11px] font-black text-blue-500 uppercase tracking-[0.3em] mb-1">Grand Payable Amount</p>
                            <h3 className="text-5xl font-black text-white tracking-tighter italic">रु {grandTotal.toFixed(2)}</h3>
                        </div>
                        <div className="p-4 bg-white/5 rounded-2xl border border-white/10 text-center">
                            <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest leading-none mb-1">Payment</p>
                            <p className="text-white font-black text-sm">CASH-POS</p>
                        </div>
                    </div>

                    <button
                        className="w-full py-6 bg-gradient-to-r from-blue-600 to-indigo-700 hover:from-blue-500 hover:to-indigo-600 text-white rounded-[28px] font-black text-xl flex items-center justify-center gap-4 shadow-2xl shadow-blue-600/30 transition-all active:scale-[0.98] group"
                    >
                        <Printer size={24} className="group-hover:-rotate-12 transition-transform" />
                        FINALIZE & PRINT RECEIPT
                    </button>
                </div>
            </div>

            <style>{`
         .custom-scrollbar-light::-webkit-scrollbar { width: 4px; }
         .custom-scrollbar-light::-webkit-scrollbar-track { background: transparent; }
         .custom-scrollbar-light::-webkit-scrollbar-thumb { background: #e2e8f0; border-radius: 10px; }
         .no-scrollbar::-webkit-scrollbar { display: none; }
      `}</style>
        </div>
    );
};

export default Billing;
