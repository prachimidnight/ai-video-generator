# AI Video Generator

This project consists of a FastAPI backend and a React (Vite) frontend.

## Project Structure

- `backend/`: Python FastAPI server
- `frontend/`: React Vite application

## Getting Started

### Backend Setup (Python)

1. **Navigate to the backend folder**:
   ```bash
   cd backend
   ```

2. **Create a Virtual Environment** (like `node_modules` but for Python):
   ```bash
   python3 -m venv venv
   ```

3. **Activate the Virtual Environment**:
   - **Linux/macOS**: `source venv/bin/activate`
   - **Windows**: `venv\Scripts\activate`

4. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Start the Server**:
   ```bash
   python main.py
   ```
   *The server will run at http://localhost:8000*

### Frontend Setup (React)

1. **Navigate to the frontend folder**:
   ```bash
   cd frontend
   ```

2. **Install Dependencies**:
   ```bash
   npm install
   ```

3. **Start the Dev Server**:
   ```bash
   npm run dev
   ```
   *The app will run at http://localhost:5173 (or similar)*

## Testing the API

You can test the backend independently using the built-in **Swagger UI**:
1. Start the backend server.
2. Open your browser and go to: `http://localhost:8000/docs`
3. You will see the `/generate` endpoint. Click "Try it out" to test with an image and text.
