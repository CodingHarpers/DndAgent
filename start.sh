#!/bin/bash

# A.R.C.A.N.A Start Script

echo "Checking for .env file..."
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    echo "GOOGLE_API_KEY=your_key_here" > .env
    echo "Please update .env with your Google API Key."
fi

echo "Building and starting services..."
docker-compose up --build -d

echo "Services started!"
echo "Backend API: http://localhost:8000/docs"
echo "Neo4j Browser: http://localhost:7474"
echo "Use 'docker-compose logs -f' to follow logs."
