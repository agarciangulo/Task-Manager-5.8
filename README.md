# AI Team Support

## Environment Setup Guide

### Prerequisites
- Python 3.9 or higher
- Docker Desktop
- Git
- Notion API access
- OpenAI API key

### Quick Start

1. **Clone the Repository**
   ```bash
   git clone [your-repository-url]
   cd ai-team-support
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
OPENAI_API_KEY=your_openai_key

# Application Settings
FLASK_APP=app_flask.py
FLASK_ENV=development  # or staging/production
FLASK_DEBUG=1  # 0 for staging/production
```

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