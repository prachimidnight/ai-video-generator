import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
    Upload,
    Video,
    Sparkles,
    Image as ImageIcon,
    CheckCircle2,
    AlertCircle,
    Play,
    Loader2,
    RefreshCcw,
    X,
    MessageSquare,
    Settings,
    Music,
    Layers,
    Download,
    History,
    ChevronRight,
    Languages,
    Clock,
    User,
    Volume2,
    Zap,
    Subtitles,
    Globe,
    Monitor,
    Smartphone,
    Square,
    Copy,
    Check,
    ChevronDown,
    ChevronUp,
    BarChart3,
    IndianRupee,
    DollarSign,
    Activity,
    LogOut,
    Cpu,
    Mic,
    Menu
} from 'lucide-react';
import { API_BASE_URL } from './config';
import './VideoGenerator.css';
import LoadingScreen from './LoadingScreen';



const VOICES = {
    'English': [
        { id: 'en-US-AndrewNeural', name: 'Andrew (Male)', gender: 'male' },
        { id: 'en-US-AvaNeural', name: 'Ava (Female)', gender: 'female' },
        { id: 'en-US-BrianNeural', name: 'Brian (Male)', gender: 'male' },
        { id: 'en-US-EmmaNeural', name: 'Emma (Female)', gender: 'female' },
        { id: 'en-US-AriaNeural', name: 'Aria (Female)', gender: 'female' },
        { id: 'en-US-GuyNeural', name: 'Guy (Male)', gender: 'male' }
    ],
    'English (India)': [
        { id: 'en-IN-NeerjaNeural', name: 'Neerja (Female)', gender: 'female' },
        { id: 'en-IN-PrabhatNeural', name: 'Prabhat (Male)', gender: 'male' },
        { id: 'en-IN-NeerjaExpressiveNeural', name: 'Neerja (Expressive)', gender: 'female' }
    ],
    'Hindi': [
        { id: 'hi-IN-SwaraNeural', name: 'Swara (Female)', gender: 'female' },
        { id: 'hi-IN-MadhurNeural', name: 'Madhur (Male)', gender: 'male' }
    ],
    'Bengali': [
        { id: 'bn-IN-TanishaaNeural', name: 'Tanishaa (Female)', gender: 'female' },
        { id: 'bn-IN-BashkarNeural', name: 'Bashkar (Male)', gender: 'male' }
    ],
    'Gujarati': [
        { id: 'gu-IN-DhwaniNeural', name: 'Dhwani (Female)', gender: 'female' },
        { id: 'gu-IN-NiranjanNeural', name: 'Niranjan (Male)', gender: 'male' }
    ],
    'Marathi': [
        { id: 'mr-IN-AarohiNeural', name: 'Aarohi (Female)', gender: 'female' },
        { id: 'mr-IN-ManoharNeural', name: 'Manohar (Male)', gender: 'male' }
    ],
    'Tamil': [
        { id: 'ta-IN-PallaviNeural', name: 'Pallavi (Female)', gender: 'female' },
        { id: 'ta-IN-ValluvarNeural', name: 'Valluvar (Male)', gender: 'male' }
    ],
    'Telugu': [
        { id: 'te-IN-ShrutiNeural', name: 'Shruti (Female)', gender: 'female' },
        { id: 'te-IN-MohanNeural', name: 'Mohan (Male)', gender: 'male' }
    ],
    'Kannada': [
        { id: 'kn-IN-SapnaNeural', name: 'Sapna (Female)', gender: 'female' },
        { id: 'kn-IN-GaganNeural', name: 'Gagan (Male)', gender: 'male' }
    ],
    'Malayalam': [
        { id: 'ml-IN-SobhanaNeural', name: 'Sobhana (Female)', gender: 'female' },
        { id: 'ml-IN-MidhunNeural', name: 'Midhun (Male)', gender: 'male' }
    ]
};

const BACKGROUNDS = [
    { id: 'original', name: 'Original Photo', icon: ImageIcon },
    { id: 'office', name: 'Modern Office', icon: Layers },
    { id: 'studio', name: 'TV Studio', icon: Layers },
    { id: 'nature', name: 'Nature View', icon: Layers }
];

const MUSIC = [
    { id: 'none', name: 'No Music' },
    { id: 'calm', name: 'Calm & Relaxing' },
    { id: 'energetic', name: 'High Energy' },
    { id: 'tech', name: 'Tech & Future' }
];

const CAPTION_STYLES = [
    { id: 'default', name: 'Default', desc: 'Clean white text with outline' },
    { id: 'bold', name: 'Bold', desc: 'Large bold yellow text' },
    { id: 'minimal', name: 'Minimal', desc: 'Small subtle text' },
    { id: 'karaoke', name: 'Karaoke', desc: 'Green impact-style text' }
];

const DUB_LANGUAGES = [
    { id: 'Hindi', name: 'Hindi', flag: '🇮🇳' },
    { id: 'English', name: 'English', flag: '🇺🇸' },
    { id: 'English (India)', name: 'English (India)', flag: '🇮🇳' },
    { id: 'Bengali', name: 'Bengali', flag: '🇮🇳' },
    { id: 'Tamil', name: 'Tamil', flag: '🇮🇳' },
    { id: 'Telugu', name: 'Telugu', flag: '🇮🇳' },
    { id: 'Marathi', name: 'Marathi', flag: '🇮🇳' },
    { id: 'Gujarati', name: 'Gujarati', flag: '🇮🇳' },
    { id: 'Kannada', name: 'Kannada', flag: '🇮🇳' },
    { id: 'Malayalam', name: 'Malayalam', flag: '🇮🇳' },
    { id: 'Spanish', name: 'Spanish', flag: '🇪🇸' },
    { id: 'French', name: 'French', flag: '🇫🇷' },
    { id: 'German', name: 'German', flag: '🇩🇪' },
    { id: 'Japanese', name: 'Japanese', flag: '🇯🇵' },
    { id: 'Korean', name: 'Korean', flag: '🇰🇷' },
    { id: 'Chinese', name: 'Chinese', flag: '🇨🇳' },
    { id: 'Arabic', name: 'Arabic', flag: '🇸🇦' },
    { id: 'Portuguese', name: 'Portuguese', flag: '🇧🇷' },
    { id: 'Russian', name: 'Russian', flag: '🇷🇺' },
    { id: 'Italian', name: 'Italian', flag: '🇮🇹' },
];

const FORMAT_ICONS = {
    '16:9': Monitor,
    '9:16': Smartphone
};

const PRESET_CHARACTERS = [
    { id: 'girl1', name: 'Professional Girl 1', url: '/characters/girl1.png', gender: 'female' },
    { id: 'girl2', name: 'Professional Girl 2', url: '/characters/girl2.png', gender: 'female' },
    { id: 'boy1', name: 'Professional Boy 1', url: '/characters/boy1.png', gender: 'male' },
    { id: 'boy2', name: 'Professional Boy 2', url: '/characters/boy2.png', gender: 'male' },
    { id: 'boy3', name: 'Professional Boy 3', url: '/characters/boy3.png', gender: 'male' },
];

const CustomSelect = ({ value, onChange, options, icon: Icon }) => {
    const [isOpen, setIsOpen] = useState(false);
    const containerRef = useRef(null);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (containerRef.current && !containerRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const selectedOption = options.find(opt => opt.value === value) || options[0];

    return (
        <div className="custom-select" ref={containerRef}>
            <div
                className={`select-trigger ${isOpen ? 'active' : ''}`}
                onClick={() => setIsOpen(!isOpen)}
            >
                <div className="select-value">
                    {Icon && <Icon size={16} />}
                    {selectedOption.label}
                </div>
                {isOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </div>
            {isOpen && (
                <div className="select-dropdown">
                    {options.map((opt) => (
                        <div
                            key={opt.value}
                            className={`select-option ${opt.value === value ? 'selected' : ''}`}
                            onClick={() => {
                                onChange(opt.value);
                                setIsOpen(false);
                            }}
                        >
                            <span>{opt.label}</span>
                            {opt.value === value && <Check size={14} className="select-option-check" />}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

const VideoGenerator = ({ navigate }) => {
    // Mobile sidebar state
    const [sidebarOpen, setSidebarOpen] = useState(false);

    // Pipeline State
    const [step, setStep] = useState(1);
    const [topic, setTopic] = useState('');
    const [image, setImage] = useState(null);
    const [previewUrl, setPreviewUrl] = useState(null);
    const [script, setScript] = useState('');

    // Settings State
    const [language, setLanguage] = useState('English');
    const [duration, setDuration] = useState(15);
    const [selectedVoice, setSelectedVoice] = useState(VOICES['English'][0].id);
    const [voiceSpeed, setVoiceSpeed] = useState(0);
    const [voicePitch, setVoicePitch] = useState(0);
    const [bgType, setBgType] = useState('original');
    const [bgMusic, setBgMusic] = useState('none');
    const [musicVolume, setMusicVolume] = useState(0.2);
    const [aspectRatio, setAspectRatio] = useState("16:9");
    const [generationEngine, setGenerationEngine] = useState("gemini");
    const [scriptModel, setScriptModel] = useState('gemini-2.5-flash');

    // Caption State
    const [captionsEnabled, setCaptionsEnabled] = useState(false);
    const [captionStyle, setCaptionStyle] = useState('default');

    // Veo State
    const [veoQuality, setVeoQuality] = useState('fast');

    // Multi-Format State
    const [generateAllFormats, setGenerateAllFormats] = useState(false);


    // Status State
    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState('idle');
    const [statusMessage, setStatusMessage] = useState('');
    const [activeModule, setActiveModule] = useState('studio');
    const [result, setResult] = useState(null);
    const [history, setHistory] = useState([]);

    // Post-processing state
    const [postProcessing, setPostProcessing] = useState(false);
    const [formatResults, setFormatResults] = useState({});
    const [copiedText, setCopiedText] = useState(null);

    // Subscription State
    const handleLogout = async () => {
        try {
            await fetch(`${API_BASE_URL}/logout`, { method: 'POST' });
        } catch (error) {
            console.error('Logout request failed:', error);
        } finally {
            localStorage.removeItem('access_token');
            localStorage.removeItem('user');
            localStorage.removeItem('video_history');
            navigate('/login');
        }
    };
    const [lastGenerationUsage, setLastGenerationUsage] = useState(null);
    // Subscription State
    const [subscriptionTier, setSubscriptionTier] = useState('free');
    const [showPricingModal, setShowPricingModal] = useState(false);
    const [credits, setCredits] = useState({ remaining: 0, limit: 2 });

    // Cinematic options
    const [useTts, setUseTts] = useState(true); // if false => Silent cinematic (no voiceover)
    const [useImage, setUseImage] = useState(true); // if false => Prompt-only, no face image

    const fetchCreditData = async () => {
        try {
            const userStr = localStorage.getItem('user');
            if (!userStr) return;
            const user = JSON.parse(userStr);

            const res = await fetch(`${API_BASE_URL}/user/credits?email=${user.email}`);
            const data = await res.json();
            setCredits({
                remaining: data.available_credits,
                limit: data.subscription_tier === 'pro' ? 100 : 2
            });
            setSubscriptionTier(data.subscription_tier);
        } catch (e) {
            console.log('Credit data not available');
        }
    };

    // Character state
    const [selectedCharacterId, setSelectedCharacterId] = useState(null);
    const [voiceOnlyUrl, setVoiceOnlyUrl] = useState(null);
    const [generatingVoice, setGeneratingVoice] = useState(false);

    useEffect(() => {
        const saved = localStorage.getItem('video_history');
        if (saved) setHistory(JSON.parse(saved));
        fetchCreditData();
    }, []);

    // Update voice when language changes
    useEffect(() => {
        if (VOICES[language]) {
            setSelectedVoice(VOICES[language][0].id);
        }
    }, [language]);

    const saveToHistory = (item) => {
        const newHistory = [item, ...history].slice(0, 10);
        setHistory(newHistory);
        localStorage.setItem('video_history', JSON.stringify(newHistory));
    };

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            setImage(file);
            setPreviewUrl(URL.createObjectURL(file));
            setSelectedCharacterId(null);
        }
    };

    const handleSelectCharacter = async (char) => {
        setSelectedCharacterId(char.id);
        setPreviewUrl(char.url);

        // Fetch the image and convert to File object
        try {
            const response = await fetch(char.url);
            const blob = await response.blob();
            const file = new File([blob], `${char.id}.png`, { type: 'image/png' });
            setImage(file);
        } catch (error) {
            console.error('Error selecting character:', error);
        }
    };

    const handleGenerateVoiceOnly = async () => {
        if (!script) return;
        setGeneratingVoice(true);
        try {
            const formData = new FormData();
            formData.append('script', script);
            formData.append('voice', selectedVoice);
            formData.append('speed', voiceSpeed);
            formData.append('pitch', voicePitch);

            const response = await fetch(`${API_BASE_URL}/generate-voice`, {
                method: 'POST',
                body: formData,
            });
            const data = await response.json();
            if (data.status === 'success') {
                setVoiceOnlyUrl(data.data.audio_url);
                alert('AI Voice generated successfully!');
            }
        } catch (error) {
            console.error('Voice generation failed:', error);
            alert('Failed to generate voice');
        } finally {
            setGeneratingVoice(false);
        }
    };


    const handleDraftScript = async () => {
        if (!topic || (useImage && !image)) return;
        setLoading(true);
        try {
            const formData = new FormData();
            const user = JSON.parse(localStorage.getItem('user'));
            formData.append('topic', topic);
            formData.append('language', language);
            formData.append('duration', duration);
            formData.append('user_email', user.email);
            formData.append('script_model', scriptModel);

            const response = await fetch(`${API_BASE_URL}/draft-script`, {
                method: 'POST',
                body: formData,
            });
            const data = await response.json();
            setScript(data.script);
            setStep(2);
        } catch (error) {
            console.error(error);
            alert('Failed to draft script');
        } finally {
            setLoading(false);
        }
    };

    const handleFinalGenerate = async () => {
        if (credits.remaining <= 0) {
            setShowPricingModal(true);
            return;
        }

        setLoading(true);
        setStatus('generating');
        setStatusMessage('Initializing generation pipeline...');
        try {
            const formData = new FormData();
            formData.append('topic', topic);
            if (useImage && image) {
                formData.append('image', image);
            }
            formData.append('script', script);
            formData.append('language', language);
            formData.append('voice', selectedVoice);
            formData.append('speed', voiceSpeed);
            formData.append('pitch', voicePitch);
            formData.append('background_type', bgType);
            formData.append('music', bgMusic);
            formData.append('music_volume', musicVolume);
            formData.append('duration', duration);
            formData.append('aspect_ratio', aspectRatio);
            formData.append('engine', generationEngine);
            formData.append('veo_quality', veoQuality);
            // Cinematic toggles
            formData.append('use_tts', useTts ? 'true' : 'false');
            formData.append('use_image', useImage ? 'true' : 'false');

            const user = JSON.parse(localStorage.getItem('user'));
            formData.append('user_email', user.email);

            // Caption params
            formData.append('captions_enabled', captionsEnabled ? 'true' : 'false');
            formData.append('caption_style', captionStyle);

            // Multi-format params
            formData.append('generate_all_formats', generateAllFormats ? 'true' : 'false');


            setStatusMessage('Generating video... This may take a few minutes.');
            const response = await fetch(`${API_BASE_URL}/generate`, {
                method: 'POST',
                body: formData,
            });
            const data = await response.json();
            if (data.status === 'error') {
                setStatus('error');
                setResult(data);
                setStep(3);
                return;
            }
            setResult(data);
            fetchCreditData(); // Refresh credits after deduction

            // Extract extra results
            if (data.data?.format_urls) {
                setFormatResults(data.data.format_urls);
            }

            saveToHistory({
                id: Date.now(),
                topic,
                video_url: data.data.video_url,
                date: new Date().toLocaleDateString()
            });
            setStep(3);
            setStatus('success');
            // Refresh credits after deduction
            fetchCreditData();
            setCredits(prev => ({ ...prev, remaining: Math.max(0, prev.remaining - 1) }));

            // Set last generation usage
            if (data.data?.usage) {
                setLastGenerationUsage(data.data.usage);
            }
        } catch (error) {
            console.error(error);
            setStatus('error');
        } finally {
            setLoading(false);
        }
    };

    // Post-generation: convert to a specific format
    const handleConvertFormat = async (targetRatio) => {
        if (!result?.data?.video_url) return;
        setPostProcessing(true);
        try {
            const videoFilename = result.data.video_url.split('/temp/')[1];
            const formData = new FormData();
            formData.append('video_filename', videoFilename);
            formData.append('target_ratio', targetRatio);
            formData.append('mode', 'fit');

            const response = await fetch(`${API_BASE_URL}/convert-format`, {
                method: 'POST',
                body: formData,
            });
            const data = await response.json();
            if (data.status === 'success') {
                setFormatResults(prev => ({
                    ...prev,
                    [targetRatio]: data.data.converted_video_url
                }));
            }
        } catch (error) {
            console.error('Format conversion failed:', error);
        } finally {
            setPostProcessing(false);
        }
    };

    // Post-generation: add captions to existing video 
    const handlePostCaptions = async () => {
        if (!result?.data?.video_url) return;
        setPostProcessing(true);
        try {
            const videoFilename = result.data.video_url.split('/temp/')[1];
            const formData = new FormData();
            formData.append('video_filename', videoFilename);
            formData.append('script', script);
            formData.append('caption_style', captionStyle);
            formData.append('aspect_ratio', aspectRatio);

            const response = await fetch(`${API_BASE_URL}/add-captions`, {
                method: 'POST',
                body: formData,
            });
            const data = await response.json();
            if (data.status === 'success') {
                setResult(prev => ({
                    ...prev,
                    data: {
                        ...prev.data,
                        captioned_video_url: data.data.captioned_video_url
                    }
                }));
            }
        } catch (error) {
            console.error('Caption failed:', error);
        } finally {
            setPostProcessing(false);
        }
    };


    const copyToClipboard = (text, id) => {
        navigator.clipboard.writeText(text);
        setCopiedText(id);
        setTimeout(() => setCopiedText(null), 2000);
    };

    const renderStep1 = () => (
        <div className="wizard-step">
            <div className="section-header">
                <h2>Create Your Masterpiece</h2>
                {/* <p>Start with a topic and your character photo.</p> */}
            </div>

            <div className="modern-form">
                <div className="input-group">
                    <label>Topic / Prompt</label>
                    <textarea
                        value={topic}
                        onChange={(e) => setTopic(e.target.value)}
                        placeholder="Explain how AI works to a 5-year old..."
                        rows="3"
                    />
                </div>

                <div className="grid-2">
                    <div className="input-group">
                        <label><Cpu size={14} /> AI Script Engine</label>
                        <CustomSelect
                            value={scriptModel}
                            onChange={setScriptModel}
                            options={[
                                { value: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro' },
                                { value: 'gemini-1.5-flash', label: 'Gemini 1.5 Flash' },
                                { value: 'gemini-2.5-flash', label: 'Gemini 2.5 Flash' },
                            ]}
                        />
                    </div>
                    <div className="input-group">
                        <label><Languages size={14} /> Language</label>
                        <CustomSelect
                            value={language}
                            onChange={setLanguage}
                            options={Object.keys(VOICES).map(lang => ({
                                value: lang,
                                label: lang === 'English' ? 'English (US/UK)' : lang
                            }))}
                        />
                    </div>
                    <div className="input-group">
                        <label><Clock size={14} /> Duration</label>
                        <CustomSelect
                            value={duration}
                            onChange={(val) => setDuration(parseInt(val))}
                            options={[
                                { value: 15, label: '15 Seconds' },
                                { value: 30, label: '30 Seconds' },
                                { value: 60, label: '60 Seconds' }
                            ]}
                        />
                        {generationEngine === 'gemini' && (
                            <span className="info-subtext">Gemini shots are capped at ~8s</span>
                        )}
                    </div>
                    <div className="input-group">
                        <label><Layers size={14} /> Ratio</label>
                        <CustomSelect
                            value={aspectRatio}
                            onChange={setAspectRatio}
                            options={[
                                { value: '16:9', label: '16:9 (YouTube)' },
                                { value: '9:16', label: '9:16 (Reels/TikTok)' }
                            ]}
                        />
                    </div>
                </div>

                <div className="input-group">
                    <label><User size={14} /> Quick Select Character</label>
                    <div className="character-grid">
                        {PRESET_CHARACTERS.map(char => (
                            <div
                                key={char.id}
                                className={`character-card ${selectedCharacterId === char.id ? 'active' : ''}`}
                                onClick={() => handleSelectCharacter(char)}
                            >
                                <img src={char.url} alt={char.name} />
                                {selectedCharacterId === char.id && (
                                    <div className="char-check">
                                        <CheckCircle2 size={16} />
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                    <div className="or-divider">OR</div>
                    <label><ImageIcon size={14} /> Upload Custom Face</label>
                    {!useImage ? (
                        <div className="preview-mini">
                            <span className="selected-tag">Face image not required (prompt-only)</span>
                        </div>
                    ) : !previewUrl || selectedCharacterId ? (
                        <div className="upload-zone">
                            <input type="file" accept="image/*" onChange={handleFileChange} id="img-up" hidden />
                            <label htmlFor="img-up" className="upload-label">
                                <Upload size={24} />
                                <span>Upload Face Photo</span>
                            </label>
                        </div>
                    ) : (
                        <div className="preview-mini">
                            <img src={previewUrl} alt="face" />
                            <button onClick={() => { setImage(null); setPreviewUrl(null); setSelectedCharacterId(null) }}><X size={14} /></button>
                        </div>
                    )}
                    {selectedCharacterId && (
                        <div className="preview-mini">
                            <img src={previewUrl} alt="face" />
                            <span className="selected-tag">Selected AI Character</span>
                            <button onClick={() => { setImage(null); setPreviewUrl(null); setSelectedCharacterId(null) }}><X size={14} /></button>
                        </div>
                    )}
                </div>

                <button
                    className="primary-btn"
                    onClick={handleDraftScript}
                    disabled={!topic || (useImage && !image) || loading}
                >
                    {loading ? <Loader2 className="spinning" /> : <ChevronRight />}
                    Draft Script
                </button>
            </div>
        </div>
    );

    const renderStep2 = () => (
        <div className="wizard-step wide">
            <div className="section-header">
                <Settings className="header-icon" />
                <h2>Studio Controls</h2>
                <p>Fine-tune your script, voice, and atmosphere.</p>
            </div>

            <div className="studio-layout">
                <div className="studio-main">
                    <div className="input-group">
                        <label><MessageSquare size={14} /> Edit Script</label>
                        <textarea
                            value={script}
                            onChange={(e) => setScript(e.target.value)}
                            rows="10"
                            className="script-editor"
                        />
                    </div>

                    {/* Auto-Captions Card */}
                    <div className="feature-card">
                        <div className="feature-card-header" onClick={() => setCaptionsEnabled(!captionsEnabled)}>
                            <div className="feature-info">
                                <Subtitles size={18} />
                                <div>
                                    <h4>Auto Captions / Subtitles</h4>
                                    <p>Burn subtitles directly into the video</p>
                                </div>
                            </div>
                            <label className="toggle-switch" onClick={(e) => e.stopPropagation()}>
                                <input
                                    type="checkbox"
                                    checked={captionsEnabled}
                                    onChange={(e) => setCaptionsEnabled(e.target.checked)}
                                />
                                <span className="toggle-slider"></span>
                            </label>
                        </div>
                        {captionsEnabled && (
                            <div className="feature-card-body">
                                <div className="caption-styles">
                                    {CAPTION_STYLES.map(style => (
                                        <button
                                            key={style.id}
                                            className={`caption-style-btn ${captionStyle === style.id ? 'active' : ''}`}
                                            onClick={() => setCaptionStyle(style.id)}
                                        >
                                            <span className="style-name">{style.name}</span>
                                            <span className="style-desc">{style.desc}</span>
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Multi-Format Card */}
                    <div className="feature-card">
                        <div className="feature-card-header" onClick={() => setGenerateAllFormats(!generateAllFormats)}>
                            <div className="feature-info">
                                <Monitor size={18} />
                                <div>
                                    <h4>Multi-Format Output</h4>
                                    <p>Auto-generate 16:9 and 9:16 versions</p>
                                </div>
                            </div>
                            <label className="toggle-switch" onClick={(e) => e.stopPropagation()}>
                                <input
                                    type="checkbox"
                                    checked={generateAllFormats}
                                    onChange={(e) => setGenerateAllFormats(e.target.checked)}
                                />
                                <span className="toggle-slider"></span>
                            </label>
                        </div>
                        {generateAllFormats && (
                            <div className="feature-card-body">
                                <div className="format-preview-grid">
                                    {Object.entries(FORMAT_ICONS).map(([ratio, Icon]) => (
                                        <div key={ratio} className={`format-preview-item ${ratio === aspectRatio ? 'original' : ''}`}>
                                            <Icon size={24} />
                                            <span>{ratio}</span>
                                            {ratio === aspectRatio && <span className="badge">Primary</span>}
                                        </div>
                                    ))}
                                  </div>
                            </div>
                        )}
                    </div>
                </div>

                <div className="studio-sidebar">
                    <div className="settings-card">
                        <h3><Zap size={16} /> Generation Engine</h3>
                        <div className="engine-toggle-grid">
                            <button
                                className="engine-btn active"
                                disabled
                            >
                                <div className="engine-icon-wrap"><Sparkles size={20} /></div>
                                <div className="engine-info">
                                    <div className="engine-name">Gemini Veo</div>
                                    <div className="engine-desc">Cinematic Video (Selected)</div>
                                </div>
                            </button>
                        </div>
                    </div>

                    <div className="settings-card">
                        <h3><Settings size={16} /> Cinematic Options</h3>
                        <div className="toggle-row">
                            <label className="toggle-switch">
                                <input
                                    type="checkbox"
                                    checked={!useTts}
                                    onChange={(e) => setUseTts(!e.target.checked)}
                                />
                                <span className="toggle-slider"></span>
                            </label>
                            <div className="toggle-text">
                                <div className="t-title">Silent Cinematic</div>
                                <div className="t-desc">No voiceover (no TTS)</div>
                            </div>
                        </div>
                        <div className="toggle-row" style={{ marginTop: 10 }}>
                            <label className="toggle-switch">
                                <input
                                    type="checkbox"
                                    checked={!useImage}
                                    onChange={(e) => setUseImage(!e.target.checked)}
                                />
                                <span className="toggle-slider"></span>
                            </label>
                            <div className="toggle-text">
                                <div className="t-title">Generate Without Face Image</div>
                                <div className="t-desc">Prompt-only cinematic shot</div>
                            </div>
                        </div>
                    </div>

                    {generationEngine === 'gemini' && (
                        <div className="settings-card">
                            <h3><Sparkles size={16} /> Veo Quality</h3>
                            <div className="quality-toggle">
                                <button
                                    className={`q-btn ${veoQuality === 'fast' ? 'active' : ''}`}
                                    onClick={() => setVeoQuality('fast')}
                                >
                                    <div className="q-name">Veo 3.1 Fast</div>
                                    <div className="q-desc code-desc">veo-3.1-fast-generate-preview</div>
                                </button>
                                <button
                                    className={`q-btn ${veoQuality === 'standard' ? 'active' : ''}`}
                                    onClick={() => setVeoQuality('standard')}
                                >
                                    <div className="q-name">Veo 3.1 Standard</div>
                                    <div className="q-desc code-desc">veo-3.1-generate-preview</div>
                                </button>
                            </div>
                        </div>
                    )}

                    <div className="settings-card">
                        <h3><User size={16} /> Voice Settings</h3>
                        <div className="input-group" style={{ opacity: useTts ? 1 : 0.5 }}>
                            <label>Pick a Voice</label>
                            <CustomSelect
                                value={selectedVoice}
                                onChange={setSelectedVoice}
                                options={VOICES[language].map(v => ({
                                    value: v.id,
                                    label: v.name
                                }))}
                                />
                        </div>
                        <div className="range-controls" style={{ opacity: useTts ? 1 : 0.5 }}>
                            <div className="range-item">
                                <span>Speed: {voiceSpeed}%</span>
                                <input type="range" min="-50" max="50" value={voiceSpeed} onChange={(e) => setVoiceSpeed(parseInt(e.target.value))} disabled={!useTts} />
                            </div>
                            <div className="range-item">
                                <span>Pitch: {voicePitch}Hz</span>
                                <input type="range" min="-20" max="20" value={voicePitch} onChange={(e) => setVoicePitch(parseInt(e.target.value))} disabled={!useTts} />
                            </div>
                        </div>
                    </div>

                    <div className="settings-card">
                        <h3><Music size={16} /> Atmosphere</h3>
                        <div className="input-group">
                            <label>Background Music</label>
                            <CustomSelect
                                value={bgMusic}
                                onChange={setBgMusic}
                                options={MUSIC.map(m => ({
                                    value: m.id,
                                    label: m.name
                                }))}
                            />
                        </div>
                        {bgMusic !== 'none' && (
                            <div className="range-item">
                                <span>Volume: {Math.round(musicVolume * 100)}%</span>
                                <input type="range" min="0" max="1" step="0.1" value={musicVolume} onChange={(e) => setMusicVolume(parseFloat(e.target.value))} />
                            </div>
                        )}
                    </div>

                    <div className="settings-card">
                        <h3><Layers size={16} /> Visuals</h3>
                        <div className="bg-grid">
                            {BACKGROUNDS.map(bg => (
                                <button
                                    key={bg.id}
                                    className={`bg-option ${bgType === bg.id ? 'active' : ''}`}
                                    onClick={() => setBgType(bg.id)}
                                >
                                    <bg.icon size={16} />
                                    <span>{bg.name}</span>
                                </button>
                            ))}
                        </div>
                    </div>

                    {voiceOnlyUrl && useTts && (
                        <div className="voice-download-card">
                            <div className="voice-info">
                                <Activity size={18} />
                                <div>
                                    <div className="v-title">AI Voice Generated</div>
                                    <div className="v-desc">Ready for download</div>
                                </div>
                            </div>
                            <a href={voiceOnlyUrl} target="_blank" download className="v-dl-btn">
                                <Download size={14} /> Download Voice
                            </a>
                        </div>
                    )}

                    {useTts && (
                        <button
                            className="voice-only-btn"
                            onClick={handleGenerateVoiceOnly}
                            disabled={loading || generatingVoice || !script}
                        >
                            {generatingVoice ? <Loader2 className="spinning" /> : <Mic size={18} />}
                            Generate Voice Only
                        </button>
                    )}

                    <button className="generate-final-btn" onClick={handleFinalGenerate} disabled={loading}>
                        {loading ? <Loader2 className="spinning" /> : <Play size={18} />}
                        Generate Final Video
                    </button>
                    <button className="back-btn" onClick={() => setStep(1)}>Back to Step 1</button>
                </div>
            </div>
        </div>
    );

    const renderStep3 = () => (
        <div className="wizard-step">
            {status === 'generating' ? (
                <LoadingScreen message="SECURE ENTERPRISE ENVIRONMENT" />
            ) : status === 'success' ? (
                <div className="result-view">
                    <div className="success-banner">
                        <CheckCircle2 size={24} />
                        <h2>Video Generated Successfully!</h2>
                    </div>

                    {/* Main Video Player */}
                    <div className="final-video-card">
                        <video controls autoPlay src={result.data.video_url} className="cinema-player" />
                        <div className="video-actions">
                            <a href={result.data.video_url} target="_blank" download className="download-cta">
                                <Download size={18} /> Download MP4
                            </a>
                            <button className="restart-btn" onClick={() => { setStep(1); setResult(null); setStatus('idle'); setFormatResults({}); setDubResults([]); setLastGenerationUsage(null) }}>
                                <RefreshCcw size={16} /> Create Another
                            </button>
                        </div>
                    </div>

                    {/* Generation Cost Summary */}
                    {lastGenerationUsage && (
                        <div className="generation-cost-summary">
                            <div className="cost-summary-header">
                                <Sparkles size={16} />
                                <h3>Generation Details & Cost</h3>
                            </div>
                            <div className="cost-summary-grid">
                                <div className="cost-item">
                                    <div className="cost-label">Script Tokens</div>
                                    <div className="cost-value">
                                        {(lastGenerationUsage.script_input_tokens || 0) + (lastGenerationUsage.script_output_tokens || 0)}
                                    </div>
                                </div>
                                <div className="cost-item">
                                    <div className="cost-label">TTS Characters</div>
                                    <div className="cost-value">{lastGenerationUsage.tts_characters || script.length}</div>
                                </div>
                                <div className="cost-item">
                                    <div className="cost-label">Estimated Cost (USD)</div>
                                    <div className="cost-value highlight-usd">${(lastGenerationUsage.cost?.total_usd ?? 0).toFixed(4)}</div>
                                </div>
                                <div className="cost-item">
                                    <div className="cost-label">Estimated Cost (INR)</div>
                                    <div className="cost-value highlight-inr">₹{(lastGenerationUsage.cost?.total_inr ?? 0).toFixed(2)}</div>
                                </div>
                                <div className="cost-item">
                                    <div className="cost-label">Credits Deducted</div>
                                    <div className="cost-value">1</div>
                                </div>
                                <div className="cost-item">
                                    <div className="cost-label">Credits Remaining</div>
                                    <div className="cost-value">{credits.remaining}</div>
                                </div>
                            </div>
                            {lastGenerationUsage.cost?.breakdown && (
                                <p className="cost-pricing-note">
                                    Duration: {lastGenerationUsage.cost.breakdown.duration || 0}s • Tokens: {lastGenerationUsage.cost.breakdown.tokens || 0} • Chars: {lastGenerationUsage.cost.breakdown.chars || 0} • Dubs: {lastGenerationUsage.cost.breakdown.languages || 0}
                                </p>
                            )}
                        </div>
                    )}

                    {/* Post-Processing Tools */}
                    <div className="post-tools-section">
                        <h3 className="post-tools-title">
                            <Settings size={18} /> Post-Processing Tools
                        </h3>

                        {/* Multi-Format Downloads */}
                        <div className="post-tool-card">
                            <div className="post-tool-header">
                                <Monitor size={18} />
                                <h4>Multi-Format Export</h4>
                            </div>
                            <div className="format-export-grid">
                                {['16:9', '9:16'].map(ratio => {
                                    const Icon = FORMAT_ICONS[ratio];
                                    const hasFormat = formatResults[ratio];
                                    return (
                                        <div key={ratio} className="format-export-item">
                                            <div className="format-icon-label">
                                                <Icon size={20} />
                                                <span>{ratio}</span>
                                                <span className="format-label">
                                                    {ratio === '16:9' ? 'YouTube' : ratio === '9:16' ? 'Reels' : 'Square'}
                                                </span>
                                            </div>
                                            {hasFormat ? (
                                                <a href={formatResults[ratio]} target="_blank" download className="format-download-btn downloaded">
                                                    <Download size={14} /> Download
                                                </a>
                                            ) : (
                                                <button
                                                    className="format-download-btn"
                                                    onClick={() => handleConvertFormat(ratio)}
                                                    disabled={postProcessing}
                                                >
                                                    {postProcessing ? <Loader2 size={14} className="spinning" /> : <Play size={14} />}
                                                    Convert
                                                </button>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        </div>

                        {/* Add Captions Post */}
                        {!result.data.captioned_video_url && (
                            <div className="post-tool-card">
                                <div className="post-tool-header">
                                    <Subtitles size={18} />
                                    <h4>Add Captions</h4>
                                </div>
                                <div className="post-tool-body">
                                    <div className="caption-style-select-mini">
                                        {CAPTION_STYLES.map(s => (
                                            <button
                                                key={s.id}
                                                className={`mini-style-btn ${captionStyle === s.id ? 'active' : ''}`}
                                                onClick={() => setCaptionStyle(s.id)}
                                            >
                                                {s.name}
                                            </button>
                                        ))}
                                    </div>
                                    <button
                                        className="post-action-btn"
                                        onClick={handlePostCaptions}
                                        disabled={postProcessing}
                                    >
                                        {postProcessing ? <Loader2 size={14} className="spinning" /> : <Subtitles size={14} />}
                                        Burn Captions
                                    </button>
                                </div>
                            </div>
                        )}

                        {result.data.captioned_video_url && (
                            <div className="post-tool-card success-card">
                                <div className="post-tool-header">
                                    <CheckCircle2 size={18} />
                                    <h4>Captioned Video Ready</h4>
                                </div>
                                <a href={result.data.captioned_video_url} target="_blank" download className="format-download-btn downloaded">
                                    <Download size={14} /> Download Captioned
                                </a>
                            </div>
                        )}


                    </div>
                </div>
            ) : (
                <div className="error-view">
                    <AlertCircle size={48} color="#ef4444" />
                    <h2>Something went wrong</h2>
                    <p>{result?.message || 'We hit a snag during rendering. Please try again or check your API configuration.'}</p>
                    <button onClick={() => setStep(2)}>Try Again</button>
                </div>
            )}
        </div>
    );

    const [paymentLoading, setPaymentLoading] = useState(null); // plan being paid

    const handleRazorpayPayment = async (planId) => {
        const userStr = localStorage.getItem('user');
        if (!userStr) { alert('Please login to upgrade.'); return; }
        const user = JSON.parse(userStr);

        setPaymentLoading(planId);
        try {
            // 1. Create order on backend
            const fd = new FormData();
            fd.append('plan_id', planId);
            fd.append('user_email', user.email);
            const res = await fetch(`${API_BASE_URL}/payment/create-order`, { method: 'POST', body: fd });
            const data = await res.json();
            if (data.status !== 'success') throw new Error(data.detail || 'Order creation failed');
            const { order_id, amount, currency, key_id, plan_name, plan_credits } = data.data;

            // 2. Load Razorpay script dynamically
            await new Promise((resolve, reject) => {
                if (window.Razorpay) return resolve();
                const script = document.createElement('script');
                script.src = 'https://checkout.razorpay.com/v1/checkout.js';
                script.onload = resolve;
                script.onerror = reject;
                document.body.appendChild(script);
            });

            // 3. Open Razorpay checkout
            const options = {
                key: key_id,
                amount,
                currency,
                name: 'Social Stamp',
                description: `${plan_name} Plan — ${plan_credits} Credits`,
                order_id,
                prefill: { name: user.full_name || '', email: user.email },
                theme: { color: '#00a859' },
                handler: async (response) => {
                    // 4. Verify payment on backend
                    try {
                        const vfd = new FormData();
                        vfd.append('razorpay_order_id', response.razorpay_order_id);
                        vfd.append('razorpay_payment_id', response.razorpay_payment_id);
                        vfd.append('razorpay_signature', response.razorpay_signature);
                        vfd.append('user_email', user.email);
                        const vRes = await fetch(`${API_BASE_URL}/payment/verify`, { method: 'POST', body: vfd });
                        const vData = await vRes.json();
                        if (vData.status === 'success') {
                            alert(`✅ Payment Successful!\n${vData.message}`);
                            fetchCreditData();
                            setShowPricingModal(false);
                        } else {
                            alert('❌ Payment verification failed. Contact support.');
                        }
                    } catch (e) {
                        alert('Payment verification error. Please contact support.');
                    }
                },
                modal: { ondismiss: () => setPaymentLoading(null) },
            };
            const rzp = new window.Razorpay(options);
            rzp.open();
        } catch (e) {
            alert(`Payment failed: ${e.message}`);
        } finally {
            setPaymentLoading(null);
        }
    };

    const renderPricingModal = () => {
        if (!showPricingModal) return null;

        return (
            <div className="pricing-overlay" onClick={() => setShowPricingModal(false)}>
                <div className="pricing-modal" onClick={e => e.stopPropagation()}>
                    <button className="modal-close" onClick={() => setShowPricingModal(false)}><X size={20} /></button>

                    <div className="pricing-header">
                        <h2>Choose Your Plan</h2>
                        <p>Unlock the full power of Social Stamp for your brand.</p>
                    </div>

                    <div className="pricing-grid">
                        <div className="pricing-card">
                            <div className="plan-lvl">Basic</div>
                            <div className="plan-price">₹0 <div>/ month</div></div>
                            <ul className="plan-features">
                                <li><Check size={16} /> 2 Videos Per Day</li>
                                <li><Check size={16} /> 720p Resolution</li>
                                <li><Check size={16} /> Standard Voices</li>
                                <li><Check size={16} /> Basic Support</li>
                            </ul>
                            <button className="plan-btn" onClick={() => setShowPricingModal(false)}>Current Plan</button>
                        </div>

                        <div className="pricing-card featured">
                            <div className="featured-badge">Most Popular</div>
                            <div className="plan-lvl">Professional</div>
                            <div className="plan-price">₹2,499 <div>/ month</div></div>
                            <ul className="plan-features">
                                <li><Check size={16} /> 50 Videos Per Day</li>
                                <li><Check size={16} /> 1080p Full HD</li>
                                <li><Check size={16} /> All Premium Voices</li>
                                <li><Check size={16} /> Advanced Captions</li>
                                <li><Check size={16} /> Priority Support</li>
                            </ul>
                            <button
                                className="plan-btn primary"
                                disabled={paymentLoading === 'pro'}
                                onClick={() => handleRazorpayPayment('pro')}
                            >
                                {paymentLoading === 'pro' ? '⏳ Processing...' : '💳 Pay ₹2,499'}
                            </button>
                        </div>

                        <div className="pricing-card">
                            <div className="plan-lvl">Agency</div>
                            <div className="plan-price">₹7,999 <div>/ month</div></div>
                            <ul className="plan-features">
                                <li><Check size={16} /> Unlimited Videos</li>
                                <li><Check size={16} /> 4K Ultra HD</li>
                                <li><Check size={16} /> Team Access</li>
                                <li><Check size={16} /> API Integration</li>
                                <li><Check size={16} /> White-label Output</li>
                                <li><Check size={16} /> 24/7 Dedicated Support</li>
                            </ul>
                            <button
                                className="plan-btn"
                                disabled={paymentLoading === 'agency'}
                                onClick={() => handleRazorpayPayment('agency')}
                            >
                                {paymentLoading === 'agency' ? '⏳ Processing...' : '💳 Pay ₹7,999'}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        );
    };

    return (
        <div className="studio-app">
            {renderPricingModal()}

            {/* Mobile sidebar overlay */}
            {sidebarOpen && (
                <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)} />
            )}

            <aside className={`sidebar ${sidebarOpen ? 'sidebar-open' : ''}`}>
                <div className="sidebar-brand">
                    <img src="/logo.png" alt="Logo" className="brand-logo" />
                    <div className="brand-text">
                        <span className="brand-title-top">SOCIAL</span>
                        <span className="brand-title-bottom">STAMP</span>
                    </div>
                    <button className="sidebar-close-btn" onClick={() => setSidebarOpen(false)}>
                        <X size={18} />
                    </button>
                </div>

                <div className="nav-menu">
                    <div
                        className={`nav-item ${activeModule === 'studio' ? 'active' : ''}`}
                        onClick={() => { setActiveModule('studio'); setSidebarOpen(false); }}
                    >
                        <Monitor size={16} /> Content Studio
                    </div>
                    <div
                        className="nav-item subscription-btn"
                        onClick={() => { setShowPricingModal(true); setSidebarOpen(false); }}
                    >
                        <Zap size={16} color="#fbbf24" fill="#fbbf24" /> Upgrade to Pro
                    </div>
                </div>

                <nav className="history-list">
                    <div className="history-header"><History size={14} /> Recent Videos</div>
                    {history.length === 0 ? (
                        <div className="history-empty">No projects yet</div>
                    ) : (
                        history.map(item => (
                            <div key={item.id} className="history-item" onClick={() => window.open(item.video_url)}>
                                <div className="item-topic">{item.topic}</div>
                                <div className="item-date">{item.date}</div>
                            </div>
                        ))
                    )}
                </nav>

                <div className="credit-card">
                    <div className="credit-info">
                        <span>Daily Credits</span>
                        <span>{credits.remaining} / {credits.limit}</span>
                    </div>
                    <div className="credit-bar">
                        <div
                            className="credit-fill"
                            style={{ width: `${(credits.remaining / credits.limit) * 100}%` }}
                        ></div>
                    </div>
                    <button className="upgrade-link" onClick={() => setShowPricingModal(true)}>
                        <Zap size={12} /> Get More Credits
                    </button>
                </div>

            </aside>

            <main className="main-content">
                <header className="top-header">
                    <div className="header-left">
                        <button className="mobile-menu-btn" onClick={() => setSidebarOpen(true)}>
                            <Menu size={22} />
                        </button>
                        <div className="header-breadcrumbs">
                            <span>SOCIAL STAMP</span> /
                            <span>{activeModule === 'studio' ? 'Content Studio' : 'Dashboard'}</span>
                        </div>
                    </div>
                    <div className="header-actions">
                        <div className="api-badge">
                            <div className="pulse-dot"></div>
                            <span className="api-badge-text">API Active</span>
                        </div>
                        <button className="logout-btn" onClick={handleLogout} title="Logout">
                            <LogOut size={18} />
                            <span className="logout-text">Logout</span>
                        </button>
                    </div>
                </header>

                <div className="content-area">
                    {activeModule === 'studio' ? (
                        <>
                            <div className="wizard-progress">
                                <div className={`progress-step ${step >= 1 ? 'active' : ''} ${step > 1 ? 'done' : ''}`}>1</div>
                                <div className={`progress-line ${step > 1 ? 'active' : ''}`}></div>
                                <div className={`progress-step ${step >= 2 ? 'active' : ''} ${step > 2 ? 'done' : ''}`}>2</div>
                                <div className={`progress-line ${step > 2 ? 'active' : ''}`}></div>
                                <div className={`progress-step ${step >= 3 ? 'active' : ''}`}>3</div>
                            </div>
                            {step === 1 && renderStep1()}
                            {step === 2 && renderStep2()}
                            {step === 3 && renderStep3()}
                        </>
                    ) : (
                        <div className="empty-state">Select a module from the sidebar</div>
                    )}
                </div>
                <footer className="app-footer">
                    POWERED BY <span>RUNR</span>
                </footer>
            </main>
        </div>
    );
};

export default VideoGenerator;
