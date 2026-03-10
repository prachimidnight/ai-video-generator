import React, { useState } from 'react';
import { User, Mail, Lock, ArrowRight, Wand2, Github } from 'lucide-react';
import './LoginPage.css'; // Reusing login styles for consistency

const SignupPage = ({ navigate }) => {
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const response = await fetch(`${apiUrl}/signup`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    full_name: name,
                    email: email,
                    password: password
                }),
            });

            const data = await response.json();

            if (response.ok) {
                console.log('Signup successful:', data);
                navigate('/login');
            } else {
                setError(data.detail || 'Signup failed');
            }
        } catch (err) {
            setError('Connection error. Is the backend running?');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="login-container">
            {/* Background elements matches landing page */}
            <div className="login-glow login-glow-1"></div>
            <div className="login-glow login-glow-2"></div>

            <div className="login-wrapper">
                <div className="login-logo clickable" onClick={() => navigate('/')}>
                    <img src="/logo.png" alt="Social Stamp logo" className="logo-icon" />
                    <span>Social Stamp</span>
                </div>

                <div className="login-card">
                    <div className="login-header">
                        <h2>Create an Account</h2>
                        <p>Sign up to start creating stunning AI videos</p>
                    </div>

                    <form className="login-form" onSubmit={handleSubmit}>
                        {error && (
                            <div style={{ color: '#ef4444', backgroundColor: 'rgba(239, 68, 68, 0.1)', padding: '0.75rem', borderRadius: '0.5rem', fontSize: '0.875rem', textAlign: 'center' }}>
                                {error}
                            </div>
                        )}
                        <div className="input-group">
                            <label htmlFor="name">Full Name</label>
                            <div className="input-wrapper">
                                <User className="input-icon" size={20} />
                                <input
                                    type="text"
                                    id="name"
                                    placeholder="John Doe"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    required
                                    disabled={loading}
                                />
                            </div>
                        </div>

                        <div className="input-group">
                            <label htmlFor="email">Email Address</label>
                            <div className="input-wrapper">
                                <Mail className="input-icon" size={20} />
                                <input
                                    type="email"
                                    id="email"
                                    placeholder="you@example.com"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    required
                                    disabled={loading}
                                />
                            </div>
                        </div>

                        <div className="input-group">
                            <div className="flex-between">
                                <label htmlFor="password">Password</label>
                            </div>
                            <div className="input-wrapper">
                                <Lock className="input-icon" size={20} />
                                <input
                                    type="password"
                                    id="password"
                                    placeholder="••••••••"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required
                                    disabled={loading}
                                />
                            </div>
                        </div>

                        <button type="submit" className="login-btn" disabled={loading}>
                            {loading ? 'Creating Account...' : 'Sign Up'}
                            <ArrowRight className="btn-icon" size={20} />
                        </button>
                    </form>



                    <div className="login-footer">
                        Already have an account? <span className="text-secondary clickable" onClick={() => navigate('/login')}>Log in</span>
                    </div>
                </div>
            </div>

            {/* Main Footer */}
            <div className="login-page-footer">
                <p>POWERED BY <span className="text-primary font-bold">RUNR</span></p>
            </div>
        </div>
    );
};

export default SignupPage;
