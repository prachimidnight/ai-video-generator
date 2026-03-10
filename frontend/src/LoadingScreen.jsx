import React, { useState, useEffect } from 'react';
import './LoadingScreen.css';

const LoadingScreen = ({ message = "SECURE ENTERPRISE ENVIRONMENT" }) => {
    const [progress, setProgress] = useState(0);

    useEffect(() => {
        // Simulate a staggered progress up to 99%
        const interval = setInterval(() => {
            setProgress(prev => {
                const step = Math.random() * 5 + 1; // 1 to 6% per tick
                if (prev + step >= 99) {
                    clearInterval(interval);
                    return 99; // Hold at 99% until externally finished
                }
                return prev + step;
            });
        }, 1500);

        return () => clearInterval(interval);
    }, []);

    return (
        <div className="custom-loading-wrapper">
            <div className="custom-loading-content">
                <div className="custom-loading-logo-wrapper">
                    <img src="/logo.png" alt="Social Stamp" className="custom-loading-logo" />
                </div>

                <div className="custom-loading-header">
                    <div className="custom-loading-left">
                        <span className="prepared-text">PREPARING</span>
                        <span className="prepared-badge">SYSTEMS V2.4</span>
                    </div>
                    <div className="custom-loading-percentage">
                        {Math.floor(progress)}%
                    </div>
                </div>

                <div className="custom-loading-bar-container">
                    <div
                        className="custom-loading-bar-fill"
                        style={{ width: `${progress}%` }}
                    ></div>
                </div>

                <div className="custom-loading-subtext">
                    {message}
                </div>
            </div>
        </div>
    );
};

export default LoadingScreen;
