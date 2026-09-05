"""Tutor evaluation corpus: 110 distinct Biology prompts.

Each entry: prompt, topic tokens (characteristic NCERT terms; at least one
must appear in title+reply+evidence), chapter_hint (substring expected in the
returned chapter name; None = tokens-only judgement).

Phrasing, topics, and switch pairs here are the VISIBLE set. The holdout set
(tutor_evaluation/holdout.py) uses different topics/phrasings and is run last.
"""
CORPUS = [
    # ---- CELL BIOLOGY (10) ----
    dict(prompt="teach me cell membrane and its parts", tokens=["membrane", "phospholipid", "bilayer"], chapter="cell"),
    dict(prompt="can you explain nucleus structure", tokens=["nucleus", "nucleolus", "chromatin"], chapter="cell"),
    dict(prompt="what are mitochondria and why are they important", tokens=["mitochondria", "atp", "cristae"], chapter="cell"),
    dict(prompt="help me understand ribosomes", tokens=["ribosome", "protein", "rrna"], chapter="cell"),
    dict(prompt="lysosome function please", tokens=["lysosome", "hydrolytic", "suicidal"], chapter="cell"),
    dict(prompt="tell me about endoplasmic reticulum", tokens=["endoplasmic", "reticulum", "rough", "smooth"], chapter="cell"),
    dict(prompt="explain Golgi apparatus in simple words", tokens=["golgi", "cisternae", "glycosylation"], chapter="cell"),
    dict(prompt="what happens in cell cycle", tokens=["cell cycle", "interphase", "mitosis"], chapter="cell cycle"),
    dict(prompt="teach mitosis stages for NEET", tokens=["mitosis", "prophase", "metaphase", "anaphase"], chapter="cell cycle"),
    dict(prompt="i don't understand meiosis", tokens=["meiosis", "homologous", "crossing over"], chapter="cell cycle"),
    # ---- BIOMOLECULES (8) ----
    dict(prompt="teach me carbohydrates", tokens=["carbohydrate", "glucose", "monosaccharide"], chapter="biomolecule"),
    dict(prompt="explain proteins and their structure", tokens=["protein", "amino acid", "peptide"], chapter="biomolecule"),
    dict(prompt="what are lipids", tokens=["lipid", "fatty acid", "triglyceride"], chapter="biomolecule"),
    dict(prompt="nucleic acids explained", tokens=["nucleic", "nucleotide", "nitrogenous"], chapter="biomolecule"),
    dict(prompt="how do enzymes work", tokens=["enzyme", "active site", "substrate"], chapter="biomolecule"),
    dict(prompt="vitamins and deficiency diseases", tokens=["vitamin", "deficiency", "retinol"], chapter=None),
    dict(prompt="tell me about polysaccharides", tokens=["polysaccharide", "starch", "glycogen", "cellulose"], chapter="biomolecule"),
    dict(prompt="protein denaturation please", tokens=["denaturation", "tertiary", "primary structure"], chapter="biomolecule"),
    # ---- PLANT PHYSIOLOGY (12) ----
    dict(prompt="explain photosynthesis", tokens=["photosynthesis", "chlorophyll", "chloroplast"], chapter="photosynthesis"),
    dict(prompt="what happens in the light reaction", tokens=["light", "photosystem", "thylakoid", "atp", "nadph"], chapter="photosynthesis"),
    dict(prompt="teach me Calvin cycle steps", tokens=["calvin", "rubisco", "carboxylation", "g3p"], chapter="photosynthesis"),
    dict(prompt="plant respiration explained", tokens=["respiration", "glycolysis", "krebs", "mitochondria"], chapter="respiration"),
    dict(prompt="what is transpiration", tokens=["transpiration", "stomata", "cohesion"], chapter=None),
    dict(prompt="mineral nutrition in plants", tokens=["mineral", "nitrogen", "deficiency", "macronutrient"], chapter=None),
    dict(prompt="plant growth hormones overview", tokens=["auxin", "gibberellin", "cytokinin"], chapter="growth"),
    dict(prompt="what is photoperiodism", tokens=["photoperiod"], chapter=None,
         expect_refusal=True),  # coverage gap: only incidental mention exists
    dict(prompt="how does water travel up in tall trees", tokens=["xylem", "transpiration pull", "cohesion"], chapter=None),
    dict(prompt="explain phloem transport", tokens=["phloem", "translocation", "pressure flow", "sieve"], chapter=None),
    dict(prompt="teach me glycolysis", tokens=["glycolysis", "pyruvate", "cytoplasm"], chapter="respiration"),
    dict(prompt="kreb cycle steps please", tokens=["krebs", "citric", "acetyl", "oxaloacetate"], chapter="respiration"),
    # ---- REPRODUCTION (14) ----
    dict(prompt="can u teach me flower and its parts", tokens=["flower", "sepal", "petal", "stamen", "carpel"], chapter="morphology"),
    dict(prompt="explain androecium", tokens=["androecium", "stamen", "anther", "filament"], chapter="morphology"),
    dict(prompt="what is gynoecium", tokens=["gynoecium", "carpel", "ovary", "stigma", "style"], chapter="morphology"),
    dict(prompt="tell me about pollen grains", tokens=["pollen", "microspore", "exine", "intine"], chapter="reproduction"),
    dict(prompt="ovule structure please", tokens=["ovule", "nucellus", "integument", "micropyle"], chapter="reproduction"),
    dict(prompt="how does pollination happen", tokens=["pollination", "anemophily", "entomophily"], chapter="reproduction"),
    dict(prompt="what is fertilization in plants", tokens=["fertilization", "syngamy", "zygote"], chapter="reproduction"),
    dict(prompt="explain double fertilization", tokens=["double fertilization", "triple fusion", "endosperm"], chapter="reproduction"),
    dict(prompt="teach me embryo development in plants", tokens=["embryo", "globular", "heart-shaped", "cotyledon"], chapter="reproduction"),
    dict(prompt="how are seeds formed", tokens=["seed", "endosperm", "testa", "dormancy"], chapter="reproduction"),
    dict(prompt="fruit formation explained", tokens=["fruit", "ovary wall", "pericarp", "parthenocarpy"], chapter="reproduction"),
    dict(prompt="sexual reproduction in flowering plants overview", tokens=["flower", "pollination", "embryo sac"], chapter="reproduction"),
    dict(prompt="parts of a flower for NEET", tokens=["calyx", "corolla", "androecium", "gynoecium"], chapter="morphology"),
    dict(prompt="embryo sac structure", tokens=["embryo sac", "synergid", "antipodal", "polar nuclei"], chapter="reproduction"),
    # ---- HUMAN PHYSIOLOGY (16) ----
    dict(prompt="explain digestion of food", tokens=["digestion", "amylase", "pepsin", "trypsin"], chapter="digestion"),
    dict(prompt="how does breathing work", tokens=["breathing", "diaphragm", "alveoli", "inspiration"], chapter="breathing"),
    dict(prompt="gas exchange in alveoli", tokens=["alveoli", "diffusion", "oxygen", "carbon dioxide"], chapter="breathing"),
    dict(prompt="teach me cardiac cycle", tokens=["cardiac", "systole", "diastole"], chapter="circulation"),
    dict(prompt="blood circulation pathway", tokens=["circulation", "pulmonary", "systemic", "ventricle"], chapter="circulation"),
    dict(prompt="what is a nephron", tokens=["nephron", "glomerulus", "filtrate", "tubule"], chapter="excretory"),
    dict(prompt="explain urine formation", tokens=["urine", "filtration", "reabsorption", "secretion"], chapter="excretory"),
    dict(prompt="nervous system overview", tokens=["neuron", "axon", "dendrite", "synapse"], chapter="neural"),
    dict(prompt="what happens at a synapse", tokens=["synapse", "neurotransmitter", "acetylcholine"], chapter="neural"),
    dict(prompt="endocrine glands and hormones", tokens=["endocrine", "pituitary", "thyroid", "hormone"], chapter="coordination"),
    dict(prompt="how does insulin work", tokens=["insulin", "glucagon", "blood sugar", "pancreas"], chapter="coordination"),
    dict(prompt="immunity types explained", tokens=["immunity", "antibody", "antigen", "lymphocyte"], chapter="health"),
    dict(prompt="human reproductive system", tokens=["testis", "ovary", "gamete", "uterus"], chapter="reproduction"),
    dict(prompt="explain sliding filament theory", tokens=["actin", "myosin", "sarcomere", "troponin"], chapter="locomotion"),
    dict(prompt="how do bones and muscles move joints", tokens=["joint", "muscle", "tendon", "ligament"], chapter="locomotion"),
    dict(prompt="ECG and heart sounds", tokens=["ecg", "lub", "dub", "cardiac"], chapter="circulation"),
    # ---- GENETICS (12) ----
    dict(prompt="explain Mendel laws of inheritance", tokens=["mendel", "dominance", "segregation"], chapter="inheritance"),
    dict(prompt="monohybrid cross ratio please", tokens=["monohybrid", "3:1", "punnett"], chapter="inheritance"),
    dict(prompt="dihybrid cross explained", tokens=["dihybrid", "9:3:3:1", "independent assortment"], chapter="inheritance"),
    dict(prompt="how does DNA replicate", tokens=["replicat", "semiconservative", "helicase", "okazaki", "leading strand"], chapter="molecular"),
    dict(prompt="teach me transcription", tokens=["transcription", "mrna", "promoter", "rna polymerase"], chapter="molecular"),
    dict(prompt="translation process in protein synthesis", tokens=["translation", "ribosome", "codon", "trna"], chapter="molecular"),
    dict(prompt="what is the genetic code", tokens=["genetic code", "codon", "degenerate", "universal"], chapter="molecular"),
    dict(prompt="causes of mutation", tokens=["mutation", "mutagen", "point mutation", "frameshift"], chapter="molecular"),
    dict(prompt="linkage and crossing over", tokens=["linkage", "recombination", "morgan"], chapter="inheritance"),
    dict(prompt="lac operon concept", tokens=["operon", "lactose", "repressor", "operator"], chapter="molecular"),
    dict(prompt="DNA fingerprinting basics", tokens=["fingerprinting", "vntr", "probe"], chapter="molecular"),
    dict(prompt="chromosomal disorders like Down syndrome", tokens=["trisomy", "down", "klinefelter", "turner"], chapter="inheritance"),
    # ---- EVOLUTION (8) ----
    dict(prompt="explain natural selection", tokens=["natural selection", "fitness", "darwin"], chapter="evolution"),
    dict(prompt="what is Darwinism", tokens=["darwin", "struggle", "survival of the fittest"], chapter="evolution"),
    dict(prompt="genetic drift meaning", tokens=["genetic drift", "bottleneck", "founder effect"], chapter="evolution"),
    dict(prompt="Hardy Weinberg principle", tokens=["hardy", "weinberg", "equilibrium", "p2"], chapter="evolution"),
    dict(prompt="how does speciation occur", tokens=["speciation", "reproductive isolation", "allopatric"], chapter="evolution"),
    dict(prompt="adaptive radiation examples", tokens=["adaptive radiation", "darwin", "finches", "lemur"], chapter="evolution"),
    dict(prompt="evidence of evolution from fossils", tokens=["fossil", "homologous", "analogous", "vestigial"], chapter="evolution"),
    dict(prompt="Lamarck theory vs Darwin", tokens=["lamarck", "acquired characters", "darwin"], chapter="evolution"),
    # ---- ECOLOGY (10) ----
    dict(prompt="what is an ecosystem", tokens=["ecosystem", "biotic", "abiotic", "producers"], chapter="ecosystem"),
    dict(prompt="explain food chain", tokens=["food chain", "trophic", "producer", "consumer"], chapter="ecosystem"),
    dict(prompt="food web vs food chain", tokens=["food web", "interconnected", "trophic"], chapter="ecosystem"),
    dict(prompt="ecological pyramids types", tokens=["pyramid", "biomass", "energy", "number"], chapter="ecosystem"),
    dict(prompt="population growth curves", tokens=["exponential", "logistic", "carrying capacity"], chapter="organisms"),
    dict(prompt="what is biodiversity", tokens=["biodiversity", "species richness", "hotspot"], chapter="biodiversity"),
    dict(prompt="ecological succession stages", tokens=["succession", "pioneer", "climax", "sere"], chapter="organisms"),
    dict(prompt="nitrogen cycle steps", tokens=["nitrogen", "nitrification", "denitrification", "ammonification"], chapter="ecosystem"),
    dict(prompt="carbon cycle explained", tokens=["carbon", "photosynthesis", "respiration", "fossil fuel"], chapter="ecosystem"),
    dict(prompt="population interactions like predation", tokens=["predation", "competition", "mutualism", "parasitism"], chapter="organisms"),
    # ---- MICROBES / BIOTECH (10) ----
    dict(prompt="tell me about bacteria", tokens=["bacteria", "peptidoglycan", "binary fission", "eubacteria"], chapter="classification"),
    dict(prompt="virus structure and replication", tokens=["virus", "capsid", "bacteriophage", "lytic", "viroid"], chapter="classification"),  # multi-aspect: needs virus row, not pure replication
    dict(prompt="fermentation process", tokens=["fermentation", "anaerobic", "lactic acid", "ethanol"], chapter="respiration"),
    dict(prompt="recombinant DNA steps", tokens=["recombinant", "plasmid", "restriction", "ligase"], chapter="biotechnology"),
    dict(prompt="how does PCR work", tokens=["pcr", "denaturation", "annealing", "taq polymerase"], chapter="biotechnology"),
    dict(prompt="what is cloning", tokens=["cloning", "dolly", "somatic cell nuclear transfer"], chapter="biotechnology"),
    dict(prompt="gene therapy basics", tokens=["gene therapy", "vector", "scid"], chapter="biotechnology"),
    dict(prompt="Bt cotton explained", tokens=["bt cotton", "cry", "bacillus thuringiensis"], chapter="biotechnology"),
    dict(prompt="role of microbes in sewage treatment", tokens=["sewage", "flocs", "bod", "aeration"], chapter="microbes"),
    dict(prompt="antibiotics from microbes", tokens=["antibiotic", "penicillin", "alexander fleming"], chapter="microbes"),
    # ---- ANATOMY / DIVERSITY (10) ----
    dict(prompt="plant tissues types", tokens=["parenchyma", "collenchyma", "sclerenchyma", "xylem"], chapter="anatomy"),
    dict(prompt="animal epithelial tissue", tokens=["epithelial", "squamous", "cuboidal", "columnar"], chapter="tissues"),
    dict(prompt="root morphology", tokens=["root", "taproot", "fibrous", "root hair"], chapter="morphology"),
    dict(prompt="leaf venation and phyllotaxy", tokens=["venation", "reticulate", "parallel", "phyllotaxy"], chapter="morphology"),
    dict(prompt="five kingdom classification", tokens=["whittaker", "monera", "protista", "fungi", "plantae"], chapter="classification"),
    dict(prompt="what is binomial nomenclature", tokens=["binomial", "genus", "species", "linnaeus"], chapter="living world"),
    dict(prompt="taxonomic hierarchy levels", tokens=["kingdom", "phylum", "class", "order", "family", "genus"], chapter="living world"),
    dict(prompt="difference between algae and fungi", tokens=["algae", "fungi", "chlorophyll", "chitin"], chapter="classification"),
    dict(prompt="cockroach morphology", tokens=["cockroach", "periplaneta", "malpighian", "ommatidia"], chapter="tissues"),
    dict(prompt="frog anatomy overview", tokens=["frog", "rana", "hibernation", "tympanum"], chapter="tissues"),
]

assert len(CORPUS) >= 100, f"corpus too small: {len(CORPUS)}"

# PhRase variations for Phase 5 (same concept, unseen wordings).
PHRASE_VARIANTS = {
    "flower": ["can you explain flower structure", "what are the parts of a flower?",
               "help me understand flower morphology", "tell me about the structure of a flower",
               "flower parts please", "i don't understand the flower", "teach flower for NEET",
               "explain flower in simple words", "FLOWER AND ITS PARTS???", "flower"],
    "nephron": ["nephron structure pls", "explain nephron simply", "what does a nephron do",
                "nephron diagram explanation", "tell me nephron", "NEPHRON"],
    "photosynthesis": ["photosynthesis pls explain", "how does photosynthesis work",
                       "why do plants photosynthesize", "photosynthesis equation meaning"],
    "dna replication": ["dna replication steps", "how is dna copied", "explain semiconservative replication"],
    "cardiac cycle": ["cardiac cycle phases", "explain heartbeat mechanism", "systole vs diastole"],
}

# Topic-switch pairs for contamination tests (prior -> current).
SWITCH_PAIRS = [
    ("Explain cardiac cycle.", "can u teach me flower and its parts"),
    ("Explain photosynthesis.", "Now teach me nephron."),
    ("Teach me genetics.", "Explain digestion of food."),
    ("What is an ecosystem?", "How does DNA replicate?"),
    ("Explain respiration in plants.", "Tell me about the nervous system."),
    ("Teach me flower structure.", "Explain blood circulation."),
    ("Explain cell membrane.", "What is biodiversity?"),
    ("What is immunity?", "Teach me Calvin cycle."),
    ("Explain natural selection.", "What is a synapse?"),
    ("Tell me about bacteria.", "Explain meiosis."),
    ("What is digestion?", "Teach me double fertilization."),
    ("Explain transcription.", "What is a food web?"),
]

# Genuine follow-ups (must KEEP prior topic).
FOLLOWUPS = [
    ("Explain photosynthesis.", "make it simpler"),
    ("Explain photosynthesis.", "what about the light reaction?"),
    ("Teach me nephron.", "what does it do?"),
    ("Explain cardiac cycle.", "why?"),
    ("Teach me flower structure.", "give another example"),
    ("What is DNA replication?", "explain that again"),
    ("Explain meiosis.", "what about the next step?"),
    ("Teach me immunity.", "what does that mean?"),
]
