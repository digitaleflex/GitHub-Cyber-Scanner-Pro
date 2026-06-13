FROM node:20-slim
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable

WORKDIR /app

# Installer les dépendances
COPY package.json pnpm-lock.yaml ./
RUN pnpm install

# Copier le reste du code
COPY . .

# TanStack Start par défaut sur le port 3000
EXPOSE 3000
CMD ["pnpm", "dev", "--host"]
