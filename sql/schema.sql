-- Legacy Obituary Scraper — MySQL Schema
-- Enhanced with name splitting per data field standards

CREATE TABLE IF NOT EXISTS obituaries (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    site_id         VARCHAR(50)   NOT NULL,
    legacy_url      VARCHAR(500)  NOT NULL UNIQUE,   -- dedup key
    deceased_name   VARCHAR(255),                     -- full name (convenience)
    first_name      VARCHAR(100),                     -- parsed first name
    middle_name     VARCHAR(100),                     -- parsed middle name
    last_name       VARCHAR(100),                     -- parsed last name
    name_suffix     VARCHAR(20),                      -- Jr, Sr, III, etc.
    published_date  DATE,
    death_date      DATE,
    funeral_home    VARCHAR(255),
    city            VARCHAR(100),                     -- from Legacy.com location.city.fullName
    state           VARCHAR(2),                       -- from Legacy.com location.state.code
    county          VARCHAR(100),                     -- from markets.json config
    obit_text       LONGTEXT,
    scraped_at      DATETIME      DEFAULT CURRENT_TIMESTAMP,
    sent_to_cms     TINYINT(1)    DEFAULT 0,
    duplicate_of    INT           DEFAULT NULL,  -- NULL=primary, else points to primary row id

    -- Single-column indexes
    INDEX idx_site_id (site_id),
    INDEX idx_published_date (published_date),
    INDEX idx_death_date (death_date),
    INDEX idx_funeral_home (funeral_home),
    INDEX idx_scraped_at (scraped_at),
    INDEX idx_sent_to_cms (sent_to_cms),
    INDEX idx_first_name (first_name),
    INDEX idx_last_name (last_name),
    INDEX idx_city (city),
    INDEX idx_state (state),
    INDEX idx_county (county),
    INDEX idx_duplicate_of (duplicate_of),

    -- Composite indexes for common query patterns
    INDEX idx_last_first (last_name, first_name),
    INDEX idx_site_published (site_id, published_date),
    INDEX idx_state_county_city (state, county, city),
    INDEX idx_dedup_scraped (duplicate_of, scraped_at),

    -- FULLTEXT index for name search
    FULLTEXT idx_ft_deceased_name (deceased_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- View: deduplicated obituaries with key lookup fields
CREATE OR REPLACE VIEW v_obituaries AS
SELECT
    id,
    first_name,
    middle_name,
    last_name,
    name_suffix,
    city,
    county,
    state,
    legacy_url,
    death_date,
    published_date,
    scraped_at,
    funeral_home,
    deceased_name,
    obit_text
FROM obituaries
WHERE duplicate_of IS NULL
ORDER BY scraped_at DESC;

CREATE TABLE IF NOT EXISTS scrape_log (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    site_id     VARCHAR(50) NOT NULL,
    run_date    DATE        NOT NULL,
    obits_found INT         DEFAULT 0,
    obits_new   INT         DEFAULT 0,
    errors      TEXT,
    run_at      DATETIME    DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_run_date (run_date),
    INDEX idx_site_run (site_id, run_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
