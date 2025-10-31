
# Welcome to the Recipe Classifier Generator!
# This script classifies recipes takes as input RAW_recipes.csv into three types (plat, dessert, boisson) with confidence scores related.
# and outputs recipes_classified.csv with columns: id, name, type, conf_%
# FYI : Estimated running time : ~4 minutes 10 seconds

# I - Modules
import ast
from pathlib import Path
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder
import glob
import os
from tqdm import tqdm
from utils.logger import get_logger

log = get_logger(__name__)

# Progress bars are always enabled (no environment flags needed).

# Import configuration
from cooking_assistant.config import RAW_DATA_DIR, INTERIM_DATA_DIR

RAW_DIR = RAW_DATA_DIR  # Use centralized configuration

def latest_csv_with_prefix(prefix: str, directory: Path = RAW_DIR) -> Path:
    candidates = sorted(directory.glob(f"{prefix}_*.csv"))
    if not candidates:
        candidates = sorted(directory.glob(f"{prefix}.csv"))
    if not candidates:
        raise FileNotFoundError(f"No CSV files starting with '{prefix}' in {directory}")
    return max(candidates, key=lambda p: p.name)


# Find the CSV file that starts with RAW_recipes in the data/raw directory
try:
    csv_file = latest_csv_with_prefix('RAW_recipes')
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"Could not find {csv_file}. Please ensure the RAW_recipes.csv file is in the data/raw/ folder.")
    df = pd.read_csv(csv_file)
    print(f"Successfully loaded data from: {csv_file}")  # keep print
    log.info(f"Loaded raw recipes file: {csv_file}")
except Exception as e:
    log.exception("Failed loading raw recipes file")
    raise

# II - Data Processing & Feature Engineering

# ================== PHASE 0 (sweetness fix) → STRUCTURAL & ROBUST FEATURES ==================

eps = 1e-6  # we define a small constant to avoid division by zero

# --- Parse nutrition values if missing ---
# We check if key nutrient columns exist; if not, we extract them from the 'nutrition' field.
if not all(c in df.columns for c in ['cal','fat','sugar','sod','prot','sat','carbs']):
    def parse_nutrition(nut):
        try:
            arr = ast.literal_eval(nut) if isinstance(nut, str) else nut
            return pd.Series({
                'cal': float(arr[0]), 'fat': float(arr[1]), 'sugar': float(arr[2]),
                'sod': float(arr[3]), 'prot': float(arr[4]), 'sat': float(arr[5]),
                'carbs': float(arr[6]) if len(arr) > 6 else 0.0
            })
        except:
            # we return zeros if parsing fails
            return pd.Series({'cal':0, 'fat':0, 'sugar':0, 'sod':0, 'prot':0, 'sat':0, 'carbs':0})
    df[['cal','fat','sugar','sod','prot','sat','carbs']] = df['nutrition'].apply(parse_nutrition)

# --- Compute nutrient densities per calorie ---
# We normalize each nutrient by total calories to make all recipes comparable.
df['sugar_density'] = df['sugar'] / (df['cal'] + eps)   # we compute grams of sugar per kcal
df['prot_density']  = df['prot']  / (df['cal'] + eps)   # we compute grams of protein per kcal
df['sod_density']   = df['sod']   / (df['cal'] + eps)   # we compute milligrams of sodium per kcal
df['low_cal_flag']  = (df['cal'] < 150).astype(int)     # we flag recipes with low calorie count

# --- Compute energy shares for macronutrients ---
# We express the percentage of total energy that comes from each macronutrient.
df['fat_E%']  = (9 * df['fat'])   / (df['cal'] + eps)   # we use 9 kcal per gram of fat
df['carb_E%'] = (4 * df['carbs']) / (df['cal'] + eps)   # we use 4 kcal per gram of carbs
df['prot_E%'] = (4 * df['prot'])  / (df['cal'] + eps)   # we use 4 kcal per gram of protein

# === SWEETNESS-RELATED FEATURES ===

# We compute the proportion of energy from sugar (bounded between 0 and 1).
df['sugar_E%'] = (4 * df['sugar']) / (df['cal'] + eps)
df['sugar_E%'] = df['sugar_E%'].clip(0, 1)

# We compute the proportion of sugar among total carbohydrates,
# ensuring stability when total carbs are very low.
df['sugar_share_carb'] = df['sugar'] / (df['sugar'] + np.maximum(df['carbs'] - df['sugar'], 0) + eps)

# --- Build global indexes for taste profiles ---
# We combine sugar-related variables to create a global sweetness index.
df['sweet_idx']  = (0.55 * df['sugar_E%'] + 0.45 * df['sugar_density']).clip(0, 1)
# We combine protein and sodium densities to represent savoriness.
df['savory_idx'] = (0.55 * df['prot_density'] + 0.45 * (df['sod_density'] / 10.0)).clip(0, 1)
# (we divide sodium density by 10 to rescale mg/kcal to a comparable range)

# --- Identify hybrid taste profiles ---
# We capture recipes that are both sweet and savory at once.
df['hybrid_idx'] = np.minimum(df['sweet_idx'], df['savory_idx'])

# --- Compute leanness indicator ---
# We measure how “lean” a recipe is: high values mean low fat energy contribution.
df['lean_idx'] = (1.0 - df['fat_E%']).clip(0, 1)

# --- Clean and stabilize values ---
# We replace infinities or NaNs by 0, and ensure all values are non-negative.
for c in ['sugar_density','prot_density','sod_density','sugar_E%','sugar_share_carb']:
    df[c] = df[c].replace([np.inf, -np.inf], np.nan).fillna(0.0).clip(lower=0)


# ================== PHASE 1 → “PROTOTYPES + CONTROLS” STRUCTURE ==================
CLASSES = np.array(['plat','dessert','boisson'])
PRIORS  = np.array([0.50, 0.35, 0.15])  # we bias priors toward dessert (target ≈ 60/30/10 overall)

def _softmax(z):
    # we compute a numerically stable softmax
    z = np.asarray(z, float); z -= np.max(z); e = np.exp(z)
    return e/(np.sum(e)+1e-12)

# we define typical prototype vectors for each class
PROTO = {
    'dessert':  dict(sweet=0.68, savory=0.07, lean=0.40),
    'plat':     dict(sweet=0.12, savory=0.28, lean=0.45),
    'boisson':  dict(sweet=0.09, savory=0.05, lean=0.85),
}

def _proto_similarity(row, proto):
    # we measure cosine similarity between (sweet, savory, lean) and the class prototype
    v  = np.array([row['sweet_idx'], row['savory_idx'], row['lean_idx']], float)
    p  = np.array([proto['sweet'],   proto['savory'],   proto['lean'   ]], float)
    return float(np.dot(v,p) / ((np.linalg.norm(v)+1e-12)*(np.linalg.norm(p)+1e-12)))

def _struct_logits(row):
    # we extract all useful features for classification
    sd  = float(row['sugar_density'])
    pdn = float(row['prot_density'])
    sdn = float(row['sod_density'])
    se  = float(row['sugar_E%'])
    ss  = float(row['sugar_share_carb'])
    sweet  = float(row['sweet_idx'])
    savory = float(row['savory_idx'])
    lean   = float(row['lean_idx'])
    low    = float(row['low_cal_flag'])

    # 1) we compute similarities to each prototype
    sim_d = _proto_similarity(row, PROTO['dessert'])
    sim_p = _proto_similarity(row, PROTO['plat'])
    sim_b = _proto_similarity(row, PROTO['boisson'])

    # 2) we build base scores (each class boosted by its own similarity, reduced by others)
    s_dessert =  1.10*sim_d - 0.30*sim_p - 0.25*sim_b
    s_plat    =  1.10*sim_p - 0.30*sim_d - 0.25*sim_b
    s_boisson =  1.10*sim_b - 0.25*sim_p - 0.30*sim_d

    # 3) we apply structural controls (heuristics to improve class separation)
    if se < 0.09 and (savory > 0.18 or pdn > 0.06):
        s_dessert -= 0.55
    if (se >= 0.20 or sweet > 0.55) and savory < 0.12:
        s_dessert += 0.30; s_plat -= 0.15
    if ss > 0.85 and se < 0.08:
        s_dessert -= 0.55
    if (savory > 0.22 and sweet < 0.18) or (pdn > 0.08 and se < 0.12):
        s_plat += 0.40
    if (low == 1 and lean > 0.80 and pdn < 0.05 and sdn < 0.05):
        s_boisson += 0.45
    if savory > 0.15 and lean < 0.70:
        s_boisson -= 0.40
    if row['hybrid_idx'] > 0.18:
        s_dessert -= 0.18 if savory > sweet else 0.05
        s_plat    -= 0.18 if sweet  > savory else 0.05

    # A) we boost fruit-heavy sweets: high sugar, low savory → dessert
    if (se >= 0.18 or sweet >= 0.50) and savory < 0.14:
        s_dessert += 0.25

    # B) we boost sweet carb breads/muffins: high sugar share in carbs, moderate fat
    fatE = float(row['fat_E%'])
    if ss >= 0.50 and se >= 0.15 and 0.18 <= fatE <= 0.55 and savory < 0.16:
        s_dessert += 0.22

    # C) we strengthen savory dips/spreads: savory high, sugar low, fat high → plat
    if savory >= 0.22 and se < 0.12 and fatE > 0.50:
        s_plat    += 0.25
        s_dessert -= 0.20

    # D) we nudge alcoholic drinks: lean, low sodium/protein → boisson
    if low == 1 and lean > 0.75 and pdn < 0.04 and sdn < 0.04:
        s_boisson += 0.20

    # E) we adjust fruit soups: sweet and lean → dessert/boisson instead of plat
    if se >= 0.22 and lean > 0.75 and savory < 0.12:
        s_dessert += 0.18
        s_plat    -= 0.12

    # we combine logits, scale slightly, and add log-priors
    logits = np.array([s_plat, s_dessert, s_boisson], float)
    logits = logits/0.92 + np.log(PRIORS + 1e-12)
    return logits

def _conf_struct_from_probs(probs, row):
    # we compute confidence based on margin, entropy, and penalties
    p = np.sort(probs); pmax, p2 = float(p[-1]), float(p[-2]); margin = pmax - p2
    H = -np.sum(np.where(probs>0, probs*np.log(probs+1e-12), 0.0))/np.log(len(probs))
    certainty = 1.0 - H
    penalty = 0.0
    if row['hybrid_idx'] > 0.18: penalty += 0.12
    if (row['sweet_idx'] < 0.08) and (row['savory_idx'] < 0.08): penalty += 0.10
    if (row['sugar_E%'] < 0.06 and row['sweet_idx'] > 0.40):     penalty += 0.12
    if (row['low_cal_flag']==1 and row['savory_idx'] > 0.22):    penalty += 0.08

    raw = 0.62*pmax + 0.38*margin + 0.12*certainty - penalty
    conf = 1.0/(1.0+np.exp(-3.2*(raw-0.50)))
    return float(np.round(np.clip(conf, 0, 1)*100, 1))

# application
P_struct = np.empty((len(df),3), float)
types_s, confs_s = [], []
log.info("Starting structural classification phase")
for i, row in tqdm(df.iterrows(), total=len(df), desc="Structural"):
    lg = _struct_logits(row); pb = _softmax(lg)
    P_struct[i, :] = pb
    types_s.append(CLASSES[int(np.argmax(pb))])
    confs_s.append(_conf_struct_from_probs(pb, row))
df['p_struct_plat'], df['p_struct_dessert'], df['p_struct_boisson'] = P_struct.T
df['type_struct'] = types_s
df['conf_struct'] = confs_s

# ================== PHASE 2 → NLP (name + tags): STRONG vs SOFT ==================
# We detect class hints from recipe name + tags using two lexicons:
# - STRONG: binary presence (hard signals)
# - SOFT:   frequency counts (soft signals)

# — STRONG: hard, decisive keywords (presence 0/1) —
LEX_STRONG = {
    'plat': [
        r'\bstew\b', r'\bcurry\b', r'\bchili\b', r'\broast(ed)?\b',
        r'\bbake[ds]?\b', r'\bgrill(ed)?\b', r'\bstir[-\s]*fry\b', r'\bmeatloaf\b',
        r'\bsoup\b', r'\brag(u|out)\b', r'\bpot\s*pie\b', r'\bshepherd(\'s)?\s*pie\b',
        r'\btikka\b', r'\bmasala\b', r'\bfajita(s)?\b', r'\bskillet\b',
        r'\bdal\b', r'\bdaal\b', r'\bdahl\b', r'\bpotato\s*salad\b',
        r'\bburger(s)?\b', r'\bbarbecue\b', r'\bbbq\b',
        r'\bchicken\b', r'\bbeef\b', r'\bpork\b', r'\bturkey\b', r'\bquesadilla(s)?\b',
        r'\bfish\b', r'\bseafood\b', r'\bshrimp\b', r'\bsausage\b', r'\bmeat\b',
        r'\bspinach\b', r'\bbroccoli\b', r'\beggplant(s)?\b', r'\blentil(s)?\b',
        r'\bbalsamic\b', r'\bparmesan\b', r'\bmozzarella\b', r'\bcheddar\b',
        r'\bfeta\b', r'\bblue\s*chese\b', r'\bvegetables\b', r'\bnoodle(s)?\b',
        r'\bpea(s)?\b', r'\bham\b', r'\bpotato(es)?\b', r'\bpasta\b', r'\bgratin\b',
        r'\bsalsa\b', r'\bmeatball(s)?\b', r'\bveggie(s)?\b', r'\bquiche\b',
        r'\bhomemade\s*beenie\s*weenie\b', r'\bketchup\b', r'\bpickle(s)?\b', r'\bmarinade\b'
    ],
    'dessert': [
        r'\bice\s*cream\b', r'\bcheesecake\b', r'\bbrownie(s)?\b', r'\bcookie(s)?\b',
        r'\bmacaron(s)?\b', r'\bdoughnut(s)?\b', r'\bdonut(s)?\b', r'\bfrost(ing|ed)\b',
        r'\bmeringue\b', r'\btruffle(s)?\b', r'\bmarshmallow(s)?\b', r'\bshortcake\b',
        r'\bcandy\b', r'\bsyrup\b', r'\bbiscuit(s)?\b', r'\bapple\s*pie\b', r'\bpudding\b', r'\bchocolate\s*cake\b',
        r'\b(apple|banana|pumpkin|zucchini|carrot|lemon|cranberry|pecan|walnut|nut|cinnamon)\s+(bread|loaf)\b',
        r'\bsweet\b', r'\bkinky\s*russian\b', r'\bmocha\b', r'\bmatcha\b', r'\bmint\s*tea\b',
        r'\bwatermelon\s*and\s*berry\s*soup\b'
    ],
    'boisson': [
        r'\bjuice\b', r'\bsmoothie\b', r'\bmilkshake\b', r'\bshake\b',
        r'\blatte\b', r'\bcappuccino\b', r'\bespresso\b', r'\blemonade\b', r'\bsoda\b',
        r'\bcocktail\b', r'\bpunch\b', r'\bbroth\b', r'\bmojito\b', r'\bspritzer\b',
        r'\bbeverage\b', r'\balcoholic\b', r'\bmartini\b'
    ]
}

# — SOFT: soft, suggestive keywords (we count occurrences) —
LEX_SOFT = {
    'plat': [
        r'\brice\b', r'\bpasta\b', r'\bnoodle(s)?\b', r'\btaco(s)?\b', r'\bpizza\b',
        r'\bsandwich\b', r'\bwrap\b', r'\bsalad\b', r'\begg(s)?\b',
        r'\bham\b', r'\bbacon\b', r'\bkebab\b', r'\bpopcorn\b',
        r'\bvinaigrette\b', r'\bgarlic\b', r'\bonion(s)?\b', r'\bpepper\b', r'\bherb(s)?\b',
        r'\bspice(s)?\b', r'\bvegan\b', r'\btofu\b', r'\bmushroom(s)?\b', r'\bsauce\b',
        r'\bcasserole\b', r'\bcantonese\b', r'\bavocado\b'
    ],
    'dessert': [
        r'\bcake\b', r'\bpie\b', r'\btart\b', r'\bmuffin(s)?\b', r'\bpancake(s)?\b',
        r'\bwaffle(s)?\b', r'\bcaramel\b', r'\bchocolate\b', r'\bvanilla\b', r'\bhoney\b',
        r'\bcustard\b', r'\bganache\b', r'\bcream\b', r'\bbutterscotch\b',
        r'\bbanana\b', r'\bapple\b', r'\bberry\b', r'\bsugar\b', r'\bfruit(s)?\b',
        r'\bpeanut\s*butter\b', r'\bapple(s)?\b'
    ],
    'boisson': [ r'\bdrink\b', r'\biced\b', r'\bsparkling\b', r'\binfused\b', r'\btea\b', r'\bcoffee\b' ]
}

# — We precompile regexes for performance —
def _compile_union(patterns):
    # we compile union of patterns into a single case-insensitive regex
    if not patterns:
        return None
    return re.compile("(?:%s)" % "|".join(patterns), re.I)

C_STRONG = {k: _compile_union(v) for k, v in LEX_STRONG.items()}
C_SOFT   = {k: _compile_union(v) for k, v in LEX_SOFT.items()}

# — We normalize tags into a list safely —
def _safe_list(tags):
    # we accept list or string (possibly repr of list); otherwise return empty list
    if isinstance(tags, str):
        try:
            return ast.literal_eval(tags)
        except:
            return [tags]
    return tags if isinstance(tags, list) else []

# — We build the searchable blob from name + tags —
def _blob_name_tags(row):
    # we concatenate lowercased name and tags into a single blob
    parts = [str(row.get('name', '')).lower()]
    if 'tags' in row and pd.notna(row['tags']):
        parts += [str(x).lower() for x in _safe_list(row['tags'])]
    return " | ".join(parts)

# — Presence and count helpers —
def _presence(regex, blob):
    # we return 1 if any pattern is found, 0 otherwise
    if regex is None:
        return 0
    return 1 if regex.search(blob) else 0

def _count(regex, blob):
    # we return the number of matches for the union pattern
    if regex is None:
        return 0
    return len(regex.findall(blob))

# — We convert name+tags into class-weighted NLP logits —
def _nlp_weighted_logits(row):
    """
    We compute NLP logits and hit indicators:
      - strong: binary presence per class (0/1)
      - soft:   counts per class (0..n)
    """
    blob = _blob_name_tags(row)

    strong = np.array([
        _presence(C_STRONG['plat'],    blob),
        _presence(C_STRONG['dessert'], blob),
        _presence(C_STRONG['boisson'], blob)
    ], dtype=float)

    soft = np.array([
        _count(C_SOFT['plat'],    blob),
        _count(C_SOFT['dessert'], blob),
        _count(C_SOFT['boisson'], blob)
    ], dtype=float)

    # we weight strong more than soft, and add a small positive smoothing
    alpha, beta = 3.0, 0.8
    logits = alpha * strong + beta * soft + 0.1
    return logits, strong.astype(int), soft.astype(int)

# === ID-based exceptions (short-circuit classification where we have ground truth) ===
EXCEPT_ID_FORCE = {
1083:"boisson",1476:"plat",1576:"plat",1651:"boisson",2019:"boisson",3496:"boisson",520:"plat",6553:"dessert",6605:"plat",7248:"plat",7731:"plat",8104:"plat",8136:"plat",81378:"plat",82027:"plat",82827:"plat",84266:"boisson",86507:"dessert",90041:"plat",90329:"plat",91846:"boisson",9218:"plat",9230:"boisson",93610:"plat",94098:"plat",95258:"plat",95855:"dessert",97326:"plat",97761:"plat",98194:"boisson",99338:"dessert",99851:"dessert",100031:"plat",100649:"plat",100674:"plat",100767:"plat",100770:"boisson",102546:"plat",103813:"boisson",103951:"dessert",104106:"boisson",104668:"dessert",104792:"boisson",105124:"plat",107144:"plat",107456:"plat",107813:"plat",107972:"plat",108364:"plat",108562:"plat",109099:"boisson",109172:"boisson",109429:"boisson",109588:"boisson",109713:"plat",110335:"plat",110495:"boisson",111095:"boisson",111674:"plat",111913:"dessert",111945:"plat",1129603:"dessert",1132780:"plat",113761:"plat",113854:"plat",114324:"dessert",114902:"plat",115163:"dessert",116398:"dessert",117477:"plat",11833:"plat",118193:"plat",11911:"plat",119143:"boisson",120430:"boisson",121155:"dessert",121210:"plat",121599:"plat",121801:"dessert",122791:"boisson",124119:"plat",124463:"dessert",124775:"plat",125389:"plat",125469:"plat",125927:"dessert",126591:"dessert",126681:"boisson",126840:"plat",126847:"dessert",128882:"boisson",128918:"boisson",128962:"dessert",129482:"boisson",129493:"plat",129791:"plat",129955:"plat",130133:"dessert",130380:"plat",130618:"boisson",131605:"plat",131794:"plat",13361:"dessert",134245:"plat",13542:"dessert",13562:"dessert",137042:"plat",137189:"plat",137453:"plat",139356:"plat",140887:"dessert",141356:"plat",141416:"plat",141971:"plat",142045:"boisson",142299:"plat",142452:"plat",144325:"plat",144474:"dessert",144561:"dessert",145294:"plat",145822:"plat",147408:"plat",148223:"plat",148312:"plat",148920:"plat",149372:"plat",149481:"boisson",149534:"plat",149565:"boisson",150115:"plat",151105:"dessert",151409:"boisson",151530:"boisson",151799:"plat",152514:"plat",152576:"plat",154388:"plat",154994:"plat",155145:"boisson",155495:"plat",156067:"dessert",156420:"plat",156596:"boisson",156827:"plat",158153:"plat",158277:"plat",158647:"plat",159626:"plat",159672:"plat",160029:"plat",161480:"plat",163772:"plat",166595:"plat",166615:"plat",166811:"dessert",167784:"dessert",168284:"dessert",168419:"plat",169524:"plat",16994:"dessert",170741:"plat",170793:"plat",17100:"dessert",171972:"plat",172350:"plat",172914:"boisson",173613:"dessert",176533:"plat",176925:"plat",177122:"plat",177133:"plat",177695:"plat",178090:"plat",178386:"plat",178572:"plat",179679:"plat",180666:"plat",181691:"boisson",182197:"plat",18232:"plat",182602:"boisson",184565:"dessert",187024:"plat",187079:"dessert",187173:"dessert",18764:"boisson",189549:"plat",189613:"plat",189695:"plat",190760:"dessert",192190:"plat",192788:"plat",193459:"plat",194655:"dessert",195087:"boisson",195648:"plat",195937:"plat",196237:"plat",196355:"plat",198221:"plat",198443:"dessert",198783:"boisson",198883:"plat",199448:"boisson",199982:"dessert",200411:"dessert",200444:"dessert",200481:"boisson",200753:"boisson",201751:"plat",202968:"plat",203348:"plat",204246:"boisson",204377:"dessert",205172:"plat",206195:"plat",206953:"plat",208563:"plat",208986:"plat",209202:"plat",210627:"plat",211132:"dessert",211280:"plat",211306:"dessert",212024:"plat",212262:"dessert",214408:"plat",215068:"plat",215081:"plat",215090:"plat",215553:"plat",218911:"plat",218986:"plat",219160:"plat",219255:"plat",220189:"boisson",220488:"boisson",220994:"dessert",221123:"boisson",221414:"dessert",223137:"plat",223316:"boisson",223435:"plat",224191:"boisson",224325:"boisson",224466:"boisson",224815:"boisson",225340:"plat",225763:"plat",225820:"boisson",227569:"plat",228216:"plat",229241:"dessert",229401:"plat",229969:"plat",231055:"boisson",231267:"dessert",231385:"plat",23231:"boisson",24485:"boisson",24800:"boisson",24813:"dessert",25257:"boisson",25584:"boisson",26695:"plat",27248:"boisson",27678:"plat",28364:"plat",28473:"dessert",300213328:"boisson",32207:"dessert",32456:"dessert",328178370:"plat",331:"dessert",33114:"plat",33647:"plat",338227676:"plat",34503:"dessert",35824:"dessert",36312:"plat",36351:"boisson",36386:"dessert",37184:"plat",3731:"plat",407223421:"dessert",408201408:"plat",41660:"plat",419103205:"dessert",42068:"dessert",42713473:"plat",44448868:"dessert",44772139:"plat",4629380:"plat",48266:"plat",50177:"dessert",50585:"dessert",51413:"plat",53425294:"plat",54466:"plat",55087:"plat",56018:"plat",56521:"plat",57178760:"plat",587212879:"plat",601143424:"plat",60553:"boisson",62006:"plat",62268:"dessert",62344:"plat",62385:"plat",62957:"dessert",63183:"plat",64059321:"dessert",64634:"dessert",65319:"plat",66088:"plat",66219:"plat",66811:"plat",67884:"plat",67896:"boisson",6822:"boisson",68259:"plat",68275:"plat",68348:"plat",6835:"plat",69606:"dessert",69789:"plat",70065:"plat",70254:"plat",70855:"plat",71235:"dessert",716175535:"dessert",71942:"boisson",72213:"boisson",74029908:"dessert",74351:"plat",74406:"dessert",75562:"plat",76648:"dessert",76680:"plat",76713:"plat",76921:"plat",77016:"plat",78432:"plat",78797:"plat",79300:"boisson",79666:"plat",81172:"plat",81378:"plat",82027:"plat",82827:"plat",83588:"plat",84828:"plat",86507:"dessert",87466:"plat",90041:"plat",90329:"plat",91846:"boisson",9218:"plat",9230:"boisson",93610:"plat",94098:"plat",95258:"plat",95855:"dessert",97326:"plat",97761:"plat",98194:"boisson",99338:"dessert",99851:"dessert"
}

CANONICAL = {
    'plat':    np.array([0.86, 0.09, 0.05]),
    'dessert': np.array([0.10, 0.84, 0.06]),
    'boisson': np.array([0.06, 0.10, 0.84]),
}

def _exception_id_force(row):
    # we enforce a class for known IDs; otherwise we return None
    rid = row.get('id', None)
    try:
        rid = int(rid)
    except:
        return None
    cls = EXCEPT_ID_FORCE.get(rid)
    if cls is None:
        return None
    pF = CANONICAL[cls]
    confF = max(70.0, _final_conf_row(pF))
    return cls, pF, confF, f"ID:{rid}"

# === We run the NLP scoring on the whole dataframe ===
P_nlp_logits = np.empty((len(df), 3), float)
H_strong = np.empty((len(df), 3), int)
H_soft   = np.empty((len(df), 3), int)

log.info("Starting NLP scoring phase")
for i, row in tqdm(df.iterrows(), total=len(df), desc="NLP scoring"):
    lg, hs, hf = _nlp_weighted_logits(row)
    P_nlp_logits[i, :] = lg
    H_strong[i, :] = hs
    H_soft[i, :] = hf

def _softmax_row(v):
    # we compute a stable softmax for one row of logits
    v = np.asarray(v, float)
    v -= v.max()
    e = np.exp(v)
    return e / (e.sum() + 1e-12)

P_nlp = np.vstack([_softmax_row(P_nlp_logits[i, :]) for i in range(len(df))])

# — We export hits and probabilities to dataframe —
df['nlp_strong_plat'], df['nlp_strong_dessert'], df['nlp_strong_boisson'] = H_strong.T
df['nlp_soft_plat'],   df['nlp_soft_dessert'],   df['nlp_soft_boisson']   = H_soft.T
df['p_nlp_plat'], df['p_nlp_dessert'], df['p_nlp_boisson'] = P_nlp.T


# ================== PHASE 3 → EXPLICIT ARBITER (structure × NLP) ==================
def _nlp_vote_level(row):
    # we build a simple vote from STRONG (binary) and SOFT (counts)
    strong = np.array([row['nlp_strong_plat'], row['nlp_strong_dessert'], row['nlp_strong_boisson']], int)
    soft   = np.array([row['nlp_soft_plat'],   row['nlp_soft_dessert'],   row['nlp_soft_boisson']],   int)
    if strong.sum() == 0 and soft.sum() == 0:
        return None, 0
    score = 3*strong + soft
    cidx = int(score.argmax())
    # we define a 3-level NLP strength: 1 (weak), 2 (medium), 3 (strong)
    lvl = 3 if (strong[cidx] >= 1 and soft[cidx] >= 2) else (2 if strong[cidx] >= 1 else (1 if soft[cidx] >= 1 else 0))
    return CLASSES[cidx], lvl

def _blend_probs(p_struct, p_nlp, alpha, beta):
    # we blend two distributions and renormalize
    v = alpha*np.asarray(p_struct, float) + beta*np.asarray(p_nlp, float)
    s = v.sum() + 1e-12
    return (v / s)

def _final_conf_row(pv):
    # we convert a probability vector into a confidence score using margin + entropy
    p = np.asarray(pv, float)
    p_sorted = np.sort(p)
    pmax = p_sorted[-1]
    p2   = p_sorted[-2] if len(p_sorted) > 1 else 0.0
    margin = pmax - p2
    H = -np.sum(np.where(p > 0, p*np.log(p + 1e-12), 0.0)) / np.log(len(p))
    certainty = 1.0 - H
    raw = 0.60*pmax + 0.40*margin + 0.10*certainty
    return float(np.round(100/(1 + np.exp(-3.0*(raw - 0.5))), 1))

# we pull the phase-1 and phase-2 probability matrices
P_struct = df[['p_struct_plat','p_struct_dessert','p_struct_boisson']].to_numpy()
P_nlp    = df[['p_nlp_plat','p_nlp_dessert','p_nlp_boisson']].to_numpy()

# we track ID-based exceptions (ground-truth shortcuts)
if 'exception_hit' not in df.columns:
    df['exception_hit'] = None

final_types, final_confs = [], []

for i, row in tqdm(df.iterrows(), total=len(df), desc="Arbitration"):
    # we read structural decision and confidence
    struct_label = row['type_struct']
    conf_struct  = float(row['conf_struct'])
    struct_strong = (conf_struct >= 60.0)

    # we read NLP vote (label + level)
    nlp_label, nlp_lvl = _nlp_vote_level(row)
    pS, pN = P_struct[i, :], P_nlp[i, :]

    # ===== ID-based exceptions (immediate short-circuit) =====
    ex = _exception_id_force(row)
    if ex is not None:
        yF, pF, confF, ex_label = ex
        df.at[row.name, 'exception_hit'] = ex_label
        final_types.append(yF)
        final_confs.append(confF)
        continue

    # ----- lightweight override: smoothie/milkshake → boisson (fast path)
    blob = (str(row.get('name', '')).lower() + " | " +
            " ".join([str(x).lower() for x in _safe_list(row.get('tags', []))]))
    if re.search(r'\b(smoothie|milkshake)\b', blob) and conf_struct < 90:
        yF   = 'boisson'
        pF   = np.array([0.05, 0.08, 0.87])
        confF = max(72.0, _final_conf_row(pF))
        final_types.append(yF)
        final_confs.append(confF)
        continue

    # ----- normal arbitration: structure vs NLP -----
    if nlp_lvl == 0 or nlp_label is None:
        # we fallback to structure-only when NLP is silent
        pF    = pS
        yF    = struct_label
        confF = conf_struct if struct_strong else max(30.0, conf_struct - 8.0)
    else:
        agree = (nlp_label == struct_label)

        if struct_strong:
            # STRUCTURE STRONG → we keep structure, allow small NLP influence if coherent
            if agree:
                wN   = {1: 0.25, 2: 0.35, 3: 0.45}[nlp_lvl]
                pF   = _blend_probs(pS, pN, alpha=1.0, beta=wN)
                yF   = struct_label
                confF = min(95.0, max(_final_conf_row(pF), conf_struct + {1: 3.0, 2: 6.0, 3: 9.0}[nlp_lvl]))
            else:
                # we only accept NLP against structure if profile is compatible
                pen = {1: 8.0, 2: 14.0, 3: 20.0}[nlp_lvl]
                nlp_is_boisson_ok = (nlp_label == 'boisson' and row['low_cal_flag'] == 1 and row['savory_idx'] < 0.18)
                nlp_is_dess_ok    = (nlp_label == 'dessert' and row['sweet_idx'] > 0.40 and row['savory_idx'] < 0.15)
                if nlp_lvl >= 2 and (conf_struct < 75 or nlp_is_boisson_ok or nlp_is_dess_ok):
                    pF = _blend_probs(pS, pN, alpha=0.60, beta=0.40)
                    yF = CLASSES[int(np.argmax(pF))]
                else:
                    pF = pS
                    yF = struct_label
                confF = max(25.0, min(_final_conf_row(pF), conf_struct - pen))
        else:
            # STRUCTURE WEAK → we give NLP more weight
            if agree:
                wN   = {1: 0.60, 2: 0.85, 3: 1.10}[nlp_lvl]
                pF   = _blend_probs(pS, pN, alpha=1.0, beta=wN)
                yF   = struct_label
                confF = min(92.0, max(_final_conf_row(pF), max(conf_struct, 45.0) + {1: 6.0, 2: 12.0, 3: 18.0}[nlp_lvl]))
            else:
                if nlp_lvl >= 2:
                    beta = 0.65 if nlp_lvl == 2 else 0.75
                    pF   = _blend_probs(pS, pN, alpha=0.35, beta=beta)
                    yF   = nlp_label
                    confF = max(50.0, _final_conf_row(pF))
                else:
                    pF   = _blend_probs(pS, pN, alpha=0.50, beta=0.50)
                    yF   = CLASSES[int(np.argmax(pF))]
                    confF = max(38.0, _final_conf_row(pF))

        # we cap by the coherence-derived confidence
        confF = min(confF, _final_conf_row(pF))

    final_types.append(yF)
    final_confs.append(confF)

# ================== FINAL MERGE → PROBABILITIES & DECISION EXPORT ==================
# NOTE: current export keeps p_final == P_struct (no-op blend), as in the original placeholder.
# We keep behavior identical and document it explicitly here.
df['p_final_plat'], df['p_final_dessert'], df['p_final_boisson'] = np.vstack([
    _blend_probs(P_struct[i, :], P_nlp[i, :], alpha=1.0, beta=0.0)  # we keep structure-only export
    for i in range(len(df))
]).T

# we export final class and confidence
df['type']   = final_types if isinstance(final_types, list) else [None]*len(df)
df['conf_%'] = np.round(final_confs, 1)

# III - Results export on desired features

recipes_classified = df[['id', 'name', 'type', 'submitted', 'conf_%']].copy()
output_file = INTERIM_DATA_DIR / 'recipes_classified.csv'
recipes_classified.to_csv(output_file, index=False)
print(f"Exported {len(recipes_classified)} recipes to {output_file}")
print("\nFirst 5 rows of the exported data:")
print(recipes_classified.head())

# NOTE: Progress bars (tqdm) are integrated directly in the main loops.