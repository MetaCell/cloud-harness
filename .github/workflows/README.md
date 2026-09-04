# GitHub Actions - Docker Build and Push

This workflow builds the CloudHarness development container and pushes it to Google Cloud Registry.

## Required Secrets

You need to configure the following secrets in your GitHub repository settings:

### 1. `GCP_PROJECT_ID`
- **Description**: Your Google Cloud Project ID
- **Example**: `my-cloudharness-project`
- **How to find**: Go to Google Cloud Console → Project Info → Project ID

### 2. `GCP_SA_KEY`
- **Description**: Google Cloud Service Account key (JSON format)
- **Format**: Complete JSON key file content
- **Required permissions**: 
  - `Storage Admin` (for pushing to Container Registry)
  - `Container Registry Service Agent`

## Setting up the Service Account

1. **Create a Service Account**:
   ```bash
   gcloud iam service-accounts create github-actions \
     --description="Service account for GitHub Actions" \
     --display-name="GitHub Actions"
   ```

2. **Grant necessary permissions**:
   ```bash
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/storage.admin"
   
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/containerregistry.ServiceAgent"
   ```

3. **Create and download the key**:
   ```bash
   gcloud iam service-accounts keys create github-actions-key.json \
     --iam-account=github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com
   ```

4. **Add the key to GitHub Secrets**:
   - Copy the entire content of `github-actions-key.json`
   - Go to GitHub repository → Settings → Secrets and variables → Actions
   - Create new secret named `GCP_SA_KEY`
   - Paste the JSON content

## Workflow Triggers

The workflow runs on:
- **Push to main/develop**: Builds and pushes with branch name and `latest` tags
- **Pull requests**: Builds and pushes with PR reference tags
- **Manual trigger**: Can be run manually from GitHub Actions tab
- **File changes**: Only triggers when relevant files are modified

## Image Tags

The workflow creates multiple tags:
- `latest` (only for main branch)
- `<branch-name>` (for branch pushes)
- `<branch-name>-<sha>` (with git commit SHA)
- `pr-<number>` (for pull requests)

## Multi-platform Support

The workflow builds for both:
- `linux/amd64` (Intel/AMD processors)
- `linux/arm64` (ARM processors, including Apple Silicon)

## Registry Location

Images are pushed to: `gcr.io/YOUR_PROJECT_ID/cloudharness-dev`

## Usage

After the workflow runs, you can pull the image:

```bash
# Pull latest (from main branch)
docker pull gcr.io/YOUR_PROJECT_ID/cloudharness-dev:latest

# Pull specific branch
docker pull gcr.io/YOUR_PROJECT_ID/cloudharness-dev:develop

# Pull specific commit
docker pull gcr.io/YOUR_PROJECT_ID/cloudharness-dev:main-abc1234
```
