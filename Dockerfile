# ---- Build stage ----
FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /workspace

# Copy pom.xml and download dependencies (cached layer)
COPY pom.xml .
RUN mvn -q -B dependency:go-offline

# Copy source and build
COPY src ./src
RUN mvn -q -B -DskipTests package

# ---- Runtime stage ----
FROM eclipse-temurin:17-jre
WORKDIR /app

# Copy the fat jar
COPY --from=build /workspace/target/*-SNAPSHOT.jar app.jar

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/api/throws/health || exit 1

EXPOSE 8080

# Use environment variables for configuration
# ML_SERVICE_URL will be set by Railway
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
