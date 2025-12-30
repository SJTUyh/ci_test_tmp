# Issue Content Check Script

This script uses Gemini API to check if GitHub issue content is complete based on the required sections defined in the issue templates.

## Configuration

### 1. Gemini API Key

To use this script, you need to set up a Gemini API key in your GitHub repository secrets:

1. Go to your GitHub repository
2. Click on "Settings"
3. In the left sidebar, click on "Secrets and variables" > "Actions"
4. Click on "New repository secret"
5. Enter `GEMINI_API_KEY` as the name
6. Enter your Gemini API key as the value
7. Click on "Add secret"

### 2. GitHub Token

The script uses the built-in `GITHUB_TOKEN` secret, which is automatically available in GitHub Actions workflows.

## Supported Issue Types

The script currently supports the following issue types:
- Bug reports
- Feature requests
- Documentation updates
- Consultation requests

It automatically detects the language (Chinese/English) and checks the relevant sections based on the issue template.

## Workflow

The GitHub Actions workflow is triggered when an issue is opened or edited. It runs the script to check the issue content and posts a comment with the results.
