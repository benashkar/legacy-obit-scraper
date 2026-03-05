"""Generate markets.json with all counties for 9 priority states."""

import json
import os

MARKETS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config",
    "markets.json",
)

# Load existing markets
with open(MARKETS_FILE, "r") as f:
    existing = json.load(f)

existing_ids = {m["site_id"] for m in existing}

# County data: (state_abbrev, state_name, county_name, slug)
COUNTIES = []


def add_counties(abbrev, state_name, data_str):
    for line in data_str.strip().split("\n"):
        parts = line.split("\t")
        if len(parts) == 2:
            name, slug = parts
            COUNTIES.append((abbrev, state_name, name, slug))


# TEXAS (254 counties)
add_counties("TX", "texas", """Anderson\tanderson-county
Andrews\tandrews-county
Angelina\tangelina-county
Aransas\taransas-county
Archer\tarcher-county
Armstrong\tarmstrong-county
Atascosa\tatascosa-county
Austin\taustin-county
Bailey\tbailey-county
Bandera\tbandera-county
Bastrop\tbastrop-county
Baylor\tbaylor-county
Bee\tbee-county
Bell\tbell-county
Bexar\tbexar-county
Blanco\tblanco-county
Borden\tborden-county
Bosque\tbosque-county
Bowie\tbowie-county
Brazoria\tbrazoria-county
Brazos\tbrazos-county
Brewster\tbrewster-county
Briscoe\tbriscoe-county
Brooks\tbrooks-county
Brown\tbrown-county
Burleson\tburleson-county
Burnet\tburnet-county
Caldwell\tcaldwell-county
Calhoun\tcalhoun-county
Callahan\tcallahan-county
Cameron\tcameron-county
Camp\tcamp-county
Carson\tcarson-county
Cass\tcass-county
Castro\tcastro-county
Chambers\tchambers-county
Cherokee\tcherokee-county
Childress\tchildress-county
Clay\tclay-county
Cochran\tcochran-county
Coke\tcoke-county
Coleman\tcoleman-county
Collin\tcollin-county
Collingsworth\tcollingsworth-county
Colorado\tcolorado-county
Comal\tcomal-county
Comanche\tcomanche-county
Concho\tconcho-county
Cooke\tcooke-county
Coryell\tcoryell-county
Cottle\tcottle-county
Crane\tcrane-county
Crockett\tcrockett-county
Crosby\tcrosby-county
Culberson\tculberson-county
Dallam\tdallam-county
Dallas\tdallas-county
Dawson\tdawson-county
Deaf Smith\tdeaf-smith-county
Delta\tdelta-county
Denton\tdenton-county
DeWitt\tdewitt-county
Dickens\tdickens-county
Dimmit\tdimmit-county
Donley\tdonley-county
Duval\tduval-county
Eastland\teastland-county
Ector\tector-county
Edwards\tedwards-county
El Paso\tel-paso-county
Ellis\tellis-county
Erath\terath-county
Falls\tfalls-county
Fannin\tfannin-county
Fayette\tfayette-county
Fisher\tfisher-county
Floyd\tfloyd-county
Foard\tfoard-county
Fort Bend\tfort-bend-county
Franklin\tfranklin-county
Freestone\tfreestone-county
Frio\tfrio-county
Gaines\tgaines-county
Galveston\tgalveston-county
Garza\tgarza-county
Gillespie\tgillespie-county
Glasscock\tglasscock-county
Goliad\tgoliad-county
Gonzales\tgonzales-county
Gray\tgray-county
Grayson\tgrayson-county
Gregg\tgregg-county
Grimes\tgrimes-county
Guadalupe\tguadalupe-county
Hale\thale-county
Hall\thall-county
Hamilton\thamilton-county
Hansford\thansford-county
Hardeman\thardeman-county
Hardin\thardin-county
Harris\tharris-county
Harrison\tharrison-county
Hartley\thartley-county
Haskell\thaskell-county
Hays\thays-county
Hemphill\themphill-county
Henderson\thenderson-county
Hidalgo\thidalgo-county
Hill\thill-county
Hockley\thockley-county
Hood\thood-county
Hopkins\thopkins-county
Houston\thouston-county
Howard\thoward-county
Hudspeth\thudspeth-county
Hunt\thunt-county
Hutchinson\thutchinson-county
Irion\tirion-county
Jack\tjack-county
Jackson\tjackson-county
Jasper\tjasper-county
Jeff Davis\tjeff-davis-county
Jefferson\tjefferson-county
Jim Hogg\tjim-hogg-county
Jim Wells\tjim-wells-county
Johnson\tjohnson-county
Jones\tjones-county
Karnes\tkarnes-county
Kaufman\tkaufman-county
Kendall\tkendall-county
Kenedy\tkenedy-county
Kent\tkent-county
Kerr\tkerr-county
Kimble\tkimble-county
King\tking-county
Kinney\tkinney-county
Kleberg\tkleberg-county
Knox\tknox-county
Lamar\tlamar-county
Lamb\tlamb-county
Lampasas\tlampasas-county
La Salle\tla-salle-county
Lavaca\tlavaca-county
Lee\tlee-county
Leon\tleon-county
Liberty\tliberty-county
Limestone\tlimestone-county
Lipscomb\tlipscomb-county
Live Oak\tlive-oak-county
Llano\tllano-county
Loving\tloving-county
Lubbock\tlubbock-county
Lynn\tlynn-county
Madison\tmadison-county
Marion\tmarion-county
Martin\tmartin-county
Mason\tmason-county
Matagorda\tmatagorda-county
Maverick\tmaverick-county
McCulloch\tmcculloch-county
McLennan\tmclennan-county
McMullen\tmcmullen-county
Medina\tmedina-county
Menard\tmenard-county
Midland\tmidland-county
Milam\tmilam-county
Mills\tmills-county
Mitchell\tmitchell-county
Montague\tmontague-county
Montgomery\tmontgomery-county
Moore\tmoore-county
Morris\tmorris-county
Motley\tmotley-county
Nacogdoches\tnacogdoches-county
Navarro\tnavarro-county
Newton\tnewton-county
Nolan\tnolan-county
Nueces\tnueces-county
Ochiltree\tochiltree-county
Oldham\toldham-county
Orange\torange-county
Palo Pinto\tpalo-pinto-county
Panola\tpanola-county
Parker\tparker-county
Parmer\tparmer-county
Pecos\tpecos-county
Polk\tpolk-county
Potter\tpotter-county
Presidio\tpresidio-county
Rains\trains-county
Randall\trandall-county
Reagan\treagan-county
Real\treal-county
Red River\tred-river-county
Reeves\treeves-county
Refugio\trefugio-county
Roberts\troberts-county
Robertson\trobertson-county
Rockwall\trockwall-county
Runnels\trunnels-county
Rusk\trusk-county
Sabine\tsabine-county
San Augustine\tsan-augustine-county
San Jacinto\tsan-jacinto-county
San Patricio\tsan-patricio-county
San Saba\tsan-saba-county
Schleicher\tschleicher-county
Scurry\tscurry-county
Shackelford\tshackelford-county
Shelby\tshelby-county
Sherman\tsherman-county
Smith\tsmith-county
Somervell\tsomervell-county
Starr\tstarr-county
Stephens\tstephens-county
Sterling\tsterling-county
Stonewall\tstonewall-county
Sutton\tsutton-county
Swisher\tswisher-county
Tarrant\ttarrant-county
Taylor\ttaylor-county
Terrell\tterrell-county
Terry\tterry-county
Throckmorton\tthrockmorton-county
Titus\ttitus-county
Tom Green\ttom-green-county
Travis\ttravis-county
Trinity\ttrinity-county
Tyler\ttyler-county
Upshur\tupshur-county
Upton\tupton-county
Uvalde\tuvalde-county
Val Verde\tval-verde-county
Van Zandt\tvan-zandt-county
Victoria\tvictoria-county
Walker\twalker-county
Waller\twaller-county
Ward\tward-county
Washington\twashington-county
Webb\twebb-county
Wharton\twharton-county
Wheeler\twheeler-county
Wichita\twichita-county
Wilbarger\twilbarger-county
Willacy\twillacy-county
Williamson\twilliamson-county
Wilson\twilson-county
Winkler\twinkler-county
Wise\twise-county
Wood\twood-county
Yoakum\tyoakum-county
Young\tyoung-county
Zapata\tzapata-county
Zavala\tzavala-county""")

# OHIO (88 counties)
add_counties("OH", "ohio", """Adams\tadams-county
Allen\tallen-county
Ashland\tashland-county
Ashtabula\tashtabula-county
Athens\tathens-county
Auglaize\tauglaize-county
Belmont\tbelmont-county
Brown\tbrown-county
Butler\tbutler-county
Carroll\tcarroll-county
Champaign\tchampaign-county
Clark\tclark-county
Clermont\tclermont-county
Clinton\tclinton-county
Columbiana\tcolumbiana-county
Coshocton\tcoshocton-county
Crawford\tcrawford-county
Cuyahoga\tcuyahoga-county
Darke\tdarke-county
Defiance\tdefiance-county
Delaware\tdelaware-county
Erie\terie-county
Fairfield\tfairfield-county
Fayette\tfayette-county
Franklin\tfranklin-county
Fulton\tfulton-county
Gallia\tgallia-county
Geauga\tgeauga-county
Greene\tgreene-county
Guernsey\tguernsey-county
Hamilton\thamilton-county
Hancock\thancock-county
Hardin\thardin-county
Harrison\tharrison-county
Henry\thenry-county
Highland\thighland-county
Hocking\thocking-county
Holmes\tholmes-county
Huron\thuron-county
Jackson\tjackson-county
Jefferson\tjefferson-county
Knox\tknox-county
Lake\tlake-county
Lawrence\tlawrence-county
Licking\tlicking-county
Logan\tlogan-county
Lorain\tlorain-county
Lucas\tlucas-county
Madison\tmadison-county
Mahoning\tmahoning-county
Marion\tmarion-county
Medina\tmedina-county
Meigs\tmeigs-county
Mercer\tmercer-county
Miami\tmiami-county
Monroe\tmonroe-county
Montgomery\tmontgomery-county
Morgan\tmorgan-county
Morrow\tmorrow-county
Muskingum\tmuskingum-county
Noble\tnoble-county
Ottawa\tottawa-county
Paulding\tpaulding-county
Perry\tperry-county
Pickaway\tpickaway-county
Pike\tpike-county
Portage\tportage-county
Preble\tpreble-county
Putnam\tputnam-county
Richland\trichland-county
Ross\tross-county
Sandusky\tsandusky-county
Scioto\tscioto-county
Seneca\tseneca-county
Shelby\tshelby-county
Stark\tstark-county
Summit\tsummit-county
Trumbull\ttrumbull-county
Tuscarawas\ttuscarawas-county
Union\tunion-county
Van Wert\tvan-wert-county
Vinton\tvinton-county
Warren\twarren-county
Washington\twashington-county
Wayne\twayne-county
Williams\twilliams-county
Wood\twood-county
Wyandot\twyandot-county""")

# GEORGIA (159 counties)
add_counties("GA", "georgia", """Appling\tappling-county
Atkinson\tatkinson-county
Bacon\tbacon-county
Baker\tbaker-county
Baldwin\tbaldwin-county
Banks\tbanks-county
Barrow\tbarrow-county
Bartow\tbartow-county
Ben Hill\tben-hill-county
Berrien\tberrien-county
Bibb\tbibb-county
Bleckley\tbleckley-county
Brantley\tbrantley-county
Brooks\tbrooks-county
Bryan\tbryan-county
Bulloch\tbulloch-county
Burke\tburke-county
Butts\tbutts-county
Calhoun\tcalhoun-county
Camden\tcamden-county
Candler\tcandler-county
Carroll\tcarroll-county
Catoosa\tcatoosa-county
Charlton\tcharlton-county
Chatham\tchatham-county
Chattahoochee\tchattahoochee-county
Chattooga\tchattooga-county
Cherokee\tcherokee-county
Clarke\tclarke-county
Clay\tclay-county
Clayton\tclayton-county
Clinch\tclinch-county
Cobb\tcobb-county
Coffee\tcoffee-county
Colquitt\tcolquitt-county
Columbia\tcolumbia-county
Cook\tcook-county
Coweta\tcoweta-county
Crawford\tcrawford-county
Crisp\tcrisp-county
Dade\tdade-county
Dawson\tdawson-county
Decatur\tdecatur-county
DeKalb\tdekalb-county
Dodge\tdodge-county
Dooly\tdooly-county
Dougherty\tdougherty-county
Douglas\tdouglas-county
Early\tearly-county
Echols\techols-county
Effingham\teffingham-county
Elbert\telbert-county
Emanuel\temanuel-county
Evans\tevans-county
Fannin\tfannin-county
Fayette\tfayette-county
Floyd\tfloyd-county
Forsyth\tforsyth-county
Franklin\tfranklin-county
Fulton\tfulton-county
Gilmer\tgilmer-county
Glascock\tglascock-county
Glynn\tglynn-county
Gordon\tgordon-county
Grady\tgrady-county
Greene\tgreene-county
Gwinnett\tgwinnett-county
Habersham\thabersham-county
Hall\thall-county
Hancock\thancock-county
Haralson\tharalson-county
Harris\tharris-county
Hart\thart-county
Heard\theard-county
Henry\thenry-county
Houston\thouston-county
Irwin\tirwin-county
Jackson\tjackson-county
Jasper\tjasper-county
Jeff Davis\tjeff-davis-county
Jefferson\tjefferson-county
Jenkins\tjenkins-county
Johnson\tjohnson-county
Jones\tjones-county
Lamar\tlamar-county
Lanier\tlanier-county
Laurens\tlaurens-county
Lee\tlee-county
Liberty\tliberty-county
Lincoln\tlincoln-county
Long\tlong-county
Lowndes\tlowndes-county
Lumpkin\tlumpkin-county
Macon\tmacon-county
Madison\tmadison-county
Marion\tmarion-county
McDuffie\tmcduffie-county
McIntosh\tmcintosh-county
Meriwether\tmeriwether-county
Miller\tmiller-county
Mitchell\tmitchell-county
Monroe\tmonroe-county
Montgomery\tmontgomery-county
Morgan\tmorgan-county
Murray\tmurray-county
Muscogee\tmuscogee-county
Newton\tnewton-county
Oconee\toconee-county
Oglethorpe\toglethorpe-county
Paulding\tpaulding-county
Peach\tpeach-county
Pickens\tpickens-county
Pierce\tpierce-county
Pike\tpike-county
Polk\tpolk-county
Pulaski\tpulaski-county
Putnam\tputnam-county
Quitman\tquitman-county
Rabun\trabun-county
Randolph\trandolph-county
Richmond\trichmond-county
Rockdale\trockdale-county
Schley\tschley-county
Screven\tscreven-county
Seminole\tseminole-county
Spalding\tspalding-county
Stephens\tstephens-county
Stewart\tstewart-county
Sumter\tsumter-county
Talbot\ttalbot-county
Taliaferro\ttaliaferro-county
Tattnall\ttattnall-county
Taylor\ttaylor-county
Telfair\ttelfair-county
Terrell\tterrell-county
Thomas\tthomas-county
Tift\ttift-county
Toombs\ttoombs-county
Towns\ttowns-county
Treutlen\ttreutlen-county
Troup\ttroup-county
Turner\tturner-county
Twiggs\ttwiggs-county
Union\tunion-county
Upson\tupson-county
Walker\twalker-county
Walton\twalton-county
Ware\tware-county
Warren\twarren-county
Washington\twashington-county
Wayne\twayne-county
Webster\twebster-county
Wheeler\twheeler-county
White\twhite-county
Whitfield\twhitfield-county
Wilcox\twilcox-county
Wilkes\twilkes-county
Wilkinson\twilkinson-county
Worth\tworth-county""")

# MASSACHUSETTS (14 counties)
add_counties("MA", "massachusetts", """Barnstable\tbarnstable-county
Berkshire\tberkshire-county
Bristol\tbristol-county
Dukes\tdukes-county
Essex\tessex-county
Franklin\tfranklin-county
Hampden\thampden-county
Hampshire\thampshire-county
Middlesex\tmiddlesex-county
Nantucket\tnantucket-county
Norfolk\tnorfolk-county
Plymouth\tplymouth-county
Suffolk\tsuffolk-county
Worcester\tworcester-county""")

# NORTH CAROLINA (100 counties)
add_counties("NC", "north-carolina", """Alamance\talamance-county
Alexander\talexander-county
Alleghany\talleghany-county
Anson\tanson-county
Ashe\tashe-county
Avery\tavery-county
Beaufort\tbeaufort-county
Bertie\tbertie-county
Bladen\tbladen-county
Brunswick\tbrunswick-county
Buncombe\tbuncombe-county
Burke\tburke-county
Cabarrus\tcabarrus-county
Caldwell\tcaldwell-county
Camden\tcamden-county
Carteret\tcarteret-county
Caswell\tcaswell-county
Catawba\tcatawba-county
Chatham\tchatham-county
Cherokee\tcherokee-county
Chowan\tchowan-county
Clay\tclay-county
Cleveland\tcleveland-county
Columbus\tcolumbus-county
Craven\tcraven-county
Cumberland\tcumberland-county
Currituck\tcurrituck-county
Dare\tdare-county
Davidson\tdavidson-county
Davie\tdavie-county
Duplin\tduplin-county
Durham\tdurham-county
Edgecombe\tedgecombe-county
Forsyth\tforsyth-county
Franklin\tfranklin-county
Gaston\tgaston-county
Gates\tgates-county
Graham\tgraham-county
Granville\tgranville-county
Greene\tgreene-county
Guilford\tguilford-county
Halifax\thalifax-county
Harnett\tharnett-county
Haywood\thaywood-county
Henderson\thenderson-county
Hertford\thertford-county
Hoke\thoke-county
Hyde\thyde-county
Iredell\tiredell-county
Jackson\tjackson-county
Johnston\tjohnston-county
Jones\tjones-county
Lee\tlee-county
Lenoir\tlenoir-county
Lincoln\tlincoln-county
Macon\tmacon-county
Madison\tmadison-county
Martin\tmartin-county
McDowell\tmcdowell-county
Mecklenburg\tmecklenburg-county
Mitchell\tmitchell-county
Montgomery\tmontgomery-county
Moore\tmoore-county
Nash\tnash-county
New Hanover\tnew-hanover-county
Northampton\tnorthampton-county
Onslow\tonslow-county
Orange\torange-county
Pamlico\tpamlico-county
Pasquotank\tpasquotank-county
Pender\tpender-county
Perquimans\tperquimans-county
Person\tperson-county
Pitt\tpitt-county
Polk\tpolk-county
Randolph\trandolph-county
Richmond\trichmond-county
Robeson\trobeson-county
Rockingham\trockingham-county
Rowan\trowan-county
Rutherford\trutherford-county
Sampson\tsampson-county
Scotland\tscotland-county
Stanly\tstanly-county
Stokes\tstokes-county
Surry\tsurry-county
Swain\tswain-county
Transylvania\ttransylvania-county
Tyrrell\ttyrrell-county
Union\tunion-county
Vance\tvance-county
Wake\twake-county
Warren\twarren-county
Washington\twashington-county
Watauga\twatauga-county
Wayne\twayne-county
Wilkes\twilkes-county
Wilson\twilson-county
Yadkin\tyadkin-county
Yancey\tyancey-county""")

# MINNESOTA (87 counties)
add_counties("MN", "minnesota", """Aitkin\taitkin-county
Anoka\tanoka-county
Becker\tbecker-county
Beltrami\tbeltrami-county
Benton\tbenton-county
Big Stone\tbig-stone-county
Blue Earth\tblue-earth-county
Brown\tbrown-county
Carlton\tcarlton-county
Carver\tcarver-county
Cass\tcass-county
Chippewa\tchippewa-county
Chisago\tchisago-county
Clay\tclay-county
Clearwater\tclearwater-county
Cook\tcook-county
Cottonwood\tcottonwood-county
Crow Wing\tcrow-wing-county
Dakota\tdakota-county
Dodge\tdodge-county
Douglas\tdouglas-county
Faribault\tfaribault-county
Fillmore\tfillmore-county
Freeborn\tfreeborn-county
Goodhue\tgoodhue-county
Grant\tgrant-county
Hennepin\thennepin-county
Houston\thouston-county
Hubbard\thubbard-county
Isanti\tisanti-county
Itasca\titasca-county
Jackson\tjackson-county
Kanabec\tkanabec-county
Kandiyohi\tkandiyohi-county
Kittson\tkittson-county
Koochiching\tkoochiching-county
Lac qui Parle\tlac-qui-parle-county
Lake\tlake-county
Lake of the Woods\tlake-of-the-woods-county
Le Sueur\tle-sueur-county
Lincoln\tlincoln-county
Lyon\tlyon-county
Mahnomen\tmahnomen-county
Marshall\tmarshall-county
Martin\tmartin-county
McLeod\tmcleod-county
Meeker\tmeeker-county
Mille Lacs\tmille-lacs-county
Morrison\tmorrison-county
Mower\tmower-county
Murray\tmurray-county
Nicollet\tnicollet-county
Nobles\tnobles-county
Norman\tnorman-county
Olmsted\tolmsted-county
Otter Tail\totter-tail-county
Pennington\tpennington-county
Pine\tpine-county
Pipestone\tpipestone-county
Polk\tpolk-county
Pope\tpope-county
Ramsey\tramsey-county
Red Lake\tred-lake-county
Redwood\tredwood-county
Renville\trenville-county
Rice\trice-county
Rock\trock-county
Roseau\troseau-county
St. Louis\tsaint-louis-county
Scott\tscott-county
Sherburne\tsherburne-county
Sibley\tsibley-county
Stearns\tstearns-county
Steele\tsteele-county
Stevens\tstevens-county
Swift\tswift-county
Todd\ttodd-county
Traverse\ttraverse-county
Wabasha\twabasha-county
Wadena\twadena-county
Waseca\twaseca-county
Washington\twashington-county
Watonwan\twatonwan-county
Wilkin\twilkin-county
Winona\twinona-county
Wright\twright-county
Yellow Medicine\tyellow-medicine-county""")

# WISCONSIN (72 counties)
add_counties("WI", "wisconsin", """Adams\tadams-county
Ashland\tashland-county
Barron\tbarron-county
Bayfield\tbayfield-county
Brown\tbrown-county
Buffalo\tbuffalo-county
Burnett\tburnett-county
Calumet\tcalumet-county
Chippewa\tchippewa-county
Clark\tclark-county
Columbia\tcolumbia-county
Crawford\tcrawford-county
Dane\tdane-county
Dodge\tdodge-county
Door\tdoor-county
Douglas\tdouglas-county
Dunn\tdunn-county
Eau Claire\teau-claire-county
Florence\tflorence-county
Fond du Lac\tfond-du-lac-county
Forest\tforest-county
Grant\tgrant-county
Green\tgreen-county
Green Lake\tgreen-lake-county
Iowa\tiowa-county
Iron\tiron-county
Jackson\tjackson-county
Jefferson\tjefferson-county
Juneau\tjuneau-county
Kenosha\tkenosha-county
Kewaunee\tkewaunee-county
La Crosse\tla-crosse-county
Lafayette\tlafayette-county
Langlade\tlanglade-county
Lincoln\tlincoln-county
Manitowoc\tmanitowoc-county
Marathon\tmarathon-county
Marinette\tmarinette-county
Marquette\tmarquette-county
Menominee\tmenominee-county
Milwaukee\tmilwaukee-county
Monroe\tmonroe-county
Oconto\toconto-county
Oneida\toneida-county
Outagamie\toutagamie-county
Ozaukee\tozaukee-county
Pepin\tpepin-county
Pierce\tpierce-county
Polk\tpolk-county
Portage\tportage-county
Price\tprice-county
Racine\tracine-county
Richland\trichland-county
Rock\trock-county
Rusk\trusk-county
St. Croix\tsaint-croix-county
Sauk\tsauk-county
Sawyer\tsawyer-county
Shawano\tshawano-county
Sheboygan\tsheboygan-county
Taylor\ttaylor-county
Trempealeau\ttrempealeau-county
Vernon\tvernon-county
Vilas\tvilas-county
Walworth\twalworth-county
Washburn\twashburn-county
Washington\twashington-county
Waukesha\twaukesha-county
Waupaca\twaupaca-county
Waushara\twaushara-county
Winnebago\twinnebago-county
Wood\twood-county""")

# ARIZONA (15 counties)
add_counties("AZ", "arizona", """Apache\tapache-county
Cochise\tcochise-county
Coconino\tcoconino-county
Gila\tgila-county
Graham\tgraham-county
Greenlee\tgreenlee-county
La Paz\tla-paz-county
Maricopa\tmaricopa-county
Mohave\tmohave-county
Navajo\tnavajo-county
Pima\tpima-county
Pinal\tpinal-county
Santa Cruz\tsanta-cruz-county
Yavapai\tyavapai-county
Yuma\tyuma-county""")

# Build new entries, skipping duplicates
new_entries = []
for abbrev, state_name, county_name, slug in COUNTIES:
    county_slug = slug.replace("-county", "")
    site_id = f"{abbrev.lower()}-{county_slug}"

    if site_id in existing_ids:
        continue

    new_entries.append({
        "site_id": site_id,
        "state": state_name,
        "legacy_slug": slug,
        "type": "county",
        "county": county_name,
    })
    existing_ids.add(site_id)

all_markets = existing + new_entries

print(f"Existing: {len(existing)}")
print(f"New county entries: {len(new_entries)}")
print(f"Total markets: {len(all_markets)}")

from collections import Counter
by_state = Counter(m["state"] for m in all_markets)
for state, count in sorted(by_state.items()):
    print(f"  {state}: {count}")

with open(MARKETS_FILE, "w") as f:
    json.dump(all_markets, f, indent=2)

print("Written to config/markets.json")
