FROM problemtools/minimal

WORKDIR /app

RUN apt-get update && apt-get install -y python3-pip wget

RUN wget https://github.com/jgm/pandoc/releases/download/3.6.4/pandoc-3.6.4-1-amd64.deb \
    && dpkg -i pandoc-3.6.4-1-amd64.deb \
    && rm pandoc-3.6.4-1-amd64.deb

RUN pip install poetry

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-root --with production

COPY . .

EXPOSE 8000

CMD ["poetry", "run", "gunicorn", "-b", "0.0.0.0:8000", "main"]
