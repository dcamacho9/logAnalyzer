# ==============================================
# Dockerfile para Log Analyzer Omni Gateway
# MuleSoft Runtime 4.11.6
# ==============================================

# Stage 1: Build
FROM docker.m.daocloud.io/library/maven:3.9-eclipse-temurin-17 as builder

WORKDIR /build

# Copiar archivos del proyecto
COPY pom.xml .
COPY mule-artifact.json .
COPY src ./src

# Build del proyecto MuleSoft
RUN mvn clean package -DskipTests

# Stage 2: Runtime
FROM docker.m.daocloud.io/library/eclipse-temurin:17-jre-jammy

LABEL maintainer="DevOps Team"
LABEL description="Log Analyzer Omni Gateway - MuleSoft Runtime 4.11.6"
LABEL version="1.0.0"

# Variables de entorno
ENV MULE_HOME=/opt/mule \
    JAVA_OPTS="-Xmx1024m -Xms512m" \
    PORT=8081

# Instalar dependencias de runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Descargar y configurar Mule Runtime
WORKDIR /opt
RUN curl -L https://repository.mulesoft.org/nexus/content/repositories/releases/org/mule/distributions/mule-runtime-impl-standalone/4.11.6/mule-runtime-impl-standalone-4.11.6.tar.gz \
    -o mule-runtime.tar.gz && \
    tar -xzf mule-runtime.tar.gz && \
    mv mule-runtime-impl-standalone-4.11.6 mule && \
    rm mule-runtime.tar.gz && \
    chmod +x /opt/mule/bin/mule

# Crear usuario no-root
RUN useradd -m -d /home/muleuser -s /sbin/nologin muleuser

# Copiar la aplicación compilada
COPY --from=builder /build/target/*.jar /opt/mule/apps/
COPY --from=builder /build/target/mule-application.jar /opt/mule/apps/log-analyzer-omni-gateway.jar

# Cambiar permisos
RUN chown -R muleuser:muleuser /opt/mule

USER muleuser

WORKDIR /opt/mule

# Exponer puerto
EXPOSE ${PORT}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=60s \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Comando de inicio
CMD ["./bin/mule", "-M", "-D", "app.home=/opt/mule"]
