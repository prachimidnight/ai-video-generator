import React from 'react';
import './LegalPages.css';

const PrivacyPolicy = ({ navigate }) => {
  const lastUpdated = '19 Mar 2026';

  return (
    <div className="legal-container">
      <div className="legal-shell">
        <div className="legal-topbar">
          <div className="legal-brand">
            <img src="/logo.png" alt="Social Stamp logo" />
            <span>Social Stamp</span>
          </div>
          <button className="legal-back" onClick={() => navigate('/')}>Back to Home</button>
        </div>

        <h1 className="legal-title">Privacy Policy</h1>
        <p className="legal-meta">Last updated: {lastUpdated}</p>

        <div className="legal-content">
          <p>
            This Privacy Policy explains how Social Stamp (“we”, “us”, “our”) collects, uses, and protects information
            when you use our AI video generation platform (the “Service”).
          </p>

          <h2>Information we collect</h2>
          <ul>
            <li><strong>Account details</strong>: name, email, and login information you provide.</li>
            <li><strong>Generation inputs</strong>: prompts/topics, scripts, and optional uploaded images.</li>
            <li><strong>Usage & diagnostics</strong>: timestamps, performance logs, feature flags, and error reports.</li>
            <li><strong>Payments</strong>: payment status and transaction identifiers (we do not store full card details).</li>
          </ul>

          <h2>How we use information</h2>
          <ul>
            <li><strong>Provide the Service</strong>: create, render, and deliver your videos.</li>
            <li><strong>Improve quality</strong>: monitor reliability, fix bugs, and enhance outputs.</li>
            <li><strong>Security & abuse prevention</strong>: detect fraud, enforce limits, and protect accounts.</li>
            <li><strong>Support</strong>: respond to your requests and help troubleshoot issues.</li>
          </ul>

          <h2>Video generation metadata (audit logs)</h2>
          <p>
            For security and compliance, we store a private generation audit record on our servers (e.g. time, settings used).
            This record is not publicly accessible. When available, we may also embed a non-sensitive summary into the file’s
            container metadata (e.g. a hashed user identifier, generation engine, and settings) to help with traceability.
          </p>

          <h2>Data retention</h2>
          <p>
            We retain information only as long as needed to operate the Service, meet legal obligations, resolve disputes, and
            enforce agreements. You can request deletion where applicable.
          </p>

          <h2>Sharing</h2>
          <p>
            We may share limited information with infrastructure, analytics, and payment providers strictly to operate the
            Service. We do not sell your personal data.
          </p>

          <h2>Security</h2>
          <p>
            We use reasonable administrative, technical, and organizational safeguards. No method of transmission or storage
            is 100% secure, but we continuously improve protections.
          </p>

          <h2>Your choices</h2>
          <ul>
            <li><strong>Access</strong>: you can view and update your profile information.</li>
            <li><strong>Deletion</strong>: you may request deletion of your account and associated data where applicable.</li>
          </ul>

          <h2>Contact</h2>
          <p>
            If you have questions about this policy, contact us at your support email or through the admin channel.
          </p>
        </div>

        <div className="legal-divider">
          This page is provided for transparency. If you need region-specific clauses (GDPR/CCPA), we can add them.
        </div>
      </div>
    </div>
  );
};

export default PrivacyPolicy;

