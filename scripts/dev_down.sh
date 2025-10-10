#!/bin/bash

# dev_down.sh - Stop local development environment
# Usage: ./scripts/dev_down.sh

set -e

echo "🛑 Stopping AI-Powered Learning Recommendation System (Local Dev)"
echo "================================================================"

# Stop and remove containers
echo "🐳 Stopping Docker Compose services..."
docker-compose down

echo ""
echo "✅ All services stopped"
echo ""
echo "💾 Data volumes preserved. To remove all data:"
echo "   docker-compose down -v"
echo ""
echo "To start services again, run: ./scripts/dev_up.sh"
