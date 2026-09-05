"""
BioNEETPro - Comprehensive Biology Concept Normalizer & Ontology Mapper
========================================================================
Provides robust biological concept identification, typo correction,
and canonical concept mapping for NEET Biology.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DATA_DIR = Path(__file__).resolve().parent / "data"
INDEX_FILE = DATA_DIR / "ncert_textbook_index.json"


class BiologyConceptNormalizer:
    """Normalizes biological aliases and terms to canonical concepts."""

    def __init__(self):
        # Canonical Aliases with standard lowercase chapter_id (c01 - c38)
        self.CONCEPT_ALIASES = {
            # Cell Biology (Chapter 8 / Unit 3)
            'powerhouse of cell': {'canonical_name': 'Mitochondria', 'concept_id': 'BIO-C08-01', 'chapter_id': 'c08', 'topic': 'Cell Organelles'},
            'powerhouse of the cell': {'canonical_name': 'Mitochondria', 'concept_id': 'BIO-C08-01', 'chapter_id': 'c08', 'topic': 'Cell Organelles'},
            "cell's powerhouse": {'canonical_name': 'Mitochondria', 'concept_id': 'BIO-C08-01', 'chapter_id': 'c08', 'topic': 'Cell Organelles'},
            'mitochondria': {'canonical_name': 'Mitochondria', 'concept_id': 'BIO-C08-01', 'chapter_id': 'c08', 'topic': 'Cell Organelles'},
            'mitochondrion': {'canonical_name': 'Mitochondria', 'concept_id': 'BIO-C08-01', 'chapter_id': 'c08', 'topic': 'Cell Organelles'},
            'cristae': {'canonical_name': 'Cristae', 'concept_id': 'BIO-C08-01', 'chapter_id': 'c08', 'topic': 'Cell Organelles'},
            'folds of mitochondria': {'canonical_name': 'Cristae', 'concept_id': 'BIO-C08-01', 'chapter_id': 'c08', 'topic': 'Cell Organelles'},
            'mitochondrial folds': {'canonical_name': 'Cristae', 'concept_id': 'BIO-C08-01', 'chapter_id': 'c08', 'topic': 'Cell Organelles'},
            'basic unit of life': {'canonical_name': 'Cell', 'concept_id': 'BIO-C08-00', 'chapter_id': 'c08', 'topic': 'Cell: The Unit of Life'},
            'structural and functional unit of life': {'canonical_name': 'Cell', 'concept_id': 'BIO-C08-00', 'chapter_id': 'c08', 'topic': 'Cell: The Unit of Life'},
            'cell': {'canonical_name': 'Cell', 'concept_id': 'BIO-C08-00', 'chapter_id': 'c08', 'topic': 'Cell: The Unit of Life'},
            'cells': {'canonical_name': 'Cell', 'concept_id': 'BIO-C08-00', 'chapter_id': 'c08', 'topic': 'Cell: The Unit of Life'},
            'suicide bags': {'canonical_name': 'Lysosomes', 'concept_id': 'BIO-C08-03', 'chapter_id': 'c08', 'topic': 'Cell Organelles'},
            'suicide bag': {'canonical_name': 'Lysosomes', 'concept_id': 'BIO-C08-03', 'chapter_id': 'c08', 'topic': 'Cell Organelles'},
            'suicidal bags': {'canonical_name': 'Lysosomes', 'concept_id': 'BIO-C08-03', 'chapter_id': 'c08', 'topic': 'Cell Organelles'},
            'lysosome': {'canonical_name': 'Lysosomes', 'concept_id': 'BIO-C08-03', 'chapter_id': 'c08', 'topic': 'Cell Organelles'},
            'lysosomes': {'canonical_name': 'Lysosomes', 'concept_id': 'BIO-C08-03', 'chapter_id': 'c08', 'topic': 'Cell Organelles'},
            'protein factory': {'canonical_name': 'Ribosome', 'concept_id': 'BIO-C08-05', 'chapter_id': 'c08', 'topic': 'Cell Organelles'},
            'site of protein synthesis': {'canonical_name': 'Ribosome', 'concept_id': 'BIO-C08-05', 'chapter_id': 'c08', 'topic': 'Cell Organelles'},
            'ribosome': {'canonical_name': 'Ribosome', 'concept_id': 'BIO-C08-05', 'chapter_id': 'c08', 'topic': 'Cell Organelles'},
            'ribosomes': {'canonical_name': 'Ribosome', 'concept_id': 'BIO-C08-05', 'chapter_id': 'c08', 'topic': 'Cell Organelles'},
            'packaging organelle': {'canonical_name': 'Golgi apparatus', 'concept_id': 'BIO-C08-06', 'chapter_id': 'c08', 'topic': 'Cell Organelles'},
            'golgi apparatus': {'canonical_name': 'Golgi apparatus', 'concept_id': 'BIO-C08-06', 'chapter_id': 'c08', 'topic': 'Cell Organelles'},
            'golgi body': {'canonical_name': 'Golgi apparatus', 'concept_id': 'BIO-C08-06', 'chapter_id': 'c08', 'topic': 'Cell Organelles'},
            'brain of cell': {'canonical_name': 'Nucleus', 'concept_id': 'BIO-C08-07', 'chapter_id': 'c08', 'topic': 'Cell Organelles'},
            'director of cell': {'canonical_name': 'Nucleus', 'concept_id': 'BIO-C08-07', 'chapter_id': 'c08', 'topic': 'Cell Organelles'},
            'nucleus': {'canonical_name': 'Nucleus', 'concept_id': 'BIO-C08-07', 'chapter_id': 'c08', 'topic': 'Cell Organelles'},

            # Photosynthesis & Chloroplast (Chapters 8 & 11/13)
            'kitchen of cell': {'canonical_name': 'Chloroplasts', 'concept_id': 'BIO-C13-04', 'chapter_id': 'c13', 'topic': 'Photosynthesis'},
            'food factory': {'canonical_name': 'Chloroplasts', 'concept_id': 'BIO-C13-04', 'chapter_id': 'c13', 'topic': 'Photosynthesis'},
            'food factory of the cell': {'canonical_name': 'Chloroplasts', 'concept_id': 'BIO-C13-04', 'chapter_id': 'c13', 'topic': 'Photosynthesis'},
            'food factory of cell': {'canonical_name': 'Chloroplasts', 'concept_id': 'BIO-C13-04', 'chapter_id': 'c13', 'topic': 'Photosynthesis'},
            'chloroplast': {'canonical_name': 'Chloroplasts', 'concept_id': 'BIO-C13-04', 'chapter_id': 'c13', 'topic': 'Photosynthesis'},
            'chloroplasts': {'canonical_name': 'Chloroplasts', 'concept_id': 'BIO-C13-04', 'chapter_id': 'c13', 'topic': 'Photosynthesis'},
            'photosynthesis': {'canonical_name': 'Photosynthesis', 'concept_id': 'BIO-C13-01', 'chapter_id': 'c13', 'topic': 'Photosynthesis in Higher Plants'},
            'food making process in plants': {'canonical_name': 'Photosynthesis', 'concept_id': 'BIO-C13-01', 'chapter_id': 'c13', 'topic': 'Photosynthesis in Higher Plants'},
            'light reaction': {'canonical_name': 'Photochemical Phase', 'concept_id': 'BIO-C13-02', 'chapter_id': 'c13', 'topic': 'Photosynthesis in Higher Plants'},
            'dark reaction': {'canonical_name': 'Biosynthetic Phase', 'concept_id': 'BIO-C13-03', 'chapter_id': 'c13', 'topic': 'Photosynthesis in Higher Plants'},
            'c3 cycle': {'canonical_name': 'Calvin Cycle', 'concept_id': 'BIO-C13-04', 'chapter_id': 'c13', 'topic': 'Photosynthesis in Higher Plants'},
            'calvin cycle': {'canonical_name': 'Calvin Cycle', 'concept_id': 'BIO-C13-04', 'chapter_id': 'c13', 'topic': 'Photosynthesis in Higher Plants'},
            'c4 cycle': {'canonical_name': 'Hatch and Slack Pathway', 'concept_id': 'BIO-C13-05', 'chapter_id': 'c13', 'topic': 'Photosynthesis in Higher Plants'},
            'kranz anatomy': {'canonical_name': 'Hatch and Slack Pathway', 'concept_id': 'BIO-C13-05', 'chapter_id': 'c13', 'topic': 'Photosynthesis in Higher Plants'},

            # Cellular Respiration (Chapter 12/14)
            'site of cellular respiration': {'canonical_name': 'Mitochondria', 'concept_id': 'BIO-C08-01', 'chapter_id': 'c08', 'topic': 'Cell Organelles'},
            'power currency of cell': {'canonical_name': 'ATP', 'concept_id': 'BIO-C14-01', 'chapter_id': 'c14', 'topic': 'Respiration in Plants'},
            'energy currency': {'canonical_name': 'ATP', 'concept_id': 'BIO-C14-01', 'chapter_id': 'c14', 'topic': 'Respiration in Plants'},
            'atp': {'canonical_name': 'ATP', 'concept_id': 'BIO-C14-01', 'chapter_id': 'c14', 'topic': 'Respiration in Plants'},
            'cellular respiration': {'canonical_name': 'Respiration in Plants', 'concept_id': 'BIO-C14-01', 'chapter_id': 'c14', 'topic': 'Respiration in Plants'},
            'respiration': {'canonical_name': 'Respiration in Plants', 'concept_id': 'BIO-C14-01', 'chapter_id': 'c14', 'topic': 'Respiration in Plants'},
            'glycolysis': {'canonical_name': 'Glycolysis', 'concept_id': 'BIO-C14-01', 'chapter_id': 'c14', 'topic': 'Respiration in Plants'},
            'emp pathway': {'canonical_name': 'Glycolysis', 'concept_id': 'BIO-C14-01', 'chapter_id': 'c14', 'topic': 'Respiration in Plants'},
            'emp': {'canonical_name': 'Glycolysis', 'concept_id': 'BIO-C14-01', 'chapter_id': 'c14', 'topic': 'Respiration in Plants'},
            'glycolytic pathway': {'canonical_name': 'Glycolysis', 'concept_id': 'BIO-C14-01', 'chapter_id': 'c14', 'topic': 'Respiration in Plants'},
            'atp yield': {'canonical_name': 'Glycolysis', 'concept_id': 'BIO-C14-01', 'chapter_id': 'c14', 'topic': 'Respiration in Plants'},
            'atp yield in glycolysis': {'canonical_name': 'Glycolysis', 'concept_id': 'BIO-C14-01', 'chapter_id': 'c14', 'topic': 'Respiration in Plants'},
            'glycolysis atp yield': {'canonical_name': 'Glycolysis', 'concept_id': 'BIO-C14-01', 'chapter_id': 'c14', 'topic': 'Respiration in Plants'},
            'krebs cycle': {'canonical_name': 'Krebs Cycle', 'concept_id': 'BIO-C14-02', 'chapter_id': 'c14', 'topic': 'Respiration in Plants'},
            'tca cycle': {'canonical_name': 'Krebs Cycle', 'concept_id': 'BIO-C14-02', 'chapter_id': 'c14', 'topic': 'Respiration in Plants'},
            'citric acid cycle': {'canonical_name': 'Krebs Cycle', 'concept_id': 'BIO-C14-02', 'chapter_id': 'c14', 'topic': 'Respiration in Plants'},

            # Structural Organisation in Animals & Cockroach (Chapter 7)
            'cockroach': {'canonical_name': 'Cockroach', 'concept_id': 'BIO-C07-04', 'chapter_id': 'c07', 'topic': 'Structural Organisation in Animals'},
            'cockroach chapter': {'canonical_name': 'Cockroach', 'concept_id': 'BIO-C07-04', 'chapter_id': 'c07', 'topic': 'Structural Organisation in Animals'},
            'periplaneta': {'canonical_name': 'Cockroach', 'concept_id': 'BIO-C07-04', 'chapter_id': 'c07', 'topic': 'Structural Organisation in Animals'},
            'periplaneta americana': {'canonical_name': 'Cockroach', 'concept_id': 'BIO-C07-04', 'chapter_id': 'c07', 'topic': 'Structural Organisation in Animals'},
            'malpighian tubules': {'canonical_name': 'Cockroach Excretion', 'concept_id': 'BIO-C07-04', 'chapter_id': 'c07', 'topic': 'Structural Organisation in Animals'},
            'ommatidia': {'canonical_name': 'Cockroach Vision', 'concept_id': 'BIO-C07-06', 'chapter_id': 'c07', 'topic': 'Structural Organisation in Animals'},
            'mosaic vision': {'canonical_name': 'Cockroach Vision', 'concept_id': 'BIO-C07-06', 'chapter_id': 'c07', 'topic': 'Structural Organisation in Animals'},
            'spiracles': {'canonical_name': 'Cockroach Respiration', 'concept_id': 'BIO-C07-05', 'chapter_id': 'c07', 'topic': 'Structural Organisation in Animals'},
            'structural organisation in animals': {'canonical_name': 'Structural Organisation in Animals', 'concept_id': 'BIO-C07-01', 'chapter_id': 'c07', 'topic': 'Structural Organisation in Animals'},
            'earthworm': {'canonical_name': 'Earthworm', 'concept_id': 'BIO-C04-05', 'chapter_id': 'c04', 'topic': 'Animal Kingdom'},
            'pheretima': {'canonical_name': 'Earthworm', 'concept_id': 'BIO-C04-05', 'chapter_id': 'c04', 'topic': 'Animal Kingdom'},
            'common indian earthworm': {'canonical_name': 'Earthworm', 'concept_id': 'BIO-C04-05', 'chapter_id': 'c04', 'topic': 'Animal Kingdom'},
            'annelid': {'canonical_name': 'Earthworm', 'concept_id': 'BIO-C04-05', 'chapter_id': 'c04', 'topic': 'Animal Kingdom'},
            'annelida': {'canonical_name': 'Earthworm', 'concept_id': 'BIO-C04-05', 'chapter_id': 'c04', 'topic': 'Animal Kingdom'},
            'frog': {'canonical_name': 'Frog', 'concept_id': 'BIO-C04-06', 'chapter_id': 'c04', 'topic': 'Animal Kingdom'},
            'indian frog': {'canonical_name': 'Frog', 'concept_id': 'BIO-C04-06', 'chapter_id': 'c04', 'topic': 'Animal Kingdom'},
            'rana tigrina': {'canonical_name': 'Frog', 'concept_id': 'BIO-C04-06', 'chapter_id': 'c04', 'topic': 'Animal Kingdom'},
            'toad': {'canonical_name': 'Frog', 'concept_id': 'BIO-C04-06', 'chapter_id': 'c04', 'topic': 'Animal Kingdom'},

            # Neural Control & Nervous System (Chapter 18/21)
            'brain': {'canonical_name': 'Brain', 'concept_id': 'BIO-C21-01', 'chapter_id': 'c21', 'topic': 'Neural Control and Coordination'},
            'human brain': {'canonical_name': 'Brain', 'concept_id': 'BIO-C21-01', 'chapter_id': 'c21', 'topic': 'Neural Control and Coordination'},
            'forebrain': {'canonical_name': 'Brain', 'concept_id': 'BIO-C21-01', 'chapter_id': 'c21', 'topic': 'Neural Control and Coordination'},
            'cerebrum': {'canonical_name': 'Brain', 'concept_id': 'BIO-C21-01', 'chapter_id': 'c21', 'topic': 'Neural Control and Coordination'},
            'cerebellum': {'canonical_name': 'Brain', 'concept_id': 'BIO-C21-01', 'chapter_id': 'c21', 'topic': 'Neural Control and Coordination'},
            'medulla': {'canonical_name': 'Brain', 'concept_id': 'BIO-C21-01', 'chapter_id': 'c21', 'topic': 'Neural Control and Coordination'},
            'neuron': {'canonical_name': 'Neuron', 'concept_id': 'BIO-C21-01', 'chapter_id': 'c21', 'topic': 'Neural Control and Coordination'},
            'longest cell in human body': {'canonical_name': 'Neuron', 'concept_id': 'BIO-C21-01', 'chapter_id': 'c21', 'topic': 'Neural Control and Coordination'},
            'structural and functional unit of nervous system': {'canonical_name': 'Neuron', 'concept_id': 'BIO-C21-01', 'chapter_id': 'c21', 'topic': 'Neural Control and Coordination'},
            'master clock': {'canonical_name': 'Suprachiasmatic Nucleus', 'concept_id': 'BIO-C21-02', 'chapter_id': 'c21', 'topic': 'Neural Control and Coordination'},

            # Cell Cycle & Division (Chapter 10)
            'cell division': {'canonical_name': 'Cell Cycle and Cell Division', 'concept_id': 'BIO-C10-01', 'chapter_id': 'c10', 'topic': 'Cell Cycle and Cell Division'},
            'cell cycle': {'canonical_name': 'Cell Cycle and Cell Division', 'concept_id': 'BIO-C10-01', 'chapter_id': 'c10', 'topic': 'Cell Cycle and Cell Division'},
            'mitosis': {'canonical_name': 'Mitosis', 'concept_id': 'BIO-C10-02', 'chapter_id': 'c10', 'topic': 'Cell Cycle and Cell Division'},
            'equational division': {'canonical_name': 'Mitosis', 'concept_id': 'BIO-C10-02', 'chapter_id': 'c10', 'topic': 'Cell Cycle and Cell Division'},
            'meiosis': {'canonical_name': 'Meiosis', 'concept_id': 'BIO-C10-01', 'chapter_id': 'c10', 'topic': 'Cell Cycle and Cell Division'},
            'reduction division': {'canonical_name': 'Meiosis', 'concept_id': 'BIO-C10-01', 'chapter_id': 'c10', 'topic': 'Cell Cycle and Cell Division'},
            'crossing over': {'canonical_name': 'Crossing Over in Pachytene', 'concept_id': 'BIO-C10-01', 'chapter_id': 'c10', 'topic': 'Cell Cycle and Cell Division'},
            'pachytene': {'canonical_name': 'Crossing Over in Pachytene', 'concept_id': 'BIO-C10-01', 'chapter_id': 'c10', 'topic': 'Cell Cycle and Cell Division'},

            # Genetics & Molecular Biology (Class 12 Chapters 4 & 5 / c04, c05)
            'dna': {'canonical_name': 'DNA', 'concept_id': 'BIO-C06-01', 'chapter_id': 'c06', 'topic': 'Molecular Basis of Inheritance'},
            'dna replication': {'canonical_name': 'DNA Replication', 'concept_id': 'BIO-C06-02', 'chapter_id': 'c06', 'topic': 'Molecular Basis of Inheritance'},
            'semi conservative replication': {'canonical_name': 'DNA Replication', 'concept_id': 'BIO-C06-02', 'chapter_id': 'c06', 'topic': 'Molecular Basis of Inheritance'},
            'hereditary material': {'canonical_name': 'DNA', 'concept_id': 'BIO-C06-01', 'chapter_id': 'c06', 'topic': 'Molecular Basis of Inheritance'},
            'gene': {'canonical_name': 'Gene', 'concept_id': 'BIO-C05-01', 'chapter_id': 'c05', 'topic': 'Principles of Inheritance and Variation'},
            'unit of inheritance': {'canonical_name': 'Gene', 'concept_id': 'BIO-C05-01', 'chapter_id': 'c05', 'topic': 'Principles of Inheritance and Variation'},
            'father of genetics': {'canonical_name': 'Gregor Mendel', 'concept_id': 'BIO-C05-02', 'chapter_id': 'c05', 'topic': 'Principles of Inheritance and Variation'},
            'mendel': {'canonical_name': 'Gregor Mendel', 'concept_id': 'BIO-C05-02', 'chapter_id': 'c05', 'topic': 'Principles of Inheritance and Variation'},
            'jumping genes': {'canonical_name': 'Transposons', 'concept_id': 'BIO-C06-03', 'chapter_id': 'c06', 'topic': 'Molecular Basis of Inheritance'},

            # Human Physiology (Circulation, Excretion, Endocrine, Digestion, Locomotion)
            'pacemaker of heart': {'canonical_name': 'SA Node', 'concept_id': 'BIO-C18-02', 'chapter_id': 'c18', 'topic': 'Body Fluids and Circulation'},
            'heart': {'canonical_name': 'Cardiac Cycle', 'concept_id': 'BIO-C18-01', 'chapter_id': 'c18', 'topic': 'Body Fluids and Circulation'},
            'blood': {'canonical_name': 'Blood Composition', 'concept_id': 'BIO-C18-01', 'chapter_id': 'c18', 'topic': 'Body Fluids and Circulation'},
            'graveyard of rbc': {'canonical_name': 'Spleen', 'concept_id': 'BIO-C18-03', 'chapter_id': 'c18', 'topic': 'Body Fluids and Circulation'},
            'graveyard of rbcs': {'canonical_name': 'Spleen', 'concept_id': 'BIO-C18-03', 'chapter_id': 'c18', 'topic': 'Body Fluids and Circulation'},
            'kidney': {'canonical_name': 'Excretory Products and Elimination', 'concept_id': 'BIO-C19-01', 'chapter_id': 'c19', 'topic': 'Excretory Products and their Elimination'},
            'nephron': {'canonical_name': 'Nephron', 'concept_id': 'BIO-C19-01', 'chapter_id': 'c19', 'topic': 'Excretory Products and their Elimination'},
            'structural and functional unit of kidney': {'canonical_name': 'Nephron', 'concept_id': 'BIO-C19-01', 'chapter_id': 'c19', 'topic': 'Excretory Products and their Elimination'},
            'bone': {'canonical_name': 'Locomotion and Movement', 'concept_id': 'BIO-C20-01', 'chapter_id': 'c20', 'topic': 'Locomotion and Movement'},
            'bones': {'canonical_name': 'Locomotion and Movement', 'concept_id': 'BIO-C20-01', 'chapter_id': 'c20', 'topic': 'Locomotion and Movement'},
            'skeleton': {'canonical_name': 'Locomotion and Movement', 'concept_id': 'BIO-C20-01', 'chapter_id': 'c20', 'topic': 'Locomotion and Movement'},
            'master gland': {'canonical_name': 'Pituitary Gland', 'concept_id': 'BIO-C22-01', 'chapter_id': 'c22', 'topic': 'Chemical Coordination'},
            'master gland of human endocrine system': {'canonical_name': 'Pituitary Gland', 'concept_id': 'BIO-C22-01', 'chapter_id': 'c22', 'topic': 'Chemical Coordination'},
            'blood sugar hormone': {'canonical_name': 'Insulin', 'concept_id': 'BIO-C22-01', 'chapter_id': 'c22', 'topic': 'Chemical Coordination'},
            'insulin': {'canonical_name': 'Insulin', 'concept_id': 'BIO-C22-01', 'chapter_id': 'c22', 'topic': 'Chemical Coordination'},
            'emergency hormone': {'canonical_name': 'Adrenaline', 'concept_id': 'BIO-C22-03', 'chapter_id': 'c22', 'topic': 'Endocrine Glands'},
            'fight or flight hormone': {'canonical_name': 'Adrenaline', 'concept_id': 'BIO-C22-03', 'chapter_id': 'c22', 'topic': 'Endocrine Glands'},
            'pregnancy hormone': {'canonical_name': 'Progesterone', 'concept_id': 'BIO-C03-01', 'chapter_id': 'c03', 'topic': 'Human Reproduction'},
            'birth hormone': {'canonical_name': 'Oxytocin', 'concept_id': 'BIO-C22-04', 'chapter_id': 'c22', 'topic': 'Endocrine Glands'},
            'milk let down hormone': {'canonical_name': 'Oxytocin', 'concept_id': 'BIO-C22-04', 'chapter_id': 'c22', 'topic': 'Endocrine Glands'},
            'anti diuretic hormone': {'canonical_name': 'Vasopressin', 'concept_id': 'BIO-C22-05', 'chapter_id': 'c22', 'topic': 'Endocrine Glands'},
            'sleep hormone': {'canonical_name': 'Melatonin', 'concept_id': 'BIO-C22-06', 'chapter_id': 'c22', 'topic': 'Endocrine Glands'},
            'largest gland': {'canonical_name': 'Liver', 'concept_id': 'BIO-C16-01', 'chapter_id': 'c16', 'topic': 'Digestion and Absorption'},
            'largest organ': {'canonical_name': 'Skin', 'concept_id': 'BIO-C07-01', 'chapter_id': 'c07', 'topic': 'Structural Organisation in Animals'},
            'largest internal organ': {'canonical_name': 'Liver', 'concept_id': 'BIO-C16-01', 'chapter_id': 'c16', 'topic': 'Digestion and Absorption'},
            'building blocks of proteins': {'canonical_name': 'Amino Acids', 'concept_id': 'BIO-C09-01', 'chapter_id': 'c09', 'topic': 'Biomolecules'},
            'molecular scissors': {'canonical_name': 'Restriction Endonucleases', 'concept_id': 'BIO-C11-02', 'chapter_id': 'c11', 'topic': 'Biotechnology: Principles and Processes'},
            'chemical scalpels': {'canonical_name': 'Restriction Endonucleases', 'concept_id': 'BIO-C11-02', 'chapter_id': 'c11', 'topic': 'Biotechnology: Principles and Processes'},
            'amphibians of plant kingdom': {'canonical_name': 'Bryophytes', 'concept_id': 'BIO-C03-02', 'chapter_id': 'c03', 'topic': 'Plant Kingdom'},
            'reptiles of plant kingdom': {'canonical_name': 'Pteridophytes', 'concept_id': 'BIO-C03-03', 'chapter_id': 'c03', 'topic': 'Plant Kingdom'},

            # High-frequency NEET terms that TF-IDF alone misroutes (beast hardening)
            'fluid mosaic model': {'canonical_name': 'Plasma Membrane', 'concept_id': 'BIO-C08-02', 'chapter_id': 'c08', 'topic': 'Cell Organelles'},
            'plasma membrane': {'canonical_name': 'Plasma Membrane', 'concept_id': 'BIO-C08-02', 'chapter_id': 'c08', 'topic': 'Cell Organelles'},
            'peptide bond': {'canonical_name': 'Amino Acids', 'concept_id': 'BIO-C09-01', 'chapter_id': 'c09', 'topic': 'Biomolecules'},
            'prophase': {'canonical_name': 'Mitosis', 'concept_id': 'BIO-C10-02', 'chapter_id': 'c10', 'topic': 'Cell Cycle and Cell Division'},
            'z scheme': {'canonical_name': 'Photochemical Phase', 'concept_id': 'BIO-C13-02', 'chapter_id': 'c13', 'topic': 'Photosynthesis in Higher Plants'},
            'z-scheme': {'canonical_name': 'Photochemical Phase', 'concept_id': 'BIO-C13-02', 'chapter_id': 'c13', 'topic': 'Photosynthesis in Higher Plants'},
            'photosystem': {'canonical_name': 'Photochemical Phase', 'concept_id': 'BIO-C13-02', 'chapter_id': 'c13', 'topic': 'Photosynthesis in Higher Plants'},
            'stroma': {'canonical_name': 'Calvin Cycle', 'concept_id': 'BIO-C13-04', 'chapter_id': 'c13', 'topic': 'Photosynthesis in Higher Plants'},
            'rubisco': {'canonical_name': 'Calvin Cycle', 'concept_id': 'BIO-C13-04', 'chapter_id': 'c13', 'topic': 'Photosynthesis in Higher Plants'},
            'pyruvate': {'canonical_name': 'Glycolysis', 'concept_id': 'BIO-C14-01', 'chapter_id': 'c14', 'topic': 'Respiration in Plants'},
            'atp synthase': {'canonical_name': 'ATP', 'concept_id': 'BIO-C14-01', 'chapter_id': 'c14', 'topic': 'Respiration in Plants'},
            'apical dominance': {'canonical_name': 'Plant Growth Regulators', 'concept_id': 'BIO-C15-01', 'chapter_id': 'c15', 'topic': 'Plant Growth and Development'},
            'vernalization': {'canonical_name': 'Plant Growth Regulators', 'concept_id': 'BIO-C15-01', 'chapter_id': 'c15', 'topic': 'Plant Growth and Development'},
            'dental formula': {'canonical_name': 'Digestion and Absorption', 'concept_id': 'BIO-C16-01', 'chapter_id': 'c16', 'topic': 'Digestion and Absorption'},
            'teeth': {'canonical_name': 'Digestion and Absorption', 'concept_id': 'BIO-C16-01', 'chapter_id': 'c16', 'topic': 'Digestion and Absorption'},
            'emulsification': {'canonical_name': 'Digestion and Absorption', 'concept_id': 'BIO-C16-01', 'chapter_id': 'c16', 'topic': 'Digestion and Absorption'},
            'tidal volume': {'canonical_name': 'Breathing Mechanism', 'concept_id': 'BIO-C17-01', 'chapter_id': 'c17', 'topic': 'Breathing and Exchange of Gases'},
            'vital capacity': {'canonical_name': 'Breathing Mechanism', 'concept_id': 'BIO-C17-01', 'chapter_id': 'c17', 'topic': 'Breathing and Exchange of Gases'},
            'diastole': {'canonical_name': 'Cardiac Cycle', 'concept_id': 'BIO-C18-01', 'chapter_id': 'c18', 'topic': 'Body Fluids and Circulation'},
            'systole': {'canonical_name': 'Cardiac Cycle', 'concept_id': 'BIO-C18-01', 'chapter_id': 'c18', 'topic': 'Body Fluids and Circulation'},
            'pacemaker': {'canonical_name': 'SA Node', 'concept_id': 'BIO-C18-02', 'chapter_id': 'c18', 'topic': 'Body Fluids and Circulation'},
            'sa node': {'canonical_name': 'SA Node', 'concept_id': 'BIO-C18-02', 'chapter_id': 'c18', 'topic': 'Body Fluids and Circulation'},
            'sinoatrial node': {'canonical_name': 'SA Node', 'concept_id': 'BIO-C18-02', 'chapter_id': 'c18', 'topic': 'Body Fluids and Circulation'},
            'gfr': {'canonical_name': 'Nephron', 'concept_id': 'BIO-C19-01', 'chapter_id': 'c19', 'topic': 'Excretory Products and their Elimination'},
            'glomerular filtration rate': {'canonical_name': 'Nephron', 'concept_id': 'BIO-C19-01', 'chapter_id': 'c19', 'topic': 'Excretory Products and their Elimination'},
            'countercurrent': {'canonical_name': 'Nephron', 'concept_id': 'BIO-C19-01', 'chapter_id': 'c19', 'topic': 'Excretory Products and their Elimination'},
            'countercurrent mechanism': {'canonical_name': 'Nephron', 'concept_id': 'BIO-C19-01', 'chapter_id': 'c19', 'topic': 'Excretory Products and their Elimination'},
            'uric acid': {'canonical_name': 'Nephron', 'concept_id': 'BIO-C19-01', 'chapter_id': 'c19', 'topic': 'Excretory Products and their Elimination'},
            'action potential': {'canonical_name': 'Neuron', 'concept_id': 'BIO-C21-01', 'chapter_id': 'c21', 'topic': 'Neural Control and Coordination'},
            'acetylcholine': {'canonical_name': 'Neuron', 'concept_id': 'BIO-C21-01', 'chapter_id': 'c21', 'topic': 'Neural Control and Coordination'},
            'pituitary': {'canonical_name': 'Pituitary Gland', 'concept_id': 'BIO-C22-01', 'chapter_id': 'c22', 'topic': 'Chemical Coordination'},
            'diabetes': {'canonical_name': 'Insulin', 'concept_id': 'BIO-C22-01', 'chapter_id': 'c22', 'topic': 'Chemical Coordination'},
            'diabetes mellitus': {'canonical_name': 'Insulin', 'concept_id': 'BIO-C22-01', 'chapter_id': 'c22', 'topic': 'Chemical Coordination'},
            'spermiogenesis': {'canonical_name': 'Spermiogenesis', 'concept_id': 'BIO-C24-01', 'chapter_id': 'c24', 'topic': 'Human Reproduction'},
            'spermatid': {'canonical_name': 'Spermiogenesis', 'concept_id': 'BIO-C24-01', 'chapter_id': 'c24', 'topic': 'Human Reproduction'},
            'seminiferous tubules': {'canonical_name': 'Spermiogenesis', 'concept_id': 'BIO-C24-01', 'chapter_id': 'c24', 'topic': 'Human Reproduction'},
            'uterus': {'canonical_name': 'Human Reproduction', 'concept_id': 'BIO-C24-02', 'chapter_id': 'c24', 'topic': 'Human Reproduction'},
            'iud': {'canonical_name': 'Contraception', 'concept_id': 'BIO-C25-01', 'chapter_id': 'c25', 'topic': 'Reproductive Health'},
            'iuds': {'canonical_name': 'Contraception', 'concept_id': 'BIO-C25-01', 'chapter_id': 'c25', 'topic': 'Reproductive Health'},
            'copper-t': {'canonical_name': 'Contraception', 'concept_id': 'BIO-C25-01', 'chapter_id': 'c25', 'topic': 'Reproductive Health'},
            'allele': {'canonical_name': 'Gene', 'concept_id': 'BIO-C05-01', 'chapter_id': 'c05', 'topic': 'Principles of Inheritance and Variation'},
            'lactose': {'canonical_name': 'Lac Operon', 'concept_id': 'BIO-C27-01', 'chapter_id': 'c27', 'topic': 'Molecular Basis of Inheritance'},
            'meselson': {'canonical_name': 'DNA Replication', 'concept_id': 'BIO-C06-02', 'chapter_id': 'c06', 'topic': 'Molecular Basis of Inheritance'},
            'meselson and stahl': {'canonical_name': 'DNA Replication', 'concept_id': 'BIO-C06-02', 'chapter_id': 'c06', 'topic': 'Molecular Basis of Inheritance'},
            'meselson-stahl experiment': {'canonical_name': 'DNA Replication', 'concept_id': 'BIO-C06-02', 'chapter_id': 'c06', 'topic': 'Molecular Basis of Inheritance'},
            'vntr': {'canonical_name': 'DNA Fingerprinting', 'concept_id': 'BIO-C27-02', 'chapter_id': 'c27', 'topic': 'Molecular Basis of Inheritance'},
            'mrna': {'canonical_name': 'Transcription', 'concept_id': 'BIO-C27-03', 'chapter_id': 'c27', 'topic': 'Molecular Basis of Inheritance'},
            'malaria': {'canonical_name': 'Malaria', 'concept_id': 'BIO-C29-01', 'chapter_id': 'c29', 'topic': 'Human Health and Disease'},
            'plasmodium': {'canonical_name': 'Malaria', 'concept_id': 'BIO-C29-01', 'chapter_id': 'c29', 'topic': 'Human Health and Disease'},
            'antibody': {'canonical_name': 'Immunity', 'concept_id': 'BIO-C29-02', 'chapter_id': 'c29', 'topic': 'Human Health and Disease'},
            'bod': {'canonical_name': 'Sewage Treatment', 'concept_id': 'BIO-C30-01', 'chapter_id': 'c30', 'topic': 'Microbes in Human Welfare'},
            'biological oxygen demand': {'canonical_name': 'Sewage Treatment', 'concept_id': 'BIO-C30-01', 'chapter_id': 'c30', 'topic': 'Microbes in Human Welfare'},
            'sewage': {'canonical_name': 'Sewage Treatment', 'concept_id': 'BIO-C30-01', 'chapter_id': 'c30', 'topic': 'Microbes in Human Welfare'},
            'methanogen': {'canonical_name': 'Biogas', 'concept_id': 'BIO-C30-03', 'chapter_id': 'c30', 'topic': 'Microbes in Human Welfare'},
            'logistic growth': {'canonical_name': 'Population Growth', 'concept_id': 'BIO-C33-01', 'chapter_id': 'c33', 'topic': 'Organisms and Populations'},
            'carrying capacity': {'canonical_name': 'Population Growth', 'concept_id': 'BIO-C33-01', 'chapter_id': 'c33', 'topic': 'Organisms and Populations'},
            'commensalism': {'canonical_name': 'Population Interactions', 'concept_id': 'BIO-C33-02', 'chapter_id': 'c33', 'topic': 'Organisms and Populations'},
            'mutualism': {'canonical_name': 'Population Interactions', 'concept_id': 'BIO-C33-02', 'chapter_id': 'c33', 'topic': 'Organisms and Populations'},
            'ecological succession': {'canonical_name': 'Ecological Succession', 'concept_id': 'BIO-C34-01', 'chapter_id': 'c34', 'topic': 'Ecosystem'},
            'pioneer': {'canonical_name': 'Ecological Succession', 'concept_id': 'BIO-C34-01', 'chapter_id': 'c34', 'topic': 'Ecosystem'},
            'pioneer species': {'canonical_name': 'Ecological Succession', 'concept_id': 'BIO-C34-01', 'chapter_id': 'c34', 'topic': 'Ecosystem'},
            'ommatidia': {'canonical_name': 'Cockroach Vision', 'concept_id': 'BIO-C07-06', 'chapter_id': 'c07', 'topic': 'Structural Organisation in Animals'},
            'endosperm': {'canonical_name': 'Double Fertilization', 'concept_id': 'BIO-C23-01', 'chapter_id': 'c23', 'topic': 'Sexual Reproduction in Flowering Plants'},
            'stigma': {'canonical_name': 'Pollination', 'concept_id': 'BIO-C23-02', 'chapter_id': 'c23', 'topic': 'Sexual Reproduction in Flowering Plants'},
            'aestivation': {'canonical_name': 'Flower Morphology', 'concept_id': 'BIO-C05-03', 'chapter_id': 'c05', 'topic': 'Morphology of Flowering Plants'},
            'myasthenia gravis': {'canonical_name': 'Muscle Disorders', 'concept_id': 'BIO-C20-02', 'chapter_id': 'c20', 'topic': 'Locomotion and Movement'},
            'gout': {'canonical_name': 'Joints', 'concept_id': 'BIO-C20-03', 'chapter_id': 'c20', 'topic': 'Locomotion and Movement'},
        }

        # Common typos mapped to corrected terms
        self.TYPO_MAP = {
            'mitocondria': 'mitochondria',
            'mitocondrion': 'mitochondrion',
            'mitochondrian': 'mitochondria',
            'mitochodria': 'mitochondria',
            'criste': 'cristae',
            'cristae': 'cristae',
            'crista': 'cristae',
            'fotosynthesis': 'photosynthesis',
            'photosynthesys': 'photosynthesis',
            'chroloplast': 'chloroplast',
            'chloroplats': 'chloroplast',
            'respiraton': 'respiration',
            'glcolysis': 'glycolysis',
            'ribosom': 'ribosome',
            'nefron': 'nephron',
            'dialisis': 'dialysis',
            'sarcomere': 'sarcomere',
            'sercomere': 'sarcomere',
            'meiossis': 'meiosis',
            'mitossis': 'mitosis'
        }

        self._load_dynamic_concepts_from_index()

    def _load_dynamic_concepts_from_index(self):
        """Loads concepts discovered in NCERT textbook chunks into normalizer."""
        if not INDEX_FILE.exists():
            return
        try:
            with open(INDEX_FILE, "r", encoding="utf-8") as f:
                chunks = json.load(f)
            for c in chunks:
                chap_num = c.get("chapter_number", 1)
                chap_id = f"c{chap_num:02d}"
                for concept in c.get("concepts", []):
                    c_key = concept.lower().strip()
                    if c_key and c_key not in self.CONCEPT_ALIASES:
                        self.CONCEPT_ALIASES[c_key] = {
                            "canonical_name": concept,
                            "concept_id": f"NCERT-{chap_id.upper()}-{concept.upper()[:6]}",
                            "chapter_id": chap_id,
                            "topic": c.get("chapter_title", "NCERT Biology")
                        }
        except Exception:
            pass

    def correct_typos(self, text: str) -> str:
        """Corrects known biology typos."""
        tokens = text.split()
        corrected = []
        for t in tokens:
            cleaned = re.sub(r'[^\w]', '', t).lower()
            if cleaned in self.TYPO_MAP:
                rep = self.TYPO_MAP[cleaned]
                # Preserve punctuation
                corrected.append(t.lower().replace(cleaned, rep))
            else:
                corrected.append(t)
        return " ".join(corrected)

    def normalize(self, query: str) -> Dict[str, dict]:
        """
        Detects known aliases and concepts in a query and returns matched concept info.
        Handles variations with articles ('the', 'a', 'an'), typos, and punctuation.
        """
        matches = {}
        cleaned_query = self.correct_typos(query or "")
        query_clean = re.sub(r"[^\w\s]", " ", cleaned_query.lower())
        query_no_articles = re.sub(r"\b(the|a|an)\b", " ", query_clean)
        query_compact = " ".join(query_no_articles.split())

        for alias, info in self.CONCEPT_ALIASES.items():
            alias_clean = re.sub(r"[^\w\s]", " ", alias.lower())
            alias_no_articles = re.sub(r"\b(the|a|an)\b", " ", alias_clean)
            alias_compact = " ".join(alias_no_articles.split())

            if re.search(r'\b' + re.escape(alias_compact) + r'\b', query_compact):
                matches[alias] = info

        return matches

    def get_canonical_concept_name(self, query: str) -> Optional[str]:
        """
        Extracts the primary canonical biology concept from a query if present.
        """
        matches = self.normalize(query)
        if matches:
            # Prefer most specific match (multi-word concepts e.g. 'calvin cycle' over 'photosynthesis')
            best_alias = max(matches.keys(), key=lambda a: (len(a.split()), len(a)))
            return matches[best_alias].get("canonical_name")
        return None

    def get_aliases(self, concept_id: str) -> List[str]:
        """
        Returns all known aliases for a given concept ID.
        """
        return [alias for alias, info in self.CONCEPT_ALIASES.items() if info.get('concept_id') == concept_id]

    def expand_query_with_concepts(self, query: str) -> str:
        """
        Adds canonical terms to a query containing aliases to improve search recall.
        """
        expanded_query = query
        matches = self.normalize(query)
        for alias, info in matches.items():
            canonical_name = info['canonical_name']
            if canonical_name.lower() not in query.lower():
                expanded_query += f" ({canonical_name})"
        return expanded_query


concept_normalizer = BiologyConceptNormalizer()
