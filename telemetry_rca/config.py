"""Configuration settings using pydantic-settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    backend: str = "local"  # local or cluster
    kafka_bootstrap_servers: str = "localhost:9092"
    cassandra_hosts: list[str] = ["127.0.0.1"]
    window_size_seconds: int = 60
    anomaly_threshold: float = 3.0
    random_seed: int = 42
    rca_llm: str = "rules"  # rules or anthropic

    class Config:
        env_prefix = "RCA_"
        env_file = ".env"
        extra = "ignore"


settings = Settings()
