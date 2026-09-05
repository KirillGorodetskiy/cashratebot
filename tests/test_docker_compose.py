import pathlib
import unittest


COMPOSE_PATH = (
    pathlib.Path(__file__).resolve().parents[1] / 'docker-compose.yml'
)


def load_compose_text() -> str:
    return COMPOSE_PATH.read_text(encoding='utf-8')


class TestDockerComposeRestart(unittest.TestCase):
    def test_app_restarts_after_reboot(self) -> None:
        compose = load_compose_text()
        app_block = compose.split('\n  redis:', 1)[0]
        self.assertIn('restart: unless-stopped', app_block)

    def test_redis_restarts_after_reboot(self) -> None:
        compose = load_compose_text()
        redis_block = compose.split('\n  redis:', 1)[1]
        self.assertIn('restart: unless-stopped', redis_block)


class TestDockerComposeRedisIsolation(unittest.TestCase):
    def test_redis_has_no_published_ports(self) -> None:
        compose = load_compose_text()
        self.assertNotIn('ports:', compose)
        self.assertNotIn('6380:6379', compose)

    def test_app_uses_internal_redis_host(self) -> None:
        compose = load_compose_text()
        self.assertIn('REDIS_HOST: redis', compose)
        self.assertIn('REDIS_PORT: "6379"', compose)

    def test_app_waits_for_healthy_redis(self) -> None:
        compose = load_compose_text()
        self.assertIn('condition: service_healthy', compose)
        self.assertIn('redis-cli', compose)


if __name__ == '__main__':
    unittest.main()
