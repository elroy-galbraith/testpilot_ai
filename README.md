# TestPilot AI - AI-Powered Test Generation Platform

TestPilot AI is a comprehensive platform that generates automated tests from natural language specifications using AI agents. The platform includes a FastAPI backend, React frontend, Slack integration, and Playwright test execution engine.

## 🏗️ Project Structure

```
testpilot_ai/
├── frontend/          # React dashboard application
├── backend/           # FastAPI server with LLM integration
├── infra/            # Infrastructure as Code (Terraform)
├── scripts/          # Utility scripts and tools
├── .github/          # GitHub Actions workflows
└── .taskmaster/      # Task management and project planning
```

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- Docker and Docker Compose
- AWS CLI (for deployment)
- Terraform (for infrastructure)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd testpilot_ai
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. **Start development services**
   ```bash
   # Start backend
   cd backend
   pip install -r requirements.txt
   uvicorn main:app --reload --port 8000

   # Start frontend (in another terminal)
   cd frontend
   npm install
   npm start
   ```

## 🏷️ Task Management

This project uses TaskMaster AI for task management and project planning. Tasks are organized in the `.taskmaster/` directory.

### View Current Tasks
```bash
task-master list
```

### Get Next Task
```bash
task-master next
```

### View Task Details
```bash
task-master show <task-id>
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest --cov=. --cov-report=html
```

### Frontend Tests
```bash
cd frontend
npm test
```

### End-to-End Tests
```bash
npm run test:e2e
```

## 🐳 Docker Development

### Build Images
```bash
# Build all services
docker-compose build

# Build specific service
docker-compose build backend
```

### Run Services
```bash
# Start all services
docker-compose up

# Start specific service
docker-compose up backend
```

## 🔧 Development Guidelines

### Code Style

**Backend (Python)**
- Use Black for code formatting
- Use isort for import sorting
- Use Flake8 for linting
- Follow PEP 8 guidelines
- Use type hints

**Frontend (React/TypeScript)**
- Use ESLint and Prettier
- Follow React best practices
- Use TypeScript for type safety
- Use functional components with hooks

### Git Workflow

1. Create feature branches from `develop`
2. Use conventional commit messages
3. Submit pull requests for review
4. Ensure CI/CD pipeline passes
5. Merge to `develop` for staging
6. Merge to `main` for production

### Commit Message Format
```
type(scope): description

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### Environment Management

- Use `.env` files for local development
- Use GitHub Secrets for CI/CD
- Use AWS Parameter Store for production secrets
- Never commit sensitive data

## 🚀 Deployment

### Staging Deployment
- Automatic deployment on push to `develop` branch
- Uses GitHub Actions workflow
- Deploys to AWS ECS staging cluster

### Production Deployment
- Manual deployment from `main` branch
- Requires approval in GitHub Actions
- Deploys to AWS ECS production cluster

### Infrastructure Deployment
```bash
cd infra
terraform init
terraform plan -var-file=staging.tfvars
terraform apply -var-file=staging.tfvars
```

## 📊 Monitoring and Logging

- Application logs: CloudWatch Logs
- Metrics: CloudWatch Metrics
- Alerts: CloudWatch Alarms
- Health checks: ECS health checks and load balancer health checks

## 🔐 Security

- All API endpoints require authentication
- Use JWT tokens for session management
- Implement rate limiting
- Use HTTPS in production
- Follow OWASP security guidelines
- Regular security audits and dependency updates

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📝 API Documentation

- Backend API docs: `http://localhost:8000/docs` (Swagger UI)
- API specification: OpenAPI 3.0
- Postman collection available in `/docs` directory

## 🆘 Troubleshooting

### Common Issues

**Backend won't start**
- Check if all dependencies are installed
- Verify environment variables are set
- Check if port 8000 is available

**Frontend build fails**
- Clear node_modules and reinstall
- Check Node.js version compatibility
- Verify all environment variables

**Docker build fails**
- Check Dockerfile syntax
- Verify all required files are present
- Check Docker daemon is running

### Getting Help

- Check the [Issues](https://github.com/your-repo/issues) page
- Review the [Wiki](https://github.com/your-repo/wiki)
- Contact the development team

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- FastAPI for the backend framework
- React for the frontend framework
- Playwright for test automation
- LangChain for LLM integration
- AWS for cloud infrastructure 