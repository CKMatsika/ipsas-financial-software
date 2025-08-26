# Use official Node.js runtime as the base image
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm config set fetch-retries 5 && \
	npm config set fetch-retry-factor 2 && \
	npm config set fetch-retry-maxtimeout 600000 && \
	npm install --production --legacy-peer-deps

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Install a simple HTTP server to serve the static files
RUN npm install -g serve

# Expose the port
EXPOSE 3000

# Start the app
CMD ["serve", "-s", "build", "-l", "3000"]
