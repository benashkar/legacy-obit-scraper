-- Add city, state, and county columns to obituaries table
-- city/state come from Legacy.com location JSON; county from markets.json config

ALTER TABLE obituaries
    ADD COLUMN city   VARCHAR(100) DEFAULT NULL AFTER funeral_home,
    ADD COLUMN state  VARCHAR(2)   DEFAULT NULL AFTER city,
    ADD COLUMN county VARCHAR(100) DEFAULT NULL AFTER state;

-- Indexes for dashboard filtering
CREATE INDEX idx_city   ON obituaries (city);
CREATE INDEX idx_state  ON obituaries (state);
CREATE INDEX idx_county ON obituaries (county);
