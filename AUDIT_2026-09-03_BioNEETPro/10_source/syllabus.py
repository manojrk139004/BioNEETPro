"""
BioNEETPro - Official 38-Chapter NEET Biology Syllabus Registry & Boundary Validator
Covers Class 11 (22 Chapters across 5 Units) and Class 12 (16 Chapters across 5 Units).
Strictly enforces syllabus boundaries: non-Biology and out-of-syllabus questions are rejected with polite guidance.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DATA_DIR = Path(__file__).resolve().parent / "data"
SYLLABUS_FILE = DATA_DIR / "syllabus_registry.json"

OFFICIAL_SYLLABUS = {
    "class_11": {
        "unit_1": {
            "unit_name": "Diversity in the Living World",
            "chapters": {
                "c01": {
                    "chapter_name": "The Living World",
                    "keywords": ["living", "characteristics of life", "taxonomic categories", "taxonomical aids", "herbarium", "botanical garden", "museum", "zoological parks", "key", "binomial nomenclature", "carolus linnaeus", "genus", "species", "family", "order", "class", "phylum", "division"],
                },
                "c02": {
                    "chapter_name": "Biological Classification",
                    "keywords": ["five kingdom", "rh whittaker", "monera", "bacteria", "archaebacteria", "methanogens", "eubacteria", "mycoplasma", "protista", "chrysophytes", "diatoms", "dinoflagellates", "euglenoids", "slime moulds", "protozoans", "fungi", "phycomycetes", "ascomycetes", "basidiomycetes", "deuteromycetes", "lichens", "mycorrhiza", "virus", "viroid", "prion"],
                },
                "c03": {
                    "chapter_name": "Plant Kingdom",
                    "keywords": ["algae", "chlorophyceae", "phaeophyceae", "rhodophyceae", "bryophytes", "liverworts", "mosses", "pteridophytes", "ferns", "gymnosperms", "cycas", "pinus", "angiosperms", "alternation of generations", "haplontic", "diplontic", "haplo-diplontic"],
                },
                "c04": {
                    "chapter_name": "Animal Kingdom",
                    "keywords": ["animal kingdom", "porifera", "sponges", "sycon", "coelenterata", "cnidaria", "hydra", "ctenophora", "platyhelminthes", "taenia", "aschelminthes", "ascaris", "annelida", "annelid", "earthworm", "pheretima", "nereis", "leech", "hirudinaria", "setae", "parapodia", "metamerism", "metameres", "clitellum", "arthropoda", "periplaneta", "mollusca", "pila", "snail", "echinodermata", "asterias", "starfish", "hemichordata", "chordata", "cyclostomata", "chondrichthyes", "scoliodon", "shark", "osteichthyes", "labeo", "rohu", "amphibia", "rana", "frog", "toad", "bufo", "reptilia", "aves", "columba", "pigeon", "mammalia", "oryctolagus", "rabbit", "coelom", "symmetry", "notochord", "euglena", "paramecium", "plasmodium"],
                },
            },
        },
        "unit_2": {
            "unit_name": "Structural Organisation in Plants and Animals",
            "chapters": {
                "c05": {
                    "chapter_name": "Morphology of Flowering Plants",
                    "keywords": ["root", "stem", "leaf", "inflorescence", "flower", "fruit", "seed", "racemose", "cymose", "calyx", "corolla", "androecium", "gynoecium", "aestivation", "placentation", "fabaceae", "solanaceae", "liliaceae"],
                },
                "c06": {
                    "chapter_name": "Anatomy of Flowering Plants",
                    "keywords": ["meristematic tissue", "permanent tissue", "parenchyma", "collenchyma", "sclerenchyma", "xylem", "phloem", "tracheids", "vessels", "sieve tube", "companion cell", "epidermal tissue", "ground tissue", "vascular bundles", "dicot root", "monocot root", "dicot stem", "monocot stem", "dicot leaf", "monocot leaf", "secondary growth", "vascular cambium", "cork cambium"],
                },
                "c07": {
                    "chapter_name": "Structural Organisation in Animals / Tissues",
                    "keywords": ["epithelial tissue", "squamous", "cuboidal", "columnar", "ciliated", "compound epithelium", "connective tissue", "areolar", "adipose", "tendon", "ligament", "cartilage", "bone", "blood", "muscle tissue", "striated", "smooth", "cardiac", "neural tissue", "cockroach", "periplaneta americana", "malpighian tubules", "earthworm", "pheretima", "frog", "rana tigrina"],
                },
            },
        },
        "unit_3": {
            "unit_name": "Cell Structure and Function",
            "chapters": {
                "c08": {
                    "chapter_name": "Cell: The Unit of Life",
                    "keywords": ["cell theory", "schleiden", "schwann", "virchow", "prokaryotic cell", "eukaryotic cell", "plasma membrane", "fluid mosaic model", "singer nicolson", "cell wall", "endomembrane system", "endoplasmic reticulum", "golgi apparatus", "lysosome", "vacuole", "mitochondria", "chloroplast", "ribosomes", "cytoskeleton", "cilia", "flagella", "centrosome", "nucleus", "chromosomes"],
                },
                "c09": {
                    "chapter_name": "Biomolecules",
                    "keywords": ["biomolecules", "amino acids", "proteins", "primary structure", "secondary structure", "tertiary structure", "quaternary structure", "peptide bond", "lipids", "fatty acids", "phospholipids", "nucleic acids", "dna", "rna", "nucleotides", "carbohydrates", "polysaccharides", "starch", "glycogen", "cellulose", "enzymes", "activation energy", "michaelis menten", "competitive inhibition", "allosteric"],
                },
                "c10": {
                    "chapter_name": "Cell Cycle and Cell Division",
                    "keywords": ["cell cycle", "interphase", "g1 phase", "s phase", "g2 phase", "g0 phase", "mitosis", "prophase", "metaphase", "anaphase", "telophase", "cytokinesis", "meiosis", "meiosis i", "prophase i", "leptotene", "zygotene", "pachytene", "diplotene", "diakinesis", "synapsis", "crossing over", "chiasmata", "meiosis ii"],
                },
            },
        },
        "unit_4": {
            "unit_name": "Plant Physiology",
            "chapters": {
                "c13": {
                    "chapter_name": "Photosynthesis in Higher Plants",
                    "keywords": ["photosynthesis", "chlorophyll", "chloroplast", "thylakoid", "stroma", "light reaction", "photophosphorylation", "ps i", "ps ii", "z-scheme", "photolysis of water", "calvin cycle", "c3 pathway", "rubisco", "c4 pathway", "hatch slack", "kranz anatomy", "pep carboxylase", "photorespiration", "blackman law"],
                },
                "c14": {
                    "chapter_name": "Respiration in Plants",
                    "keywords": ["cellular respiration", "glycolysis", "emp pathway", "pyruvate", "fermentation", "krebs cycle", "tca cycle", "citric acid cycle", "mitochondria", "electron transport system", "ets", "oxidative phosphorylation", "atp synthase", "chemiosmosis", "respiratory quotient", "rq"],
                },
                "c15": {
                    "chapter_name": "Plant Growth and Development",
                    "keywords": ["plant growth", "differentiation", "dedifferentiation", "redifferentiation", "auxin", "gibberellin", "cytokinin", "ethylene", "abscisic acid", "aba", "photoperiodism", "vernalization", "seed dormancy", "apical dominance"],
                },
            },
        },
        "unit_5": {
            "unit_name": "Human Physiology",
            "chapters": {
                "c16": {
                    "chapter_name": "Digestion and Absorption",
                    "keywords": ["alimentary canal", "teeth", "dental formula", "stomach", "gastric glands", "pepsin", "hydrochloric acid", "hcl", "parietal cells", "intrinsic factor", "pancreas", "pancreatic juice", "trypsin", "liver", "bile", "emulsification", "small intestine", "succus entericus", "villi", "lacteals", "absorption", "kwashiorkor", "marasmus"],
                },
                "c17": {
                    "chapter_name": "Breathing and Exchange of Gases",
                    "keywords": ["respiratory system", "lungs", "alveoli", "mechanism of breathing", "inspiration", "expiration", "respiratory volumes", "tidal volume", "vital capacity", "exchange of gases", "partial pressure", "po2", "pco2", "transport of oxygen", "oxygen dissociation curve", "bohr effect", "transport of co2", "bicarbonate", "respiratory rhythm center", "asthma", "emphysema"],
                },
                "c18": {
                    "chapter_name": "Body Fluids and Circulation",
                    "keywords": ["blood", "plasma", "formed elements", "erythrocytes", "rbc", "leukocytes", "wbc", "platelets", "thrombocytes", "abo blood groups", "rh factor", "erythroblastosis foetalis", "blood clotting", "coagulation", "lymph", "lymph node", "heart", "cardiac cycle", "sa node", "sinoatrial node", "pacemaker", "av node", "bundle of his", "systole", "diastole", "ecg", "double circulation", "blood pressure", "hypertension", "arteries", "veins"],
                },
                "c19": {
                    "chapter_name": "Excretory Products and Elimination",
                    "keywords": ["excretion", "kidney", "nephron", "glomerulus", "bowman capsule", "pct", "loop of henle", "dct", "collecting duct", "urine formation", "glomerular filtration", "gfr", "reabsorption", "tubular secretion", "counter current mechanism", "vasa recta", "raas", "renin", "angiotensin", "aldosterone", "adh", "vasopressin", "anf", "micturition", "urochrome", "uremia", "dialysis"],
                },
                "c20": {
                    "chapter_name": "Locomotion and Movement",
                    "keywords": ["locomotion", "movement", "muscle", "skeletal muscle", "sarcomere", "actin", "myosin", "sliding filament theory", "tropomyosin", "troponin", "sarcoplasmic reticulum", "skeletal system", "206 bones", "axial skeleton", "skull", "vertebral column", "ribs", "sternum", "appendicular skeleton", "limbs", "girdles", "joints", "synovial joints", "saddle joint", "pivot joint", "myasthenia gravis", "tetany", "osteoporosis", "gout", "hydroxyapatite"],
                },
                "c21": {
                    "chapter_name": "Neural Control and Coordination",
                    "keywords": ["nervous system", "neuron", "axon", "dendrite", "myelin sheath", "schwann cell", "nodes of ranvier", "generation of nerve impulse", "action potential", "depolarization", "synapse", "neurotransmitter", "acetylcholine", "central nervous system", "brain", "forebrain", "cerebrum", "cerebral cortex", "white matter", "grey matter", "hypothalamus", "midbrain", "hindbrain", "cerebellum", "medulla", "spinal cord", "reflex arc", "eye", "retina", "rods", "cones", "rhodopsin", "ear", "organ of corti"],
                },
                "c22": {
                    "chapter_name": "Chemical Coordination and Integration",
                    "keywords": ["endocrine system", "hormones", "hypothalamus", "pituitary gland", "growth hormone", "thyroid gland", "thyroxine", "parathyroid gland", "pth", "thymus", "adrenal gland", "adrenaline", "noradrenaline", "corticoids", "pancreas", "islets of langerhans", "insulin", "glucagon", "diabetes mellitus", "testis", "testosterone", "ovary", "estrogen", "progesterone", "mechanism of hormone action", "secondary messengers", "camp"],
                },
            },
        },
    },
    "class_12": {
        "unit_6": {
            "unit_name": "Reproduction",
            "chapters": {
                "c23": {
                    "chapter_name": "Sexual Reproduction in Flowering Plants",
                    "keywords": ["flower", "stamen", "microsporangium", "pollen grain", "microsporogenesis", "pistil", "megasporangium", "ovule", "megasporogenesis", "embryo sac", "pollination", "anemophily", "hydrophily", "entomophily", "outbreeding devices", "pollen pistil interaction", "double fertilization", "triple fusion", "endosperm", "embryo", "seed", "apomixis", "polyembryony"],
                },
                "c24": {
                    "chapter_name": "Human Reproduction",
                    "keywords": ["male reproductive system", "testes", "seminiferous tubules", "sertoli cells", "leydig cells", "female reproductive system", "ovaries", "fallopian tubes", "uterus", "gametogenesis", "spermatogenesis", "spermiogenesis", "oogenesis", "menstrual cycle", "follicular phase", "ovulation", "lh surge", "luteal phase", "corpus luteum", "fertilization", "acrosome", "zona pellucida", "cleavage", "blastocyst", "implantation", "pregnancy", "placenta", "hcg", "parturition", "lactation", "colostrum"],
                },
                "c25": {
                    "chapter_name": "Reproductive Health",
                    "keywords": ["reproductive health", "population explosion", "birth control", "contraceptive methods", "iud", "iuds", "copper-t", "oral pills", "saheli", "medical termination of pregnancy", "mtp", "sexually transmitted infections", "sti", "aids", "syphilis", "gonorrhoea", "infertility", "assisted reproductive technologies", "art", "ivf", "test tube baby", "zift", "gift", "icsi", "amniocentesis"],
                },
            },
        },
        "unit_7": {
            "unit_name": "Genetics and Evolution",
            "chapters": {
                "c26": {
                    "chapter_name": "Principles of Inheritance and Variation",
                    "keywords": ["mendelian inheritance", "mendel laws", "law of dominance", "law of segregation", "law of independent assortment", "monohybrid cross", "dihybrid cross", "incomplete dominance", "codominance", "multiple alleles", "abo blood", "pleiotropy", "polygenic inheritance", "chromosomal theory of inheritance", "sutton boveri", "linkage", "recombination", "morgan", "sex determination", "mutation", "pedigree analysis", "mendelian disorders", "hemophilia", "sickle cell anemia", "phenylketonuria", "thalassemia", "chromosomal disorders", "down syndrome", "klinefelter syndrome", "turner syndrome"],
                },
                "c27": {
                    "chapter_name": "Molecular Basis of Inheritance",
                    "keywords": ["dna", "structure of dna", "watson crick", "double helix", "packaging of dna", "nucleosome", "histones", "griffith experiment", "transforming principle", "avery macleod mccarty", "hershey chase experiment", "dna replication", "semi conservative", "meselson stahl", "dna polymerase", "transcription", "promoter", "rna polymerase", "genetic code", "codons", "trna", "translation", "ribosome", "lac operon", "human genome project", "hgp", "dna fingerprinting"],
                },
                "c28": {
                    "chapter_name": "Evolution",
                    "keywords": ["origin of life", "miller urey experiment", "chemical evolution", "oparin haldane", "evidence for evolution", "homologous organs", "divergent evolution", "analogous organs", "convergent evolution", "adaptive radiation", "darwin finches", "biological evolution", "natural selection", "lamarckism", "hugo de vries", "mutation theory", "hardy weinberg principle", "genetic drift", "founder effect", "human evolution", "dryopithecus", "australopithecus", "homo habilis", "homo erectus", "neanderthal", "homo sapiens"],
                },
            },
        },
        "unit_8": {
            "unit_name": "Biology in Human Welfare",
            "chapters": {
                "c29": {
                    "chapter_name": "Human Health and Disease",
                    "keywords": ["common infectious diseases", "typhoid", "salmonella typhi", "widal test", "pneumonia", "streptococcus pneumoniae", "common cold", "rhinovirus", "malaria", "plasmodium", "sporozoite", "hemozoin", "amoebiasis", "entamoeba histolytica", "ascariasis", "filariasis", "wuchereria bancrofti", "ringworm", "immunity", "innate immunity", "acquired immunity", "b lymphocytes", "t lymphocytes", "antibodies", "immunoglobulin", "humoral immunity", "cell mediated immunity", "active immunity", "passive immunity", "vaccination", "allergies", "ige", "autoimmunity", "immune system", "lymphoid organs", "aids", "hiv", "cancer", "oncogenes", "metastasis", "drugs and alcohol abuse"],
                },
                "c30": {
                    "chapter_name": "Microbes in Human Welfare",
                    "keywords": ["microbes", "household products", "curd", "lactobacillus", "lab", "cheese", "fermented beverages", "yeast", "saccharomyces cerevisiae", "antibiotics", "penicillin", "alexander fleming", "chemicals", "enzymes", "organic acids", "citric acid", "cyclosporin a", "statins", "sewage treatment", "primary treatment", "secondary treatment", "bod", "biogas production", "methanogens", "biocontrol agents", "bacillus thuringiensis", "trichoderma", "biofertilizers", "rhizobium", "azospirillum", "azotobacter", "mycorrhiza", "cyanobacteria"],
                },
            },
        },
        "unit_9": {
            "unit_name": "Biotechnology",
            "chapters": {
                "c31": {
                    "chapter_name": "Biotechnology: Principles and Processes",
                    "keywords": ["recombinant dna technology", "genetic engineering", "restriction enzymes", "restriction endonucleases", "palindromic sequence", "ecori", "ligase", "cloning vectors", "plasmids", "pbr322", "selectable markers", "insertional inactivation", "transformation", "competent host", "gel electrophoresis", "ethidium bromide", "pcr", "polymerase chain reaction", "taq polymerase", "bioreactors", "downstream processing"],
                },
                "c32": {
                    "chapter_name": "Biotechnology and Its Applications",
                    "keywords": ["biotechnological applications", "agriculture", "bt cotton", "cry genes", "pest resistant plants", "rna interference", "rnai", "meloidogyne incognita", "genetically engineered insulin", "elililly", "proinsulin", "gene therapy", "ada deficiency", "adenosine deaminase", "molecular diagnosis", "elisa", "transgenic animals", "ethical issues", "geac", "biopiracy"],
                },
            },
        },
        "unit_10": {
            "unit_name": "Ecology and Environment",
            "chapters": {
                "c33": {
                    "chapter_name": "Organisms and Populations",
                    "keywords": ["organism and environment", "abiotic factors", "temperature", "water", "light", "soil", "responses to abiotic factors", "regulators", "conformers", "migration", "suspension", "adaptations", "population attributes", "birth rate", "death rate", "sex ratio", "age pyramids", "population growth", "exponential growth", "logistic growth", "carrying capacity", "population interactions", "predation", "competition", "competitive exclusion", "gause", "parasitism", "commensalism", "mutualism", "amensalism"],
                },
                "c34": {
                    "chapter_name": "Ecosystem",
                    "keywords": ["ecosystem structure", "productivity", "gross primary productivity", "gpp", "net primary productivity", "npp", "decomposition", "detritivores", "energy flow", "10 percent law", "lindeman", "food chain", "food web", "trophic levels", "ecological pyramids", "pyramid of numbers", "pyramid of biomass", "pyramid of energy", "ecological succession", "pioneer species", "climax community", "hydrarch", "xerarch", "nutrient cycling", "carbon cycle", "phosphorus cycle"],
                },
                "c35": {
                    "chapter_name": "Biodiversity and Conservation",
                    "keywords": ["biodiversity", "genetic diversity", "species diversity", "ecological diversity", "latitudinal gradients", "species area relationship", "alexander von humboldt", "importance of biodiversity", "rivet popper hypothesis", "paul ehrlich", "loss of biodiversity", "evil quartet", "habitat loss", "over exploitation", "alien species invasion", "co-extinctions", "biodiversity conservation", "in-situ conservation", "national parks", "sanctuaries", "biosphere reserves", "hotspots", "ex-situ conservation", "zoological parks", "botanical gardens", "cryopreservation", "earth summit"],
                },
            },
        },
    },
}

CANONICAL_CHAPTER_NAMES = {
    'the living world': 'The Living World',
    'biological classification': 'Biological Classification',
    'plant kingdom': 'Plant Kingdom',
    'animal kingdom': 'Animal Kingdom',
    'morphology of flowering plants': 'Morphology of Flowering Plants',
    'anatomy of flowering plants': 'Anatomy of Flowering Plants',
    'structural organisation in animals': 'Structural Organisation in Animals / Tissues',
    'structural organisation in animals / tissues': 'Structural Organisation in Animals / Tissues',
    'tissues': 'Structural Organisation in Animals / Tissues',
    'cell the unit of life': 'Cell: The Unit of Life',
    'cell: the unit of life': 'Cell: The Unit of Life',
    'cell - the unit of life': 'Cell: The Unit of Life',
    'biomolecules': 'Biomolecules',
    'cell cycle and cell division': 'Cell Cycle and Cell Division',
    'photosynthesis in higher plants': 'Photosynthesis in Higher Plants',
    'photosynthesis': 'Photosynthesis in Higher Plants',
    'respiration in plants': 'Respiration in Plants',
    'plant growth and development': 'Plant Growth and Development',
    'digestion and absorption': 'Digestion and Absorption',
    'breathing and exchange of gases': 'Breathing and Exchange of Gases',
    'body fluids and circulation': 'Body Fluids and Circulation',
    'excretory products and elimination': 'Excretory Products and Elimination',
    'excretory products and their elimination': 'Excretory Products and Elimination',
    'locomotion and movement': 'Locomotion and Movement',
    'neural control and coordination': 'Neural Control and Coordination',
    'chemical coordination and integration': 'Chemical Coordination and Integration',
    'sexual reproduction in flowering plants': 'Sexual Reproduction in Flowering Plants',
    'human reproduction': 'Human Reproduction',
    'reproductive health': 'Reproductive Health',
    'principles of inheritance and variation': 'Principles of Inheritance and Variation',
    'principles of inheritance': 'Principles of Inheritance and Variation',
    'molecular basis of inheritance': 'Molecular Basis of Inheritance',
    'evolution': 'Evolution',
    'human health and disease': 'Human Health and Disease',
    'microbes in human welfare': 'Microbes in Human Welfare',
    'biotechnology principles and processes': 'Biotechnology: Principles and Processes',
    'biotechnology: principles and processes': 'Biotechnology: Principles and Processes',
    'biotechnology - principles': 'Biotechnology: Principles and Processes',
    'biotechnology and its applications': 'Biotechnology and Its Applications',
    'organisms and populations': 'Organisms and Populations',
    'ecosystem': 'Ecosystem',
    'biodiversity and conservation': 'Biodiversity and Conservation',
}

# Explicitly disallowed non-biology domains
OUT_OF_SYLLABUS_DOMAINS = [
    # Physics
    "kinematics", "projectile", "quantum", "gravity", "newton law", "newton's", "thermodynamics physics", "electromagnetism", "optics ray", "optics", "optical", "prism", "refraction", "reflection light", "diffraction", "semiconductors physics", "relativity", "nuclear physics", "electric flux", "gauss law", "capacitance", "velocity", "acceleration", "friction", "moment of inertia", "magnetic field", "kirchhoff",
    # Chemistry
    "organic chemistry mechanism", "sn1", "sn2", "electrochemistry", "stoichiometry", "thermodynamics enthalpy", "coordination compounds chemistry", "periodic table trends", "haloalkanes", "alcohols phenols ethers", "polymers chemistry", "molarity", "molality", "chemical kinetics", "equilibrium constant", "le chatelier", "redox",
    # Math
    "integration", "differentiation math", "calculus", "trigonometry", "algebra", "geometry", "matrices", "determinants", "probability math", "statistics math", "complex numbers", "vectors math",
    # General non-science / Programming
    "python", "javascript", "react", "programming", "coding", "java", "c++", "html", "css", "sql", "database", "algorithm",
    "movie", "celebrity", "cricket", "football", "politics", "election", "stock market", "cryptocurrency", "bitcoin", "history", "geography", "economics"
]

OUT_OF_SYLLABUS_MESSAGE = (
    "👩‍⚕️ **Dr. Priya (AI Biology Mentor):**\n"
    "*\"I am strictly specialized in the **BioNEETPro NEET Biology Syllabus** (Class 11 & Class 12 NCERT Botany and Zoology).*\"\n\n"
    "⚠️ **Syllabus Boundary Notice:**\n"
    "Your question appears to be outside our approved 38-chapter Biology curriculum (or belongs to non-biology domains like Physics, Chemistry, or general topics).\n\n"
    "📚 **What you can ask me instead:**\n"
    "• *Human Physiology (Heart, Brain, Bones, Blood, Digestion, Excretion, Endocrine)*\n"
    "• *Plant Physiology (Photosynthesis, Respiration, Plant Hormones)*\n"
    "• *Genetics & Evolution (Mendel's Laws, DNA Replication, Lac Operon)*\n"
    "• *Cell Biology, Biotechnology, Reproduction, or Ecology*\n\n"
    "Please rephrase your doubt around an NCERT Biology concept!"
)


class SyllabusValidator:
    """
    Validates queries against the 38-chapter NEET Biology syllabus.
    """
    def __init__(self, syllabus: Dict[str, Any] = OFFICIAL_SYLLABUS):
        self.syllabus = syllabus
        self._ensure_syllabus_file()
        self.all_keywords = self._build_keyword_index()

    def _ensure_syllabus_file(self):
        if not SYLLABUS_FILE.exists():
            SYLLABUS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(SYLLABUS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.syllabus, f, indent=2)

    def _build_keyword_index(self) -> List[Tuple[str, str, str, str]]:
        index = []
        for class_key, class_data in self.syllabus.items():
            for unit_key, unit_data in class_data.items():
                for chap_id, chap_data in unit_data["chapters"].items():
                    for kw in chap_data["keywords"]:
                        index.append((kw.lower(), chap_id, chap_data["chapter_name"], unit_data["unit_name"]))
        return index

    _tb_vocab: Optional[Dict[str, int]] = None  # word -> chunk-hit count (lazy, cached)

    def _textbook_vocab(self) -> Dict[str, int]:
        """Chunk-hit counts per word from the ingested NCERT index (built once)."""
        if SyllabusValidator._tb_vocab is not None:
            return SyllabusValidator._tb_vocab
        vocab: Dict[str, int] = {}
        try:
            idx_file = DATA_DIR / "ncert_textbook_index.json"
            if idx_file.exists():
                with open(idx_file, "r", encoding="utf-8") as f:
                    chunks = json.load(f)
                for c in chunks:
                    words = set(re.findall(r"[a-z]{5,}", str(c.get("text", "")).lower()))
                    for w in words:
                        vocab[w] = vocab.get(w, 0) + 1
        except Exception:
            pass
        SyllabusValidator._tb_vocab = vocab
        return vocab

    def _textbook_rare_hits(self, clean_query: str) -> List[str]:
        vocab = self._textbook_vocab()
        if not vocab:
            return []
        tokens = set(re.findall(r"[a-z]{5,}", clean_query))
        hits = [t for t in tokens if 1 <= vocab.get(t, 0) <= 15]
        return sorted(hits, key=lambda t: vocab.get(t, 99))

    def check_query_syllabus(self, query: str) -> Dict[str, Any]:
        """
        Validates whether a query belongs to the NEET Biology syllabus.
        Returns validation status, matched chapter info, or out-of-syllabus guidance.
        """
        clean = (query or "").lower().strip()
        if not clean:
            return {"is_valid": False, "reason": "empty_query", "message": "Please enter a biology question."}

        # 1. Reject explicitly non-biology queries
        for banned in OUT_OF_SYLLABUS_DOMAINS:
            if re.search(r"\b" + re.escape(banned) + r"\b", clean):
                return {
                    "is_valid": False,
                    "reason": "non_biology_domain",
                    "matched_out_domain": banned,
                    "refusal_message": OUT_OF_SYLLABUS_MESSAGE,
                }

        # 2. Match against biology keywords & concepts
        matches = []
        for kw, chap_id, chap_name, unit_name in self.all_keywords:
            if re.search(r"\b" + re.escape(kw) + r"\b", clean) or (len(kw) > 4 and kw in clean):
                matches.append({"keyword": kw, "chapter_id": chap_id, "chapter_name": chap_name, "unit_name": unit_name})

        generic_bio_words = [
            "cell", "cells", "dna", "rna", "gene", "genes", "protein", "proteins", "blood", "bone", "bones",
            "skeleton", "skeletal", "heart", "brain", "leaf", "leaves", "urine", "kidney", "kidneys",
            "nephron", "nephrons", "neuron", "neurons", "muscle", "muscles", "sarcomere", "joints", "joint",
            "cartilage", "ligament", "tendon", "hormone", "hormones", "enzyme", "enzymes", "plants", "plant",
            "animals", "animal", "photosynthesis", "respiration", "bacteria", "virus", "reproduction", "embryo",
            "mitochondria", "chloroplast", "ribosome", "lysosome", "organelle", "organelles", "alveoli", "lungs",
            "lung", "stomach", "pancreas", "liver", "bile", "insulin", "glucose", "atp", "gamete", "gametes",
            "zygote", "flower", "flowers", "root", "roots", "stem", "stems", "xylem", "phloem", "stomata",
            "transpiration", "seed", "seeds", "fruit", "fruits", "ecology", "neet", "ncert", "biology",
            "mcq", "mcqs", "question", "questions", "quiz", "genetics", "evolution", "biotech", "biotechnology",
            "physiology", "botany", "zoology", "inheritance", "immunity", "pathogen", "rbc", "rbcs", "wbc", "wbcs",
            "spleen", "graveyard", "antibody", "antibodies", "antigen", "antigens", "platelet", "platelets",
            "earthworm", "pheretima", "annelid", "annelida", "setae", "metamerism", "clitellum", "leech",
            "frog", "rana", "toad", "rabbit", "snail", "pila", "starfish", "shark", "rohu",
            "ascaris", "tapeworm", "taenia", "plasmodium", "paramecium", "euglena", "hydra", "nereis",
            "iud", "iuds", "gfr", "bod", "sinoatrial", "countercurrent", "node of ranvier",
            "allele", "lactose", "meselson", "vntr", "mrna", "malaria", "sewage", "methanogen",
            "commensalism", "mutualism", "succession", "pioneer", "ommatidia", "endosperm",
            "stigma", "aestivation", "diabetes", "spermiogenesis", "myasthenia", "gout"
        ]
        has_generic_bio = any(re.search(r"\b" + re.escape(gb) + r"\b", clean) for gb in generic_bio_words)

        if not has_generic_bio:
            try:
                from concept_normalizer import concept_normalizer
                if concept_normalizer.normalize(clean):
                    has_generic_bio = True
            except Exception:
                pass

        # Textbook rarity fallback: a specific term (len>=5) appearing in only a
        # handful of NCERT chunks (1-15) is near-certainly a real NCERT term the
        # keyword lists missed (e.g. earthworm=5 chunks). Generic words hit dozens
        # of chunks and stay refused, so physics questions can't sneak through.
        if not has_generic_bio and not matches:
            try:
                hits = self._textbook_rare_hits(clean)
                if hits:
                    return {
                        "is_valid": True,
                        "confidence": "medium",
                        "chapter_id": "general_biology",
                        "chapter_name": "NEET Biology Curriculum",
                        "unit_name": "Core NCERT Concepts",
                        "matched_keywords": hits[:3],
                    }
            except Exception:
                pass

        if matches:
            top_match = matches[0]
            return {
                "is_valid": True,
                "confidence": "high" if len(matches) > 1 else "medium",
                "chapter_id": top_match["chapter_id"],
                "chapter_name": top_match["chapter_name"],
                "unit_name": top_match["unit_name"],
                "matched_keywords": [m["keyword"] for m in matches[:5]],
            }

        if has_generic_bio:
            return {
                "is_valid": True,
                "confidence": "medium",
                "chapter_id": "general_biology",
                "chapter_name": "NEET Biology Curriculum",
                "unit_name": "Core NCERT Concepts",
                "matched_keywords": ["general_biology"],
            }

        # Non-matching question
        return {
            "is_valid": False,
            "reason": "outside_neet_syllabus",
            "refusal_message": OUT_OF_SYLLABUS_MESSAGE,
        }

    def get_canonical_chapter_name(self, name: str) -> str:
        """Normalizes chapter names."""
        clean_name = name.lower().strip()
        return CANONICAL_CHAPTER_NAMES.get(clean_name, name)

    def get_chapter_id_for_name(self, name: str) -> Optional[str]:
        """Fuzzy chapter lookup by name."""
        canonical = self.get_canonical_chapter_name(name).lower()
        for class_data in self.syllabus.values():
            for unit_data in class_data.values():
                for chap_id, chap_data in unit_data["chapters"].items():
                    if chap_data["chapter_name"].lower() == canonical:
                        return chap_id
        return None

    def validate_concept_syllabus(self, concept_title: str, chapter_name: str) -> bool:
        """Concept-level validation."""
        canon_chap = self.get_canonical_chapter_name(chapter_name)

        # Check against out of syllabus domains
        clean_title = concept_title.lower().strip()
        for banned in OUT_OF_SYLLABUS_DOMAINS:
            if re.search(r"\b" + re.escape(banned) + r"\b", clean_title):
                return False

        # Simple check: does the chapter exist in our syllabus?
        return self.get_chapter_id_for_name(canon_chap) is not None

    def normalize_chapter_id(self, raw: str) -> Optional[str]:
        """Accepts frontend (c1) and backend (c01) forms; maps removed NCERT chapters to rationalized set."""
        if not raw:
            return None
        clean = str(raw).strip().lower()
        m = re.fullmatch(r"c0*(\d{1,2})", clean)
        if m:
            num = int(m.group(1))
            # Legacy pre-rationalization frontend ids must map first:
            # numbering diverged (e.g. frontend c23 = Reproduction in Organisms,
            # backend c23 = Sexual Reproduction in Flowering Plants).
            legacy_map = {
                11: "c13", 12: "c13", 23: "c24", 31: "c30", 38: "c35",
            }
            if num in legacy_map:
                return legacy_map[num]
            candidate = f"c{num:02d}"
            if self.chapter_exists(candidate):
                return candidate
            return None
        # Try name lookup as fallback
        return self.get_chapter_id_for_name(str(raw))

    def chapter_exists(self, chapter_id: str) -> bool:
        for class_data in self.syllabus.values():
            for unit_data in class_data.values():
                if chapter_id in unit_data.get("chapters", {}):
                    return True
        return False


syllabus_validator = SyllabusValidator()
