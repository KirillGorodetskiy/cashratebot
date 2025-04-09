# My Telegram Bot

This Telegram bot provides up-to-date buy/sell currency exchange rates for the city you select. The data is sourced from [cash.rbc.ru](https://cash.rbc.ru). Please note that the rates shown may vary, and it’s always recommended to confirm the rates directly with the bank before visiting.

This bot was created for educational purposes to demonstrate how to work with the Telegram Bot API and fetch live data. It uses **Redis** for caching and **PostgreSQL** as the database to store user information and other relevant data. The bot itself and **Redis** are managed in Docker containers.

## Features

- Up-to-date cash currency exchange rates for selected cities (Moscow or Saint Petersburg).
- Data sourced from [cash.rbc.ru](https://cash.rbc.ru).
- Educational project showcasing Telegram Bot API and live data fetching.

## Installation

### Prerequisites

- Docker: [Install Docker](https://docs.docker.com/get-docker/)
- Docker Compose: [Install Docker Compose](https://docs.docker.com/compose/install/)

### Steps to Run with Docker

```bash
# Clone the repository
git clone https://github.com/KirillGorodetskiy/cashratebot
cd cashratebot
```

```bash
# Create a .env file in the root directory and add the following:
```

```env

BOT_TOKEN=<your_token>

REDIS_HOST=<redis_host>
REDIS_PORT=<redis_port>

NUM_OF_RETURNED_BANKS=7 # how many bank`s quotes show to the user. Banks are sorted by best price.

TTL_QUOTES_IN_REDIS=600 # time to live quotes for chosen City in Redis cash in seconds
TTL_STATS_IN_REDIS=600 # time to live stats for chosen City in Redis cash in seconds

DB_NAME=<db_name>
DB_USER=<db_user>
DB_PASSWORD=<db_password>
DB_HOST=<db_host>
DB_PORT=<db_port>
```

```bash
# Build and start the services
docker-compose up --build
```

```bash
# Optional: Run in detached mode
docker-compose up -d
```

```bash
# To stop all containers
docker-compose down
```

## Usage

```text
/start           - Start interacting with the bot
```

## Docker Setup

### Dockerfile

The `Dockerfile` builds the bot container with the necessary dependencies and configuration.
The "docker-compose.yml" builds 2 containers, one with the Bot and one with the Redis.

### docker-compose.yml

This file defines the following services:

- `bot`: The Telegram bot itself  
- `redis`: Redis caching service  
- `db`: PostgreSQL database service  

## Contributing



## License


