-- Backfill state from site_id prefix for existing rows
-- site_id format: "tx-brown", "oh-franklin", "ma-grafton", "ga-claxton"

UPDATE obituaries SET state = 'TX' WHERE state IS NULL AND site_id LIKE 'tx-%';
UPDATE obituaries SET state = 'OH' WHERE state IS NULL AND site_id LIKE 'oh-%';
UPDATE obituaries SET state = 'MA' WHERE state IS NULL AND site_id LIKE 'ma-%';
UPDATE obituaries SET state = 'GA' WHERE state IS NULL AND site_id LIKE 'ga-%';

-- Backfill county from site_id for existing rows
-- Texas (all county-type markets)
UPDATE obituaries SET county = 'Brown'       WHERE county IS NULL AND site_id = 'tx-brown';
UPDATE obituaries SET county = 'Erath'       WHERE county IS NULL AND site_id = 'tx-erath';
UPDATE obituaries SET county = 'Palo Pinto'  WHERE county IS NULL AND site_id = 'tx-palo-pinto';
UPDATE obituaries SET county = 'Somervell'   WHERE county IS NULL AND site_id = 'tx-somervell';
UPDATE obituaries SET county = 'Runnels'     WHERE county IS NULL AND site_id = 'tx-runnels';
UPDATE obituaries SET county = 'Ellis'       WHERE county IS NULL AND site_id = 'tx-ellis';
UPDATE obituaries SET county = 'Jim Wells'   WHERE county IS NULL AND site_id = 'tx-jim-wells';
UPDATE obituaries SET county = 'Grayson'     WHERE county IS NULL AND site_id = 'tx-grayson';
UPDATE obituaries SET county = 'Fannin'      WHERE county IS NULL AND site_id = 'tx-fannin';

-- Ohio
UPDATE obituaries SET county = 'Franklin'    WHERE county IS NULL AND site_id = 'oh-franklin';
UPDATE obituaries SET county = 'Franklin'    WHERE county IS NULL AND site_id IN ('oh-obetz','oh-canal-winch','oh-hamilton-twp','oh-lockbourne','oh-groveport','oh-madison-twp','oh-west-columbus','oh-lincoln-vil','oh-prairie-twp','oh-westgate','oh-galloway','oh-hilliard','oh-grove-city','oh-urbancrest');
UPDATE obituaries SET county = 'Fairfield'   WHERE county IS NULL AND site_id = 'oh-lithopolis';
UPDATE obituaries SET county = 'Pickaway'    WHERE county IS NULL AND site_id = 'oh-comm-point';

-- Massachusetts
UPDATE obituaries SET county = 'Worcester'   WHERE county IS NULL AND site_id IN ('ma-grafton','ma-millbury','ma-sutton','ma-holden');

-- Georgia
UPDATE obituaries SET county = 'Evans'       WHERE county IS NULL AND site_id = 'ga-claxton';
