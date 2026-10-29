#!/bin/bash
# QuantumAlpha Kubernetes Deployment Script
# This script handles Kubernetes-specific deployment tasks for the QuantumAlpha platform

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
ACTION="apply"
COMPONENTS="all"
NAMESPACE=""
KUBE_CONTEXT=""
DRY_RUN=false
WAIT=true

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    -e|--env)
      ENV="$2"
      shift
      shift
      ;;
    -a|--action)
      ACTION="$2"
      shift
      shift
      ;;
    -c|--components)
      COMPONENTS="$2"
      shift
      shift
      ;;
    -n|--namespace)
      NAMESPACE="$2"
      shift
      shift
      ;;
    -k|--kube-context)
      KUBE_CONTEXT="$2"
      shift
      shift
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --no-wait)
      WAIT=false
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  -e, --env ENV          Environment (dev, staging, prod). Default: dev"
      echo "  -a, --action ACTION    Action to perform (apply, delete). Default: apply"
      echo "  -c, --components COMP  Components to deploy (all, infrastructure, services, monitoring)"
      echo "                         Comma-separated list for multiple components. Default: all"
      echo "  -n, --namespace NS     Kubernetes namespace. If not specified, uses environment-based namespace"
      echo "  -k, --kube-context CTX Kubernetes context. If not specified, uses environment-based context"
      echo "  --dry-run              Print commands without executing them"
      echo "  --no-wait              Don't wait for resources to be ready"
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

# Validate action
if [[ "$ACTION" != "apply" && "$ACTION" != "delete" ]]; then
  echo -e "${RED}Error: Invalid action '$ACTION'. Must be one of: apply, delete${NC}"
  exit 1
fi

# Set namespace based on environment if not provided
if [[ -z "$NAMESPACE" ]]; then
  NAMESPACE="quantumalpha-$ENV"
fi

# Set Kubernetes context based on environment if not provided
if [[ -z "$KUBE_CONTEXT" ]]; then
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
fi

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}  QuantumAlpha Kubernetes Deployment     ${NC}"
echo -e "${BLUE}  Environment: $ENV                      ${NC}"
echo -e "${BLUE}  Namespace: $NAMESPACE                  ${NC}"
echo -e "${BLUE}  Action: $ACTION                        ${NC}"
echo -e "${BLUE}=========================================${NC}"

# Function to execute or print command
execute_cmd() {
  if $DRY_RUN; then
    echo -e "${YELLOW}[DRY RUN] ${BLUE}$1${NC}"
  else
    echo -e "${BLUE}Executing: $1${NC}"
    eval $1
  fi
}

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

# Set Kubernetes context
CONTEXT_CMD="kubectl config use-context $KUBE_CONTEXT"
execute_cmd "$CONTEXT_CMD"

# Parse components
if [[ "$COMPONENTS" == "all" ]]; then
  COMPONENTS_ARRAY=("infrastructure" "services" "monitoring")
else
  IFS=',' read -ra COMPONENTS_ARRAY <<< "$COMPONENTS"
fi

# Create namespace if it doesn't exist (for apply action)
if [[ "$ACTION" == "apply" ]]; then
  echo -e "\n${YELLOW}Ensuring namespace exists: $NAMESPACE${NC}"

  NAMESPACE_CMD="kubectl get namespace $NAMESPACE 2>/dev/null || kubectl create namespace $NAMESPACE"
  execute_cmd "$NAMESPACE_CMD"

  echo -e "${GREEN}✓ Namespace ready: $NAMESPACE${NC}"
fi

# Process each component
for COMPONENT in "${COMPONENTS_ARRAY[@]}"; do
  echo -e "\n${YELLOW}Processing component: $COMPONENT${NC}"

  case $COMPONENT in
    infrastructure)
      echo -e "\n${BLUE}Deploying infrastructure components...${NC}"

      # Define infrastructure components
      INFRA_COMPONENTS=("postgres" "influxdb" "redis" "kafka" "zookeeper")

      for INFRA in "${INFRA_COMPONENTS[@]}"; do
        echo -e "\n${BLUE}Processing $INFRA...${NC}"

        YAML_FILE="$PROJECT_ROOT/infrastructure/kubernetes/base/$INFRA.yaml"

        if [[ ! -f "$YAML_FILE" ]]; then
          echo -e "${YELLOW}Warning: YAML file not found: $YAML_FILE${NC}"
          continue
        fi

        # Apply or delete the resource
        KUBE_CMD="kubectl $ACTION -f $YAML_FILE -n $NAMESPACE"
        execute_cmd "$KUBE_CMD"

        # Wait for resource to be ready if applying
        if [[ "$ACTION" == "apply" && "$WAIT" == true ]]; then
          if [[ "$INFRA" == "postgres" || "$INFRA" == "influxdb" || "$INFRA" == "redis" ]]; then
            WAIT_CMD="kubectl rollout status statefulset/$INFRA -n $NAMESPACE --timeout=300s"
            execute_cmd "$WAIT_CMD"
          elif [[ "$INFRA" == "kafka" || "$INFRA" == "zookeeper" ]]; then
            WAIT_CMD="kubectl rollout status statefulset/$INFRA -n $NAMESPACE --timeout=300s"
            execute_cmd "$WAIT_CMD"
          fi
        fi

        echo -e "${GREEN}✓ Processed $INFRA${NC}"
      done
      ;;

    services)
      echo -e "\n${BLUE}Deploying service components...${NC}"

      # Define service components
      SERVICE_COMPONENTS=("data-service" "ai-engine" "risk-service" "execution-service" "web-frontend")

      for SERVICE in "${SERVICE_COMPONENTS[@]}"; do
        echo -e "\n${BLUE}Processing $SERVICE...${NC}"

        YAML_FILE="$PROJECT_ROOT/infrastructure/kubernetes/base/$SERVICE.yaml"

        if [[ ! -f "$YAML_FILE" ]]; then
          echo -e "${YELLOW}Warning: YAML file not found: $YAML_FILE${NC}"
          continue
        fi

        # Apply or delete the resource
        KUBE_CMD="kubectl $ACTION -f $YAML_FILE -n $NAMESPACE"
        execute_cmd "$KUBE_CMD"

        # Wait for resource to be ready if applying
        if [[ "$ACTION" == "apply" && "$WAIT" == true ]]; then
          WAIT_CMD="kubectl rollout status deployment/$SERVICE -n $NAMESPACE --timeout=300s"
          execute_cmd "$WAIT_CMD"
        fi

        echo -e "${GREEN}✓ Processed $SERVICE${NC}"
      done
      ;;

    monitoring)
      echo -e "\n${BLUE}Deploying monitoring components...${NC}"

      # Define monitoring components
      MONITORING_COMPONENTS=("prometheus" "grafana" "elasticsearch" "fluentd" "kibana")

      for MONITOR in "${MONITORING_COMPONENTS[@]}"; do
        echo -e "\n${BLUE}Processing $MONITOR...${NC}"

        YAML_FILE="$PROJECT_ROOT/infrastructure/monitoring/$MONITOR.yaml"

        if [[ ! -f "$YAML_FILE" ]]; then
          echo -e "${YELLOW}Warning: YAML file not found: $YAML_FILE${NC}"
          continue
        fi

        # Apply or delete the resource
        KUBE_CMD="kubectl $ACTION -f $YAML_FILE -n $NAMESPACE"
        execute_cmd "$KUBE_CMD"

        # Wait for resource to be ready if applying
        if [[ "$ACTION" == "apply" && "$WAIT" == true ]]; then
          if [[ "$MONITOR" == "prometheus" || "$MONITOR" == "grafana" || "$MONITOR" == "kibana" ]]; then
            WAIT_CMD="kubectl rollout status deployment/$MONITOR -n $NAMESPACE --timeout=300s"
            execute_cmd "$WAIT_CMD"
          elif [[ "$MONITOR" == "elasticsearch" ]]; then
            WAIT_CMD="kubectl rollout status statefulset/elasticsearch -n $NAMESPACE --timeout=300s"
            execute_cmd "$WAIT_CMD"
          elif [[ "$MONITOR" == "fluentd" ]]; then
            WAIT_CMD="kubectl rollout status daemonset/fluentd -n $NAMESPACE --timeout=300s"
            execute_cmd "$WAIT_CMD"
          fi
        fi

        echo -e "${GREEN}✓ Processed $MONITOR${NC}"
      done
      ;;

    *)
      echo -e "${RED}Error: Unknown component: $COMPONENT${NC}"
      echo "Available components: infrastructure, services, monitoring"
      ;;
  esac
done

# Apply environment-specific overlays if action is apply
if [[ "$ACTION" == "apply" ]]; then
  echo -e "\n${YELLOW}Applying environment-specific overlays...${NC}"

  KUSTOMIZE_DIR="$PROJECT_ROOT/infrastructure/kubernetes/overlays/$ENV"

  if [[ ! -d "$KUSTOMIZE_DIR" ]]; then
    echo -e "${RED}Error: Kustomize directory not found: $KUSTOMIZE_DIR${NC}"
  else
    cd "$KUSTOMIZE_DIR"

    # Apply kustomization
    APPLY_CMD="kustomize build . | kubectl apply -f - -n $NAMESPACE"
    execute_cmd "$APPLY_CMD"

    echo -e "${GREEN}✓ Applied environment-specific overlays${NC}"
  fi
fi

# Show service URLs if action is apply
if [[ "$ACTION" == "apply" ]]; then
  echo -e "\n${YELLOW}Service URLs:${NC}"

  # Wait a moment for services to be ready
  sleep 5

  # Get web frontend URL
  if [[ "$ENV" == "dev" ]]; then
    # For local development, use NodePort
    PORT_CMD="kubectl get service web-frontend -n $NAMESPACE -o jsonpath='{.spec.ports[0].nodePort}'"
    PORT=$(eval $PORT_CMD 2>/dev/null || echo "")

    if [[ ! -z "$PORT" ]]; then
      if [[ "$KUBE_CONTEXT" == "minikube" ]]; then
        IP_CMD="minikube ip"
        IP=$(eval $IP_CMD 2>/dev/null || echo "localhost")
        echo -e "${BLUE}Web Frontend: http://$IP:$PORT${NC}"
      else
        echo -e "${BLUE}Web Frontend: http://localhost:$PORT${NC}"
      fi
    else
      echo -e "${YELLOW}Web Frontend URL not available yet${NC}"
    fi
  else
    # For staging/prod, use Ingress
    URL_CMD="kubectl get ingress -n $NAMESPACE -o jsonpath='{.items[?(@.metadata.name==\"web-frontend\")].status.loadBalancer.ingress[0].ip}'"
    URL=$(eval $URL_CMD 2>/dev/null || echo "")

    if [[ ! -z "$URL" ]]; then
      echo -e "${BLUE}Web Frontend: http://$URL${NC}"
    else
      echo -e "${YELLOW}Web Frontend URL not available yet${NC}"
    fi
  fi

  # Show backend service URLs
  SERVICES=("data-service" "ai-engine" "risk-service" "execution-service")

  for SERVICE in "${SERVICES[@]}"; do
    PORT_CMD="kubectl get service $SERVICE -n $NAMESPACE -o jsonpath='{.spec.ports[0].port}'"
    PORT=$(eval $PORT_CMD 2>/dev/null || echo "")

    if [[ ! -z "$PORT" ]]; then
      echo -e "${BLUE}$SERVICE: http://$SERVICE.$NAMESPACE.svc.cluster.local:$PORT${NC}"
    fi
  done
fi

echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}  QuantumAlpha Kubernetes Deployment     ${NC}"
echo -e "${GREEN}  Completed                              ${NC}"
echo -e "${GREEN}=========================================${NC}"
