# Deployment Guide

The take-home submission asks for:

1. A source code repository URL.
2. A deployed application URL that Treasury can access and test.

This project is deploy-ready for a simple Python web service.

## Recommended Path: GitHub + Render

Render is a good fit for this prototype because it can run the standard-library Python server with no extra framework.

### 1. Create A GitHub Repository

From the project folder:

```bash
cd "/Users/danielfields/Documents/AI Job Test"
git init
git add .
git commit -m "TTB label compliance prototype"
```

Create a new GitHub repository, then connect it:

```bash
git remote add origin https://github.com/YOUR_USERNAME/ttb-label-compliance-prototype.git
git branch -M main
git push -u origin main
```

Your source code answer will be:

```text
https://github.com/YOUR_USERNAME/ttb-label-compliance-prototype
```

### 2. Deploy On Render

1. Go to `https://render.com`.
2. Create a new Web Service.
3. Connect the GitHub repository.
4. Use these settings:

   ```text
   Runtime: Python
   Build Command: pip install -r requirements.txt
   Start Command: python3 app.py --no-browser
   ```

5. Deploy.

Render will provide a public URL like:

```text
https://ttb-label-compliance-prototype.onrender.com
```

That URL is your deployed application answer.

## Important Deployment Note

The deployed version remains a prototype. On a public host:

- Do not upload real PII.
- Do not upload sensitive government documents.
- Use sample labels only.
- Saved cases may reset depending on host filesystem behavior.

The production recommendation remains local or government-controlled deployment with encrypted storage and formal access controls.

