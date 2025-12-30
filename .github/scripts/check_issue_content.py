import os
import json
import google.genai as genai
from github import Github
from github import Auth
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Initialize GitHub client
auth = Auth.Token(os.getenv('GITHUB_TOKEN'))
github = Github(auth=auth)

# Load GitHub event data
event_path = os.getenv('GITHUB_EVENT_PATH')
with open(event_path, 'r') as f:
    event = json.load(f)

# Determine event type and get issue information
event_name = os.getenv('GITHUB_EVENT_NAME')

if event_name == 'issues':
    # For issues event
    issue_number = event['issue']['number']
    issue_title = event['issue']['title']
    issue_body = event['issue']['body']
    issue_labels = [label['name'] for label in event['issue']['labels']]
    repo_full_name = event['repository']['full_name']
elif event_name == 'issue_comment':
    # For issue_comment event
    issue_number = event['issue']['number']
    issue_title = event['issue']['title']
    issue_body = event['issue']['body']
    issue_labels = [label['name'] for label in event['issue']['labels']]
    repo_full_name = event['repository']['full_name']
    comment_body = event['comment']['body']
else:
    # Unsupported event type
    print(f"Unsupported event type: {event_name}")
    exit(0)

# Determine the issue type based on title or labels
issue_type = "bug"  # Default to bug
if any(label in ['feature', 'Feature'] for label in issue_labels):
    issue_type = "feature"
elif any(label in ['doc', 'documentation', 'Documentation'] for label in issue_labels):
    issue_type = "documentation"
elif any(label in ['consult', 'Consult'] for label in issue_labels):
    issue_type = "consult"

# Define required sections based on issue type
required_sections = {
    "bug": {
        "zh": [
            "操作系统及版本",
            "安装工具的python环境",
            "python版本",
            "AISBench工具版本",
            "AISBench执行命令",
            "模型配置文件或自定义配置文件内容",
            "实际行为"
        ],
        "en": [
            "Operating System and Version",
            "Python Environment for Tool Installation",
            "Python Version",
            "AISBench Tool Version",
            "AISBench Execution Command",
            "Model Configuration File or Custom Configuration File Content",
            "Actual Behavior"
        ]
    },
    "feature": {
        "zh": ["功能描述", "实现思路", "预期效果"],
        "en": ["Feature Description", "Implementation Ideas", "Expected Effects"]
    },
    "documentation": {
        "zh": ["文档类型", "文档位置", "修改内容"],
        "en": ["Documentation Type", "Documentation Location", "Modification Content"]
    },
    "consult": {
        "zh": ["咨询问题", "相关背景", "已尝试的方法"],
        "en": ["Consultation Question", "Related Background", "Methods Tried"]
    }
}

# Detect language of the issue body
def detect_language(text):
    if re.search(r'[\u4e00-\u9fa5]', text):
        return "zh"
    return "en"

language = detect_language(issue_body)

# Get the appropriate sections for the detected language and issue type
sections_to_check = required_sections.get(issue_type, {}).get(language, required_sections["bug"][language])

# Create prompt for Gemini API
prompt = f"""
You are an assistant that checks if GitHub issue content is complete based on the required sections.

Issue Title: {issue_title}
Issue Body:
{issue_body}

Required Sections ({language}):
{chr(10).join([f"- {section}" for section in sections_to_check])}

Please check if the issue contains all the required sections with sufficient information. For each section:
1. Indicate if it's present and complete
2. If not complete, specify what information is missing or needs to be补充 (in {language})

Format your response as follows:

## 问题内容检查结果

### 检查状态
[PASS/FAIL]

### 详细检查
{chr(10).join([f"- {section}: [COMPLETE/INCOMPLETE]" for section in sections_to_check])}

### 改进建议
[List specific suggestions for each incomplete section, or "所有内容已完备！"]

### 补充说明
[Any additional comments]

Please respond in {language} and ensure your response is clear and helpful.
"""

# Call Gemini API
try:
    # Use the new genai package with correct model name
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(prompt)
    comment_body = response.text

    # Post comment to GitHub issue
    repo = github.get_repo(repo_full_name)
    issue = repo.get_issue(number=issue_number)
    issue.create_comment(comment_body)

    print("Issue content check completed and comment posted.")

except Exception as e:
    print(f"Error occurred: {str(e)}")

    # Post error comment
    repo = github.get_repo(repo_full_name)
    issue = repo.get_issue(number=issue_number)
    error_comment = f"""
    ## 问题内容检查失败

    在检查问题内容时发生错误：
    ```
    {str(e)}
    ```

    请稍后重试或联系仓库管理员。
    """
    issue.create_comment(error_comment)
