FROM node:20-alpine

WORKDIR /workspace/frontend/react-app

COPY frontend/react-app/package.json ./package.json
RUN npm install

COPY frontend/react-app /workspace/frontend/react-app

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]