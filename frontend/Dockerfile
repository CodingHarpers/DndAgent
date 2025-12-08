FROM node:20-alpine

WORKDIR /app

# Install dependencies based on package.json
COPY package.json package-lock.json* ./
RUN npm ci

# Copy source code
COPY . .

# Build the Next.js app
RUN npm run build

# Start the app
CMD ["npm", "start"]

EXPOSE 3000
