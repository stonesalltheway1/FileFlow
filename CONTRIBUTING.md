# Contributing to FileFlow

Thank you for considering contributing to FileFlow! This document outlines the process for contributing to the project.

## Code of Conduct

By participating in this project, you are expected to uphold our Code of Conduct. Please be respectful and constructive in all interactions.

## How Can I Contribute?

### Reporting Bugs

Bug reports help us improve FileFlow. To report a bug:

1. **Use the GitHub issue tracker** - Submit your bug report using our [bug report template](https://github.com/stonesalltheway1/FileFlow/issues/new?template=bug_report.md).
2. **Provide detailed information** - Include steps to reproduce, expected vs. actual behavior, and your environment details.
3. **Include screenshots/logs** - If applicable, add screenshots or log outputs that demonstrate the issue.

### Suggesting Features

Have an idea to make FileFlow better? Great!

1. **Check existing issues/PRs** - Ensure your suggestion hasn't already been proposed.
2. **Open a feature request** - Use our [feature request template](https://github.com/stonesalltheway1/FileFlow/issues/new?template=feature_request.md).
3. **Be specific** - Clearly describe the feature, why it's valuable, and how it should work.

### Submitting Changes

1. **Fork the repository** - Create your own fork of the project.
2. **Create a branch** - Make your changes in a new branch based on `master`.
3. **Follow coding standards** - Match the existing coding style.
4. **Add tests** - Include tests for new features or bug fixes.
5. **Update documentation** - Keep docs in sync with code changes.
6. **Submit a pull request** - Use our [PR template](https://github.com/stonesalltheway1/FileFlow/blob/master/.github/PULL_REQUEST_TEMPLATE.md).

## Development Workflow

### Setting Up Your Development Environment

1. Clone your fork of the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the test suite to ensure everything works:
   ```
   pytest
   ```

### Testing and Validation

Before submitting a PR, please:

1. Run all tests
2. Ensure no new linting issues are introduced
3. Test the license functionality with test licenses
4. Verify changes work across operating systems (if applicable)

## License Considerations

FileFlow uses a proprietary licensing system. When contributing:

1. Be mindful of the tiered feature structure (Basic, Pro, Premium, Business)
2. Use the `@premium_feature` decorator for protected features
3. Do not modify the core licensing system without discussion

## Questions?

If you have questions or need help, please open an issue with the "question" label.
