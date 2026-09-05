import pandas as pd

CHAPTER_MAPPING = {
    "c01": "The Living World",
    "c02": "Biological Classification",
    "c03": "Plant Kingdom",
    "c04": "Animal Kingdom",
    "c05": "Morphology of Flowering Plants",
    "c06": "Anatomy of Flowering Plants",
    "c07": "Structural Organisation in Animals",
    "c08": "Cell: The Unit of Life",
    "c09": "Biomolecules",
    "c10": "Cell Cycle and Cell Division",
    "c11": "Photosynthesis in Higher Plants",
    "c12": "Respiration in Plants",
    "c13": "Plant Growth and Development",
    "c14": "Digestion and Absorption",
    "c15": "Breathing and Exchange of Gases",
    "c16": "Body Fluids and Circulation",
    "c17": "Excretory Products and Their Elimination",
    "c18": "Locomotion and Movement",
    "c19": "Neural Control and Coordination",
    "c20": "Chemical Coordination and Integration",
    "c21": "Sexual Reproduction in Flowering Plants",
    "c22": "Human Reproduction",
    "c23": "Reproductive Health",
    "c24": "Principles of Inheritance and Variation",
    "c25": "Molecular Basis of Inheritance",
    "c26": "Evolution",
    "c27": "Human Health and Disease",
    "c28": "Microbes in Human Welfare",
    "c29": "Biotechnology: Principles and Processes",
    "c30": "Biotechnology and Its Applications",
    "c31": "Organisms and Populations",
    "c32": "Ecosystem",
    "c33": "Biodiversity and Conservation"
}

df = pd.read_csv('data/neet_knowledge_base.csv')
print("Initial records:", len(df))

# Standardize existing chapter names first. We can do string matching.
# We will just map by some keywords for existing records if chapter_id is wrong, OR we can just update chapter_name by mapping chapter_id?
# Wait, the instructions say:
# "The chapter_id mapping should be: c01=The Living World... "
# And "c12=Respiration in Plants (note: currently some use c13/c14 for these)"
# "just fix the chapter_name values where they're inconsistent."
# Let's map chapter_id based on the correct chapter_name, and then update chapter_name.

# Actually, the user says "preserve all existing IDs, just fix the chapter_name values where they're inconsistent"
# Wait, "The chapter_id mapping should be: c01=The Living World... c12=Respiration in Plants (note: currently some use c13/c14 for these)"
# This means I need to update the chapter_id for Respiration to c12, and then update chapter_name based on the new chapter_id.
# Let's see the current unique chapters and their IDs.
print(df[['chapter_id', 'chapter_name']].drop_duplicates().to_string())
