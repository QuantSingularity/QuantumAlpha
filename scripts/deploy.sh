#!/bin/bash
# QuantumAlpha Deployment Script
# This script handles building, tagging, and deploying Docker images for the QuantumAlpha platform

set -e

# Color codes for output formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Default options
ENV="dev"
SERVICES="all"
BUILD=true
PUSH=true
DEPLOY=true
TAG="latest"
REGISTRY=""
NAMESPACE="quantumalpha"
DRY_RUN=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    -e|--env)
      ENV="$2"
      shift
      shift
      ;;
    -s|--services)
      SERVICES="$2"
      shift
      shift
      ;;
    --no-build)
      BUILD=false
      shift
      ;;
    --no-push)
      PUSH=false
      shift
      ;;
    --no-deploy)
      DEPLOY=false
      shift
      ;;
    -t|--tag)
      TAG="$2"
      shift
      shift
      ;;
    -r|--registry)
      REGISTRY="$2"
      shift
      shift
      ;;
    -n|--namespace)
      NAMESPACE="$2"
      shift
      shift
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  -e, --env ENV          Environment to deploy to (dev, staging, prod). Default: dev"
      echo "  -s, --services SERVICES Services to deploy (all, data-service, ai-engine, risk-service, execution-service, web-frontend)"
      echo "                         Comma-separated list for multiple services. Default: all"
      echo "  --no-build             Skip building Docker images"
      echo "  --no-push              Skip pushing Docker images to registry"
      echo "  --no-deploy            Skip deploying to Kubernetes"
      echo "  -t, --tag TAG          Image tag. Default: latest"
      echo "  -r, --registry REGISTRY Docker registry URL"
      echo "  -n, --namespace NS     Kubernetes namespace. Default: quantumalpha"
      echo "  --dry-run              Print commands without executing them"
      echo "  -h, --help             Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use -h or --help for usage information"
      exit 1
      ;;
  esac
done

# Validate environment
if [[ "$ENV" != "dev" && "$ENV" != "staging" && "$ENV" != "prod" ]]; then
  echo -e "${RED}Error: Invalid environment '$ENV'. Must be one of: dev, staging, prod${NC}"
  exit 1
fi

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}  QuantumAlpha Deployment ($ENV)         ${NC}"
echo -e "${BLUE}=========================================${NC}"

# Set registry based on environment if not provided
if [[ -z "$REGISTRY" ]]; then
  if [[ "$ENV" == "dev" ]]; then
    REGISTRY="localhost:5000"
  else
    echo -e "${RED}Error: Docker registry not specified${NC}"
    echo "Use -r or --registry to specify a Docker registry"
    exit 1
  fi
fi

# Set namespace based on environment if default
if [[ "$NAMESPACE" == "quantumalpha" ]]; then
  NAMESPACE="quantumalpha-$ENV"
fi

# Parse services
if [[ "$SERVICES" == "all" ]]; then
  SERVICES_ARRAY=("data-service" "ai-engine" "risk-service" "execution-service" "web-frontend")
else
  IFS=',' read -ra SERVICES_ARRAY <<< "$SERVICES"
fi

# Function to execute or print command
execute_cmd() {
  if $DRY_RUN; then
    echo -e "${YELLOW}[DRY RUN] ${BLUE}$1${NC}"
  else
    echo -e "${BLUE}Executing: $1${NC}"
    eval $1
  fi
}

# Build Docker images
if $BUILD; then
  echo -e "\n${YELLOW}Building Docker images...${NC}"

  for SERVICE in "${SERVICES_ARRAY[@]}"; do
    echo -e "\n${BLUE}Building $SERVICE...${NC}"

    case $SERVICE in
      web-frontend)
        BUILD_DIR="$PROJECT_ROOT/web-frontend"
        ;;
      *)
        BUILD_DIR="$PROJECT_ROOT/backend/$SERVICE"
        ;;
    esac

    if [[ ! -d "$BUILD_DIR" ]]; then
      echo -e "${RED}Error: Service directory not found: $BUILD_DIR${NC}"
      continue
    fi

    # Build Docker image
    BUILD_CMD="docker build -t $REGISTRY/$NAMESPACE/$SERVICE:$TAG $BUILD_DIR"
    execute_cmd "$BUILD_CMD"

    if [[ "$TAG" != "latest" ]]; then
      # Also tag as latest
      TAG_CMD="docker tag $REGISTRY/$NAMESPACE/$SERVICE:$TAG $REGISTRY/$NAMESPACE/$SERVICE:latest"
      execute_cmd "$TAG_CMD"
    fi

    echo -e "${GREEN}✓ Built $SERVICE${NC}"
  done
fi

# Push Docker images to registry
if $PUSH; then
  echo -e "\n${YELLOW}Pushing Docker images to registry...${NC}"

  for SERVICE in "${SERVICES_ARRAY[@]}"; do
    echo -e "\n${BLUE}Pushing $SERVICE...${NC}"

    # Push Docker image
    PUSH_CMD="docker push $REGISTRY/$NAMESPACE/$SERVICE:$TAG"
    execute_cmd "$PUSH_CMD"

    if [[ "$TAG" != "latest" ]]; then
      # Also push latest tag
      PUSH_LATEST_CMD="docker push $REGISTRY/$NAMESPACE/$SERVICE:latest"
      execute_cmd "$PUSH_LATEST_CMD"
    fi

    echo -e "${GREEN}✓ Pushed $SERVICE${NC}"
  done
fi

# Deploy to Kubernetes
if $DEPLOY; then
  echo -e "\n${YELLOW}Deploying to Kubernetes...${NC}"

  # Check if kubectl is installed
  if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl not found${NC}"
    exit 1
  fi

  # Check if kustomize is installed
  if ! command -v kustomize &> /dev/null; then
    echo -e "${RED}Error: kustomize not found${NC}"
    exit 1
  fi

  # Set Kubernetes context based on environment
  case $ENV in
    dev)
      KUBE_CONTEXT="minikube"
      ;;
    staging)
      KUBE_CONTEXT="quantumalpha-staging"
      ;;
    prod)
      KUBE_CONTEXT="quantumalpha-prod"
      ;;
  esac

  # Set Kubernetes context
  CONTEXT_CMD="kubectl config use-context $KUBE_CONTEXT"
  execute_cmd "$CONTEXT_CMD"

  # Deploy using kustomize
  KUSTOMIZE_DIR="$PROJECT_ROOT/infrastructure/kubernetes/overlays/$ENV"

  if [[ ! -d "$KUSTOMIZE_DIR" ]]; then
    echo -e "${RED}Error: Kustomize directory not found: $KUSTOMIZE_DIR${NC}"
    exit 1
  fi

  cd "$KUSTOMIZE_DIR"

  # Update image tags in kustomization
  for SERVICE in "${SERVICES_ARRAY[@]}"; do
    IMAGE_CMD="kustomize edit set image $REGISTRY/$NAMESPACE/$SERVICE:$TAG"
    execute_cmd "$IMAGE_CMD"
  done

  # Apply kustomization
  APPLY_CMD="kustomize build . | kubectl apply -f -"
  execute_cmd "$APPLY_CMD"

  echo -e "${GREEN}✓ Deployed to Kubernetes${NC}"

  # Wait for deployments to be ready
  echo -e "\n${YELLOW}Waiting for deployments to be ready...${NC}"

  for SERVICE in "${SERVICES_ARRAY[@]}"; do
    WAIT_CMD="kubectl rollout status deployment/$SERVICE -n $NAMESPACE --timeout=300s"
    execute_cmd "$WAIT_CMD"
  done

  echo -e "${GREEN}✓ All deployments are ready${NC}"

  # Show service URLs
  echo -e "\n${YELLOW}Service URLs:${NC}"

  for SERVICE in "${SERVICES_ARRAY[@]}"; do
    if [[ "$SERVICE" == "web-frontend" ]]; then
      URL_CMD="kubectl get ingress -n $NAMESPACE -o jsonpath='{.items[?(@.metadata.name==\"web-frontend\")].status.loadBalancer.ingress[0].ip}'"
      URL=$(eval $URL_CMD)

      if [[ ! -z "$URL" ]]; then
        echo -e "${BLUE}Web Frontend: http://$URL${NC}"
      else
        echo -e "${YELLOW}Web Frontend URL not available yet${NC}"
      fi
    else
      PORT_CMD="kubectl get service $SERVICE -n $NAMESPACE -o jsonpath='{.spec.ports[0].port}'"
      PORT=$(eval $PORT_CMD)

      if [[ ! -z "$PORT" ]]; then
        echo -e "${BLUE}$SERVICE: http://$SERVICE.$NAMESPACE.svc.cluster.local:$PORT${NC}"
      fi
    fi
  done
fi

echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}  QuantumAlpha Deployment Completed      ${NC}"
echo -e "${GREEN}=========================================${NC}"
