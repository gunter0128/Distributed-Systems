# Use Node.js LTS
FROM node:20-slim

# Set working directory
WORKDIR /app

# Copy package files
COPY package.json .
COPY package-lock.json* .
COPY yarn.lock* .

# Install dependencies
RUN npm install

# Copy project files
COPY . .

# Build for production
RUN npm run build

# Use Nginx to serve static files
FROM nginx:alpine
COPY --from=0 /app/build /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]