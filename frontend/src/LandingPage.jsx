import React, { useState, useEffect } from 'react';
import { PlayCircle, Wand2, Download, ArrowRight, Video, Mic, Sparkles, LayoutDashboard, Languages, ShieldCheck, Lock } from 'lucide-react';
import './LandingPage.css';

const LandingPage = ({ navigate }) => {
    const [isLoggedIn, setIsLoggedIn] = useState(false);

    useEffect(() => {
        const user = localStorage.getItem('user');
        if (user) setIsLoggedIn(true);
    }, []);
    return (
        <div className="landing-container">
            {/* Navbar overlay */}
            <nav className="landing-nav">
                <div className="landing-logo">
                    <img src="/logo.png" alt="Social Stamp logo" className="logo-icon" />
                    <span>Social Stamp</span>
                </div>
                <div className="landing-nav-links">
                    {isLoggedIn ? (
                        <button className="primary-btn-small" onClick={() => navigate('/app')}>
                            <LayoutDashboard size={16} /> Go to App
                        </button>
                    ) : (
                        <>
                            <button className="text-btn" onClick={() => navigate('/login')}>Login</button>
                            <button className="primary-btn-small" onClick={() => navigate('/app')}>Try App</button>
                        </>
                    )}
                </div>
            </nav>

            {/* Hero Section */}
            <header className="hero-section">
                <div className="hero-glow hero-glow-1"></div>
                <div className="hero-glow hero-glow-2"></div>

                <div className="hero-content">
                    <div className="hero-badge">
                        <Sparkles className="badge-icon" />
                        <span>AI Powered Video Creation</span>
                    </div>
                    <h1 className="hero-title">
                        Transform Ideas into <span className="text-gradient">Stunning Videos</span> in Seconds
                    </h1>
                    <p className="hero-subtitle">
                        Create <strong>talking character videos</strong> with lifelike voiceovers in <strong>any language</strong> — plus cinematic shots, subtitles, and export-ready formats from a single prompt.
                    </p>
                    <div className="hero-cta">
                        <button className="primary-btn-large group" onClick={() => navigate('/app')}>
                            Get Started Free
                            <ArrowRight className="btn-icon group-hover:translate-x-1 transition-transform" />
                        </button>
                    </div>
                </div>

                {/* Mockup Preview Area */}
                <div className="hero-mockup-wrapper">
                    <div className="hero-mockup">
                        <div className="mockup-header">
                            <span className="dot dot-r"></span>
                            <span className="dot dot-y"></span>
                            <span className="dot dot-g"></span>
                        </div>
                        <div className="mockup-body">
                            <div className="mockup-sidebar"></div>
                            <div className="mockup-main">
                                <div className="mockup-video-player">
                                    <PlayCircle size={48} className="play-icon" />
                                </div>
                                <div className="mockup-timeline"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </header>

            {/* Features / How it works Section */}
            <section className="features-section">
                <div className="section-header">
                    <h2>Built for talking characters</h2>
                    <p>Your specialty: generate a character that speaks your script in any language — fast, clean, and shareable.</p>
                </div>

                <div className="features-grid">
                    <div className="feature-card">
                        <div className="feature-icon-wrapper i-purple">
                            <Wand2 />
                        </div>
                        <h3>1. Write a prompt or script</h3>
                        <p>Start with a topic, paste a script, or draft one with AI — then generate a cinematic talking character video.</p>
                    </div>

                    <div className="feature-card">
                        <div className="feature-icon-wrapper i-blue">
                            <Languages />
                        </div>
                        <h3>2. Choose language & voice</h3>
                        <p>Create voiceovers in multiple languages with natural pacing — perfect for global content and regional campaigns.</p>
                    </div>

                    <div className="feature-card">
                        <div className="feature-icon-wrapper i-green">
                            <Download />
                        </div>
                        <h3>3. Export for every platform</h3>
                        <p>Download MP4 and convert to 16:9 or 9:16 — ready for YouTube, Reels, TikTok, Shorts, and ads.</p>
                    </div>
                </div>
            </section>

            {/* Capabilities Section */}
            <section className="capabilities-section">
                <div className="capabilities-content">
                    <h2>Unleash Unlimited <span className="text-gradient">Creativity</span></h2>
                    <ul className="capabilities-list">
                        <li>
                            <Video className="li-icon" />
                            <div>
                                <h4>Cinematic talking videos</h4>
                                <p>Create character-led videos that feel studio-produced — perfect for explainers, promos, and brand content.</p>
                            </div>
                        </li>
                        <li>
                            <Mic className="li-icon" />
                            <div>
                                <h4>Multi-language voiceovers</h4>
                                <p>Generate voiceovers in many languages with natural tone and pacing.</p>
                            </div>
                        </li>
                        <li>
                            <Sparkles className="li-icon" />
                            <div>
                                <h4>Captions, formats, post tools</h4>
                                <p>Add subtitles, convert aspect ratios, and ship content faster — without manual editing.</p>
                            </div>
                        </li>
                    </ul>
                </div>
                <div className="capabilities-visual">
                    <div className="floating-card c1">Scene 1 Generated...</div>
                    <div className="floating-card c2">Applying Voiceover...</div>
                    <div className="floating-card c3">Rendering Final Video</div>
                </div>
            </section>

            {/* Trust / Privacy Section */}
            <section className="features-section" style={{ marginTop: '4rem' }}>
                <div className="section-header">
                    <h2>Privacy-first by design</h2>
                    <p>Built with traceability for security, and controls to protect user data.</p>
                </div>
                <div className="features-grid">
                    <div className="feature-card">
                        <div className="feature-icon-wrapper i-purple">
                            <ShieldCheck />
                        </div>
                        <h3>Audit metadata (server-side)</h3>
                        <p>Each generated video gets a private audit record (who/when/settings), stored securely on the server for admins.</p>
                    </div>
                    <div className="feature-card">
                        <div className="feature-icon-wrapper i-blue">
                            <Lock />
                        </div>
                        <h3>Admin-only access</h3>
                        <p>Audit records are not publicly downloadable and can be fetched only through protected admin endpoints.</p>
                    </div>
                    <div className="feature-card">
                        <div className="feature-icon-wrapper i-green">
                            <Sparkles />
                        </div>
                        <h3>Optional file metadata</h3>
                        <p>We can embed a privacy-safe summary into the MP4 container metadata (hashed user ID, engine, settings).</p>
                    </div>
                </div>
            </section>

            {/* Footer CTA */}
            <section className="bottom-cta">
                <h2>Ready to create your next viral video?</h2>
                <button className="primary-btn-large" onClick={() => navigate('/login')}>
                    Start For Free Now
                </button>
            </section>

            {/* Main Footer */}
            <footer className="landing-footer">
                <div className="lp-footer-links">
                    <button className="text-btn" onClick={() => navigate('/privacy-policy')}>Privacy Policy</button>
                    <span className="lp-footer-sep">•</span>
                    <button className="text-btn" onClick={() => navigate('/disclaimer')}>Disclaimer</button>
                    <span className="lp-footer-sep">•</span>
                    <button className="text-btn" onClick={() => navigate('/terms-and-conditions')}>Terms and Conditions</button>
                </div>
                <p>POWERED BY <span className="text-gradient font-bold">RUNR</span></p>
            </footer>
        </div>
    );
};

export default LandingPage;
