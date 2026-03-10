import React, { useState, useEffect } from 'react';
import { PlayCircle, Wand2, Download, ArrowRight, Video, Mic, Sparkles, LayoutDashboard } from 'lucide-react';
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
                        Harness the power of AI to generate high-quality scenes, voiceovers, and dynamic visuals from just a simple text prompt.
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
                    <h2>How It Works</h2>
                    <p>Create professional videos in three simple steps</p>
                </div>

                <div className="features-grid">
                    <div className="feature-card">
                        <div className="feature-icon-wrapper i-purple">
                            <Wand2 />
                        </div>
                        <h3>1. Input Your Idea</h3>
                        <p>Type a prompt, a script, or an article. Our AI understands your vision and plans the entire video structure.</p>
                    </div>

                    <div className="feature-card">
                        <div className="feature-icon-wrapper i-blue">
                            <Mic />
                        </div>
                        <h3>2. Let AI Generate</h3>
                        <p>The system automatically creates ultra-realistic voiceovers, vivid imagery, and engaging cinematic transitions.</p>
                    </div>

                    <div className="feature-card">
                        <div className="feature-icon-wrapper i-green">
                            <Download />
                        </div>
                        <h3>3. Export & Share</h3>
                        <p>Review your masterpiece on the timeline, make tweaks if needed, and download your HD video instantly.</p>
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
                                <h4>Multi-Scene Generation</h4>
                                <p>Generate seamless videos with multiple dynamic scenes.</p>
                            </div>
                        </li>
                        <li>
                            <Mic className="li-icon" />
                            <div>
                                <h4>Lifelike Voiceovers</h4>
                                <p>Choose from dozens of ultra-realistic AI voices.</p>
                            </div>
                        </li>
                        <li>
                            <Sparkles className="li-icon" />
                            <div>
                                <h4>Cinematic Effects</h4>
                                <p>High-end transitions and automated animations.</p>
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

            {/* Footer CTA */}
            <section className="bottom-cta">
                <h2>Ready to create your next viral video?</h2>
                <button className="primary-btn-large" onClick={() => navigate('/login')}>
                    Start For Free Now
                </button>
            </section>

            {/* Main Footer */}
            <footer className="landing-footer">
                <p>POWERED BY <span className="text-gradient font-bold">RUNR</span></p>
            </footer>
        </div>
    );
};

export default LandingPage;
