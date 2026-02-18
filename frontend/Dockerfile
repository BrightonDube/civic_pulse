FROM node:20-alpine AS build

WORKDIR /app

# When deployed via Railway from root, files are in frontend/
# When built locally from frontend/, files are in ./
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --legacy-peer-deps

COPY frontend/ .

ARG VITE_API_URL=""
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY --from=build /app/nginx.conf /etc/nginx/templates/default.conf.template

ENV PORT=80
ENV BACKEND_URL=http://localhost:8000

EXPOSE ${PORT}

CMD ["nginx", "-g", "daemon off;"]
