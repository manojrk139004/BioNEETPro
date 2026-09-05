import pandas as pd
import json

NAME_TO_STD = {
    "The Living World": "The Living World",
    "Biological Classification": "Biological Classification",
    "Plant Kingdom": "Plant Kingdom",
    "Animal Kingdom": "Animal Kingdom",
    "Morphology of Flowering Plants": "Morphology of Flowering Plants",
    "Anatomy of Flowering Plants": "Anatomy of Flowering Plants",
    "Structural Organisation in Animals": "Structural Organisation in Animals",
    "Cell - The Unit of Life": "Cell: The Unit of Life",
    "Cell: The Unit of Life": "Cell: The Unit of Life",
    "Biomolecules": "Biomolecules",
    "Cell Cycle and Cell Division": "Cell Cycle and Cell Division",
    "Photosynthesis": "Photosynthesis in Higher Plants",
    "Photosynthesis in Higher Plants": "Photosynthesis in Higher Plants",
    "Respiration in Plants": "Respiration in Plants",
    "Plant Growth and Development": "Plant Growth and Development",
    "Digestion and Absorption": "Digestion and Absorption",
    "Breathing and Exchange of Gases": "Breathing and Exchange of Gases",
    "Body Fluids and Circulation": "Body Fluids and Circulation",
    "Excretory Products and Elimination": "Excretory Products and Their Elimination",
    "Excretory Products and Their Elimination": "Excretory Products and Their Elimination",
    "Locomotion and Movement": "Locomotion and Movement",
    "Neural Control and Coordination": "Neural Control and Coordination",
    "Chemical Coordination and Integration": "Chemical Coordination and Integration",
    "Sexual Reproduction in Flowering Plants": "Sexual Reproduction in Flowering Plants",
    "Human Reproduction": "Human Reproduction",
    "Reproductive Health": "Reproductive Health",
    "Principles of Inheritance": "Principles of Inheritance and Variation",
    "Principles of Inheritance and Variation": "Principles of Inheritance and Variation",
    "Molecular Basis of Inheritance": "Molecular Basis of Inheritance",
    "Evolution": "Evolution",
    "Human Health and Disease": "Human Health and Disease",
    "Microbes in Human Welfare": "Microbes in Human Welfare",
    "Biotechnology - Principles": "Biotechnology: Principles and Processes",
    "Biotechnology: Principles and Processes": "Biotechnology: Principles and Processes",
    "Biotechnology and its Applications": "Biotechnology and Its Applications",
    "Biotechnology and Its Applications": "Biotechnology and Its Applications",
    "Organisms and Populations": "Organisms and Populations",
    "Ecosystem": "Ecosystem",
    "Biodiversity and Conservation": "Biodiversity and Conservation"
}

STD_TO_ID = {
    "The Living World": "c01",
    "Biological Classification": "c02",
    "Plant Kingdom": "c03",
    "Animal Kingdom": "c04",
    "Morphology of Flowering Plants": "c05",
    "Anatomy of Flowering Plants": "c06",
    "Structural Organisation in Animals": "c07",
    "Cell: The Unit of Life": "c08",
    "Biomolecules": "c09",
    "Cell Cycle and Cell Division": "c10",
    "Photosynthesis in Higher Plants": "c11",
    "Respiration in Plants": "c12",
    "Plant Growth and Development": "c13",
    "Digestion and Absorption": "c14",
    "Breathing and Exchange of Gases": "c15",
    "Body Fluids and Circulation": "c16",
    "Excretory Products and Their Elimination": "c17",
    "Locomotion and Movement": "c18",
    "Neural Control and Coordination": "c19",
    "Chemical Coordination and Integration": "c20",
    "Sexual Reproduction in Flowering Plants": "c21",
    "Human Reproduction": "c22",
    "Reproductive Health": "c23",
    "Principles of Inheritance and Variation": "c24",
    "Molecular Basis of Inheritance": "c25",
    "Evolution": "c26",
    "Human Health and Disease": "c27",
    "Microbes in Human Welfare": "c28",
    "Biotechnology: Principles and Processes": "c29",
    "Biotechnology and Its Applications": "c30",
    "Organisms and Populations": "c31",
    "Ecosystem": "c32",
    "Biodiversity and Conservation": "c33"
}

df = pd.read_csv('data/neet_knowledge_base.csv')

def fix_row(row):
    old_name = row['chapter_name'].strip()
    if old_name in NAME_TO_STD:
        std_name = NAME_TO_STD[old_name]
        row['chapter_name'] = std_name
        row['chapter_id'] = STD_TO_ID[std_name]
    else:
        print(f"UNKNOWN CHAPTER: {old_name}")
    return row

df = df.apply(fix_row, axis=1)

df.to_csv('data/neet_knowledge_base.csv', index=False)
print("Updated existing records.")
print("Total rows:", len(df))
print("Unique chapters:", df['chapter_name'].nunique())
print(df['chapter_name'].value_counts().to_string())
