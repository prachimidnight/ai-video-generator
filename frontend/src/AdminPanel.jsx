import React, { useState, useEffect } from 'react';
import {
    Users,
    Video,
    BarChart3,
    Settings,
    Plus,
    Search,
    Bell,
    Download,
    ChevronRight,
    Trash2,
    Edit,
    TrendingUp,
    TrendingDown,
    Activity,
    Shield,
    X,
    LayoutDashboard,
    CreditCard,
    ArrowLeft,
    DollarSign,
    CheckCircle2,
    Clock,
    AlertCircle,
    Globe,
    Lock,
    Cpu,
    Database,
    Zap,
    LogOut,
    Twitter,
    Linkedin,
    Github,
    Instagram
} from 'lucide-react';
import './AdminPanel.css';
import './AdminAIModel.css';
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const AI_MODELS = [
    {
        id: "gemini-1.5-pro",
        name: "Gemini 1.5 Pro",
        provider: "Google",
        inputPrice: "$1.25",
        outputPrice: "$5.00",
        estCostText: "$0.005-0.015",
        monthlyEst: "$0.10 / $100",
        tags: [{ icon: Zap, text: "High Reasoning" }, { icon: Database, text: "Complex Tasks" }]
    },
    {
        id: "gemini-2.5-flash",
        name: "Gemini 3 Flash Preview",
        provider: "Google",
        inputPrice: "$0.075",
        outputPrice: "$0.30",
        estCostText: "$0.002-0.008",
        monthlyEst: "$0.01 / $100",
        tags: [{ icon: Zap, text: "Fast Inference" }, { icon: Globe, text: "Function Calling" }]
    },
    {
        id: "veo-3.1-fast-generate-preview",
        name: "Veo Fast Generate",
        provider: "Google",
        inputPrice: "N/A",
        outputPrice: "N/A",
        estCostText: "Free (Preview)",
        monthlyEst: "$0.00 / $100",
        tags: [{ icon: Video, text: "Draft Videos" }, { icon: Zap, text: "Fast Generation" }]
    },
    {
        id: "veo-3.1-generate-preview",
        name: "Veo High Quality",
        provider: "Google",
        inputPrice: "N/A",
        outputPrice: "N/A",
        estCostText: "Premium Cost",
        monthlyEst: "$1.50 / $100",
        tags: [{ icon: Video, text: "1080p/4K" }, { icon: CheckCircle2, text: "Cinematic" }]
    }
];

const AdminPanel = ({ navigate }) => {
    const [view, setView] = useState('dashboard');
    const [usageData, setUsageData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [users, setUsers] = useState([]);
    const [showUserModal, setShowUserModal] = useState(false);
    const [modalMode, setModalMode] = useState('add');
    const [selectedUser, setSelectedUser] = useState(null);
    const [modalData, setModalData] = useState({
        full_name: '',
        email: '',
        subscription_tier: 'Basic',
        available_credits: 50,
        status: true
    });

    const [analyticsData, setAnalyticsData] = useState({
        weeklyUsage: [],
        modelDistribution: []
    });
    const [transactions, setTransactions] = useState([]);
    const [topAiUsers, setTopAiUsers] = useState([]);
    const [systemStats, setSystemStats] = useState({
        total_users: 0,
        total_generations: 0,
        total_revenue_inr: 0,
        system_load: '0%',
        revenue_formatted: '₹0'
    });

    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [userIdToDelete, setUserIdToDelete] = useState(null);

    // AI Models State
    const [activeModel, setActiveModel] = useState(AI_MODELS[1]); // Default to Gemini 3 Flash
    const [confirmModel, setConfirmModel] = useState(null);
    const [showModelModal, setShowModelModal] = useState(false);

    // Toast State
    const [toast, setToast] = useState({ show: false, message: '', type: 'success' });

    const showToast = (message, type = 'success') => {
        setToast({ show: true, message, type });
        setTimeout(() => setToast({ show: false, message: '', type: 'success' }), 3000);
    };

    useEffect(() => {
        const loadAllData = async () => {
            setLoading(true);
            try {
                await Promise.all([
                    fetchUsageData(),
                    fetchUsers(),
                    fetchAnalytics(),
                    fetchTransactions(),
                    fetchSystemStats(),
                    fetchTopAiUsers()
                ]);
            } catch (err) {
                console.error("Data loading error:", err);
            }
            setLoading(false);
        };
        loadAllData();
    }, []);

    const fetchAnalytics = async () => {
        try {
            const [weeklyRes, modelRes] = await Promise.all([
                fetch(`${API_BASE_URL}/admin/analytics/weekly`),
                fetch(`${API_BASE_URL}/admin/analytics/models`)
            ]);
            const weekly = await weeklyRes.json();
            const models = await modelRes.json();

            setAnalyticsData({
                weeklyUsage: weekly.status === 'success' ? weekly.data : [],
                modelDistribution: models.status === 'success' ? models.data : []
            });
        } catch (error) {
            console.error('Failed to fetch analytics:', error);
        }
    };

    const fetchTopAiUsers = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/admin/top-users`);
            const data = await response.json();
            if (data.status === 'success') {
                setTopAiUsers(data.data);
            }
        } catch (error) {
            console.error('Failed to fetch top AI users:', error);
        }
    };

    const fetchTransactions = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/admin/transactions`);
            const data = await response.json();
            if (data.status === 'success') {
                setTransactions(data.data);
            }
        } catch (error) {
            console.error('Failed to fetch transactions:', error);
        }
    };

    const fetchSystemStats = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/admin/stats`);
            const data = await response.json();
            if (data.status === 'success') {
                setSystemStats(data.data);
            }
        } catch (error) {
            console.error('Failed to fetch stats:', error);
        }
    };

    const fetchUsageData = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/usage`);
            const data = await response.json();
            if (data.status === 'success') {
                setUsageData(data.data);
            }
        } catch (error) {
            console.error('Failed to fetch usage data:', error);
        }
    };

    const fetchUsers = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/admin/users`);
            const data = await response.json();
            if (data.status === 'success') {
                setUsers(data.data);
            } else {
                throw new Error("Failed to fetch users");
            }
        } catch (error) {
            console.error('Failed to fetch users, using fallbacks:', error);
            setUsers([
                { id: 1, name: 'Abhishek Sharma', email: 'abhishek@example.com', tier: 'Pro', status: 'Active', usage: 142, joined: '12 Jan 2026' },
                { id: 2, name: 'Priya Patel', email: 'priya.p@gmail.com', tier: 'Agency', status: 'Active', usage: 89, joined: '05 Feb 2026' },
                { id: 3, name: 'Rahul Varma', email: 'rahul.v@outlook.com', tier: 'Basic', status: 'Pending', usage: 12, joined: '01 Mar 2026' },
                { id: 4, name: 'Sanjana Reddy', email: 'sanj.reddy@yahoo.com', tier: 'Pro', status: 'Suspended', usage: 256, joined: '20 Dec 2025' },
                { id: 5, name: 'Vikram Singh', email: 'v.singh@company.in', tier: 'Agency', status: 'Active', usage: 45, joined: '15 Feb 2026' },
            ]);
        }
    };

    const handleOpenAddModal = () => {
        setModalMode('add');
        setSelectedUser(null);
        setModalData({
            full_name: '',
            email: '',
            subscription_tier: 'Basic',
            available_credits: 50,
            status: true
        });
        setShowUserModal(true);
    };

    const handleOpenEditModal = (user) => {
        setModalMode('edit');
        setSelectedUser(user);
        setModalData({
            full_name: user.name,
            email: user.email,
            subscription_tier: user.tier,
            available_credits: user.usage,
            status: user.status === 'Active'
        });
        setShowUserModal(true);
    };

    const handleSaveUser = async () => {
        try {
            if (modalMode === 'add') {
                // For simplicity, using same logic as signup but as admin
                const response = await fetch(`${API_BASE_URL}/signup`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        full_name: modalData.full_name,
                        email: modalData.email,
                        password: 'defaultPassword123' // Temporary password
                    })
                });
                if (!response.ok) throw new Error("Failed to create user");
            } else {
                const response = await fetch(`${API_BASE_URL}/admin/users/${selectedUser.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        full_name: modalData.full_name,
                        email: modalData.email,
                        subscription_tier: modalData.subscription_tier.toLowerCase(),
                        available_credits: parseInt(modalData.available_credits),
                        status: modalData.status
                    })
                });
                if (!response.ok) throw new Error("Failed to update user");
            }

            setShowUserModal(false);
            fetchUsers();
        } catch (error) {
            console.error(`Error ${modalMode === 'add' ? 'creating' : 'updating'} user:`, error);
            showToast(`Error ${modalMode === 'add' ? 'creating' : 'updating'} user. Please try again.`, 'error');
        }
    };

    const handleDeleteUser = (user_id) => {
        setUserIdToDelete(user_id);
        setShowDeleteModal(true);
    };

    const confirmDelete = async () => {
        if (!userIdToDelete) return;

        try {
            const response = await fetch(`${API_BASE_URL}/admin/users/${userIdToDelete}`, {
                method: 'DELETE'
            });
            if (response.ok) {
                fetchUsers();
                if (usageData) fetchUsageData();
                setShowDeleteModal(false);
                setUserIdToDelete(null);
            } else {
                throw new Error("Failed to delete user");
            }
        } catch (error) {
            console.error("Delete error:", error);
            showToast("Failed to delete user. Please try again.", 'error');
            setShowDeleteModal(false);
        }
    };

    const handleLogout = async () => {
        try {
            await fetch(`${API_BASE_URL}/logout`, { method: 'POST' });
            localStorage.removeItem('user');
            if (navigate) navigate('/login');
            else window.location.href = '/login';
        } catch (error) {
            console.error('Logout failed:', error);
            localStorage.removeItem('user');
            if (navigate) navigate('/login');
            else window.location.href = '/login';
        }
    };

    const renderSidebar = () => (
        <aside className="admin-sidebar">
            <div className="admin-brand">
                <div className="admin-logo">
                    <img src="/logo.png" alt="Logo" className="logo-img" />
                </div>
                <div className="admin-brand-text">
                    <span className="brand-primary">Social</span>
                    <span className="brand-secondary">Stamp</span>
                </div>
            </div>

            <nav className="admin-nav">
                <button
                    className={`admin-nav-item ${view === 'dashboard' ? 'active' : ''}`}
                    onClick={() => setView('dashboard')}
                >
                    <LayoutDashboard size={18} /> Dashboard
                </button>
                <button
                    className={`admin-nav-item ${view === 'users' ? 'active' : ''}`}
                    onClick={() => setView('users')}
                >
                    <Users size={18} /> User Management
                </button>
                <button
                    className={`admin-nav-item ${view === 'analytics' ? 'active' : ''}`}
                    onClick={() => setView('analytics')}
                >
                    <BarChart3 size={18} /> Detailed Analytics
                </button>
                <button
                    className={`admin-nav-item ${view === 'ai_models' ? 'active' : ''}`}
                    onClick={() => setView('ai_models')}
                >
                    <Cpu size={18} /> AI Models
                </button>
                <button
                    className={`admin-nav-item ${view === 'credits' ? 'active' : ''}`}
                    onClick={() => setView('credits')}
                >
                    <DollarSign size={18} /> Transactions
                </button>
                <button
                    className={`admin-nav-item ${view === 'settings' ? 'active' : ''}`}
                    onClick={() => setView('settings')}
                >
                    <Settings size={18} /> System Settings
                </button>
            </nav>

            <div className="admin-sidebar-footer">
                <div className="social-stamp">
                    <p>Connect with us</p>
                    <div className="social-icons">
                        <Twitter size={16} />
                        <Linkedin size={16} />
                        <Github size={16} />
                        <Instagram size={16} />
                    </div>
                </div>
                <button className="back-to-app" onClick={() => navigate ? navigate('/') : window.location.href = '/'}>
                    <ArrowLeft size={16} /> Back to Studio
                </button>
                <button className="admin-logout-btn" onClick={handleLogout}>
                    <LogOut size={16} /> Logout
                </button>
            </div>
        </aside>
    );

    const getAvatarColor = (name) => {
        const colors = ['#3b82f6', '#10b981', '#a855f7', '#f97316', '#ef4444', '#06b6d4'];
        let hash = 0;
        for (let i = 0; i < name.length; i++) {
            hash = name.charCodeAt(i) + ((hash << 5) - hash);
        }
        return colors[Math.abs(hash) % colors.length];
    };

    const renderDashboard = () => (
        <div className="admin-view animate-fade">
            <header className="admin-header">
                <div>
                    <h1>System Overview</h1>
                    <p>Monitoring AI resource consumption and user activity.</p>
                </div>
                <div className="admin-header-actions">
                    <div className="search-bar">
                        <Search size={14} />
                        <input type="text" placeholder="Search logs..." />
                    </div>
                    <button className="icon-btn"><Bell size={18} /></button>
                    <button className="primary-btn mini" onClick={handleOpenAddModal}><Plus size={14} /> New User</button>
                </div>
            </header>

            <div className="admin-stats-grid">
                <div className="stat-card">
                    <div className="stat-icon-wrap blue"><Users size={20} /></div>
                    <div className="stat-content">
                        <div className="stat-label">Total Users</div>
                        <div className="stat-value">{systemStats.total_users.toLocaleString()}</div>
                        <div className="stat-delta positive"><TrendingUp size={12} /> +12%</div>
                    </div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon-wrap green"><Video size={20} /></div>
                    <div className="stat-content">
                        <div className="stat-label">Videos Generated</div>
                        <div className="stat-value">{systemStats.total_generations.toLocaleString()}</div>
                        <div className="stat-delta positive"><TrendingUp size={12} /> +5.4%</div>
                    </div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon-wrap purple"><Activity size={20} /></div>
                    <div className="stat-content">
                        <div className="stat-label">System Load</div>
                        <div className="stat-value">{systemStats.system_load}</div>
                        <div className="stat-delta negative"><TrendingDown size={12} /> -2%</div>
                    </div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon-wrap orange"><CreditCard size={20} /></div>
                    <div className="stat-content">
                        <div className="stat-label">Monthly Revenue</div>
                        <div className="stat-value">{systemStats.revenue_formatted}</div>
                        <div className="stat-delta positive"><TrendingUp size={12} /> +22.1%</div>
                    </div>
                </div>
            </div>

            <div className="admin-main-grid">
                <div className="admin-section table-section">
                    <div className="section-header">
                        <h3>Recent User Activity</h3>
                        <button className="text-btn" onClick={() => setView('users')}>View All</button>
                    </div>
                    <div className="modern-table-wrap">
                        <table className="modern-table">
                            <thead>
                                <tr>
                                    <th>User</th>
                                    <th>Plan</th>
                                    <th>Status</th>
                                    <th>Generations</th>
                                    <th>Last Seen</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {users.slice(0, 5).map(user => (
                                    <tr key={user.id}>
                                        <td>
                                            <div className="user-profile">
                                                <div className="user-avatar" style={{ background: getAvatarColor(user.name) }}>
                                                    {user.name.charAt(0)}
                                                </div>
                                                <div className="user-info">
                                                    <span className="user-name">{user.name}</span>
                                                    <span className="user-email">{user.email}</span>
                                                </div>
                                            </div>
                                        </td>
                                        <td><span className={`plan-badge ${user.tier.toLowerCase()}`}>{user.tier}</span></td>
                                        <td><span className={`status-dot ${user.status.toLowerCase()}`}>{user.status}</span></td>
                                        <td>{user.usage}</td>
                                        <td>{user.joined}</td>
                                        <td>
                                            <div className="row-actions">
                                                <button className="row-btn edit" onClick={() => handleOpenEditModal(user)}><Edit size={14} /></button>
                                                <button className="row-btn delete" onClick={() => handleDeleteUser(user.id)}><Trash2 size={14} /></button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                <div className="admin-section history-section">
                    <div className="section-header">
                        <h3>Global Generation Log</h3>
                        <button className="icon-btn"><Download size={16} /></button>
                    </div>
                    <div className="gen-log-list">
                        {usageData?.recent_generations?.map(gen => (
                            <div key={gen.id} className="gen-log-item">
                                <div className="gen-type-icon">
                                    {gen.engine === 'gemini' ? <BarChart3 size={14} /> : <Users size={14} />}
                                </div>
                                <div className="gen-details">
                                    <div className="gen-topic">{gen.topic}</div>
                                    <div className="gen-meta">
                                        {gen.engine} • {gen.duration_requested}s • {gen.time}
                                    </div>
                                </div>
                                <div className="gen-cost">₹{gen.cost?.total_inr}</div>
                                <ChevronRight size={14} className="faded" />
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );

    const renderAnalytics = () => (
        <div className="admin-view animate-fade">
            <header className="admin-header">
                <div>
                    <h1>Detailed Analytics</h1>
                    <p>Deep dive into API consumption and performance metrics.</p>
                </div>
                <button className="primary-btn mini"><Download size={16} /> Export Report</button>
            </header>

            <div className="analytics-grid">
                <div className="admin-section chart-card">
                    <h3>Weekly Consumption Trend</h3>
                    <div className="chart-placeholder">
                        <div className="bar-chart">
                            {analyticsData.weeklyUsage.map((day, idx) => (
                                <div key={idx} className="bar-wrap">
                                    <div className="bar" style={{ height: `${(day.count / 120) * 100}%` }}>
                                        <span className="bar-tooltip">{day.count} gens</span>
                                    </div>
                                    <span className="bar-label">{day.day}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                <div className="admin-section distribution-card">
                    <h3>Model Distribution</h3>
                    <div className="distribution-list">
                        {analyticsData.modelDistribution.map((model, idx) => (
                            <div key={idx} className="dist-item">
                                <div className="dist-info">
                                    <span>{model.name}</span>
                                    <span>{model.share}%</span>
                                </div>
                                <div className="progress-bar">
                                    <div className="progress-fill" style={{ width: `${model.share}%` }}></div>
                                </div>
                            </div>
                        ))}
                    </div>
                    <div className="analytics-insight">
                        <Zap size={16} className="zap-icon" />
                        <p><strong>Insight:</strong> Gemini 2.0 Flash usage has increased by 15% this week due to lower latency.</p>
                    </div>
                </div>
            </div>

            <div className="usage-breakdown-grid">
                <div className="admin-section">
                    <h3>Token Usage Breakdown</h3>
                    <div className="metric-row">
                        <span>Input Tokens</span>
                        <span className="font-mono">{(usageData?.total_script_tokens?.input || 0).toLocaleString()}</span>
                    </div>
                    <div className="metric-row">
                        <span>Output Tokens</span>
                        <span className="font-mono">{(usageData?.total_script_tokens?.output || 0).toLocaleString()}</span>
                    </div>
                    <div className="metric-row total">
                        <span>Total Cost (USD)</span>
                        <span className="font-mono">${usageData?.total_estimated_cost_usd?.toFixed(4)}</span>
                    </div>
                </div>
                <div className="admin-section">
                    <h3>Infrastructure Health</h3>
                    <div className="health-grid">
                        <div className="health-item">
                            <Cpu size={18} />
                            <div>
                                <div className="h-label">Core Load</div>
                                <div className="h-value">12%</div>
                            </div>
                        </div>
                        <div className="health-item">
                            <Database size={18} />
                            <div>
                                <div className="h-label">DB Latency</div>
                                <div className="h-value">4ms</div>
                            </div>
                        </div>
                        <div className="health-item">
                            <Globe size={18} />
                            <div>
                                <div className="h-label">Global CDN</div>
                                <div className="h-value">99.9%</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );

    const renderTransactions = () => (
        <div className="admin-view animate-fade">
            <header className="admin-header">
                <div>
                    <h1>Transactions & Billing</h1>
                    <p>Track payments, subscriptions, and revenue flow.</p>
                </div>
            </header>

            <div className="admin-section full">
                <div className="section-header">
                    <h3>Recent Transactions</h3>
                    <div className="filter-group">
                        <button className="filter-chip active">All</button>
                        <button className="filter-chip">Completed</button>
                        <button className="filter-chip">Pending</button>
                    </div>
                </div>
                <div className="modern-table-wrap">
                    <table className="modern-table">
                        <thead>
                            <tr>
                                <th>Transaction ID</th>
                                <th>User</th>
                                <th>Amount</th>
                                <th>Plan</th>
                                <th>Date</th>
                                <th>Method</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {transactions.map(txn => (
                                <tr key={txn.id}>
                                    <td className="font-mono text-xs">{txn.id}</td>
                                    <td>
                                        <div className="user-name font-semibold">{txn.user}</div>
                                    </td>
                                    <td className="font-bold text-success">{txn.amount}</td>
                                    <td><span className={`plan-badge ${txn.plan.split(' ')[0].toLowerCase()}`}>{txn.plan}</span></td>
                                    <td>{txn.date}</td>
                                    <td>{txn.method}</td>
                                    <td>
                                        <span className={`status-pill ${txn.status.toLowerCase()}`}>
                                            {txn.status === 'Completed' && <CheckCircle2 size={12} />}
                                            {txn.status === 'Processing' && <Clock size={12} />}
                                            {txn.status === 'Failed' && <AlertCircle size={12} />}
                                            {txn.status}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );

    const renderSettings = () => (
        <div className="admin-view animate-fade">
            <header className="admin-header">
                <div>
                    <h1>System Settings</h1>
                    <p>Global configuration and security controls.</p>
                </div>
            </header>

            <div className="settings-grid">
                <div className="admin-section">
                    <div className="section-header">
                        <div className="header-with-icon">
                            <Zap size={20} className="text-primary" />
                            <h3>API Configuration</h3>
                        </div>
                    </div>
                    <div className="settings-list">
                        <div className="setting-item">
                            <div className="setting-info">
                                <label>Maintenance Mode</label>
                                <p>Disable all generation services for maintenance.</p>
                            </div>
                            <div className="toggle-switch">
                                <input type="checkbox" id="maint" />
                                <label htmlFor="maint"></label>
                            </div>
                        </div>
                        <div className="setting-item">
                            <div className="setting-info">
                                <label>High-Performance Mode</label>
                                <p>Prioritize 2.0 models for all requests.</p>
                            </div>
                            <div className="toggle-switch">
                                <input type="checkbox" id="hp" defaultChecked />
                                <label htmlFor="hp"></label>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="admin-section">
                    <div className="section-header">
                        <div className="header-with-icon">
                            <Lock size={20} className="text-primary" />
                            <h3>Security & Auth</h3>
                        </div>
                    </div>
                    <div className="settings-list">
                        <div className="setting-item">
                            <div className="setting-info">
                                <label>Two-Factor Authentication</label>
                                <p>Enforce 2FA for all admin accounts.</p>
                            </div>
                            <div className="toggle-switch">
                                <input type="checkbox" id="2fa" defaultChecked />
                                <label htmlFor="2fa"></label>
                            </div>
                        </div>
                        <div className="setting-item">
                            <div className="setting-info">
                                <label>API Key Rotation</label>
                                <p>Force rotate all keys every 30 days.</p>
                            </div>
                            <div className="toggle-switch">
                                <input type="checkbox" id="rotate" />
                                <label htmlFor="rotate"></label>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="admin-section full mt-4">
                <h3>Global Service Keys</h3>
                <div className="key-grid mt-4">
                    <div className="key-card">
                        <div className="key-label">Google Gemini API</div>
                        <div className="key-input-wrap">
                            <input type="password" value="••••••••••••••••••••••••••••" readOnly />
                            <button className="text-btn">Update</button>
                        </div>
                    </div>
                    <div className="key-card">
                        <div className="key-label">D-ID Service Key</div>
                        <div className="key-input-wrap">
                            <input type="password" value="••••••••••••••••••••••••••••" readOnly />
                            <button className="text-btn">Update</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );

    const renderAIModels = () => (
        <div className="admin-view animate-fade">
            <header className="admin-header">
                <div>
                    <h1>AI Model Settings</h1>
                    <p>Manage AI models and track usage costs.</p>
                </div>
            </header>

            <div className="ai-models-grid-top">
                <div className="admin-section active-model-card">
                    <div className="card-top-row">
                        <div className="card-title"><Cpu size={16} /> Current Active Model</div>
                        <div className="active-badge">ACTIVE</div>
                    </div>
                    <div className="model-primary-name">{activeModel.name}</div>
                    <div className="model-provider">{activeModel.provider}</div>
                    <div className="model-tags">
                        {activeModel.tags.map((tag, i) => {
                            const TagIcon = tag.icon;
                            return (
                                <span key={i} className="model-tag">
                                    <TagIcon size={12} /> {tag.text}
                                </span>
                            );
                        })}
                    </div>
                </div>

                <div className="admin-section">
                    <div className="card-title"><DollarSign size={16} /> Live Pricing</div>
                    <div className="pricing-split">
                        <div className="price-item">
                            <div className="price-label">Input</div>
                            <div className="price-value">{activeModel.inputPrice}</div>
                            {activeModel.inputPrice !== 'N/A' && <div className="price-sub">/ 1M tokens</div>}
                        </div>
                        <div className="price-item align-right">
                            <div className="price-label">Output</div>
                            <div className="price-value">{activeModel.outputPrice}</div>
                            {activeModel.outputPrice !== 'N/A' && <div className="price-sub">/ 1M tokens</div>}
                        </div>
                    </div>
                    <div className="pricing-note">
                        <AlertCircle size={14} /> Est. cost per query: <span className="highlight-green">{activeModel.estCostText}</span>
                    </div>
                </div>

                <div className="admin-section">
                    <div className="card-top-row">
                        <div className="card-title"><Activity size={16} /> Monthly Budget</div>
                        <button className="icon-btn-small"><Edit size={14} /></button>
                    </div>
                    <div className="budget-stats">
                        <div className="budget-amounts">{activeModel.monthlyEst}</div>
                        <div className="budget-inr">₹1 / ₹8225</div>
                        <div className="budget-pct">0.0% used</div>
                    </div>
                    <div className="budget-progress-bg">
                        <div className="budget-progress-fill" style={{ width: '2%' }}></div>
                    </div>
                </div>
            </div>

            <div className="admin-stats-grid ai-stats-row">
                <div className="ai-stat-card">
                    <div className="stat-label-center">TOTAL QUERIES (ALL TIME)</div>
                    <div className="stat-value-center">5</div>
                </div>
                <div className="ai-stat-card">
                    <div className="stat-label-center">QUERIES TODAY</div>
                    <div className="stat-value-center">4</div>
                </div>
                <div className="ai-stat-card">
                    <div className="stat-label-center">TOTAL COST (THIS MONTH)</div>
                    <div className="stat-value-center">$0.01</div>
                    <div className="stat-sub-center">₹0.82</div>
                </div>
                <div className="ai-stat-card">
                    <div className="stat-label-center">TOKENS PROCESSED</div>
                    <div className="stat-value-center">0.01M</div>
                </div>
            </div>

            <div className="ai-models-grid-bottom">
                <div className="admin-section table-section">
                    <div className="section-header">
                        <div className="header-with-icon">
                            <Users size={18} />
                            <h3>Top Users (This Month)</h3>
                        </div>
                    </div>
                    <table className="modern-table">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Queries</th>
                                <th>Cost ($ / ₹)</th>
                            </tr>
                        </thead>
                        <tbody>
                            {topAiUsers.map((user, idx) => {
                                const colors = ['#a855f7', '#3b82f6', '#10b981', '#f59e0b', '#ef4444'];
                                const bgColor = colors[idx % colors.length];

                                return (
                                    <tr key={idx}>
                                        <td>
                                            <div className="user-profile">
                                                <div className="user-avatar small" style={{ background: bgColor }}>
                                                    {user.initials}
                                                </div>
                                                <div className="user-info">
                                                    <span className="user-name">{user.name}</span>
                                                </div>
                                            </div>
                                        </td>
                                        <td>{user.queries}</td>
                                        <td>
                                            <div className="cost-stack">
                                                <span>${user.total_cost_usd.toFixed(4)}</span>
                                                <span className="sub-cost">₹{user.total_cost_inr.toFixed(2)}</span>
                                            </div>
                                        </td>
                                    </tr>
                                );
                            })}
                            {topAiUsers.length === 0 && (
                                <tr>
                                    <td colSpan="3" style={{ textAlign: 'center', padding: '2rem', color: 'var(--admin-text-dim)' }}>
                                        No model usage recorded yet.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>

                <div className="admin-section">
                    <div className="section-header">
                        <div className="header-with-icon">
                            <ArrowLeft size={18} className="rotate-icon" />
                            <h3>Switch AI Model</h3>
                        </div>
                    </div>

                    <div className="model-list">
                        {AI_MODELS.map((model) => (
                            <div
                                key={model.id}
                                className={`model-list-item ${activeModel.id === model.id ? 'active' : ''}`}
                                onClick={() => {
                                    if (activeModel.id !== model.id) {
                                        setConfirmModel(model);
                                        setShowModelModal(true);
                                    }
                                }}
                            >
                                <div className="model-item-info">
                                    <h4>{model.name} {activeModel.id === model.id ? null : <span className="code-id">{model.id}</span>}</h4>
                                    <div className="model-item-cost">
                                        {model.id.includes('veo') ? (model.id.includes('fast') ? 'Video Generation (Fast)' : 'Video Generation (Standard)') : `Input: ${model.inputPrice} | Output: ${model.outputPrice}`}
                                    </div>
                                </div>
                                <div className={`radio-circle ${activeModel.id === model.id ? 'active' : ''}`}>
                                    {activeModel.id === model.id && <div className="radio-inner"></div>}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );

    const renderDeleteModal = () => (
        <div className="admin-modal-overlay">
            <div className="admin-modal delete-modal animate-fade">
                <div className="modal-body">
                    <div className="delete-icon-large">
                        <Trash2 size={32} />
                    </div>
                    <h3>Confirm Deletion</h3>
                    <p>Are you sure you want to delete this user? This action will remove all associated data and cannot be undone.</p>
                    <div className="modal-actions-vertical">
                        <button className="btn-danger" onClick={confirmDelete}>Delete Account</button>
                        <button className="btn-ghost" onClick={() => setShowDeleteModal(false)}>Cancel</button>
                    </div>
                </div>
            </div>
        </div>
    );

    return (
        <div className="admin-layout">
            {renderSidebar()}
            <main className="admin-content">
                {view === 'dashboard' && renderDashboard()}
                {view === 'users' && (
                    <div className="admin-view animate-fade">
                        <header className="admin-header">
                            <div>
                                <h1>User Management</h1>
                                <p>Control user access, roles, and resource limitations.</p>
                            </div>
                            <div className="admin-header-actions">
                                <div className="search-bar">
                                    <Search size={14} />
                                    <input type="text" placeholder="Search by name/email..." />
                                </div>
                                <button className="primary-btn mini" onClick={handleOpenAddModal}>Add New</button>
                            </div>
                        </header>
                        <div className="admin-section full">
                            <div className="modern-table-wrap">
                                <table className="modern-table">
                                    <thead>
                                        <tr>
                                            <th>User ID</th>
                                            <th>Profile</th>
                                            <th>Tier</th>
                                            <th>Status</th>
                                            <th>Usage</th>
                                            <th>Registration</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {users.map(u => (
                                            <tr key={u.id}>
                                                <td className="font-mono">#US-{u.id}</td>
                                                <td>
                                                    <div className="user-profile">
                                                        <div className="user-avatar" style={{ background: getAvatarColor(u.name) }}>
                                                            {u.name.charAt(0)}
                                                        </div>
                                                        <div className="user-info">
                                                            <span className="user-name">{u.name}</span>
                                                            <span className="user-email">{u.email}</span>
                                                        </div>
                                                    </div>
                                                </td>
                                                <td><span className={`plan-badge ${u.tier.toLowerCase()}`}>{u.tier}</span></td>
                                                <td><span className={`status-dot ${u.status.toLowerCase()}`}>{u.status}</span></td>
                                                <td><span className="font-bold">{u.usage}</span> gens</td>
                                                <td>{u.joined}</td>
                                                <td>
                                                    <div className="row-actions">
                                                        <button className="row-btn edit" onClick={() => handleOpenEditModal(u)}><Edit size={14} /></button>
                                                        <button className="row-btn delete" onClick={() => handleDeleteUser(u.id)}><Trash2 size={14} /></button>
                                                    </div>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                )}
                {view === 'analytics' && renderAnalytics()}
                {view === 'ai_models' && renderAIModels()}
                {view === 'credits' && renderTransactions()}
                {view === 'settings' && renderSettings()}
            </main>

            {showDeleteModal && renderDeleteModal()}

            {showUserModal && (
                <div className="admin-modal-overlay">
                    <div className="admin-modal animate-fade">
                        <div className="modal-header">
                            <h3>{modalMode === 'add' ? 'Add New User' : 'Edit User'}</h3>
                            <button className="icon-btn" onClick={() => setShowUserModal(false)}><X size={20} /></button>
                        </div>
                        <div className="modal-body">
                            <div className="input-field">
                                <label>Full Name</label>
                                <input
                                    type="text"
                                    placeholder="John Doe"
                                    value={modalData.full_name}
                                    onChange={(e) => setModalData({ ...modalData, full_name: e.target.value })}
                                />
                            </div>
                            <div className="input-field">
                                <label>Email Address</label>
                                <input
                                    type="email"
                                    placeholder="john@example.com"
                                    value={modalData.email}
                                    onChange={(e) => setModalData({ ...modalData, email: e.target.value })}
                                />
                            </div>
                            <div className="input-row">
                                <div className="input-field">
                                    <label>Plan Tier</label>
                                    <select
                                        value={modalData.subscription_tier}
                                        onChange={(e) => setModalData({ ...modalData, subscription_tier: e.target.value })}
                                    >
                                        <option value="Basic">Basic</option>
                                        <option value="Pro">Pro</option>
                                        <option value="Agency">Agency</option>
                                    </select>
                                </div>
                                <div className="input-field">
                                    <label>Available Credits</label>
                                    <input
                                        type="number"
                                        value={modalData.available_credits}
                                        onChange={(e) => setModalData({ ...modalData, available_credits: e.target.value })}
                                    />
                                </div>
                            </div>
                            {modalMode === 'edit' && (
                                <div className="setting-item" style={{ marginTop: '1rem', background: 'transparent', padding: 0 }}>
                                    <div className="setting-info">
                                        <label style={{ fontWeight: 500 }}>User Status</label>
                                        <p style={{ margin: 0, fontSize: '0.8rem' }}>Set user account to active or inactive.</p>
                                    </div>
                                    <div className="toggle-switch">
                                        <input
                                            type="checkbox"
                                            id="user-status-modal"
                                            checked={modalData.status}
                                            onChange={(e) => setModalData({ ...modalData, status: e.target.checked })}
                                        />
                                        <label htmlFor="user-status-modal"></label>
                                    </div>
                                </div>
                            )}
                        </div>
                        <div className="modal-footer">
                            <button className="text-btn" onClick={() => setShowUserModal(false)}>Cancel</button>
                            <button className="primary-btn" onClick={handleSaveUser}>
                                {modalMode === 'add' ? 'Create User' : 'Update User'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Custom Toast Notification */}
            {toast.show && (
                <div className={`admin-toast ${toast.type}`}>
                    {toast.type === 'success' ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
                    <span>{toast.message}</span>
                </div>
            )}

            {/* Switch AI Model Confirmation Modal */}
            {showModelModal && confirmModel && (
                <div className="admin-modal-overlay">
                    <div className="admin-modal confirm-modal animate-scale">
                        <div className="modal-header">
                            <h3>Confirm Model Switch</h3>
                            <button className="close-btn" onClick={() => setShowModelModal(false)}><X size={18} /></button>
                        </div>
                        <div className="modal-body confirm-body">
                            <Cpu size={48} className="confirm-icon" style={{ color: '#10b981', margin: '0 auto 1rem', display: 'block' }} />
                            <h4 style={{ textAlign: 'center', marginBottom: '1rem' }}>Can you switch the model?</h4>
                            <p style={{ textAlign: 'center', color: 'var(--admin-text-dim)' }}>
                                You are about to switch the global AI generation model to <strong style={{ color: 'var(--admin-text)' }}>{confirmModel.name}</strong>. Traffic routing and cost estimations will be updated immediately.
                            </p>
                        </div>
                        <div className="modal-footer" style={{ justifyContent: 'center', gap: '1rem' }}>
                            <button className="text-btn" onClick={() => setShowModelModal(false)}>Cancel</button>
                            <button className="primary-btn" style={{ background: '#10b981' }} onClick={() => {
                                setActiveModel(confirmModel);
                                setShowModelModal(false);
                                showToast(`Successfully switched to ${confirmModel.name}`, 'success');
                            }}>
                                Yes, Switch Model
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default AdminPanel;
