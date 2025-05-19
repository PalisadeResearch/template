# Claude Guidelines for PalisadeResearch/template

## Project Overview
This is a template repository for research projects, particularly those that involve generating academic papers with figures. It focuses on creating a reproducible development environment, enforcing code quality, and automating the paper generation process.

## Code Style Guidelines

### Python
- Use [ruff](https://github.com/charliermarsh/ruff) for linting and formatting
- Follow PEP 8 style guide
- Use type hints when appropriate
- Write docstrings for functions and classes

### Reproducibility
- Ensure all figure generation is deterministic
- Use fixed random seeds when applicable
- Include all necessary dependencies in pyproject.toml

## Review Criteria
When reviewing code, please focus on:
1. **Reproducibility**: Ensure changes don't break the ability to reproduce results
2. **Code Quality**: Check for clear, maintainable code following project standards
3. **Documentation**: Verify that changes include appropriate documentation
4. **Performance**: Look for potential performance issues, especially in figure generation
5. **Dependencies**: Ensure new dependencies are properly added to the relevant files

## Project Structure
- `src/`: Contains Python source code
- `paper-latex/`: Contains LaTeX source files
- `paper-typst/`: Contains Typst source files
- `build.ninja`: Defines build targets
- `.github/workflows/`: Contains CI/CD configurations

## Common Tasks
- Building papers: `ninja paper`
- Generating figures: `ninja figures`
- Creating Python environment: `ninja .venv`

## Questions?
If you're unsure about anything, feel free to ask the repository maintainers. The primary contact is @dmitrii-palisaderesearch.
