FROM problemtools/minimal

WORKDIR /app

RUN apt-get update && apt-get install -y python3-pip

RUN pip install poetry

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-root --with production

COPY . .

EXPOSE 8000

CMD ["poetry", "run", "gunicorn", "main"]