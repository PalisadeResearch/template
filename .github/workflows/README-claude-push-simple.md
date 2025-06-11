# Claude Code Review Email Workflow

This workflow automatically runs Claude AI code review on every push and sends the analysis via email using AWS SES.

## How It Works

1. Triggers on every push to any branch
2. Runs Claude AI analysis on the repository and changed files
3. Extracts Claude's response from the execution log
4. Sends the analysis via AWS SES email

## Required GitHub Secrets

You need to configure the following secrets in your GitHub repository settings:

1. **ANTHROPIC_API_KEY** - Your Anthropic API key for Claude
2. **AWS_ACCESS_KEY_ID** - AWS access key with SES permissions
3. **AWS_SECRET_ACCESS_KEY** - AWS secret access key
4. **AWS_REGION** - AWS region where SES is configured (e.g., `us-east-1`)
5. **SES_FROM_EMAIL** - Verified email address in AWS SES to send from

## AWS SES Setup

1. Verify your sender email address in AWS SES
2. If in sandbox mode, also verify the recipient email (jaime.raldua.veuthey@gmail.com)
3. Ensure your AWS credentials have the following permissions:
   - `ses:SendEmail`
   - `ses:SendRawEmail`

## Email Content

Each email contains:

### Header Information
- **Repository**: Full repository name (e.g., `user/repo-name`)
- **Branch**: The branch that was pushed to
- **Commit SHA**: The specific commit hash
- **Author**: GitHub username who made the push
- **Commit Message**: The commit message from the push

### Changed Files
Lists all files that were modified in the push (up to 20 files)

### Claude's Analysis Section
This is the main content where Claude provides:

1. **Repository Overview**: Analysis of the repository's structure, purpose, and technology stack
2. **Change Analysis**: Detailed review of what was modified in the specific files
3. **Code Quality Assessment**: 
   - Potential issues like missing error handling
   - Inconsistent naming conventions
   - Refactoring opportunities
   - Best practice adherence
4. **Research-Specific Checks**:
   - Reproducibility guidelines compliance
   - Scientific validity of data processing changes
   - Analysis scripts and visualization improvements
5. **Documentation Review**:
   - Whether changes are properly documented
   - Documentation synchronization with code changes
6. **Recommendations**: Specific, actionable suggestions for improvement

The analysis is formatted in a clear, structured manner with markdown-style headers and bullet points for easy reading.

## Features

The workflow provides:
- Automated code review on every push
- Email delivery with both HTML and plain text formats
- Comprehensive AI analysis tailored for research projects

## Customization

To change the recipient email, modify the email sending step in the workflow file:
```yaml
--to "jaime.raldua.veuthey@gmail.com" \
```

To adjust the analysis prompt, modify the prompt section in the Claude action step.

## Troubleshooting

If Claude's analysis is not appearing in emails:

1. Check the GitHub Actions logs for the "Extract Claude's Response" step
2. Verify the execution file is being created by looking for "Execution file found at:" in the logs
3. Check if the JSON parsing is working - you should see "Claude response preview:" with the first 500 characters
4. If you see "Unable to parse Claude response" or "Trying alternative extraction method...", the JSON structure might have changed

The workflow expects Claude's output in this format:
```json
{
  "type": "assistant",
  "message": {
    "content": [
      {
        "type": "text",
        "text": "Claude's analysis text..."
      }
    ]
  }
}
``` 