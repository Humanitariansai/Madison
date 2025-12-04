#!/bin/bash
# Monitor EC2 LinkedIn Scraper Service
# Usage: bash monitor_service.sh [option]

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SERVICE_NAME="linkedin-scraper"

show_help() {
    echo "Usage: $0 [option]"
    echo ""
    echo "Options:"
    echo "  status      Show service status"
    echo "  logs        Follow live logs"
    echo "  restart     Restart the service"
    echo "  stop        Stop the service"
    echo "  start       Start the service"
    echo "  health      Check health endpoint"
    echo "  disk        Check disk usage"
    echo "  memory      Check memory usage"
    echo ""
}

case "$1" in
    status)
        echo "Service Status:"
        sudo systemctl status $SERVICE_NAME
        echo ""
        echo "Last 20 log entries:"
        sudo journalctl -u $SERVICE_NAME -n 20
        ;;
    logs)
        echo "Following live logs (Ctrl+C to stop)..."
        sudo journalctl -u $SERVICE_NAME -f
        ;;
    restart)
        echo "Restarting service..."
        sudo systemctl restart $SERVICE_NAME
        sleep 2
        sudo systemctl status $SERVICE_NAME
        ;;
    stop)
        echo "Stopping service..."
        sudo systemctl stop $SERVICE_NAME
        echo "Service stopped"
        ;;
    start)
        echo "Starting service..."
        sudo systemctl start $SERVICE_NAME
        sleep 2
        sudo systemctl status $SERVICE_NAME
        ;;
    health)
        echo "Checking health endpoint..."
        curl -s http://localhost/health | python3 -m json.tool 2>/dev/null || echo "Service not responding"
        ;;
    disk)
        echo "Disk Usage:"
        df -h
        echo ""
        echo "App Directory Size:"
        du -sh ~/Madison/Social-Media-Scraping/social-media-scraping-v2
        ;;
    memory)
        echo "Memory Usage:"
        free -h
        echo ""
        echo "Chrome/Python Memory:"
        ps aux | grep -E "chromium|python" | grep -v grep
        ;;
    *)
        show_help
        ;;
esac
