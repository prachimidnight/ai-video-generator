import React from 'react';
import './LegalPages.css';

const TermsAndConditions = ({ navigate }) => {
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

        <h1 className="legal-title">Terms and Conditions</h1>
        <p className="legal-meta">Last updated: {lastUpdated}</p>

        <div className="legal-content">
          <p>
            Welcome to Social Stamp. By accessing or using our AI video generation platform (the “Service”), you agree 
            to be bound by these Terms and Conditions.
          </p>

          <h2>1. Use of Service</h2>
          <p>
            You must be at least 18 years old or the age of majority in your jurisdiction to use this Service. You agree 
            to use the Service only for lawful purposes and in accordance with these Terms.
          </p>

          <h2>2. Account Registration</h2>
          <p>
            To access certain features, you may be required to create an account. You are responsible for maintaining 
            the confidentiality of your account credentials and for all activities that occur under your account.
          </p>

          <h2>3. Content Ownership and AI Generation</h2>
          <ul>
            <li><strong>User Content</strong>: You retain ownership of any prompts, scripts, or images you upload.</li>
            <li><strong>AI Output</strong>: We grant you a non-exclusive, worldwide license to use, reproduce, and distribute the videos generated through the Service for your personal or commercial use, subject to these Terms.</li>
            <li><strong>Restricted Content</strong>: You may not generate content that is illegal, harmful, threatening, abusive, harassing, defamatory, vulgar, obscene, or otherwise objectionable.</li>
          </ul>

          <h2>4. Payments and Credits</h2>
          <p>
            The Service may require payment or the use of credits. All payments are non-refundable unless otherwise 
            stated or required by law. We reserve the right to change our pricing at any time.
          </p>

          <h2>5. Prohibited Activities</h2>
          <ul>
            <li>Attempting to reverse engineer or bypass any security measures of the Service.</li>
            <li>Using the Service to generate large volumes of spam or deceptive content.</li>
            <li>Impersonating any person or entity without authorization.</li>
            <li>Systematic retrieval of data from the Service to create or compile a collection or database.</li>
          </ul>

          <h2>6. Limitation of Liability</h2>
          <p>
            In no event shall Social Stamp, its directors, employees, or agents be liable for any indirect, 
            incidental, special, consequential, or punitive damages arising out of or in connection with your use 
            of the Service.
          </p>

          <h2>7. Termination</h2>
          <p>
            We reserve the right to terminate or suspend your account and access to the Service at our sole 
            discretion, without notice, for conduct that we believe violates these Terms or is harmful to other users 
            or us.
          </p>

          <h2>8. Changes to Terms</h2>
          <p>
            We may update these Terms from time to time. Your continued use of the Service after any changes 
            constitutes your acceptance of the new Terms.
          </p>

          <h2>9. Governing Law</h2>
          <p>
            These Terms shall be governed by and construed in accordance with the laws of the jurisdiction in which 
            we operate, without regard to its conflict of law provisions.
          </p>

          <h2>10. Contact</h2>
          <p>
            If you have any questions about these Terms, please contact us at our support address.
          </p>
        </div>

        <div className="legal-divider">
          By using Social Stamp, you acknowledge that you have read and understood these Terms and Conditions.
        </div>
      </div>
    </div>
  );
};

export default TermsAndConditions;
