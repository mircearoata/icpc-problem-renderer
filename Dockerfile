FROM problemtools/minimal

WORKDIR /app

# Intalling poetry from the apt repository seems to be the easiest way to get it working
# Although it the poetry.lock was generated with poetry 2.1.1,
# and the version in the apt repo is 1.8.2 (at the moment),
# it is still able to read and install the dependencies correctly.
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y python3-poetry wget

RUN wget https://github.com/jgm/pandoc/releases/download/3.6.4/pandoc-3.6.4-1-amd64.deb \
    && dpkg -i pandoc-3.6.4-1-amd64.deb \
    && rm pandoc-3.6.4-1-amd64.deb

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-root --with production

COPY . .

EXPOSE 8000

CMD ["poetry", "run", "gunicorn", "-b", "0.0.0.0:8000", "main"]
