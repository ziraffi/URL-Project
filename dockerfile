# Use the official Python image as a base image
FROM python:alpine

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

# Create the /app directory
WORKDIR /app

# Create a non-privileged user that the app will run under.
# Specify the home directory for the user
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/home/appuser" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

# Create the .local directory to avoid permission denied issue
RUN mkdir -p /home/appuser/.local

# Copy the source code into the container.
COPY . .

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt

# Set permissions for /app/tmpf
RUN mkdir -p /app/tmpf && chmod -R 777 /app/tmpf

# Set ownership of the application directory to the non-privileged user
RUN chown -R appuser:appuser /app

# Switch to the non-privileged user
USER appuser

# Expose the port that the application listens on.
EXPOSE 8000

# Run the application with gunicorn.
CMD ["gunicorn", "myapp:app", "--worker-class=gthread", "--threads=8", "--bind=0.0.0.0:8000"]
