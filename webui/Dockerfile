# Stage 1: Build
FROM node:24.13-alpine AS build
WORKDIR /app

ENV NPM_CONFIG_LOGLEVEL=warn

COPY package*.json ./
RUN npm install --no-audit --no-fund --loglevel=error
COPY . .
RUN npm run build

# Stage 2: Production environment
FROM nginx:1.29.5-alpine

# Remove default Nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy the build output to Nginx's public folder
COPY --from=build /app/dist /usr/share/nginx/html

# Copy a custom Nginx config if you have one (optional)
RUN sed -i 's/index  index.html index.htm;/try_files $uri $uri\/ \/index.html;/g' /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]