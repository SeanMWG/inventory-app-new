# PowerShell script to set up GitHub repository and Azure deployment

# Parameters
param(
    [Parameter(Mandatory=$true)]
    [string]$githubRepoName,
    
    [Parameter(Mandatory=$true)]
    [string]$githubOrg,
    
    [Parameter(Mandatory=$false)]
    [string]$branch = "main"
)

# Ensure Azure CLI and GitHub CLI are installed
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Error "Azure CLI is not installed. Please install it first."
    exit 1
}

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Error "GitHub CLI is not installed. Please install it first."
    exit 1
}

# Check if logged in to Azure
$azContext = az account show 2>$null | ConvertFrom-Json
if (-not $azContext) {
    Write-Host "Please log in to Azure..."
    az login
}

# Check if logged in to GitHub
$ghAuth = gh auth status 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Please log in to GitHub..."
    gh auth login
}

# Get Azure Web App details from terraform-local
$webAppName = "inventory-app" # Update this if different in your terraform config
$resourceGroup = "inventory-app-rg" # Update this if different in your terraform config

# Create GitHub repository if it doesn't exist
Write-Host "Creating GitHub repository..."
gh repo create "$githubOrg/$githubRepoName" --private --confirm

# Create Azure service principal for GitHub Actions
Write-Host "Creating Azure service principal..."
$sp = az ad sp create-for-rbac --name "github-actions-$webAppName" --role contributor --scopes /subscriptions/$($azContext.id)/resourceGroups/$resourceGroup --sdk-auth | ConvertFrom-Json

# Add GitHub Secrets
Write-Host "Adding GitHub Secrets..."
gh secret set AZURE_CREDENTIALS -b $($sp | ConvertTo-Json -Compress) -R "$githubOrg/$githubRepoName"

# Get database connection string from Azure
$connectionString = az webapp config connection-string list --resource-group $resourceGroup --name $webAppName --query "[?name=='DATABASE_URL'].value" -o tsv
gh secret set DATABASE_URL -b $connectionString -R "$githubOrg/$githubRepoName"

# Initialize git repository and push to GitHub
Write-Host "Initializing git repository..."
git init
git add .
git commit -m "Initial commit"
git branch -M $branch
git remote add origin "https://github.com/$githubOrg/$githubRepoName.git"
git push -u origin $branch

Write-Host "Setup complete! Your repository is now configured for Azure deployment."
Write-Host "GitHub repository: https://github.com/$githubOrg/$githubRepoName"
Write-Host "Next steps:"
Write-Host "1. Review and update the .github/workflows/azure-deploy.yml file if needed"
Write-Host "2. Update the AZURE_WEBAPP_NAME in the workflow file to match your Azure Web App name"
Write-Host "3. Push changes to the $branch branch to trigger deployment"
