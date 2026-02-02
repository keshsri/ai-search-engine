# AI Search Engine - Frontend

Streamlit-based web interface for the AI Semantic Search Engine.

## Features

- 📤 Document upload (PDF, DOCX, TXT)
- 💬 Chat interface with conversation history
- 🔍 Semantic search over documents
- 📚 Document management (list, delete)
- 🗂️ Conversation management (view, delete)
- 📄 Source citations for answers

## Setup

### 1. Create Virtual Environment

```bash
cd frontend
python -m venv venv
```

### 2. Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure API URL

Create `.env` file:
```bash
cp .env.example .env
```

Edit `.env` and add your API Gateway URL:
```
API_BASE_URL=https://your-api-id.execute-api.us-east-1.amazonaws.com/dev
```

### 5. Run Locally

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

## Deployment

### Option 1: Streamlit Cloud (Free)

1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Select `frontend/app.py` as main file
5. Add `API_BASE_URL` in Secrets (Settings)
6. Deploy!

Your app will be available at: `https://yourapp.streamlit.app`

### Option 2: AWS (ECS/Lambda)

See main project documentation for AWS deployment options.

## Usage

1. **Upload Documents**: Use sidebar to upload PDF/DOCX/TXT files
2. **Ask Questions**: Type questions in the chat input
3. **View Sources**: Click "Sources" to see document excerpts
4. **Manage Conversations**: View and delete past conversations
5. **New Conversation**: Click "New Conversation" to start fresh

## Configuration

Edit `app.py` to customize:
- Page title and icon
- Number of sources displayed
- UI colors and styling
- Timeout values

## Troubleshooting

**Connection Error:**
- Check API_BASE_URL in `.env`
- Verify API is deployed and accessible
- Check CORS settings if needed

**Upload Timeout:**
- First request may timeout (cold start)
- Retry after 5 seconds

**Missing Conversations:**
- Conversations auto-delete after 15 days (TTL)

## Tech Stack

- **Streamlit** - Web framework
- **Requests** - HTTP client
- **Python-dotenv** - Environment variables
