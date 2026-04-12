-- ============================================================
-- STUDY PLANNER — MySQL Schema
-- ============================================================

CREATE DATABASE IF NOT EXISTS study_planner
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE study_planner;

-- ------------------------------------------------------------
-- USERS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id              INT             NOT NULL AUTO_INCREMENT,
    full_name       VARCHAR(120)    NOT NULL,
    email           VARCHAR(255)    NOT NULL,
    password        VARCHAR(255)    NOT NULL,        -- bcrypt hash
    education_level VARCHAR(80)     NOT NULL,
    course          VARCHAR(120)    NOT NULL,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_users   PRIMARY KEY (id),
    CONSTRAINT uq_users_email UNIQUE (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- SUBJECTS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS subjects (
    id          INT         NOT NULL AUTO_INCREMENT,
    user_id     INT         NOT NULL,
    name        VARCHAR(120) NOT NULL,
    difficulty  TINYINT     NOT NULL CHECK (difficulty  BETWEEN 1 AND 5),
    priority    TINYINT     NOT NULL CHECK (priority    BETWEEN 1 AND 5),
    exam_date   DATE        NOT NULL,
    created_at  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_subjects          PRIMARY KEY (id),
    CONSTRAINT fk_subjects_user     FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- STUDY_PLANS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS study_plans (
    id                  INT         NOT NULL AUTO_INCREMENT,
    user_id             INT         NOT NULL,
    day_of_week         VARCHAR(20) NOT NULL,
    subject_name        VARCHAR(120) NOT NULL,
    study_time_minutes  INT         NOT NULL,
    generated_at        DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_study_plans       PRIMARY KEY (id),
    CONSTRAINT fk_study_plans_user  FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
