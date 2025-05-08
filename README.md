# AI Team Support

A Flask-based web application for task management and team support.

## Setup Instructions

1. **Clone the repository**
   ```bash
   git clone [repository-url]
   cd AI-Team-Support
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   - Copy `.env.example` to `.env`
   - Fill in your API keys and configuration:
     ```
     OPENAI_API_KEY=your_openai_api_key
     NOTION_TOKEN=your_notion_token
     NOTION_DATABASE_ID=your_notion_database_id
     NOTION_FEEDBACK_DB_ID=your_notion_feedback_db_id
     DEBUG_MODE=False
     ```

5. **Run the application**
   ```bash
   python app_flask.py
   ```
   The application will be available at `http://localhost:5000`

## Features

- Task management and tracking
- AI-powered task analysis
- Notion integration
- Team feedback system
- Project health monitoring

## Requirements

- Python 3.13+
- OpenAI API key
- Notion API access
- Modern web browser

## Project Structure

```
.
├── app_flask.py          # Main Flask application
├── core/                 # Core functionality
│   ├── ai/              # AI-related code
│   ├── adapters/        # External service adapters
│   └── ...
├── static/              # Static files (CSS, JS)
├── templates/           # HTML templates
├── plugins/             # Plugin system
└── requirements.txt     # Python dependencies
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Your License Here] 