# Docker & Environment Setup Guide

> **Note:** This guide covers Docker-based development and multi-environment setup.  
> For the quickest setup path, see the main [README.md](../README.md).

### Prerequisites
- Python 3.9 or higher (3.11+ recommended)
- Docker Desktop (optional, for containerized deployment)
- Git
- Notion API access
- Google AI (Gemini) API key

### Quick Start

1. **Clone the Repository**
   ```bash
   git clone https://github.com/agarciangulo/Task-Manager-5.8.git
   cd Task-Manager-5.8
   ```

2. **Environment Setup**
   - Copy the appropriate environment file:
     ```bash
     # For development
     cp .env.development.example .env.development
     
     # For staging
     cp .env.staging.example .env.staging
     
     # For production
     cp .env.production.example .env.production
     ```
   - Fill in your environment variables in the `.env.[environment]` file

3. **Docker Setup**
   ```bash
   # Build the Docker image
   docker compose build
   
   # Run the application
   docker compose up
   ```

### Environment-Specific Instructions

#### Development Environment
- Use for local development and testing
- Debug mode enabled
- Local database
- Hot-reloading enabled
- Run with:
  ```bash
  docker compose up
  ```

#### Staging Environment
- Use for pre-production testing
- Mirrors production settings
- Test database
- Run with:
  ```bash
  docker compose -f docker-compose.yml -f docker-compose.staging.yml up
  ```

#### Production Environment
- Use for live deployment
- Optimized settings
- Production database
- Run with:
  ```bash
  docker compose -f docker-compose.yml -f docker-compose.production.yml up
  ```

### Required Environment Variables
```ini
# API Keys
NOTION_TOKEN=your_notion_token
NOTION_DATABASE_ID=your_database_id
NOTION_FEEDBACK_DB_ID=your_feedback_db_id
GEMINI_API_KEY=your_gemini_api_key

# AI Configuration
AI_PROVIDER=gemini  # or 'openai' if you prefer
CHAT_MODEL=gemini-1.5-flash  # Default Gemini model

# Application Settings
FLASK_APP=src.api.app_auth
FLASK_ENV=development  # or staging/production
FLASK_DEBUG=1  # 0 for staging/production
```

### AI Provider Configuration

This application supports multiple AI providers:

#### Google AI (Gemini) - Default
- **API Key**: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
- **Model**: `gemini-1.5-flash` (recommended) or `gemini-1.5-pro`
- **Environment Variable**: `GEMINI_API_KEY=your_key_here`

#### OpenAI (Alternative)
- **API Key**: Get from [OpenAI Platform](https://platform.openai.com/api-keys)
- **Model**: `gpt-4` or `gpt-3.5-turbo`
- **Environment Variable**: `OPENAI_API_KEY=your_key_here`
- **Configuration**: Set `AI_PROVIDER=openai` in your environment

### Common Tasks

#### Adding New Dependencies
1. Add to `requirements.txt`
2. Rebuild Docker container:
   ```bash
   docker compose build
   ```

#### Updating Environment Variables
1. Update the appropriate `.env.[environment]` file
2. Restart the container:
   ```bash
   docker compose down
   docker compose up
   ```

#### Accessing Logs
```bash
# View container logs
docker compose logs -f

# View specific service logs
docker compose logs -f web
```

### Troubleshooting

#### Common Issues
1. **Port Already in Use**
   - Check if port 5000 is available
   - Change port in docker-compose.yml if needed

2. **Environment Variables Not Loading**
   - Verify .env file exists
   - Check file permissions
   - Ensure correct environment file is being used

3. **Docker Build Fails**
   - Clear Docker cache: `docker system prune -a`
   - Rebuild: `docker compose build --no-cache`

4. **AI Provider Issues**
   - Verify API key is correct
   - Check AI_PROVIDER setting
   - Ensure required dependencies are installed

### Best Practices

1. **Development**
   - Always work in feature branches
   - Test locally before pushing
   - Keep .env files out of git

2. **Staging**
   - Test all features before production
   - Use production-like data
   - Verify all integrations

3. **Production**
   - Use production environment variables
   - Monitor logs and performance
   - Regular backups

### Deployment Checklist

#### Before Deployment
- [ ] All tests passing
- [ ] Environment variables set
- [ ] Database migrations ready
- [ ] Dependencies updated
- [ ] Documentation updated

#### After Deployment
- [ ] Verify application is running
- [ ] Check logs for errors
- [ ] Test critical features
- [ ] Monitor performance

### Support

For issues or questions:
1. Check the troubleshooting guide
2. Review the logs
3. Contact the development team

### Security Notes
- Never commit .env files
- Rotate API keys regularly
- Use strong passwords
- Keep dependencies updated

## Features

- Task management and tracking
- AI-powered task analysis (Gemini/OpenAI)
- Notion integration
- Team feedback system
- Project health monitoring

## Requirements

- Python 3.9+ (3.11+ recommended)
- Google AI (Gemini) API key (or OpenAI API key)
- Notion API access
- Modern web browser

## Project Structure

```
.
├── src/                   # Main source code
│   ├── api/              # Flask API layer
│   │   ├── app_auth.py   # Main Flask application
│   │   ├── routes/       # API route blueprints
│   │   └── models/       # Request/response models
│   ├── core/             # Core functionality
│   │   ├── ai/           # AI-related code
│   │   ├── agents/       # AI agents
│   │   ├── services/     # Business logic layer
│   │   └── security/     # Authentication & security
│   ├── config/           # Configuration
│   ├── plugins/          # Plugin system
│   └── utils/            # Utilities (Gmail processor, etc.)
├── tests/                # Test suite
├── static/               # Static files (CSS, JS)
├── templates/            # HTML templates
├── deployment/           # Deployment scripts
├── docs/                 # Documentation
└── requirements.txt      # Python dependencies
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Your License Here] 