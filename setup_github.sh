#!/bin/bash
# Script to help initialize and push the project to GitHub

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Setting up GitHub repository for Etherius AI Bot ===${NC}\n"

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo -e "${YELLOW}Git is not installed. Please install git first.${NC}"
    exit 1
fi

# Ask for GitHub username
echo -e "${BLUE}Enter your GitHub username:${NC}"
read github_username

# Ask for repository name
echo -e "${BLUE}Enter repository name (default: etherius-ai-bot):${NC}"
read repo_name
repo_name=${repo_name:-etherius-ai-bot}

# Ask for repository description
echo -e "${BLUE}Enter repository description (optional):${NC}"
read repo_description

echo -e "\n${BLUE}Initializing git repository...${NC}"
git init

echo -e "\n${BLUE}Adding files to git...${NC}"
git add .

echo -e "\n${BLUE}Committing files...${NC}"
git commit -m "Initial commit of Etherius AI Bot"

echo -e "\n${GREEN}Local repository initialized successfully!${NC}"
echo -e "${YELLOW}Now create a new repository on GitHub named '${repo_name}' with description: '${repo_description}'${NC}"
echo -e "${YELLOW}Then run the following commands:${NC}\n"
echo "git remote add origin https://github.com/${github_username}/${repo_name}.git"
echo "git branch -M main"
echo "git push -u origin main"

echo -e "\n${BLUE}=== Setup complete! ===${NC}"
echo -e "${BLUE}Remember to set your OPENAI_API_KEY as an environment variable or secret in your deployment environment.${NC}"