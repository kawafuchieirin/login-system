FROM public.ecr.aws/lambda/python:3.12

# Install poetry
RUN pip install poetry --no-cache-dir

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies (without dev dependencies)
RUN poetry config virtualenvs.create false && \
    poetry install --only main --no-interaction --no-ansi

# Copy application code
COPY main.py dependencies.py ./
COPY routers/ ./routers/
COPY models/ ./models/
COPY services/ ./services/
COPY clients/ ./clients/

# Set the handler
CMD ["main.handler"]
