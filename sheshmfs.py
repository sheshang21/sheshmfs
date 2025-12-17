import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
import time
import io

warnings.filterwarnings('ignore')

st.set_page_config(page_title="Indian Stock Scout - LIVE Scanner", page_icon="🎯", layout="wide", initial_sidebar_state="expanded")

# Custom CSS - Dark mode compatible
st.markdown("""<style>
.main-header{font-size:2.5rem;font-weight:700;color:#1f77b4;text-align:center;margin-bottom:1rem}
.sub-header{font-size:1.5rem;font-weight:600;margin:1rem 0}
.metric-card{background:#f8f9fb;padding:0.8rem;border-radius:8px;border-left:4px solid #1f77b4;margin:0.5rem 0}

/* Dark mode fixes */
[data-testid="stDataFrame"] {
    background-color: transparent !important;
}
[data-testid="stDataFrame"] table {
    color: inherit !important;
}
[data-testid="stDataFrame"] th {
    background-color: #1f77b4 !important;
    color: white !important;
    font-weight: 600 !important;
}
/* Light mode table styles */
@media (prefers-color-scheme: light) {
    [data-testid="stDataFrame"] td {
        color: #000 !important;
    }
}
/* Dark mode table styles */
@media (prefers-color-scheme: dark) {
    [data-testid="stDataFrame"] td {
        color: #fff !important;
    }
    .metric-card {
        background: #262730 !important;
    }
}
</style>""", unsafe_allow_html=True)

# Your custom stock list
CUSTOM_STOCKS = """JSWHL CREATIVE KINGFA NGLFINE HITECHGEAR BOSCHLTD ABBOTINDIA BANARISUG ESABINDIA SEJALLTD TASTYBITE TEAMLEASE ASTRAZEN SUNDRMBRAK RPGLIFE SUMMITSEC JKCEMENT FINEORG YASHO KICL PILANIINVS ELECTHERM ZENITHEXPO CHEVIOT WELINV ACCELYA AUTOAXLES POLYCAB RISHABH ALICON VOLTAMP INNOVACAP BELLACASA TVSSRICHAK KIRLOSIND KIRLPNU RML UNIVAFOODS SANDESH ORISSAMINE GLOSTERLTD SUNCLAY SABTNL UNICHEMLAB AKZOINDIA HPIL DIXON RANEHOLDIN TVSHLTD ORIENTBELL LINCOLN LTIM SEAMECLTD PERSISTENT SALONA ETHOSLTD PFIZER PGHH DHANUKA EIMCOELECO GALAXYSURF CRISIL MTARTECH UEL MANORG BFUTILITIE POCL WHEELS RATNAMANI GRINDWELL NUVAMA JINDRILL SAFARI STEL NUCLEUS XPROINDIA TATVA PIXTRANS MAPMYINDIA INDIGOPNTS DVL KKCL DCMSHRIRAM MODIRUBBER CAPITALSFB SPECTRUM AIAENG FOSECOIND LIBERTSHOE HEUBACHIND SHIVATEX AARTISURF NILKAMAL INDOTHAI ASAL SMARTWORKS LAMBODHARA SASKEN SAHYADRI TRF HATSUN ADVENTHTL HIRECT FMGOETZE MEDICAMEQ SOTL DOMS JCHAC NITINSPIN KIRLOSBROS GILLETTE AXISCADES POKARNA INDOTECH BHARATGEAR KEI RPTECH BAJAJ-AUTO EIHAHOTELS SEMAC TRANSWORLD NPST NATCAPSUQ LT METROPOLIS ANURAS NEOGEN ANANDRATHI HEXATRADEX MADHAV CONTROLPR ROUTE SANOFI PALASHSECU NIBE PIGL NCLIND HYUNDAI SIEMENS DELTAMAGNT MAHASTEEL NAHARSPING RAMAPHO HINDUNILVR STOVEKRAFT MANOMAY ABREL BAJAJHCARE RAYMONDREL DREDGECORP SUNDROP HLEGLAS CHOICEIN SUYOG BUTTERFLY VENKEYS POWERMECH MANORAMA BHAGCHEM IITL FLUOROCHEM GUJAPOLLO STARPAPER ERIS GNA HPL AHCL HEROMOTOCO JUBLPHARMA DMART TIINDIA UNIVPHOTO SUPERHOUSE 20MICRONS SICALLOG GESHIP MALLCOM INSPIRISYS GRWRHITECH TVSMOTOR INDOSTAR IRIS BAJAJINDEF ELIN SHYAMTEL GHCLTEXTIL RESPONIND JINDALPOLY AWFIS TITAN IFGLEXPOR AMBER ENRIN GRMOVER CPPLUS SIGIND BANSWRAS ALKYLAMINE VIMTALABS CLSEL CHEMPLASTS ALKEM GFSTEELS LANCORHOL YUKEN EMUDHRA JPOLYINVST ZIMLAB NRAIL PSPPROJECT EUROBOND BHARATWIRE PNC RHL GVPIL ZODIAC MEDPLUS RELIGARE KPEL NAVA BOROLTD MARATHON MPHASIS NESTLEIND SIYSIL PODDARMENT JSLL NATHBIOGEN PRUDENT TCS BHARTIARTL XELPMOC TORNTPOWER ALLTIME MBEL BDL BIRLACORPN NACLIND DHUNINV CARERATING JINDALPHOT PRIVISCL DICIND SOLARINDS THYROCARE AURIONPRO HAVELLS CLEDUCATE AVADHSUGAR PRICOLLTD VINYLINDIA RACE TATACOMM THERMAX KAYA NAVINFLUOR VERANDA SRD NDRAUTO HDBFS KFINTECH CPEDU ONESOURCE AAREYDRUGS GRASIM ISHANCH SSWL OILCOUNTUB SYSTMTXC PIRAMALFIN GRSE MUTHOOTFIN TIRUMALCHM KALPATARU BORORENEW GUJTHEM OBEROIRLTY GENSOL AMDIND UMIYA-MRO HARIOMPIPE ITDC VENUSPIPES DCM LTTS KMEW DYNPRO MMFL SIGNPOST GOLDENTOBC BBTC CHOLAHLDNG PNBHOUSING UFLEX JAGSNPHARM TARAPUR BHAGERIA HGM ARROWGREEN ONWARDTEC EMSLIMITED PREMEXPLN REPCOHOME SUNFLAG SWELECTES KSCL VARROC LGEINDIA KCP TATACONSUM NAUKRI HGINFRA PVRINOX CIPLA SUDARSCHEM DCMSRIND HITECHCORP HAPPSTMNDS PANACEABIO AVANTIFEED BERGEPAINT KRN ANGELONE INDIAMART MVGJL LAOPALA GANESHBE DIGISPICE PRAENG DOLPHIN SASTASUNDR VSSL APCOTEXIND ACI GALAPREC SUPRIYA PRESTIGE SINCLAIR HAL MAYURUNIQ MAGADSUGAR ACE SRHHYPOLTD MASFIN DALMIASUG AVALON VALIANTORG ENIL BGRENERGY ALKALI INDOCO WINDMACHIN ZYDUSWELL VOLTAS ESCORTS LLOYDSME EMAMIPAP NELCAST SARLAPOLY XCHANGING KHADIM SENORES RELCHEMQ PDSL IONEXCHANG DCAL INDOBORAX KROSS KRBL SKYGOLD MAMATA JGCHEM AJAXENGG COROMANDEL RKSWAMY SOUTHWEST BROOKS HONDAPOWER APLAPOLLO JBCHEPHARM WANBURY APOLLOHOSP QUADFUTURE WEIZMANIND ASTEC GODREJCP MONEYBOXX SFL SESHAPAPER LUXIND SKMEGGPROD ARSSBL INDIGO MARALOVER STCINDIA UCAL RATNAVEER IVP TOKYOPLAST AJANTPHARM SBILIFE ATLANTAELE ACUTAAS FAIRCHEMOR BBOX DEEPAKFERT LAURUSLABS SHREERAMA KOKUYOCMLN TEXMOPIPES AERONEU TIL ASAHIINDIA MINDACORP AVL MANKIND PAKKA KRONOX AUSOMENT CHEMCON MUNJALSHOW BIOFILCHEM SHREYANIND BLUEJET HBLENGINE KOTAKBANK TRANSRAILL M&M CENTUM HSCL NRBBEARING GANDHAR FINKURVE DREAMFOLKS AKSHARCHEM DIGIDRIVE BLUSPRING BLACKBUCK RVTH IIFL AMBUJACEM GRAPHITE SANATHAN OMINFRAL NAHARINDUS DEVIT MIRCELECTR REGENCERAM KANSAINER FEDFINA TIGERLOGS KEYFINSERV CRAMC ORKLAINDIA TRIVENI MODISONLTD COHANCE SUNTV SUNTECK ONELIFECAP INDIANCARD GULPOLY KRITI MHLXMIRU EBGNG DOLLAR REDINGTON DODLA EIDPARRY NAGREEKEXP DBOL ORIENTELEC CCCL UDS RUPA PROSTARM KAYNES STARHEALTH TRITURBINE KALYANKJIL DDEVPLSTIK SURAJEST PRAJIND INOXGREEN POONAWALLA NOVAAGRI TNTELE GTPL EMMBI SURANAT&P RSSOFTWARE HIMATSEIDE DEEDEV MAXHEALTH INDIANHUME STARTECK PROTEAN VMART COCHINSHIP BECTORFOOD TOLINS ANUHPHR LXCHEM MAGNUM VASWANI DOLATALGO ATAM RELTD IMAGICAA CUB ATLASCYCLE THEMISMED EKC QUESS BLAL POLICYBZR 5PAISA GANESHCP KIMS LENSKART SANGHVIMOV ADVANCE SHEKHAWATI SKIPPER HDFCLIFE LICI SPECIALITY BAJAJELEC SURYALAXMI KPIL SURAKSHA SHREEPUSHK DABUR APEX BODALCHEM BYKE RPPINFRA TARMAT RITES URBANCO BPL COMPUSOFT BALAJITELE SMLT CALSOFT HERCULES TREJHARA LPDC EXCELINDUS WOCKPHARMA PATANJALI PICCADIL VAIBHAVGBL EPACKPEB WABAG PREMIERENE AHLUCONT CHENNPETRO FABTECH MARKSANS APCL ADL TREEHOUSE MANAKALUCO PASUPTAC QUICKHEAL HERITGFOOD APOLLO GKENERGY ZUARIIND SOMANYCERA FLAIR SHANTIGEAR NYKAA NATIONALUM TI LTF SAKSOFT TRUALT STYL GUJGASLTD APOLLOTYRE LICHSGFIN HINDALCO GUJALKALI SUNDARMFIN OMAXE RAJTV EQUIPPP GREAVESCOT MUKTAARTS MAHEPC VRAJ AURUM BLSE GLOBALE A2ZINFRA SAMHI SUPREME GFLLIMITED ATL BRIGHOTEL GPTINFRA BAGFILMS CCHHL JTEKTINDIA SHAREINDIA PPLPHARMA SETCO DHAMPURSUG RAJESHEXPO MAXIND BIGBLOC AXISBANK VEDL AADHARHFC IGIL NLCINDIA STLTECH EIEL AVTNPL ADSL PRAKASH SGLTL MOSCHIP TPLPLASTEH PRECAM DCBBANK COASTCORP ISGEC SAATVIKGL ICICIPRULI ABCAPITAL MANBA ITI SCI SYMPHONY AWL FSL ABDL FAZE3Q TATATECH INDUSINDBK GMDCLTD SBGLP 3PLAND MORARJEE JAMNAAUTO REGAAL INTLCONV KITEX ADVANIHOTR FELDVR BLBLIMITED MANUGRAPH INDORAMA NFL JMFINANCIL PARACABLES UFO BHAGYANGR PILITA NARMADA MBLINFRA MADRASFERT KARURVYSYA AFSL TIJARIA IBULLSLTD GULFPETRO SHREDIGCEM DHANBANK MURUDCERA BLKASHYAP LUMAXIND MEGASTAR SALZERELEC TVSELECT POWERGRID PLATIND JSWINFRA EPACK SOLARWORLD SAMMAANCAP ITC EIHOTEL STERTOOLS ASKAUTOLTD OIL MOIL APTECHT PTL PRIMO GATEWAY OSWALGREEN ESSARSHPNG HEADSUP RUCHINFRA USK DIGITIDE SPORTKING CYBERTECH BELRISE HISARMETAL PINELABS SHRINGARMS ASHOKA BOMDYEING BHARATSE AFCONS VEEDOL GMMPFAUDLR SMSLIFE LODHA MIDWESTLTD DEEPAKNTR GODFRYPHLP AROGRANITE DAMODARIND ARIHANTCAP SBFC SMARTLINK ADFFOODS ESTER SPMLINFRA SELMC SADBHIN FMNL SCILAL KUANTUM NAVKARCORP DCW ATALREAL FLFL JAYSREETEA MANAKSTEEL ANDHRAPAP VMSTMT WCIL GEMAROMA TARC ENGINERSIN JKIPL NBCC ENERGYDEV ROML JHS VIRINCHI BANKINDIA ASHOKLEY FIBERWEB GROWW LAXMIINDIA SAURASHCEM CONFIPET MFML HINDOILEXP MUKKA SHANTIGOLD SABEVENTS ALANKIT AKI HAVISHA PIONEEREMB MSPL BALAJEE SHYAMMETL WELCORP MUTHOOTCAP PLASTIBLEN TMB RVNL PACEDIGITK NAZARA TMCV NTPC RAJRATAN KPIGREEN EPL VBL EMIL PDMJEPAPER VIPIND CUBEXTUB STALLION HERANBA BANG SHIVAMAUTO RHETAN PRITIKAUTO KAMDHENU ASHIMASYN COMPINFO MKPL ORIENTCER SAMBHV MUFIN OCCLLTD DBREALTY AVANTEL SHARDAMOTR YATHARTH PITTIENG EMCURE CSBBANK BAJFINANCE ASIANENE GREENPLY PIDILITIND DTIL BORANA MMTC DUCON RADIOCITY CTE SINDHUTRAD SNOWMAN SIGACHI PRSMJOHNSN BLISSGVS MCLOUD EQUITASBNK CESC GPTHEALTH ASHOKAMET SANGHIIND MANINFRA HARDWYN RTNINDIA UJJIVANSFB SOUTHBANK SYNCOMF SUBEXLTD RAJOOENG CAMLINFINE CANBK WALCHANNAG BHANDARI ZENITHSTL SHAH NILAINFRA PATINTLOG SUPERSPIN NSLNISP PRECWIRE KANPRPLA PATELRMART YATRA SUMEETINDS DHRUV RUSHIL VIJIFIN INVENTURE DAVANGERE GAYAHWS BTML JPPOWER EASEMYTRIP HATHWAY TAKE DNAMEDIA COUNCODOS 3IINFOLTD SECURKLOUD PRAXIS HITECH SHRIRAMPPS ABFRL MOTHERSON VPRPL SHALPAINTS RAIN TRACXN GLOTTIS RICOAUTO NHPC IRFC NTPCGREEN TFCILTD ARCHIES RAMASTEEL TRIDENT HCC ORIENTPPR UCOBANK AFIL SUVIDHAA ESSENTIA VINNY STEELXIND SAKUMA MADHUCON SARVESHWAR FCSSOFT UNITECH PRAKASHSTL SALASAR IVC PARASPETRO NAGAFERT SAGILITY VASCONEQ PAISALO OLAELEC ROSSELLIND IRCON WIPRO NDLVENTURE AMBIKCO ICRA SONACOMS PARAGMILK RRKABEL BEL WENDT WEWIN WINDLAS AKUMS EDELWEISS GULFOILLUB GOPAL PFOCUS IGARASHI DBL NORTHARC SAPPHIRE RKFORGE USHAMART SAMPANN M&MFIN MOBIKWIK BALRAMCHIN TNPL INDOWIND AGARWALEYE CRIZAC BHEL RECLTD NOIDATOLL GMRAIRPORT KCPSUGIND DGCONTENT RTNPOWER VIVIDHA FILATFASH ROLTA URJA RHFL SUZLON YESBANK TCIEXP VGL ACL MRPL EDUCOMP ALLCARGO FCONSUMER AKSHAR GATECHDVR IMPEXFERRO SUNDARAM DISHTV NKIND NILASPACES BPCL PFC GMRP&UI TECILCHEM MUKANDLTD ALOKINDS CENTRALBK PCJEWELLER GTLINFRA VIKASLIFE VIKASECO BAJAJHIND KANORICHEM BCG AXITA GREENPOWER HDIL HPAL MIRZAINT KELLTONTEC RAYMONDLSL MEDICO MANCREDIT JKPAPER SWIGGY JAYBARMARU VISAKAIND MAZDOCK BSOFT INDHOTEL JKTYRE LAXMIDENTL JYOTHYLAB VIKRAMSOLR MAHABANK OSWALPUMPS PANAMAPET CLEAN SULA POLYPLEX RAMCOCEM LATENTVIEW ROSSARI INDIANB ADANIENSOL FEDERALBNK SANSERA STEELCAS JUBLINGREA JSWSTEEL IDEAFORGE CREDITACC GANESHHOU UTIAMC MEDANTA AYMSYNTEX EMAMIREAL ORICONENT DWARKESH IRB PFS GOYALALUM SADBHAV SEPC SHYAMCENT ZEEMEDIA JYOTISTRUC HLVLTD IDEA NDL ORCHASP PARSVNATH TRU GENUSPAPER GATECH ROLLT KANANIIND SETUINFRA SKIL TPHQ ANKITMETAL GVKPIL KAMOPAINTS KESORAMIND ALMONDZ VAKRANGEE SBC KHANDSE AIRAN VIKRAN MANALIPETC CASTROLIND ADANIPOWER SHAHALLOYS IFCI JAGRAN TTML MSUMI ELECTCAST GTL TFL RETAIL RANASUG FCL UTKARSHBNK ABINFRA ASMS RCOM NAVKARURB EXCEL ARSHIYA ANSALAPI KRIDHANINF WINSOME SVPGLOB LYPSAGEMS LLOYDSENT MTNL RPOWER PATELENG MCLEODRUSS INFIBEAM LEMONTREE SJVN SAIL IOB CYBERMEDIA VLEGOV PSB NGIL JETFREIGHT NECLIFE DHARAN KEEPLEARN GOLDTECH RGL WSI IOLCP RENUKA PNB JAIBALAJI GAIL NMDC HYBRIDFIN IDFCFIRSTB BAIDFIN JISLJALEQS BCLIND JSWCEMENT AEROFLEX GIPCL VMM ANDHRSUGAR AUTOIND CELEBRITY AKSHOPTFBR CAPTRUST UYFINCORP HTMEDIA GOKUL OMKARCHEM ZEELEARN VARDMNPOLY ACCURACY TTL IGCL CANHLIFE RBA HFCL SHEMAROO SPAL ATULAUTO JSWENERGY JIOFIN SBIN RAMCOSYS DYCL JSL UPL SHALBY NOCIL IEX EXICOM STARCEMENT AFFORDABLE HMT MAWANASUG SSDL MASTERTR PENINLAND BAJAJHFL NIVABUPA SANSTAR AVONMORE IDBI ZEEL LLOYDSENGG JTLIND WEBELSOLAR SIGMA ODIGMA CEREBRAINT ALPSINDUS MTEDUCARE FLEXITUFF EXXARO HCL-INSYS BASML KOHINOOR MOREPENLAB BESTAGRO CYIENTDLM MINDTECK MIDHANI JWL CROMPTON SEQUENT HUDCO TMPV COALINDIA CHAMBLFERT BANKBARODA CAMPUS ETERNAL AARTIIND HINDCOPPER ACMESOLAR VINCOFE SHREEJISPG EMAMILTD SARDAEN TEJASNET ANTHEM CARBORUNIV INFY FILATEX BRNL MOTISONS GOENKA IL&FSTRANS SUVEN GEOJITFSL ABLBL NETWORK18 DELTACORP IREDA RADHIKAJWE INOXWIND J&KBANK LOTUSDEV DCXINDIA PTC SDBL TATASTEEL ASIANTILES ORIENTCEM IOC SITINET NECCLTD SAKHTISUG KMSUGAR MOTOGENFIN VISHWARAJ MGEL INDBANK AMBICAAGAR GSS NDTV PVSL FINPIPE KALAMANDIR HILINFRA HMAAGRO STLNETWORK MICEL HILTON XTGLOBAL AMJLAND ANMOL ORIENTALTL UMESLTD SGL MEP ESAFSFB AVROIND UNIONBANK DIACABS NCC HUHTAMAKI SPLIL VIPULLTD ASTRON SAMBHAAV REMSONSIND SATIA HEMIPROP RADIANTCMS IGL JKIL GLAXO AUROPHARMA UNITDSPR CONCORDBIO AAVAS 63MOONS CGPOWER AARTIPHARM ADANIENT FINOPB GREENLAM BLS SPIC MAANALU VSTIND ITCHOTELS MUFTI RALLIS ALEMBICLTD JINDWORLD VSTL CEIGALL DBEIL PYRAMID TREL JPASSOCIAT BALKRISHNA UMAEXPORTS GINNIFILA ONMOBILE NAGREEKCAP JAYNECOIND KHAICHEM BCONCEPTS MONTECARLO REFEX ANANTRAJ APOLLOPIPE HDFCBANK BANDHANBNK GABRIEL TIMETECHNO INDIACEM EFCIL FIVESTAR MANGLMCEM AMRUTANJAN CANFINHOME KEC APARINDS BEPL DONEAR AGSTRA SADHNANIQ SURANASOL KTKBANK PARKHOTELS INDOFARM JINDALSAW NITCO SPENCERS FEL NEXTMEDIA INFOMEDIA DBSTOCKBRO DEVYANI EMBDL MARKOLINES JAICORPLTD FISCHER HMVL RUBFILA ORIENTHOT BMWVENTLTD CIFL RUBYMILLS NIACL REDTAPE TVVISION MUNJALAU SIL DEN CORALFINAC RUCHIRA PARADEEP IPCALAB EUROPRATIK NAM-INDIA RIIL JUSTDIAL INDGN GEECEE ARVSMART CUPID ARVIND PCBL AETHER RAILTEL TATACAP IRCTC LOKESHMACH GNFC BALUFORGE ARE&M VENTIVE SIMPLEXINF ELGIEQUIP SYRMA GAEL GAYAPROJ LCCINFOTEC GOKULAGRO PAVNAIND TEXRAIL CGCL SHK OMAXAUTO MOL KABRAEXTRU GOACARBON GENUSPOWER VGUARD HINDPETRO SGFIN PETRONET MAXESTATES TINNARUBR KRSNAA TBOTEK JUBLFOOD SPLPETRO WELSPUNLIV RADAAN PREMIER ORTEL DEVX ATLANTAA PNBGILTS AARTECH BGLOBAL SURYODAY SANDUMA GSFC VINEETLAB ORTINGLOBE QUINTEGRA NIRAJ ROLEXRINGS WEL DJML SATIN SMCGLOBAL AEROENTER RCF THEINVEST CINEVISTA ROTO ANUP BAJAJFINSV HEXT BLUESTONE ANTELOPUS WONDERLA APTUS RBLBANK AGIIL TIPSMUSIC GENESYS INDOAMIN CMSINFO OAL NUVOCO SONATSOFTW HINDZINC STANLEY TGBHOTELS ARCHIDPLY KAVDEFENCE CENTRUM INCREDIBLE HEIDELBERG SWSOLAR DLF FORTIS IXIGO PAYTM DALBHARAT RAMRAT SKFINDIA ENDURANCE SANWARIA GENCON CENTEXT UFBL ARISINFRA ORIENTLTD PREMIERPOL DRCSYSTEMS SALSTEEL GPPL PLAZACABLE DIGJAMLMTD CMICABLES RAMANEWS TCIFINANCE TRIGYN MANGALAM ORCHPHARMA SIS MATRIMONY DLINKINDIA JARO PURVA ZENSARTECH EXIDEIND JASH SANDHAR THOMASCOOK KECL SYNGENE SHANKARA WSTCSTPAPR PASHUPATI MSTCLTD TATAPOWER LUPIN VHLTD ABAN CAPACITE MAHLIFE TARIL PNCINFRA STYLEBAAZA ZUARI GOCLCORP SURAJLTD BAJAJCON ADANIPORTS AVG GARUDA ELLEN WAAREERTL RPSGVENT KIRLOSENG HEG VISHNU BLUESTARCO CERA PVP VIPCLOTHNG NIITLTD FOODSIN ALPA SIMBHALS PRABHA DPWIRES SCODATUBES UGARSUGAR MANAKCOAT TVSSCS INDIQUBE ADROITINFO LAL RAJRILTD TNPETRO LALPATHLAB TERASOFT MGL CONCOR ARTEMISMED SOLARA RUBICON GSLSU PENIND NAVNETEDUL VETO INDTERRAIN VTL VRLLOG RELAXO TAJGVK SPANDANA IVALUE SMSPHARMA FIRSTCRY CSLFINANCE MHRIL GICHSGFIN INDUSTOWER ZAGGLE PRINCEPIPE MANAPPURAM AEGISLOG MARICO WEWORK SRF BANARBEADS LYKALABS ISFT TEXINFRA LASA DAMCAPITAL BOROSCI BIRLACABLE TBZ OSWALAGRO CREATIVEYE ICICIGI LUMAXTECH ICICIBANK CAPLIPOINT ICIL PRIMESECU ONGC COFFEEDAY PEARLPOLY ATHERENERG RUSTOMJEE DIFFNKG HUBTOWN MOTILALOFS FDC SAILIFE FACT KIRIINDUS RSYSTEMS RNBDENIMS SUTLEJTEX SAGCEM GLOBECIVIL BAJEL ORBTEXP SPARC GLFL ABCOTS ASALCBR SIRCA SAREGAMA IRMENERGY SUPRAJIT BALMLAWRIE HONASA RHIM GSPL VESUVIUS MAHSEAMLES SANGAMIND SURYAROSNI LANDMARK GARFIBRES GOCOLORS ALBERTDAVD GILLANDERS RSWM BIRLAMONEY WILLAMAGOR GPIL DATAMATICS RELIANCE KAJARIACER PGEL DRREDDY SBICARD IKIO MANAKSIA RBZJEWEL HIKAL TATAINVEST NIPPOBATRY THELEELA ECOSMOBLTY GOLDIAM SENCO IL&FSENGG AAATECH ACC INTELLECT TANLA NATCOPHARM ABSLAMC ATGL SHRIRAMFIN HCLTECH SHAKTIPUMP TEGA DCMFINSERV SCHAND MOHITIND NESCO TATAELXSI UNIMECH CANTABIL SHAILY ATUL MFSL BHARTIHEXA AMANTA RAYMOND BEML GICRE CHOLAFIN GODIGIT RKDL GREENPANEL KOTHARIPRO AARTIDRUGS KPITTECH 360ONE GODREJPROP ROSSTECH ARVINDFASN WHIRLPOOL DELHIVERY JKLAKSHMI BFINVEST BANSALWIRE INDSWFTLAB BILVYAPAR STUDDS ASTERDM AUBANK TITAGARH JNKINDIA AEGISVOPAK BIOCON DBCORP IPL KNRCON HINDWAREAP DHARMAJ SWANCORP IIFLCAPS JBMA ASHAPURMIN VENUSREM KOPRAN JISLDVREQS UNIECOM OBCL INDIAGLYCO WAAREEENER CELLO DENTA JAINREC ORIENTTECH GHCL GALLANTT SHILPAMED KSOLVES MALUPAPER LOVABLE MOLDTECH TICL ARENTERP OMFREIGHT COSMOFIRST DEEPINDS BLUECHIP GODAVARIB AHLEAST HARSHA SHOPERSTOP FINCABLES COFORGE CYIENT TECHM BIRLANU ARKADE RAJSREESUG BVCL CINELINE ANIKINDS ASIANPAINT TATACHEM PARAS TALBROAUTO CHEMBOND HBSL MUTHOOTMF MANYAVAR ASTRAMICRO WELENT NEWGEN POLYMED KRITINUT PRUDMOULI SOMICONVEY CIGNITITEC JUNIPER BANCOINDIA ARFIN GRANULES LORDSCHLO ADANIGREEN LTFOODS ADVENZYMES SUMICHEM LOYALTEX MEDIASSIST INNOVANA SGMART EUREKAFORB VALIANTLAB GLOBALVECT GANDHITUBE CREST CHALET SHARDACROP SUNDRMFAST SRM ALPHAGEO TEAMGTY SHIVAMILLS NIBL JITFINFRA HCG BHARATFORG LIKHITHA FUSION PROZONER ZODIACLOTH SREEL AGI KSB CARRARO PNGJL TVTODAY BBTCL LINC RITCO UNIPARTS GOKEX WESTLIFE GODREJAGRO RAMKY DSSL BRIGADE UTTAMSUGAR MENONBE DCI KPRMILL PHOENIXLTD BALKRISIND ASTRAL FIEMIND GLENMARK RAJVIR CCL ROHLTD HGS ARIES AWHCL PPAP GRINFRA TECHNOE BATAINDIA OPTIEMUS KHAITANLTD AGRITECH MPSLTD INTENTECH INDRAMEDCO VLSFINANCE ZYDUSLIFE TTKPRESTIG MONARCH RELINFRA RAINBOW INDNIPPON ELECON SJS RATEGAIN EVEREADY TDPOWERSYS AMNPLST BRITANNIA CEATLTD SUKHJITS BALPHARMA LAKPRE BALAMINES LGBBROSLTD SBCL NIITMTS KAKATCEM TARSONS SUBROS GODREJIND FORCEMOT TRENT EXPLEOSOL ENTERO SUNPHARMA AFFLE COMSYN MEIL CORDSCABLE BIKAJI RPEL INFOBEAN 21STCENMGM HARRMALAYA ARIHANTSUP URAVIDEF PONNIERODE KILITCH JAYAGROGN GANECOS ARMANFIN OLECTRA IGPL DPABHUSHAN NETWEB GRAVITA AZAD RAMCOIND CIEINDIA SCHNEIDER SEYAIND KERNEX EVERESTIND DIAMINESQ CPCAP NORBTEAEXP CHEMBONDCH IKS THOMASCOTT JINDALSTEL JYOTICNC ASHIANA DMCC INDIASHLTR VIJAYA NH KREBSBIO KAMATHOTEL GMBREW KRYSTAL CENTURYPLY WAAREEINDO APLLTD S&SPOWER RADICO COLPAL MEGASOFT INDOUS SILVERTUC IMFA SECMARK MANINDS RELIABLE MAHLOG MAHAPEXLTD BEDMUTHA THANGAMAYL JSFB QPOWER MOLDTKPAC ZENTEC VISASTEEL KOLTEPATIL ASIANHOTNR GLOBUSSPR BBL UNIENTER DCMNVL UNOMINDA CEMPRO IZMO HAPPYFORGE CHEMFAB VIDHIING NELCO V2RETAIL GUJRAFFIA KIOCL INSECTICID SCHAEFFLER EICHERMOT SHIVALIK PALREDTEC SOBHA PGIL TCPLPACK VSTTILLERS SRGHFL RVHL EUROTEXIND STYRENIX NINSYS UNIVCABLES UGROCAP KARMAENG DELPHIFX ALIVUS STAR METROBRAND CARTRADE CAMS DECCANCE BLUECOAST CEWATER SOMATEX PIIND TAINWALCHM OFSS BASF HDFCAMC DIVISLAB DATAPATTNS AGARIND LOTUSEYE GVT&D VINATIORGA HNDFDS TRAVELFOOD IMPAL GLAND REPRO UBL MODTHREAD CARYSIL MAZDA DIVGIITTS ICDSLTD IFBAGRO INOXINDIA KAUSHALYA KSL SCPL GOODLUCK RACLGEAR HINDCOMPOS VADILALIND TIIL PUNJABCHEM HOMEFIRST MAITHANALL SUPREMEIND UNIDT INTERARCH SIGNATURE CUMMINSIND JLHL CENTENKA TTKHLTCARE STYLAMIND DIAMONDYD EPIGRAL LINDEINDIA WORTHPERI MASTEK SOFTTECH TORNTPHARM GRPLTD TCI BAFNAPH DENORA NAHARCAP IFBIND ADOR ASAHISONG ABB SMLMAH NAHARPOLY NEULANDLAB CRAFTSMAN BLUEDART BSL NURECA SILINV SHRIPISTON SUPREMEINF SGIL KDDL AIIL MCX BIL GUFICBIO ALLDIGI AJMERA TIPSFILMS SANOFICONR MARUTI BAYERCROP KALYANIFRG LMW HESTERBIO NSIL TIMKEN GCSL PTCIL ECLERX VINDHYATEL GANGESSECU EMKAY ULTRACEMCO SWARAJENG ZFCVINDIA PAGEIND INGERRAND BAJAJHLDNG KRISHIVAL BHARATRAS POWERINDIA DYNAMATECH CURAA PGHL MAHSCOOTER JUBLCPL HONAUT SHREECEM SWANDEF ELDEHSG FOCUS WEALTH 3MINDIA VHL MRF KALYANI"""

NSE_STOCKS = [s.strip() for s in CUSTOM_STOCKS.split() if s.strip()]

SECTOR_MAP = {}  # Will be populated from your list

@st.cache_data(ttl=60)  # Cache for 60 seconds only - fresher data
def fetch_stock_data(symbol):
    """Fetch real-time data from Yahoo Finance"""
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        hist = ticker.history(period="3mo", interval="1d")
        
        if hist.empty:
            return None
        
        closes = hist['Close'].values
        volumes = hist['Volume'].values
        
        price = closes[-1]
        prev_close = closes[-2] if len(closes) > 1 else price
        change = ((price - prev_close) / prev_close) * 100
        
        rsi = calculate_rsi(closes)
        macd = calculate_macd(closes)
        bb_position = calculate_bb_position(closes)
        vol_multiple = calculate_volume_multiple(volumes)
        trend = detect_trend(closes)
        
        return {
            'symbol': symbol,
            'price': price,
            'change': change,
            'rsi': rsi,
            'macd': macd,
            'bb_position': bb_position,
            'vol_multiple': vol_multiple,
            'trend': trend
        }
    except Exception as e:
        return None

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculate_macd(prices):
    if len(prices) < 26:
        return 0
    ema12 = calculate_ema(prices, 12)
    ema26 = calculate_ema(prices, 26)
    return ema12 - ema26

def calculate_ema(prices, period):
    multiplier = 2 / (period + 1)
    ema = np.mean(prices[:period])
    for price in prices[period:]:
        ema = (price - ema) * multiplier + ema
    return ema

def calculate_bb_position(prices, period=20):
    if len(prices) < period:
        return 50
    recent = prices[-period:]
    sma = np.mean(recent)
    std = np.std(recent)
    upper = sma + (2 * std)
    lower = sma - (2 * std)
    current = prices[-1]
    if upper == lower:
        return 50
    position = ((current - lower) / (upper - lower)) * 100
    return max(0, min(100, position))

def calculate_volume_multiple(volumes):
    if len(volumes) < 20:
        return 1.0
    current = volumes[-1]
    avg20 = np.mean(volumes[-20:])
    if avg20 == 0:
        return 1.0
    return current / avg20

def detect_trend(prices):
    if len(prices) < 5:
        return 'Sideways'
    recent = prices[-5:]
    ups = sum(1 for i in range(1, len(recent)) if recent[i] > recent[i-1])
    if ups >= 4:
        return 'Strong Uptrend'
    elif ups >= 3:
        return 'Uptrend'
    elif ups <= 1:
        return 'Downtrend'
    else:
        return 'Sideways'

def analyze_stock(data, criteria_config):
    """Analyze stock with VERY HARD criteria"""
    if not data:
        return None
    
    price = data['price']
    change = data['change']
    rsi = data['rsi']
    macd = data['macd']
    bb = data['bb_position']
    vol = data['vol_multiple']
    trend = data['trend']
    
    potential_rs = max(20, price * 0.05)
    potential_pct = (potential_rs / price) * 100
    
    score = 0
    criteria = []
    
    # Scoring logic (same as before)
    if potential_rs >= 30 and potential_pct >= 7:
        score += 20
        criteria.append(f'✅ Potential: Excellent [20 pts]')
    elif potential_rs >= 25 and potential_pct >= 6:
        score += 15
        criteria.append(f'✅ Potential: Very Good [15 pts]')
    elif potential_rs >= 20 and potential_pct >= 5:
        score += 10
        criteria.append(f'⚠️ Potential: Good [10 pts]')
    else:
        criteria.append(f'❌ Potential: Low [0 pts]')
    
    if 58 <= rsi <= 65:
        score += 25
        criteria.append(f'✅ RSI: Perfect ({rsi:.0f}) [25 pts]')
    elif 52 <= rsi <= 68:
        score += 18
        criteria.append(f'✅ RSI: Strong ({rsi:.0f}) [18 pts]')
    elif 35 <= rsi <= 42:
        score += 20
        criteria.append(f'✅ RSI: Oversold ({rsi:.0f}) [20 pts]')
    elif 45 <= rsi <= 55:
        score += 12
        criteria.append(f'⚠️ RSI: Neutral ({rsi:.0f}) [12 pts]')
    else:
        criteria.append(f'❌ RSI: Weak ({rsi:.0f}) [0 pts]')
    
    if macd > 10:
        score += 20
        criteria.append(f'✅ MACD: Very Strong [20 pts]')
    elif macd > 5:
        score += 15
        criteria.append(f'✅ MACD: Strong [15 pts]')
    elif macd > 0:
        score += 10
        criteria.append(f'⚠️ MACD: Bullish [10 pts]')
    else:
        criteria.append(f'❌ MACD: Bearish [0 pts]')
    
    if 15 <= bb <= 30:
        score += 15
        criteria.append(f'✅ BB: Lower band [15 pts]')
    elif 60 <= bb <= 75:
        score += 12
        criteria.append(f'✅ BB: Upper band [12 pts]')
    elif 40 <= bb <= 55:
        score += 8
        criteria.append(f'⚠️ BB: Middle [8 pts]')
    else:
        criteria.append(f'❌ BB: Extreme [0 pts]')
    
    if vol >= 3.0:
        score += 20
        criteria.append(f'✅ Volume: Massive ({vol:.1f}x) [20 pts]')
    elif vol >= 2.5:
        score += 15
        criteria.append(f'✅ Volume: Very High ({vol:.1f}x) [15 pts]')
    elif vol >= 2.0:
        score += 12
        criteria.append(f'✅ Volume: High ({vol:.1f}x) [12 pts]')
    elif vol >= 1.5:
        score += 8
        criteria.append(f'⚠️ Volume: Above Avg ({vol:.1f}x) [8 pts]')
    else:
        criteria.append(f'❌ Volume: Low ({vol:.1f}x) [0 pts]')
    
    if trend == 'Strong Uptrend':
        score += 15
        criteria.append(f'✅ Trend: Strong Uptrend [15 pts]')
    elif trend == 'Uptrend':
        score += 10
        criteria.append(f'✅ Trend: Uptrend [10 pts]')
    elif trend == 'Sideways':
        score += 3
        criteria.append(f'⚠️ Trend: Sideways [3 pts]')
    else:
        criteria.append(f'❌ Trend: Downtrend [0 pts]')
    
    if change >= 5:
        score += 10
        criteria.append(f'✅ Daily: Exceptional ({change:+.1f}%) [10 pts]')
    elif change >= 3:
        score += 8
        criteria.append(f'✅ Daily: Strong ({change:+.1f}%) [8 pts]')
    elif change >= 2:
        score += 5
        criteria.append(f'✅ Daily: Good ({change:+.1f}%) [5 pts]')
    elif change >= 0:
        score += 2
        criteria.append(f'⚠️ Daily: Slight ({change:+.1f}%) [2 pts]')
    else:
        criteria.append(f'❌ Daily: Negative ({change:+.1f}%) [0 pts]')
    
    if score >= 90:
        status = '🌟 EXCELLENT'
        rating = 'Excellent'
    elif score >= 80:
        status = '💎 VERY GOOD'
        rating = 'Very Good'
    elif score >= 70:
        status = '✅ GOOD'
        rating = 'Good'
    elif score >= 65:
        status = '👍 FAIR'
        rating = 'Fair'
    elif score >= 55:
        status = '⚠️ WATCHLIST'
        rating = 'Watchlist'
    else:
        status = '❌ POOR'
        rating = 'Poor'
    
    qualified = score >= 70
    met_count = len([c for c in criteria if '✅' in c])
    
    return {
        'symbol': data['symbol'],
        'price': price,
        'change': change,
        'potential_rs': potential_rs,
        'potential_pct': potential_pct,
        'rsi': rsi,
        'macd': macd,
        'bb': bb,
        'vol': vol,
        'trend': trend,
        'score': score,
        'qualified': qualified,
        'status': status,
        'rating': rating,
        'criteria': criteria,
        'met_count': met_count,
        'sector': SECTOR_MAP.get(data['symbol'], 'Other')
    }

# Main App
st.markdown('<p class="main-header">🎯 Indian Stock Scout - LIVE AUTO-REFRESH Scanner</p>', unsafe_allow_html=True)
st.markdown("**Strict criteria | Auto-updates every 60 seconds | Dark mode optimized**")

# Sidebar
st.sidebar.header("⚙️ Configuration")

auto_refresh = st.sidebar.checkbox("🔄 Auto-Refresh (60s)", value=True,
    help="Automatically refresh data every 60 seconds")

if auto_refresh:
    st.sidebar.success("✅ Auto-refresh enabled")
    # Auto-refresh every 60 seconds
    st.empty()
    time.sleep(0.1)

scan_mode = st.sidebar.radio("Scan Mode", 
    ["Quick (100 stocks)", "Medium (500 stocks)", "Full (All stocks)"])

if scan_mode == "Quick (100 stocks)":
    stocks_to_scan = NSE_STOCKS[:100]
elif scan_mode == "Medium (500 stocks)":
    stocks_to_scan = NSE_STOCKS[:500]
else:
    stocks_to_scan = NSE_STOCKS

st.sidebar.info(f"Will scan: {len(stocks_to_scan)} stocks")

if 'scan_results' not in st.session_state:
    st.session_state.scan_results = None
    st.session_state.last_scan = None

# Auto-scan button
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("🚀 SCAN NOW", type="primary", use_container_width=True):
        st.session_state.trigger_scan = True
        st.rerun()

with col2:
    if st.button("🗑️ Clear", use_container_width=True):
        st.session_state.scan_results = None
        st.session_state.last_scan = None
        st.rerun()

# Auto-refresh logic
if auto_refresh and st.session_state.scan_results:
    if st.session_state.last_scan:
        time_since = (datetime.now() - st.session_state.last_scan).seconds
        if time_since >= 60:
            st.session_state.trigger_scan = True
            st.rerun()

# Perform scan
if st.session_state.get('trigger_scan', False):
    st.session_state.trigger_scan = False
    
    st.markdown("---")
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    results = []
    total = len(stocks_to_scan)
    
    for idx, symbol in enumerate(stocks_to_scan):
        status_text.info(f"📊 {symbol}... ({idx+1}/{total})")
        
        data = fetch_stock_data(symbol)
        if data:
            analysis = analyze_stock(data, {})
            if analysis:
                results.append(analysis)
        
        progress_bar.progress((idx + 1) / total)
        time.sleep(0.05)  # Faster scanning
    
    st.session_state.scan_results = results
    st.session_state.last_scan = datetime.now()
    
    status_text.success(f"✅ Complete! {len(results)} stocks analyzed")
    time.sleep(1)
    status_text.empty()
    progress_bar.empty()
    
    st.rerun()

# Display results
if st.session_state.scan_results:
    results = st.session_state.scan_results
    last_scan = st.session_state.last_scan
    
    if auto_refresh:
        time_since = (datetime.now() - last_scan).seconds
        next_refresh = max(0, 60 - time_since)
        st.info(f"🔄 Last updated: {last_scan.strftime('%H:%M:%S')} | Next refresh in: {next_refresh}s")
    
    df = pd.DataFrame([{
        'Symbol': r['symbol'],
        'Price': r['price'],
        'Change%': r['change'],
        'Potential₹': r['potential_rs'],
        'RSI': r['rsi'],
        'MACD': 'Bull' if r['macd'] > 0 else 'Bear',
        'Vol': f"{r['vol']:.1f}x",
        'Trend': r['trend'],
        'Score': r['score'],
        'Rating': r['rating']
    } for r in results])
    
    # Stats
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total", len(df))
    col2.metric("Excellent (≥90)", len(df[df['Score'] >= 90]))
    col3.metric("Good (≥70)", len(df[df['Score'] >= 70]))
    col4.metric("Avg Score", f"{df['Score'].mean():.1f}")
    
    st.markdown("---")
    
    # Filters
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    with filter_col1:
        rating_filter = st.selectbox("Rating", ["All", "Excellent", "Very Good", "Good", "Fair", "Watchlist", "Poor"])
    with filter_col2:
        trend_filter = st.selectbox("Trend", ["All", "Strong Uptrend", "Uptrend", "Sideways", "Downtrend"])
    with filter_col3:
        min_score = st.number_input("Min Score", 0, 100, 0, 5)
    
    filtered_df = df.copy()
    if rating_filter != "All":
        filtered_df = filtered_df[filtered_df['Rating'] == rating_filter]
    if trend_filter != "All":
        filtered_df = filtered_df[filtered_df['Trend'] == trend_filter]
    filtered_df = filtered_df[filtered_df['Score'] >= min_score]
    
    st.info(f"Showing {len(filtered_df)} / {len(df)} stocks")
    
    # Color-coded table
    def color_score(row):
        score = row['Score']
        if score >= 90:
            return ['background-color: #1a4d2e; color: white; font-weight: bold'] * len(row)
        elif score >= 80:
            return ['background-color: #2e7d32; color: white'] * len(row)
        elif score >= 70:
            return ['background-color: #66bb6a; color: black'] * len(row)
        elif score >= 65:
            return ['background-color: #ffeb3b; color: black'] * len(row)
        elif score >= 55:
            return ['background-color: #ff9800; color: white'] * len(row)
        else:
            return ['background-color: #d32f2f; color: white'] * len(row)
    
    styled_df = filtered_df.style.apply(color_score, axis=1)\
        .format({
            'Price': '₹{:.2f}',
            'Change%': '{:+.2f}%',
            'Potential₹': '₹{:.2f}',
            'RSI': '{:.1f}'
        })
    
    st.dataframe(styled_df, use_container_width=True, height=600)
    
    # Download
    st.markdown("---")
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        "📥 Download CSV",
        csv,
        f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        "text/csv",
        use_container_width=True
    )
    
    # Auto-refresh trigger
    if auto_refresh:
        time.sleep(1)
        st.rerun()

else:
    st.info("👈 Click 'SCAN NOW' or enable auto-refresh to begin")

st.markdown("---")
st.caption("🔄 Auto-refresh enabled | ⚡ Dark mode optimized | 📊 Strict criteria (≥70 to qualify)")
