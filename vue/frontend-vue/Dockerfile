FROM node:lts-alpine

WORKDIR /app

# Copiamos package.json primero para aprovechar caché de Docker
COPY package*.json ./

# Instalamos dependencias
RUN npm install

# Copiamos el resto del código
COPY . .

# Exponemos el puerto de Vite
EXPOSE 8081

# Ejecutamos Vite en modo host para permitir acceso externo
CMD ["npm", "run", "dev", "--", "--host"]