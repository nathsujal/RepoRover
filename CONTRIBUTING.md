# Contributing to RepoRover

We're excited that you're interested in contributing to RepoRover! Before you begin, please take a moment to read these guidelines.

## 🛠️ Development Setup

1. **Fork and Clone**
   - Fork the repository on GitHub
   - Clone your forked repository locally
   ```bash
   git clone https://github.com/your-username/RepoRover.git
   cd RepoRover
   ```

2. **Set up the development environment**
   - Install Poetry if you haven't already:
     ```bash
     curl -sSL https://install.python-poetry.org | python3 -
     ```
   - Install dependencies:
     ```bash
     poetry install
     ```
   - Set up pre-commit hooks:
     ```bash
     poetry run pre-commit install
     ```

3. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 🧪 Running Tests

Run the test suite with:
```bash
poetry run pytest
```

## 📝 Code Style

We use:
- **Black** for code formatting
- **isort** for import sorting
- **mypy** for static type checking
- **flake8** for linting

These are automatically checked by pre-commit hooks.

## 📜 Pull Request Process

1. Ensure all tests pass
2. Update the README.md with details of changes if needed
3. Submit a pull request with a clear description of your changes

## 🚀 Your First Contribution

Looking for a good first issue? Check the issues labeled `good first issue` in our issue tracker.

## 📄 License

By contributing, you agree that your contributions will be licensed under the project's MIT License.
