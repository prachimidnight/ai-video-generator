# Implementation Plan - Phase 2: Professional AI Video Suite

This phase transforms the AI Video Generator into a full-featured professional studio.

## 1. Feature Breakdown

### A. Script Workflow (Split into 2 steps)
- **New Endpoint `/draft-script`**: Takes topic + language, returns AI script.
- **Frontend Editor**: Editable textarea for the script.
- **Duration Tuning**: Prompt Gemini to target 15s, 30s, or 60s lengths.

### B. Voice & Audio Control
- **Voice Library**: Support 10+ English and 5+ Hindi voices.
- **Parameters**: Add slider for `rate` (speed) and `pitch`.
- **Background Music**: Integration of local audio tracks (Calm, Energetic, Techy) with volume mixing.

### C. Visual Enhancements
- **Background Selection**: 
  - Mode 1: Original (Stitch).
  - Mode 2: Studio Backgrounds (Office, Studio, Nature). Uses local image processing (Pillow) to swap backgrounds.
- **16:9 Standard**: Ensure all outputs follow widescreen format.
- **Captions**: Basic overlay support (simulated or via D-ID config if possible).

### D. Data & History
- **Video History**: Sidebar/Gallery showing previous generations (stored in LocalStorage).
- **Download Options**: choice of resolution and format.

## 2. Technical Architecture Updates

### Backend (FastAPI)
- **`main.py`**:
  - `POST /draft-script`: Initial Gemini call.
  - `POST /generate-video`: Final processing (TTS -> D-ID).
- **`services/tts_service.py`**:
  - Support `en-US` and `hi-IN` voices.
  - Integration of `voice_speed` and `voice_pitch`.
- **`services/video_service.py`**:
  - Support for background image overrides.

### Frontend (React)
- **`VideoGenerator.jsx`**:
  - Two-stage wizard (1. Draft -> 2. Edit/Configure -> 3. Generate).
  - Advanced Settings drawer.
  - History sidebar.

## 3. Step-by-Step Execution

1. [ ] **Backend Refactoring**: Create `/draft-script` and update `/generate` to take more params.
2. [ ] **TTS Overhaul**: Add voice library and prosody support.
3. [ ] **Frontend Wizard**: Implement the Step 1 (Topic) -> Step 2 (Edit) flow.
4. [ ] **Settings UI**: Create the voice/music/duration control panel.
5. [ ] **Background Processing**: Add image background replacement using Pillow.
6. [ ] **History Gallery**: Implement LocalStorage-based persistence.
