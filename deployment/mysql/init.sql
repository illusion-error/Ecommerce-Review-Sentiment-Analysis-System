CREATE DATABASE IF NOT EXISTS sentiment_analysis
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE sentiment_analysis;

CREATE TABLE IF NOT EXISTS comments (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    product_id VARCHAR(64),
    content TEXT NOT NULL,
    clean_content TEXT,
    comment_time VARCHAR(64),
    source VARCHAR(32) DEFAULT 'api',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS analysis_records (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    task_id VARCHAR(64),
    comment_id BIGINT,
    product_id VARCHAR(64),
    raw_text TEXT NOT NULL,
    clean_text TEXT,
    label TINYINT NOT NULL COMMENT '0 negative, 1 positive',
    sentiment VARCHAR(16) NOT NULL,
    confidence FLOAT NOT NULL,
    strength FLOAT NOT NULL,
    cached BOOLEAN DEFAULT FALSE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_task_id (task_id),
    INDEX idx_sentiment (sentiment),
    INDEX idx_created_at (created_at),
    CONSTRAINT fk_analysis_comment
      FOREIGN KEY (comment_id) REFERENCES comments(id)
      ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS batch_tasks (
    task_id VARCHAR(64) PRIMARY KEY,
    filename VARCHAR(255),
    status VARCHAR(32) NOT NULL,
    total INT DEFAULT 0,
    success_count INT DEFAULT 0,
    failed_count INT DEFAULT 0,
    positive_count INT DEFAULT 0,
    negative_count INT DEFAULT 0,
    avg_strength FLOAT DEFAULT 0,
    error_message TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at DATETIME NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

