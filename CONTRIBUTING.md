# Contributing to FinOpsGuard

First off, thank you for considering contributing to FinOpsGuard! It's people like you that make FinOpsGuard a great tool for cloud cost management and governance.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Community](#community)

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

**Examples of behavior that contributes to a positive environment:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Examples of unacceptable behavior:**
- The use of sexualized language or imagery
- Trolling, insulting/derogatory comments, and personal or political attacks
- Public or private harassment
- Publishing others' private information without explicit permission
- Other conduct which could reasonably be considered inappropriate

## Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:
- **Python 3.13+**: FinOpsGuard requires Python 3.13 or higher
- **PostgreSQL 14+**: For database features (optional but recommended)
- **Redis 6+**: For caching (optional but recommended)
- **Git**: For version control
- **Make**: For build automation

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/FinOpsGuard.git
   cd FinOpsGuard
   ```

3. Add the upstream repository:
   ```bash
   git remote add upstream https://github.com/honeybadger-technologies/FinOpsGuard.git
   ```

## Development Setup

### 1. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
# Install development dependencies
pip install -r requirements.txt

# Install optional cloud provider SDKs (for usage integration)
pip install boto3 google-cloud-monitoring google-cloud-bigquery \
            azure-mgmt-monitor azure-mgmt-costmanagement azure-identity
```

### 3. Configure Environment

```bash
# Copy example environment file
cp env.example .env

# Edit .env with your configuration
# Minimum required for development:
# - Set DB_ENABLED=false for simple testing
# - Set REDIS_ENABLED=false for simple testing
```

### 4. Run Database Migrations (if using PostgreSQL)

```bash
# Create database
createdb finopsguard

# Run migrations
make db-upgrade
```

### 5. Run Tests

```bash
# Run all tests
make test

# Run specific test file
pytest tests/unit/test_policy_engine.py -v

# Run with coverage
pytest --cov=finopsguard tests/
```

### 6. Start Development Server

```bash
# Start API server
make run

# Or manually:
PYTHONPATH=src uvicorn finopsguard.api.server:app --reload --host 0.0.0.0 --port 8080
```

### 7. Verify Installation

```bash
# Check health
curl http://localhost:8080/healthz

# View API docs
open http://localhost:8080/docs
```

## How to Contribute

### Types of Contributions

We welcome many types of contributions:

#### 🐛 Bug Reports
- Use the GitHub issue tracker
- Include steps to reproduce
- Provide system information (OS, Python version, etc.)
- Include error messages and stack traces

#### ✨ Feature Requests
- Open an issue to discuss before implementing
- Explain the use case and benefits
- Consider backward compatibility

#### 📝 Documentation
- Fix typos and improve clarity
- Add examples and tutorials
- Update API documentation
- Translate documentation

#### 🔧 Code Contributions
- Fix bugs
- Implement new features
- Improve performance
- Add test coverage

#### 🧪 Testing
- Write unit tests
- Add integration tests
- Improve test coverage
- Report test failures

### Contribution Workflow

1. **Check existing issues** - Look for existing issues or create a new one
2. **Discuss your approach** - Comment on the issue to discuss your solution
3. **Create a branch** - Use a descriptive name:
   ```bash
   git checkout -b feature/add-cost-optimization
   git checkout -b fix/policy-evaluation-bug
   git checkout -b docs/update-api-guide
   ```
4. **Make your changes** - Follow coding standards
5. **Test thoroughly** - Add tests for new functionality
6. **Commit your changes** - Use clear commit messages
7. **Push and create PR** - Submit a pull request

## Coding Standards

### Python Style Guide

We follow **PEP 8** with some modifications:

#### General Rules
- **Line Length**: Maximum 120 characters (configured in `.flake8`)
- **Indentation**: 4 spaces (no tabs)
- **Imports**: Organize imports (stdlib → third-party → local)
- **Docstrings**: Use Google-style docstrings
- **Type Hints**: Use type annotations for function signatures

#### Code Style

```python
# Good
def calculate_monthly_cost(
    instance_type: str,
    hours_per_month: float = 730.0,
    region: str = "us-east-1"
) -> float:
    """
    Calculate monthly cost for an instance.
    
    Args:
        instance_type: EC2 instance type (e.g., 't3.micro')
        hours_per_month: Hours in a month (default: 730)
        region: AWS region
        
    Returns:
        Estimated monthly cost in USD
        
    Raises:
        ValueError: If instance_type is not found
    """
    hourly_rate = get_instance_price(instance_type, region)
    return hourly_rate * hours_per_month
```

#### Naming Conventions
- **Functions/Variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private methods**: `_leading_underscore`

#### Error Handling

```python
# Good - Specific exceptions
try:
    result = risky_operation()
except ValueError as e:
    logger.error(f"Invalid value: {e}")
    raise
except KeyError as e:
    logger.warning(f"Missing key: {e}")
    return default_value

# Bad - Bare except
try:
    result = risky_operation()
except:  # Don't do this
    pass
```

### Linting

```bash
# Run linter
make lint

# Auto-fix some issues
autopep8 --in-place --aggressive --recursive src/

# Check specific file
flake8 src/finopsguard/api/server.py
```

### Pre-commit Checks

Before committing, run:

```bash
# Run all checks
make lint && make test

# Format code
black src/ tests/

# Sort imports
isort src/ tests/
```

## Testing Guidelines

### Test Organization

```
tests/
├── unit/              # Unit tests (fast, isolated)
│   ├── test_policy_engine.py
│   ├── test_auth.py
│   └── test_pricing.py
├── integration/       # Integration tests (slower, real services)
│   ├── test_http.py
│   └── test_usage_api.py
└── fixtures/          # Test data and fixtures
    └── sample_terraform.tf
```

### Writing Tests

#### Unit Tests

```python
import pytest
from finopsguard.engine.policy_engine import PolicyEngine

class TestPolicyEngine:
    """Test policy engine functionality."""
    
    def test_evaluate_budget_policy(self):
        """Test budget policy evaluation."""
        # Arrange
        engine = PolicyEngine()
        policy = {
            "id": "test-policy",
            "budget": {"max_monthly_cost": 100.0}
        }
        resources = [{"monthly_cost": 50.0}]
        
        # Act
        result = engine.evaluate(policy, resources)
        
        # Assert
        assert result.status == "pass"
        assert result.total_cost == 50.0
```

#### Integration Tests

```python
import pytest
from fastapi.testclient import TestClient
from finopsguard.api.server import app

@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)

def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```

### Test Coverage

- Aim for **80%+ coverage** for new code
- All public APIs must have tests
- Critical paths require 100% coverage

```bash
# Generate coverage report
pytest --cov=finopsguard --cov-report=html tests/

# View report
open htmlcov/index.html
```

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
pytest tests/unit/test_policy_engine.py -v

# Run tests matching pattern
pytest -k "test_policy" -v

# Run with markers
pytest -m "not slow" -v

# Run with verbose output
pytest -vv tests/
```

## Documentation

### Documentation Types

#### 1. Code Documentation
- Use docstrings for all public functions and classes
- Follow Google-style format
- Include examples for complex functions

#### 2. API Documentation
- Update OpenAPI spec (`docs/api/openapi.yaml`)
- Add examples to API endpoints
- Document request/response schemas

#### 3. User Documentation
- Update README.md for major features
- Add guides to `docs/` directory
- Include configuration examples

#### 4. Architecture Documentation
- Update `docs/architecture.md` for architectural changes
- Document design decisions
- Add diagrams for complex systems

### Documentation Standards

```python
def complex_function(param1: str, param2: int = 10) -> dict:
    """
    One-line summary of function.
    
    Detailed description of what the function does,
    including any important caveats or edge cases.
    
    Args:
        param1: Description of param1
        param2: Description of param2 (default: 10)
        
    Returns:
        Dictionary containing:
            - key1: Description of key1
            - key2: Description of key2
            
    Raises:
        ValueError: When param1 is empty
        KeyError: When required config is missing
        
    Example:
        >>> result = complex_function("test", 20)
        >>> print(result["key1"])
        'value1'
    """
    pass
```

## Pull Request Process

### Before Submitting

1. ✅ **Tests pass**: Run `make test`
2. ✅ **Linting passes**: Run `make lint`
3. ✅ **Documentation updated**: Update relevant docs
4. ✅ **Commit messages clear**: Follow commit message guidelines
5. ✅ **No merge conflicts**: Rebase on latest main

### PR Title Format

Use conventional commit style:

```
feat: Add Azure cost optimization recommendations
fix: Correct policy evaluation for GCP resources
docs: Update API authentication guide
test: Add integration tests for usage endpoints
refactor: Simplify pricing adapter interface
chore: Update dependencies
```

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update
- [ ] Code refactoring
- [ ] Performance improvement
- [ ] Test addition/improvement

## How Has This Been Tested?
Describe testing process

## Checklist
- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published

## Screenshots (if applicable)
Add screenshots for UI changes

## Additional Notes
Any additional information
```

### Review Process

1. **Automated Checks**: CI/CD runs tests and linting
2. **Code Review**: At least one maintainer reviews
3. **Feedback**: Address review comments
4. **Approval**: Maintainer approves PR
5. **Merge**: Maintainer merges (squash and merge preferred)

### Commit Message Guidelines

Follow conventional commits:

```bash
# Format
<type>(<scope>): <subject>

<body>

<footer>

# Examples
feat(pricing): Add Azure live pricing adapter

Implement real-time pricing fetching from Azure API.
Includes caching and error handling.

Closes #123

fix(auth): Correct JWT token expiration check

The token expiration was not properly handling timezone.
Now uses UTC consistently.

Fixes #456

docs(api): Update usage integration examples

Add complete examples for AWS, GCP, and Azure usage
data retrieval.
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements

## Issue Reporting

### Bug Reports

Use the bug report template:

```markdown
**Describe the bug**
A clear and concise description of the bug.

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior**
What you expected to happen.

**Actual behavior**
What actually happened.

**Error messages**
```
Paste error messages here
```

**Environment:**
- OS: [e.g., Ubuntu 22.04]
- Python version: [e.g., 3.13.0]
- FinOpsGuard version: [e.g., 0.3.0]
- Installation method: [e.g., pip, git]

**Additional context**
Any other relevant information.
```

### Feature Requests

```markdown
**Is your feature request related to a problem?**
A clear description of the problem.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
Alternative solutions or features you've considered.

**Additional context**
Any other context, examples, or screenshots.

**Would you like to implement this feature?**
- [ ] Yes, I'd like to implement this
- [ ] No, just requesting
```

## Community

### Getting Help

- **Documentation**: Check [docs/](docs/) directory
- **GitHub Issues**: Search existing issues
- **Discussions**: Use GitHub Discussions for questions
- **Chat**: Join our community chat (if available)

### Communication Guidelines

- Be respectful and professional
- Stay on topic
- Help others when you can
- Give constructive feedback
- Assume good intentions

### Recognition

Contributors are recognized in:
- `CONTRIBUTORS.md` file (alphabetically)
- Release notes for significant contributions
- GitHub contributors page

## License

By contributing to FinOpsGuard, you agree that your contributions will be licensed under the same license as the project (see [LICENSE](LICENSE) file).

## Questions?

Don't hesitate to ask questions! We're here to help:
- Open an issue with the `question` label
- Start a discussion on GitHub Discussions
- Reach out to maintainers

---

**Thank you for contributing to FinOpsGuard!** 🎉

Your contributions make this project better for everyone in the FinOps community.

