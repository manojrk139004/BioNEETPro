// ═══════════════════════════════════════════════════════════
//  BIONEET PRO — Configuration & Data
// ═══════════════════════════════════════════════════════════

import { initializeApp } from "https://www.gstatic.com/firebasejs/11.0.0/firebase-app.js";
import { getFirestore, collection, addDoc, getDocs, query, where, doc, setDoc, getDoc, deleteDoc, orderBy, limit } from "https://www.gstatic.com/firebasejs/11.0.0/firebase-firestore.js";
import { getAuth } from "https://www.gstatic.com/firebasejs/11.0.0/firebase-auth.js";

// ─── Firebase Config ───────────────────────────────────────
const firebaseConfig = {
  apiKey: "AIzaSyAMRHMWasox-in3OH2UfuIriCU6K14M2d8",
  authDomain: "bioneet-pro-a73d5.firebaseapp.com",
  projectId: "bioneet-pro-a73d5",
  storageBucket: "bioneet-pro-a73d5.firebasestorage.app",
  messagingSenderId: "610644641159",
  appId: "1:610644641159:web:630ee41b05390491f23f22"
};

const app = initializeApp(firebaseConfig);
const db = getFirestore(app);
const auth = getAuth(app);

// ─── API Config ────────────────────────────────────────────
const AI_BACKEND_URL = window.BIONEET_AI_BACKEND_URL || "http://127.0.0.1:5000";

// ─── Chapters Data ─────────────────────────────────────────
const CHAPTERS = [
  {id:'c1',name:'The Living World',cls:11,color:'#00E676',topics:['Biodiversity','Nomenclature','Classification','Taxonomy'],importance:3},
  {id:'c2',name:'Biological Classification',cls:11,color:'#00BCD4',topics:['Five Kingdom','Monera','Protista','Fungi','Plantae','Animalia'],importance:4},
  {id:'c3',name:'Plant Kingdom',cls:11,color:'#69F0AE',topics:['Algae','Bryophytes','Pteridophytes','Gymnosperms','Angiosperms'],importance:4},
  {id:'c4',name:'Animal Kingdom',cls:11,color:'#448AFF',topics:['Basis of Classification','Non-Chordates','Chordates'],importance:5},
  {id:'c5',name:'Morphology of Flowering Plants',cls:11,color:'#B388FF',topics:['Root','Stem','Leaf','Flower','Fruit','Seed'],importance:4},
  {id:'c6',name:'Anatomy of Flowering Plants',cls:11,color:'#FF80AB',topics:['Tissue Systems','Dicot & Monocot Anatomy'],importance:4},
  {id:'c7',name:'Structural Organisation in Animals',cls:11,color:'#80DEEA',topics:['Cockroach','Earthworm','Frog'],importance:3},
  {id:'c8',name:'Cell – The Unit of Life',cls:11,color:'#FFD600',topics:['Cell Theory','Prokaryotes','Eukaryotes','Cell Organelles'],importance:5},
  {id:'c9',name:'Biomolecules',cls:11,color:'#FF5252',topics:['Carbohydrates','Proteins','Lipids','Nucleic Acids','Enzymes'],importance:5},
  {id:'c10',name:'Cell Cycle and Cell Division',cls:11,color:'#18FFFF',topics:['Cell Cycle','Mitosis','Meiosis'],importance:5},
  {id:'c11',name:'Transport in Plants',cls:11,color:'#69F0AE',topics:['Diffusion','Osmosis','Mineral Transport','Phloem'],importance:3},
  {id:'c12',name:'Mineral Nutrition',cls:11,color:'#FFD600',topics:['Essential Minerals','Deficiency','Nitrogen Fixation'],importance:3},
  {id:'c13',name:'Photosynthesis',cls:11,color:'#00E676',topics:['Light Reactions','Calvin Cycle','C4 Pathway','CAM'],importance:5},
  {id:'c14',name:'Respiration in Plants',cls:11,color:'#448AFF',topics:['Glycolysis','Krebs Cycle','ETC'],importance:4},
  {id:'c15',name:'Plant Growth and Development',cls:11,color:'#B388FF',topics:['Growth Phases','Plant Hormones','Photoperiodism'],importance:3},
  {id:'c16',name:'Digestion and Absorption',cls:12,color:'#FF5252',topics:['Digestive System','Digestion','Absorption'],importance:5},
  {id:'c17',name:'Breathing and Exchange of Gases',cls:12,color:'#18FFFF',topics:['Respiratory Organs','Breathing Mechanism','Gas Exchange'],importance:4},
  {id:'c18',name:'Body Fluids and Circulation',cls:12,color:'#FFB300',topics:['Blood','Heart','Cardiac Cycle','ECG'],importance:5},
  {id:'c19',name:'Excretory Products and Elimination',cls:12,color:'#69F0AE',topics:['Kidneys','Urine Formation','Tubular Reabsorption','Regulation'],importance:5},
  {id:'c20',name:'Locomotion and Movement',cls:12,color:'#B388FF',topics:['Muscle Types','Muscle Contraction','Skeleton','Joints'],importance:4},
  {id:'c21',name:'Neural Control and Coordination',cls:12,color:'#FF80AB',topics:['Neuron','Brain','Spinal Cord','Reflex Action'],importance:5},
  {id:'c22',name:'Chemical Coordination',cls:12,color:'#80DEEA',topics:['Endocrine Glands','Hormones','Feedback Mechanisms'],importance:5},
  {id:'c23',name:'Reproduction in Organisms',cls:12,color:'#FFB300',topics:['Types of Reproduction','Asexual Reproduction'],importance:3},
  {id:'c24',name:'Sexual Reproduction in Flowering Plants',cls:12,color:'#00E676',topics:['Flower Structure','Pollination','Fertilisation','Seed Development'],importance:5},
  {id:'c25',name:'Human Reproduction',cls:12,color:'#448AFF',topics:['Male Reproductive System','Female Reproductive System','Gametogenesis'],importance:5},
  {id:'c26',name:'Reproductive Health',cls:12,color:'#B388FF',topics:['Contraception','STIs','MTP','Infertility'],importance:4},
  {id:'c27',name:'Principles of Inheritance',cls:12,color:'#FF5252',topics:["Mendel's Laws","Monohybrid","Dihybrid","Chromosomal Theory"],importance:5},
  {id:'c28',name:'Molecular Basis of Inheritance',cls:12,color:'#18FFFF',topics:['DNA Structure','Replication','Transcription','Translation'],importance:5},
  {id:'c29',name:'Evolution',cls:12,color:'#FFD600',topics:['Origin of Life','Theories of Evolution','Natural Selection','Speciation'],importance:4},
  {id:'c30',name:'Human Health and Disease',cls:12,color:'#69F0AE',topics:['Immunity','Vaccines','AIDS','Cancer','Drugs'],importance:5},
  {id:'c31',name:'Strategies for Enhancement in Food Production',cls:12,color:'#B388FF',topics:['Animal Breeding','Plant Breeding','Tissue Culture'],importance:3},
  {id:'c32',name:'Microbes in Human Welfare',cls:12,color:'#FF80AB',topics:['Household uses','Industrial uses','Sewage Treatment','Biogas'],importance:4},
  {id:'c33',name:'Biotechnology – Principles',cls:12,color:'#80DEEA',topics:['Genetic Engineering','rDNA Technology','PCR','Gel Electrophoresis'],importance:5},
  {id:'c34',name:'Biotechnology and its Applications',cls:12,color:'#FFB300',topics:['GM Crops','Medical Applications','Ethical Issues'],importance:4},
  {id:'c35',name:'Organisms and Populations',cls:12,color:'#00E676',topics:['Organisms and Environment','Populations','Interactions'],importance:3},
  {id:'c36',name:'Ecosystem',cls:12,color:'#448AFF',topics:['Structure','Productivity','Decomposition','Energy Flow','Nutrient Cycling'],importance:4},
  {id:'c37',name:'Biodiversity and Conservation',cls:12,color:'#B388FF',topics:['Biodiversity Levels','Threats','Conservation','Hotspots'],importance:4},
  {id:'c38',name:'Environmental Issues',cls:12,color:'#FF5252',topics:['Pollution','Global Warming','Ozone Depletion','Waste Management'],importance:3}
];

// ─── Seed MCQs ─────────────────────────────────────────────
const SEED_MCQS = [
  {id:1,q:'Which organelle is called the powerhouse of the cell?',opts:['Golgi apparatus','Mitochondria','Nucleus','Ribosome'],correct:1,chapter:'Cell – The Unit of Life',diff:'Easy',expl:'Mitochondria produce ATP through cellular respiration, hence called the powerhouse of the cell.'},
  {id:2,q:'The process by which plants prepare food using sunlight is:',opts:['Respiration','Transpiration','Photosynthesis','Fermentation'],correct:2,chapter:'Photosynthesis',diff:'Easy',expl:'Photosynthesis converts CO₂ and H₂O into glucose using light energy.'},
  {id:3,q:'DNA replication is:',opts:['Conservative','Semi-conservative','Dispersive','Both A and B'],correct:1,chapter:'Molecular Basis of Inheritance',diff:'Medium',expl:'Semi-conservative — each new DNA molecule retains one old strand and one new strand. Proved by Meselson-Stahl experiment.'},
  {id:4,q:'Which of the following is NOT a nucleotide component?',opts:['Nitrogen base','Phosphate group','Deoxyribose sugar','Amino acid'],correct:3,chapter:'Biomolecules',diff:'Medium',expl:'A nucleotide = nitrogen base + pentose sugar + phosphate group. Amino acids are protein components.'},
  {id:5,q:'The Calvin cycle occurs in which part of the chloroplast?',opts:['Thylakoid membrane','Stroma','Grana','Outer membrane'],correct:1,chapter:'Photosynthesis',diff:'Medium',expl:'Calvin cycle (dark reactions) occurs in the stroma of chloroplasts.'},
  {id:6,q:'Which hormone is called the birth hormone?',opts:['Oxytocin','Progesterone','Estrogen','LH'],correct:0,chapter:'Chemical Coordination',diff:'Easy',expl:'Oxytocin stimulates uterine contractions during childbirth.'},
  {id:7,q:'Number of chromosomes in a human somatic cell is:',opts:['23','44','46','48'],correct:2,chapter:'Cell Cycle and Cell Division',diff:'Easy',expl:'Human somatic cells are diploid (2n) with 46 chromosomes (23 pairs).'},
  {id:8,q:'Krebs cycle takes place in:',opts:['Cytoplasm','Mitochondrial matrix','Nucleus','Chloroplast'],correct:1,chapter:'Respiration in Plants',diff:'Medium',expl:'The Krebs cycle (Citric Acid Cycle) occurs in the mitochondrial matrix.'},
  {id:9,q:'Which of these is a vestigial organ in humans?',opts:['Liver','Appendix','Kidney','Heart'],correct:1,chapter:'Evolution',diff:'Easy',expl:'The vermiform appendix is a vestigial organ in humans.'},
  {id:10,q:'Bt cotton is resistant to which pest?',opts:['Aphids','Bollworms','White flies','Stem borers'],correct:1,chapter:'Biotechnology and its Applications',diff:'Medium',expl:'Bt cotton contains Cry genes from Bacillus thuringiensis that kill bollworms.'},
  {id:11,q:'The functional unit of kidney is:',opts:['Neuron','Nephron','Lobule','Villus'],correct:1,chapter:'Excretory Products and Elimination',diff:'Easy',expl:'The nephron is the functional unit of the kidney.'},
  {id:12,q:'Which blood cells are responsible for immunity?',opts:['RBCs','Platelets','WBCs','All of these'],correct:2,chapter:'Body Fluids and Circulation',diff:'Easy',expl:'WBCs (Leucocytes) are responsible for the immune response.'},
  {id:13,q:'PCR stands for:',opts:['Protein Chain Reaction','Polymerase Chain Reaction','Polymer Creation Reaction','Peptide Chain Reaction'],correct:1,chapter:'Biotechnology – Principles',diff:'Easy',expl:'PCR — Polymerase Chain Reaction — amplifies specific DNA sequences in vitro.'},
  {id:14,q:'In C4 plants, CO₂ fixation first occurs in:',opts:['Bundle sheath cells','Mesophyll cells','Guard cells','Epidermis'],correct:1,chapter:'Photosynthesis',diff:'Hard',expl:'In C4 plants, CO₂ is first fixed in mesophyll cells to form oxaloacetate (4-carbon compound).'},
  {id:15,q:'Which enzyme is called the molecular scissors?',opts:['DNA ligase','DNA polymerase','Restriction endonuclease','RNA polymerase'],correct:2,chapter:'Biotechnology – Principles',diff:'Medium',expl:'Restriction endonucleases cut DNA at specific recognition sequences.'},
  {id:16,q:'Which part of the brain controls body temperature?',opts:['Cerebrum','Medulla oblongata','Hypothalamus','Cerebellum'],correct:2,chapter:'Neural Control and Coordination',diff:'Medium',expl:'Hypothalamus is the thermoregulatory centre of the body.'},
  {id:17,q:'The Rh factor in blood is named after:',opts:['Rhinoceros','Rhesus monkey','Rhine river','Rhododendron'],correct:1,chapter:'Body Fluids and Circulation',diff:'Easy',expl:'The Rh antigen was first found in Rhesus monkeys.'},
  {id:18,q:'Which vitamin is synthesised by bacteria in the human gut?',opts:['Vitamin A','Vitamin B12','Vitamin C','Vitamin D'],correct:1,chapter:'Human Health and Disease',diff:'Medium',expl:'Vitamin B12 is synthesised by gut bacteria and is essential for red blood cell formation.'},
  {id:19,q:'The process of losing water as vapour through leaves is:',opts:['Guttation','Transpiration','Translocation','Absorption'],correct:1,chapter:'Transport in Plants',diff:'Easy',expl:'Transpiration is the loss of water vapour through the stomata of leaves.'},
  {id:20,q:'Which is the largest gland in the human body?',opts:['Pancreas','Thyroid','Liver','Spleen'],correct:2,chapter:'Digestion and Absorption',diff:'Easy',expl:'The liver is the largest gland in the human body, weighing about 1.5 kg.'},
  {id:21,q:'Meiosis results in:',opts:['2 diploid cells','4 haploid cells','2 haploid cells','4 diploid cells'],correct:1,chapter:'Cell Cycle and Cell Division',diff:'Easy',expl:'Meiosis produces 4 genetically distinct haploid cells from a single diploid cell.'},
  {id:22,q:'The fluid mosaic model of cell membrane was proposed by:',opts:['Watson and Crick','Singer and Nicolson','Schleiden and Schwann','Fleming'],correct:1,chapter:'Cell – The Unit of Life',diff:'Medium',expl:'Singer and Nicolson (1972) proposed the fluid mosaic model of the cell membrane.'},
  {id:23,q:'Which nitrogenous base is found in RNA but not in DNA?',opts:['Adenine','Uracil','Guanine','Cytosine'],correct:1,chapter:'Molecular Basis of Inheritance',diff:'Easy',expl:'Uracil replaces Thymine in RNA.'},
  {id:24,q:'The site of protein synthesis in the cell is:',opts:['Mitochondria','Ribosome','Nucleus','Golgi apparatus'],correct:1,chapter:'Cell – The Unit of Life',diff:'Easy',expl:'Ribosomes are the site of protein synthesis (translation).'},
  {id:25,q:'Which of the following is an autoimmune disease?',opts:['AIDS','Rheumatoid Arthritis','Malaria','Dengue'],correct:1,chapter:'Human Health and Disease',diff:'Medium',expl:'Rheumatoid Arthritis is an autoimmune disease where the immune system attacks the joints.'},
  {id:26,q:'The first stable product of C3 cycle is:',opts:['Oxaloacetate','Phosphoglycerate (PGA)','RuBP','Glucose'],correct:1,chapter:'Photosynthesis',diff:'Medium',expl:'The first stable product of C3 (Calvin) cycle is 3-phosphoglycerate (3-PGA), a 3-carbon compound.'},
  {id:27,q:'Crossing over occurs during which phase of meiosis?',opts:['Prophase I','Metaphase I','Anaphase II','Telophase I'],correct:0,chapter:'Cell Cycle and Cell Division',diff:'Medium',expl:'Crossing over occurs during pachytene stage of Prophase I of meiosis.'},
  {id:28,q:'Which blood group is called the universal donor?',opts:['A','B','AB','O'],correct:3,chapter:'Body Fluids and Circulation',diff:'Easy',expl:'Blood group O is the universal donor as it has no A or B antigens.'},
  {id:29,q:'The study of fossils is called:',opts:['Ecology','Paleontology','Taxonomy','Anatomy'],correct:1,chapter:'Evolution',diff:'Easy',expl:'Paleontology is the study of prehistoric life through fossils.'},
  {id:30,q:'Restriction enzymes are primarily obtained from:',opts:['Virus','Fungi','Bacteria','Plants'],correct:2,chapter:'Biotechnology – Principles',diff:'Medium',expl:'Restriction endonucleases are primarily isolated from bacteria.'}
];

// ─── Data Store ────────────────────────────────────────────
const DB = {
  users: [],
  mcqs: [],
  videos: [],
  updates: [],
  results: [],
  bookmarks: [],
  currentUser: null,
  isAdmin: false
};

// Load from localStorage
function loadDB() {
  DB.mcqs = load('mcqs') || [];
  DB.users = load('users') || [];
  DB.videos = load('videos') || [];
  DB.updates = load('updates') || [];
  DB.results = load('results') || [];
  DB.bookmarks = load('bookmarks') || [];
  DB.currentUser = JSON.parse(localStorage.getItem('currentUser') || "null");
  DB.isAdmin = JSON.parse(localStorage.getItem('isAdmin') || "false");
}

function save(key) { if (DB[key] !== undefined) localStorage.setItem(key, JSON.stringify(DB[key])); }
function load(key) { const d = localStorage.getItem(key); return d ? JSON.parse(d) : null; }

// Initial load
loadDB();

// ─── Exports ───────────────────────────────────────────────
export { app, db, auth, collection, addDoc, getDocs, query, where, doc, setDoc, getDoc, deleteDoc, orderBy, limit };
export { firebaseConfig, AI_BACKEND_URL, CHAPTERS, SEED_MCQS, DB, save, load, loadDB };
