#!/bin/bash
set -e

# Terminal colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Deploying Web Content Extractor to Azure...${NC}"

# Check if Azure CLI is installed
if ! command -v az &> /dev/null
then
    echo -e "${RED}Azure CLI could not be found. Please install it first.${NC}"
    exit 1
fi

# Generate unique identifiers for resources
TIMESTAMP=$(date +%s)
UNIQUE_ID=${TIMESTAMP: -6}

# Set variables (can be overridden by environment variables)
RESOURCE_GROUP=${RESOURCE_GROUP:-"web-extractor-rg-${UNIQUE_ID}"}
LOCATION=${LOCATION:-"westus2"}
STORAGE_ACCOUNT=${STORAGE_ACCOUNT:-"webextractor${UNIQUE_ID}"}
FUNCTION_APP=${FUNCTION_APP:-"web-extractor-func-${UNIQUE_ID}"}

echo -e "${YELLOW}Resource Group: ${RESOURCE_GROUP}${NC}"
echo -e "${YELLOW}Storage Account: ${STORAGE_ACCOUNT}${NC}"
echo -e "${YELLOW}Function App: ${FUNCTION_APP}${NC}"

# Login to Azure (if not already logged in)
echo -e "${BLUE}Checking Azure login status...${NC}"
az account show > /dev/null || az login

# Create resource group
echo -e "${BLUE}Creating resource group ${RESOURCE_GROUP}...${NC}"
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" --output none

# Create storage account
echo -e "${BLUE}Creating storage account ${STORAGE_ACCOUNT}...${NC}"
az storage account create --name "$STORAGE_ACCOUNT" \
    --resource-group "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --sku Standard_LRS \
    --output none

# Get storage connection string
echo -e "${BLUE}Getting storage connection string...${NC}"
STORAGE_CONNECTION_STRING=$(az storage account show-connection-string \
    --name "$STORAGE_ACCOUNT" \
    --resource-group "$RESOURCE_GROUP" \
    --query connectionString -o tsv)

# Create blob container for extraction results
echo -e "${BLUE}Creating blob container for extraction results...${NC}"
az storage container create \
    --name "extraction-results" \
    --connection-string "$STORAGE_CONNECTION_STRING" \
    --output none

# Create function app
echo -e "${BLUE}Creating function app ${FUNCTION_APP}...${NC}"
az functionapp create --name "$FUNCTION_APP" \
    --resource-group "$RESOURCE_GROUP" \
    --consumption-plan-location "$LOCATION" \
    --runtime python \
    --runtime-version 3.10 \
    --functions-version 4 \
    --storage-account "$STORAGE_ACCOUNT" \
    --os-type linux \
    --output none

# Set function app settings
echo -e "${BLUE}Configuring function app settings...${NC}"
az functionapp config appsettings set --name "$FUNCTION_APP" \
    --resource-group "$RESOURCE_GROUP" \
    --settings \
    "AZURE_STORAGE_CONNECTION_STRING=${STORAGE_CONNECTION_STRING}" \
    "ENABLE_ORYX_BUILD=true" \
    "SCM_DO_BUILD_DURING_DEPLOYMENT=true" \
    --output none

# Deploy the function app
echo -e "${BLUE}Deploying function app...${NC}"
cd ../azure
func azure functionapp publish "$FUNCTION_APP" --python --no-build

# Display completion message
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo -e "${GREEN}Function app is available at: https://${FUNCTION_APP}.azurewebsites.net${NC}"
echo -e "${GREEN}Extract API endpoint: https://${FUNCTION_APP}.azurewebsites.net/api/extract${NC}"
echo -e "${GREEN}Health check endpoint: https://${FUNCTION_APP}.azurewebsites.net/api/health${NC}"
echo ""
echo -e "${YELLOW}Example curl command:${NC}"
echo -e "curl -X POST https://${FUNCTION_APP}.azurewebsites.net/api/extract \\"
echo -e "  -H \"Content-Type: application/json\" \\"
echo -e "  -d '{\"url\": \"https://example.com\", \"format\": \"json\", \"save_to_blob\": true}'"
