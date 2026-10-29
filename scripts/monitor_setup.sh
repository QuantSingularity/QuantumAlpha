#!/bin/bash
# QuantumAlpha Monitoring Setup Script
# This script sets up monitoring and logging for the QuantumAlpha platform

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
COMPONENTS="all"
NAMESPACE=""
KUBE_CONTEXT=""
LOCAL=false
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
    --local)
      LOCAL=true
      shift
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  -e, --env ENV          Environment (dev, staging, prod). Default: dev"
      echo "  -c, --components COMP  Components to set up (all, metrics, logging, dashboards)"
      echo "                         Comma-separated list for multiple components. Default: all"
      echo "  -n, --namespace NS     Kubernetes namespace. If not specified, uses environment-based namespace"
      echo "  -k, --kube-context CTX Kubernetes context. If not specified, uses environment-based context"
      echo "  --local                Set up monitoring locally using Docker Compose"
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

# Set namespace based on environment if not provided
if [[ -z "$NAMESPACE" ]]; then
  NAMESPACE="quantumalpha-$ENV"
fi

# Set Kubernetes context based on environment if not provided
if [[ -z "$KUBE_CONTEXT" && "$LOCAL" == false ]]; then
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
echo -e "${BLUE}  QuantumAlpha Monitoring Setup          ${NC}"
echo -e "${BLUE}  Environment: $ENV                      ${NC}"
if [[ "$LOCAL" == true ]]; then
  echo -e "${BLUE}  Mode: Local (Docker Compose)           ${NC}"
else
  echo -e "${BLUE}  Mode: Kubernetes                       ${NC}"
  echo -e "${BLUE}  Namespace: $NAMESPACE                  ${NC}"
fi
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

# Parse components
if [[ "$COMPONENTS" == "all" ]]; then
  COMPONENTS_ARRAY=("metrics" "logging" "dashboards")
else
  IFS=',' read -ra COMPONENTS_ARRAY <<< "$COMPONENTS"
fi

# Set up monitoring locally using Docker Compose
if [[ "$LOCAL" == true ]]; then
  echo -e "\n${YELLOW}Setting up monitoring locally using Docker Compose...${NC}"

  # Create monitoring directory if it doesn't exist
  mkdir -p "$PROJECT_ROOT/monitoring/data"
  mkdir -p "$PROJECT_ROOT/monitoring/config"

  # Process each component
  for COMPONENT in "${COMPONENTS_ARRAY[@]}"; do
    case $COMPONENT in
      metrics)
        echo -e "\n${BLUE}Setting up metrics monitoring (Prometheus, Grafana)...${NC}"

        # Create Prometheus config directory
        mkdir -p "$PROJECT_ROOT/monitoring/config/prometheus"

        # Create Prometheus config file
        cat > "$PROJECT_ROOT/monitoring/config/prometheus/prometheus.yml" << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'data-service'
    static_configs:
      - targets: ['data-service:8080']

  - job_name: 'ai-engine'
    static_configs:
      - targets: ['ai-engine:8080']

  - job_name: 'risk-service'
    static_configs:
      - targets: ['risk-service:8080']

  - job_name: 'execution-service'
    static_configs:
      - targets: ['execution-service:8080']
EOF

        # Create Grafana config directory
        mkdir -p "$PROJECT_ROOT/monitoring/config/grafana/provisioning/datasources"
        mkdir -p "$PROJECT_ROOT/monitoring/config/grafana/provisioning/dashboards"

        # Create Grafana datasource config
        cat > "$PROJECT_ROOT/monitoring/config/grafana/provisioning/datasources/datasource.yml" << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false

  - name: InfluxDB
    type: influxdb
    access: proxy
    url: http://influxdb:8086
    database: market_data
    user: admin
    secureJsonData:
      password: adminpassword
    editable: false
EOF

        # Create Docker Compose file for metrics monitoring
        cat > "$PROJECT_ROOT/monitoring/docker-compose-metrics.yml" << EOF
version: '3'
services:
  prometheus:
    image: prom/prometheus:v2.30.3
    volumes:
      - ./config/prometheus:/etc/prometheus
      - ./data/prometheus:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'
    ports:
      - "9090:9090"
    restart: always

  grafana:
    image: grafana/grafana:8.2.2
    volumes:
      - ./data/grafana:/var/lib/grafana
      - ./config/grafana/provisioning:/etc/grafana/provisioning
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    ports:
      - "3000:3000"
    depends_on:
      - prometheus
    restart: always
EOF

        # Start metrics monitoring
        execute_cmd "cd $PROJECT_ROOT/monitoring && docker-compose -f docker-compose-metrics.yml up -d"

        echo -e "${GREEN}✓ Metrics monitoring set up${NC}"
        echo -e "${BLUE}Prometheus: http://localhost:9090${NC}"
        echo -e "${BLUE}Grafana: http://localhost:3000 (admin/admin)${NC}"
        ;;

      logging)
        echo -e "\n${BLUE}Setting up logging (Elasticsearch, Fluentd, Kibana)...${NC}"

        # Create Fluentd config directory
        mkdir -p "$PROJECT_ROOT/monitoring/config/fluentd/conf"

        # Create Fluentd config file
        cat > "$PROJECT_ROOT/monitoring/config/fluentd/conf/fluent.conf" << EOF
<source>
  @type forward
  port 24224
  bind 0.0.0.0
</source>

<match *.**>
  @type copy
  <store>
    @type elasticsearch
    host elasticsearch
    port 9200
    logstash_format true
    logstash_prefix fluentd
    logstash_dateformat %Y%m%d
    include_tag_key true
    type_name access_log
    tag_key @log_name
    flush_interval 1s
  </store>
  <store>
    @type stdout
  </store>
</match>
EOF

        # Create Docker Compose file for logging
        cat > "$PROJECT_ROOT/monitoring/docker-compose-logging.yml" << EOF
version: '3'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.14.0
    environment:
      - discovery.type=single-node
      - bootstrap.memory_lock=true
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ulimits:
      memlock:
        soft: -1
        hard: -1
    volumes:
      - ./data/elasticsearch:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"
    restart: always

  fluentd:
    image: fluent/fluentd:v1.13-1
    volumes:
      - ./config/fluentd/conf:/fluentd/etc
    ports:
      - "24224:24224"
      - "24224:24224/udp"
    depends_on:
      - elasticsearch
    restart: always

  kibana:
    image: docker.elastic.co/kibana/kibana:7.14.0
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
    restart: always
EOF

        # Start logging
        execute_cmd "cd $PROJECT_ROOT/monitoring && docker-compose -f docker-compose-logging.yml up -d"

        echo -e "${GREEN}✓ Logging set up${NC}"
        echo -e "${BLUE}Elasticsearch: http://localhost:9200${NC}"
        echo -e "${BLUE}Kibana: http://localhost:5601${NC}"
        ;;

      dashboards)
        echo -e "\n${BLUE}Setting up dashboards...${NC}"

        # Create Grafana dashboards directory
        mkdir -p "$PROJECT_ROOT/monitoring/config/grafana/provisioning/dashboards"

        # Create dashboard provider config
        cat > "$PROJECT_ROOT/monitoring/config/grafana/provisioning/dashboards/dashboards.yml" << EOF
apiVersion: 1

providers:
  - name: 'QuantumAlpha'
    orgId: 1
    folder: 'QuantumAlpha'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
EOF

        # Create system dashboard
        cat > "$PROJECT_ROOT/monitoring/config/grafana/provisioning/dashboards/system_dashboard.json" << EOF
{
  "annotations": {
    "list": [
      {
        "builtIn": 1,
        "datasource": "-- Grafana --",
        "enable": true,
        "hide": true,
        "iconColor": "rgba(0, 211, 255, 1)",
        "name": "Annotations & Alerts",
        "type": "dashboard"
      }
    ]
  },
  "editable": true,
  "gnetId": null,
  "graphTooltip": 0,
  "id": 1,
  "links": [],
  "panels": [
    {
      "aliasColors": {},
      "bars": false,
      "dashLength": 10,
      "dashes": false,
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "custom": {}
        },
        "overrides": []
      },
      "fill": 1,
      "fillGradient": 0,
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 0,
        "y": 0
      },
      "hiddenSeries": false,
      "id": 2,
      "legend": {
        "avg": false,
        "current": false,
        "max": false,
        "min": false,
        "show": true,
        "total": false,
        "values": false
      },
      "lines": true,
      "linewidth": 1,
      "nullPointMode": "null",
      "options": {
        "alertThreshold": true
      },
      "percentage": false,
      "pluginVersion": "7.2.0",
      "pointradius": 2,
      "points": false,
      "renderer": "flot",
      "seriesOverrides": [],
      "spaceLength": 10,
      "stack": false,
      "steppedLine": false,
      "targets": [
        {
          "expr": "process_resident_memory_bytes",
          "interval": "",
          "legendFormat": "{{job}}",
          "refId": "A"
        }
      ],
      "thresholds": [],
      "timeFrom": null,
      "timeRegions": [],
      "timeShift": null,
      "title": "Memory Usage",
      "tooltip": {
        "shared": true,
        "sort": 0,
        "value_type": "individual"
      },
      "type": "graph",
      "xaxis": {
        "buckets": null,
        "mode": "time",
        "name": null,
        "show": true,
        "values": []
      },
      "yaxes": [
        {
          "format": "bytes",
          "label": null,
          "logBase": 1,
          "max": null,
          "min": null,
          "show": true
        },
        {
          "format": "short",
          "label": null,
          "logBase": 1,
          "max": null,
          "min": null,
          "show": true
        }
      ],
      "yaxis": {
        "align": false,
        "alignLevel": null
      }
    },
    {
      "aliasColors": {},
      "bars": false,
      "dashLength": 10,
      "dashes": false,
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "custom": {}
        },
        "overrides": []
      },
      "fill": 1,
      "fillGradient": 0,
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 12,
        "y": 0
      },
      "hiddenSeries": false,
      "id": 4,
      "legend": {
        "avg": false,
        "current": false,
        "max": false,
        "min": false,
        "show": true,
        "total": false,
        "values": false
      },
      "lines": true,
      "linewidth": 1,
      "nullPointMode": "null",
      "options": {
        "alertThreshold": true
      },
      "percentage": false,
      "pluginVersion": "7.2.0",
      "pointradius": 2,
      "points": false,
      "renderer": "flot",
      "seriesOverrides": [],
      "spaceLength": 10,
      "stack": false,
      "steppedLine": false,
      "targets": [
        {
          "expr": "rate(process_cpu_seconds_total[1m])",
          "interval": "",
          "legendFormat": "{{job}}",
          "refId": "A"
        }
      ],
      "thresholds": [],
      "timeFrom": null,
      "timeRegions": [],
      "timeShift": null,
      "title": "CPU Usage",
      "tooltip": {
        "shared": true,
        "sort": 0,
        "value_type": "individual"
      },
      "type": "graph",
      "xaxis": {
        "buckets": null,
        "mode": "time",
        "name": null,
        "show": true,
        "values": []
      },
      "yaxes": [
        {
          "format": "percentunit",
          "label": null,
          "logBase": 1,
          "max": null,
          "min": null,
          "show": true
        },
        {
          "format": "short",
          "label": null,
          "logBase": 1,
          "max": null,
          "min": null,
          "show": true
        }
      ],
      "yaxis": {
        "align": false,
        "alignLevel": null
      }
    }
  ],
  "refresh": "10s",
  "schemaVersion": 26,
  "style": "dark",
  "tags": [],
  "templating": {
    "list": []
  },
  "time": {
    "from": "now-1h",
    "to": "now"
  },
  "timepicker": {},
  "timezone": "",
  "title": "System Dashboard",
  "uid": "system",
  "version": 1
}
EOF

        # Restart Grafana to load dashboards
        execute_cmd "cd $PROJECT_ROOT/monitoring && docker-compose -f docker-compose-metrics.yml restart grafana"

        echo -e "${GREEN}✓ Dashboards set up${NC}"
        echo -e "${BLUE}System Dashboard: http://localhost:3000/d/system/system-dashboard${NC}"
        ;;

      *)
        echo -e "${RED}Error: Unknown component: $COMPONENT${NC}"
        echo "Available components: metrics, logging, dashboards"
        ;;
    esac
  done

  echo -e "\n${GREEN}✓ Local monitoring setup complete${NC}"
else
  # Set up monitoring in Kubernetes
  echo -e "\n${YELLOW}Setting up monitoring in Kubernetes...${NC}"

  # Check if kubectl is installed
  if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl not found${NC}"
    exit 1
  fi

  # Set Kubernetes context
  CONTEXT_CMD="kubectl config use-context $KUBE_CONTEXT"
  execute_cmd "$CONTEXT_CMD"

  # Create namespace if it doesn't exist
  NAMESPACE_CMD="kubectl get namespace $NAMESPACE 2>/dev/null || kubectl create namespace $NAMESPACE"
  execute_cmd "$NAMESPACE_CMD"

  # Process each component
  for COMPONENT in "${COMPONENTS_ARRAY[@]}"; do
    case $COMPONENT in
      metrics)
        echo -e "\n${BLUE}Setting up metrics monitoring (Prometheus, Grafana)...${NC}"

        # Apply Prometheus configuration
        PROMETHEUS_CONFIG_CMD="kubectl apply -f $PROJECT_ROOT/infrastructure/monitoring/prometheus-config.yaml -n $NAMESPACE"
        execute_cmd "$PROMETHEUS_CONFIG_CMD"

        # Apply Prometheus deployment
        PROMETHEUS_CMD="kubectl apply -f $PROJECT_ROOT/infrastructure/monitoring/prometheus.yaml -n $NAMESPACE"
        execute_cmd "$PROMETHEUS_CMD"

        # Apply Grafana datasources
        GRAFANA_DS_CMD="kubectl apply -f $PROJECT_ROOT/infrastructure/monitoring/grafana-datasources.yaml -n $NAMESPACE"
        execute_cmd "$GRAFANA_DS_CMD"

        # Apply Grafana deployment
        GRAFANA_CMD="kubectl apply -f $PROJECT_ROOT/infrastructure/monitoring/grafana.yaml -n $NAMESPACE"
        execute_cmd "$GRAFANA_CMD"

        # Wait for deployments to be ready
        WAIT_PROM_CMD="kubectl rollout status deployment/prometheus -n $NAMESPACE --timeout=300s"
        execute_cmd "$WAIT_PROM_CMD"

        WAIT_GRAF_CMD="kubectl rollout status deployment/grafana -n $NAMESPACE --timeout=300s"
        execute_cmd "$WAIT_GRAF_CMD"

        echo -e "${GREEN}✓ Metrics monitoring set up${NC}"
        ;;

      logging)
        echo -e "\n${BLUE}Setting up logging (Elasticsearch, Fluentd, Kibana)...${NC}"

        # Apply Elasticsearch deployment
        ES_CMD="kubectl apply -f $PROJECT_ROOT/infrastructure/monitoring/elasticsearch.yaml -n $NAMESPACE"
        execute_cmd "$ES_CMD"

        # Apply Fluentd deployment
        FLUENTD_CMD="kubectl apply -f $PROJECT_ROOT/infrastructure/monitoring/fluentd.yaml -n $NAMESPACE"
        execute_cmd "$FLUENTD_CMD"

        # Apply Kibana deployment
        KIBANA_CMD="kubectl apply -f $PROJECT_ROOT/infrastructure/monitoring/kibana.yaml -n $NAMESPACE"
        execute_cmd "$KIBANA_CMD"

        # Wait for deployments to be ready
        WAIT_ES_CMD="kubectl rollout status statefulset/elasticsearch -n $NAMESPACE --timeout=300s"
        execute_cmd "$WAIT_ES_CMD"

        WAIT_KIBANA_CMD="kubectl rollout status deployment/kibana -n $NAMESPACE --timeout=300s"
        execute_cmd "$WAIT_KIBANA_CMD"

        echo -e "${GREEN}✓ Logging set up${NC}"
        ;;

      dashboards)
        echo -e "\n${BLUE}Setting up dashboards...${NC}"

        # Create ConfigMap for dashboards
        mkdir -p "$PROJECT_ROOT/monitoring/dashboards"

        # Create system dashboard
        cat > "$PROJECT_ROOT/monitoring/dashboards/system_dashboard.json" << EOF
{
  "annotations": {
    "list": [
      {
        "builtIn": 1,
        "datasource": "-- Grafana --",
        "enable": true,
        "hide": true,
        "iconColor": "rgba(0, 211, 255, 1)",
        "name": "Annotations & Alerts",
        "type": "dashboard"
      }
    ]
  },
  "editable": true,
  "gnetId": null,
  "graphTooltip": 0,
  "id": 1,
  "links": [],
  "panels": [
    {
      "aliasColors": {},
      "bars": false,
      "dashLength": 10,
      "dashes": false,
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "custom": {}
        },
        "overrides": []
      },
      "fill": 1,
      "fillGradient": 0,
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 0,
        "y": 0
      },
      "hiddenSeries": false,
      "id": 2,
      "legend": {
        "avg": false,
        "current": false,
        "max": false,
        "min": false,
        "show": true,
        "total": false,
        "values": false
      },
      "lines": true,
      "linewidth": 1,
      "nullPointMode": "null",
      "options": {
        "alertThreshold": true
      },
      "percentage": false,
      "pluginVersion": "7.2.0",
      "pointradius": 2,
      "points": false,
      "renderer": "flot",
      "seriesOverrides": [],
      "spaceLength": 10,
      "stack": false,
      "steppedLine": false,
      "targets": [
        {
          "expr": "process_resident_memory_bytes",
          "interval": "",
          "legendFormat": "{{job}}",
          "refId": "A"
        }
      ],
      "thresholds": [],
      "timeFrom": null,
      "timeRegions": [],
      "timeShift": null,
      "title": "Memory Usage",
      "tooltip": {
        "shared": true,
        "sort": 0,
        "value_type": "individual"
      },
      "type": "graph",
      "xaxis": {
        "buckets": null,
        "mode": "time",
        "name": null,
        "show": true,
        "values": []
      },
      "yaxes": [
        {
          "format": "bytes",
          "label": null,
          "logBase": 1,
          "max": null,
          "min": null,
          "show": true
        },
        {
          "format": "short",
          "label": null,
          "logBase": 1,
          "max": null,
          "min": null,
          "show": true
        }
      ],
      "yaxis": {
        "align": false,
        "alignLevel": null
      }
    },
    {
      "aliasColors": {},
      "bars": false,
      "dashLength": 10,
      "dashes": false,
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "custom": {}
        },
        "overrides": []
      },
      "fill": 1,
      "fillGradient": 0,
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 12,
        "y": 0
      },
      "hiddenSeries": false,
      "id": 4,
      "legend": {
        "avg": false,
        "current": false,
        "max": false,
        "min": false,
        "show": true,
        "total": false,
        "values": false
      },
      "lines": true,
      "linewidth": 1,
      "nullPointMode": "null",
      "options": {
        "alertThreshold": true
      },
      "percentage": false,
      "pluginVersion": "7.2.0",
      "pointradius": 2,
      "points": false,
      "renderer": "flot",
      "seriesOverrides": [],
      "spaceLength": 10,
      "stack": false,
      "steppedLine": false,
      "targets": [
        {
          "expr": "rate(process_cpu_seconds_total[1m])",
          "interval": "",
          "legendFormat": "{{job}}",
          "refId": "A"
        }
      ],
      "thresholds": [],
      "timeFrom": null,
      "timeRegions": [],
      "timeShift": null,
      "title": "CPU Usage",
      "tooltip": {
        "shared": true,
        "sort": 0,
        "value_type": "individual"
      },
      "type": "graph",
      "xaxis": {
        "buckets": null,
        "mode": "time",
        "name": null,
        "show": true,
        "values": []
      },
      "yaxes": [
        {
          "format": "percentunit",
          "label": null,
          "logBase": 1,
          "max": null,
          "min": null,
          "show": true
        },
        {
          "format": "short",
          "label": null,
          "logBase": 1,
          "max": null,
          "min": null,
          "show": true
        }
      ],
      "yaxis": {
        "align": false,
        "alignLevel": null
      }
    }
  ],
  "refresh": "10s",
  "schemaVersion": 26,
  "style": "dark",
  "tags": [],
  "templating": {
    "list": []
  },
  "time": {
    "from": "now-1h",
    "to": "now"
  },
  "timepicker": {},
  "timezone": "",
  "title": "System Dashboard",
  "uid": "system",
  "version": 1
}
EOF

        # Create ConfigMap for dashboards
        DASHBOARD_CM_CMD="kubectl create configmap grafana-dashboards --from-file=$PROJECT_ROOT/monitoring/dashboards/ -n $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -"
        execute_cmd "$DASHBOARD_CM_CMD"

        # Restart Grafana to load dashboards
        RESTART_CMD="kubectl rollout restart deployment/grafana -n $NAMESPACE"
        execute_cmd "$RESTART_CMD"

        # Wait for Grafana to be ready
        WAIT_CMD="kubectl rollout status deployment/grafana -n $NAMESPACE --timeout=300s"
        execute_cmd "$WAIT_CMD"

        echo -e "${GREEN}✓ Dashboards set up${NC}"
        ;;

      *)
        echo -e "${RED}Error: Unknown component: $COMPONENT${NC}"
        echo "Available components: metrics, logging, dashboards"
        ;;
    esac
  done

  # Show service URLs
  echo -e "\n${YELLOW}Monitoring URLs:${NC}"

  # Get Prometheus URL
  if [[ "$ENV" == "dev" ]]; then
    # For local development, use NodePort
    PORT_CMD="kubectl get service prometheus -n $NAMESPACE -o jsonpath='{.spec.ports[0].nodePort}'"
    PORT=$(eval $PORT_CMD 2>/dev/null || echo "")

    if [[ ! -z "$PORT" ]]; then
      if [[ "$KUBE_CONTEXT" == "minikube" ]]; then
        IP_CMD="minikube ip"
        IP=$(eval $IP_CMD 2>/dev/null || echo "localhost")
        echo -e "${BLUE}Prometheus: http://$IP:$PORT${NC}"
      else
        echo -e "${BLUE}Prometheus: http://localhost:$PORT${NC}"
      fi
    else
      echo -e "${YELLOW}Prometheus URL not available yet${NC}"
    fi

    # Get Grafana URL
    PORT_CMD="kubectl get service grafana -n $NAMESPACE -o jsonpath='{.spec.ports[0].nodePort}'"
    PORT=$(eval $PORT_CMD 2>/dev/null || echo "")

    if [[ ! -z "$PORT" ]]; then
      if [[ "$KUBE_CONTEXT" == "minikube" ]]; then
        IP_CMD="minikube ip"
        IP=$(eval $IP_CMD 2>/dev/null || echo "localhost")
        echo -e "${BLUE}Grafana: http://$IP:$PORT (admin/admin)${NC}"
      else
        echo -e "${BLUE}Grafana: http://localhost:$PORT (admin/admin)${NC}"
      fi
    else
      echo -e "${YELLOW}Grafana URL not available yet${NC}"
    fi

    # Get Kibana URL
    PORT_CMD="kubectl get service kibana -n $NAMESPACE -o jsonpath='{.spec.ports[0].nodePort}'"
    PORT=$(eval $PORT_CMD 2>/dev/null || echo "")

    if [[ ! -z "$PORT" ]]; then
      if [[ "$KUBE_CONTEXT" == "minikube" ]]; then
        IP_CMD="minikube ip"
        IP=$(eval $IP_CMD 2>/dev/null || echo "localhost")
        echo -e "${BLUE}Kibana: http://$IP:$PORT${NC}"
      else
        echo -e "${BLUE}Kibana: http://localhost:$PORT${NC}"
      fi
    else
      echo -e "${YELLOW}Kibana URL not available yet${NC}"
    fi
  else
    # For staging/prod, use Ingress
    PROM_URL_CMD="kubectl get ingress -n $NAMESPACE -o jsonpath='{.items[?(@.metadata.name==\"prometheus\")].status.loadBalancer.ingress[0].ip}'"
    PROM_URL=$(eval $PROM_URL_CMD 2>/dev/null || echo "")

    if [[ ! -z "$PROM_URL" ]]; then
      echo -e "${BLUE}Prometheus: http://$PROM_URL${NC}"
    else
      echo -e "${YELLOW}Prometheus URL not available yet${NC}"
    fi

    GRAFANA_URL_CMD="kubectl get ingress -n $NAMESPACE -o jsonpath='{.items[?(@.metadata.name==\"grafana\")].status.loadBalancer.ingress[0].ip}'"
    GRAFANA_URL=$(eval $GRAFANA_URL_CMD 2>/dev/null || echo "")

    if [[ ! -z "$GRAFANA_URL" ]]; then
      echo -e "${BLUE}Grafana: http://$GRAFANA_URL (admin/admin)${NC}"
    else
      echo -e "${YELLOW}Grafana URL not available yet${NC}"
    fi

    KIBANA_URL_CMD="kubectl get ingress -n $NAMESPACE -o jsonpath='{.items[?(@.metadata.name==\"kibana\")].status.loadBalancer.ingress[0].ip}'"
    KIBANA_URL=$(eval $KIBANA_URL_CMD 2>/dev/null || echo "")

    if [[ ! -z "$KIBANA_URL" ]]; then
      echo -e "${BLUE}Kibana: http://$KIBANA_URL${NC}"
    else
      echo -e "${YELLOW}Kibana URL not available yet${NC}"
    fi
  fi

  echo -e "\n${GREEN}✓ Kubernetes monitoring setup complete${NC}"
fi

echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}  QuantumAlpha Monitoring Setup Complete ${NC}"
echo -e "${GREEN}=========================================${NC}"
