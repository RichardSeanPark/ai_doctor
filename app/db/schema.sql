-- Health AI 애플리케이션 데이터베이스 스키마
-- 사용자 테이블
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    password_salt VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    birth_date DATE NOT NULL,
    gender ENUM('male', 'female', 'other') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 사용자 세션 테이블
CREATE TABLE IF NOT EXISTS user_sessions (
    session_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 사용자 알림 설정 테이블
CREATE TABLE IF NOT EXISTS notification_settings (
    user_id VARCHAR(36) PRIMARY KEY,
    device_token VARCHAR(255),
    notification_time TIME,
    voice_type ENUM('male', 'female') DEFAULT 'female',
    speech_speed FLOAT DEFAULT 1.0,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 건강 지표 테이블
CREATE TABLE IF NOT EXISTS health_metrics (
    metrics_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    weight FLOAT,
    height FLOAT,
    bmi FLOAT,
    heart_rate INT,
    blood_pressure_systolic INT,
    blood_pressure_diastolic INT,
    blood_sugar FLOAT,
    temperature FLOAT,
    oxygen_saturation INT,
    sleep_hours FLOAT,
    steps INT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 사용자 목표 테이블
CREATE TABLE IF NOT EXISTS user_goals (
    goal_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    goal_type VARCHAR(50) NOT NULL,
    target_value FLOAT NOT NULL,
    deadline DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 의학적 상태 테이블
CREATE TABLE IF NOT EXISTS medical_conditions (
    condition_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    condition_name VARCHAR(100) NOT NULL,
    diagnosis_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 식이 제한 테이블
CREATE TABLE IF NOT EXISTS dietary_restrictions (
    restriction_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    restriction_type VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 건강 평가 테이블
CREATE TABLE IF NOT EXISTS health_assessments (
    assessment_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    health_status VARCHAR(50) NOT NULL,
    has_concerns BOOLEAN DEFAULT FALSE,
    assessment_summary TEXT NOT NULL,
    query_text TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 건강 평가 우려사항 테이블
CREATE TABLE IF NOT EXISTS assessment_concerns (
    concern_id VARCHAR(36) PRIMARY KEY,
    assessment_id VARCHAR(36) NOT NULL,
    concern_text TEXT NOT NULL,
    FOREIGN KEY (assessment_id) REFERENCES health_assessments(assessment_id) ON DELETE CASCADE
);

-- 건강 평가 권장사항 테이블
CREATE TABLE IF NOT EXISTS assessment_recommendations (
    recommendation_id VARCHAR(36) PRIMARY KEY,
    assessment_id VARCHAR(36) NOT NULL,
    recommendation_text TEXT NOT NULL,
    FOREIGN KEY (assessment_id) REFERENCES health_assessments(assessment_id) ON DELETE CASCADE
);

-- 대화 세션 테이블 (추가)
CREATE TABLE IF NOT EXISTS conversation_sessions (
    conversation_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    session_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    context_summary TEXT,
    session_type VARCHAR(50) DEFAULT 'general',
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 대화 메시지 테이블 (추가)
CREATE TABLE IF NOT EXISTS conversation_messages (
    message_id VARCHAR(36) PRIMARY KEY,
    conversation_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sender ENUM('user', 'assistant') NOT NULL,
    message_text TEXT NOT NULL,
    is_important BOOLEAN DEFAULT FALSE,
    entities JSON,
    FOREIGN KEY (conversation_id) REFERENCES conversation_sessions(conversation_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 대화 요약 테이블 (추가)
CREATE TABLE IF NOT EXISTS conversation_summaries (
    summary_id VARCHAR(36) PRIMARY KEY,
    conversation_id VARCHAR(36) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    summary_text TEXT NOT NULL,
    key_points JSON,
    health_entities JSON,
    FOREIGN KEY (conversation_id) REFERENCES conversation_sessions(conversation_id) ON DELETE CASCADE
); 