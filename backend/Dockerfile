FROM public.ecr.aws/lambda/python:3.12

WORKDIR ${LAMBDA_TASK_ROOT}
COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir uv && uv pip install --system --no-cache .
CMD ["app.main.handler"]
