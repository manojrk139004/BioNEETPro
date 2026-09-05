import pandas as pd
from pathlib import Path

csv_path = Path("data/concept_dependency_graph.csv")

new_data = """BIO-C03-01,Algae,BIO-C03-02,Bryophytes,PRECEDES,c03,Algae are evolutionary precursors to bryophytes
BIO-C03-02,Bryophytes,BIO-C03-03,Pteridophytes,PRECEDES,c03,Bryophytes precede pteridophytes in plant evolution
BIO-C03-03,Pteridophytes,BIO-C03-04,Gymnosperms,PRECEDES,c03,Pteridophytes precede gymnosperms
BIO-C03-04,Gymnosperms,BIO-C03-05,Angiosperms,PRECEDES,c03,Gymnosperms precede angiosperms
BIO-C03-01,Algae,BIO-C03-05,Angiosperms,CONTRASTS_WITH,c03,Simple thallus algae contrast with highly differentiated angiosperms
BIO-C04-01,Porifera,BIO-C04-02,Cnidaria,PRECEDES,c04,Cellular level porifera precede tissue level cnidaria
BIO-C04-02,Cnidaria,BIO-C04-03,Ctenophora,RELATED_TO,c04,Both exhibit radial symmetry and tissue level organization
BIO-C04-04,Platyhelminthes,BIO-C04-05,Aschelminthes,PRECEDES,c04,Acoelomate flatworms precede pseudocoelomate roundworms
BIO-C04-05,Aschelminthes,BIO-C04-06,Annelida,PRECEDES,c04,Pseudocoelomates precede true coelomate annelids
BIO-C04-06,Annelida,BIO-C04-07,Arthropoda,RELATED_TO,c04,Both exhibit metameric segmentation
BIO-C04-07,Arthropoda,BIO-C04-08,Mollusca,CONTRASTS_WITH,c04,Segmented arthropods contrast with unsegmented molluscs
BIO-C04-09,Echinodermata,BIO-C04-10,Hemichordata,PRECEDES,c04,Echinoderms share deuterostome affinity with hemichordates
BIO-C04-10,Hemichordata,BIO-C04-11,Chordata,PRECEDES,c04,Hemichordates are a connecting link to chordates
BIO-C05-01,Root System,BIO-C05-02,Stem System,RELATED_TO,c05,Root absorbs water while stem conducts it
BIO-C05-02,Stem System,BIO-C05-03,Leaf System,REQUIRED_FOR,c05,Stem provides support and vascular connection for leaves
BIO-C05-03,Leaf System,BIO-C05-04,Inflorescence and Flower,PRECEDES,c05,Vegetative leaves precede reproductive floral shoots
BIO-C05-04,Inflorescence and Flower,BIO-C05-05,Fruit and Seed,RESULTS_IN,c05,Floral fertilization results in fruit and seed formation
BIO-C02-01,Microsporogenesis,BIO-C02-02,Pollen Grains,RESULTS_IN,c02,Microsporogenesis produces pollen grains
BIO-C02-03,Megasporogenesis,BIO-C02-04,Embryo Sac,RESULTS_IN,c02,Megasporogenesis produces female gametophyte
BIO-C02-02,Pollen Grains,BIO-C02-05,Pollination,REQUIRED_FOR,c02,Pollen grains are transferred during pollination
BIO-C02-05,Pollination,BIO-C02-06,Double Fertilization,PRECEDES,c02,Pollination is prerequisite for fertilization in angiosperms
BIO-C02-06,Double Fertilization,BIO-C02-07,Endosperm and Embryo,RESULTS_IN,c02,Double fertilization yields diploid embryo and triploid endosperm
BIO-C24-01,Mendel's Laws,BIO-C25-01,DNA Structure,PREREQUISITE_OF,c24,Understanding inheritance patterns requires knowledge of DNA as hereditary material
BIO-C24-01,Mendel's Laws,BIO-C24-03,Incomplete Dominance,CONTRASTS_WITH,c24,Incomplete dominance deviates from classical Mendelian dominance
BIO-C24-04,Chromosomal Theory of Inheritance,BIO-C24-05,Linkage and Recombination,RELATED_TO,c24,Genes on same chromosome show linkage
BIO-C25-01,DNA Structure,BIO-C25-02,DNA Replication,REQUIRED_FOR,c25,Double helical structure explains semi-conservative replication
BIO-C25-02,DNA Replication,BIO-C25-03,Transcription,PRECEDES,c25,DNA must be accessible for transcription
BIO-C25-03,Transcription,BIO-C25-04,Translation,PRECEDES,c25,mRNA synthesis precedes protein synthesis
BIO-C25-04,Translation,BIO-C25-05,Gene Expression Regulation,RELATED_TO,c25,Translation is controlled by gene expression mechanisms
BIO-C26-02,Origin of Life,BIO-C26-03,Biological Evolution,PRECEDES,c26,Chemical evolution precedes biological evolution
BIO-C26-03,Biological Evolution,BIO-C26-01,Natural Selection,CAUSES,c26,Natural selection is a mechanism of evolution
BIO-C26-01,Natural Selection,BIO-C26-04,Speciation,CAUSES,c26,Natural selection acting on populations leads to speciation
BIO-C26-05,Hardy-Weinberg Principle,BIO-C26-01,Natural Selection,CONTRASTS_WITH,c26,Hardy-Weinberg assumes no selection while natural selection drives change
BIO-C26-06,Adaptive Radiation,BIO-C26-07,Convergent Evolution,CONTRASTS_WITH,c26,Divergent adaptive radiation contrasts with convergent evolution
BIO-C36-01,Organisms and Environment,BIO-C36-02,Populations,PART_OF,c36,Organisms constitute populations
BIO-C36-02,Populations,BIO-C36-03,Ecological Communities,PART_OF,c36,Interacting populations form communities
BIO-C36-03,Ecological Communities,BIO-C34-01,Ecosystem Structure,PART_OF,c34,Communities interact with abiotic factors to form ecosystems
BIO-C34-01,Ecosystem Structure,BIO-C34-03,Food Chains and Webs,RELATED_TO,c34,Ecosystems feature trophic structure like food webs
BIO-C34-03,Food Chains and Webs,BIO-C34-01,Ecosystem Productivity and Energy Flow,CAUSES,c34,Feeding relationships drive energy flow
BIO-C34-04,Ecological Pyramids,BIO-C34-02,10 Percent Law of Energy Transfer (Lindeman),EXAMPLE_OF,c34,Pyramid of energy illustrates the 10 percent law
BIO-C34-05,Ecological Succession,BIO-C34-06,Climax Community,RESULTS_IN,c34,Successional stages lead to a stable climax community
BIO-C34-07,Biogeochemical Cycles,BIO-C34-01,Ecosystem Structure,REQUIRED_FOR,c34,Nutrient cycling is vital for ecosystem functioning
BIO-C31-01,Tools of Recombinant DNA: Restriction Enzymes and pBR322,BIO-C31-02,Polymerase Chain Reaction (PCR),RELATED_TO,c31,Both are core techniques in genetic engineering
BIO-C31-02,Polymerase Chain Reaction (PCR),BIO-C31-03,Gene Cloning,REQUIRED_FOR,c31,Gene amplification is often needed before cloning
BIO-C31-03,Gene Cloning,BIO-C31-04,Downstream Processing,PRECEDES,c31,Cloning and expression precede product extraction
BIO-C31-04,Downstream Processing,BIO-C32-02,Genetically Engineered Human Insulin,REQUIRED_FOR,c32,Purification is necessary for commercial insulin production
BIO-C31-03,Gene Cloning,BIO-C32-03,Gene Therapy,REQUIRED_FOR,c32,Cloning vectors deliver genes in therapy
BIO-C16-01,Digestion and Pancreatic Secretions,BIO-C16-02,Absorption of Nutrients,PRECEDES,c16,Digestion breaks down food before absorption
BIO-C16-02,Absorption of Nutrients,BIO-C18-02,Blood Transport,REQUIRED_FOR,c16,Absorbed nutrients enter blood for transport
BIO-C18-02,Blood Transport,BIO-C14-03,Cellular Respiration,REQUIRED_FOR,c18,Blood delivers glucose and oxygen for respiration
BIO-C17-01,Mechanism of Breathing and Gas Exchange,BIO-C18-02,Blood Transport,PRECEDES,c17,Gas exchange oxygenates blood for transport
BIO-C18-02,Blood Transport,BIO-C19-01,Nephron Function and Countercurrent Mechanism,REQUIRED_FOR,c19,Blood circulation delivers waste to kidneys
BIO-C11-01,Light Reaction,BIO-C11-02,Calvin Cycle,PRECEDES,c11,Light reactions produce ATP and NADPH used by Calvin cycle
BIO-C11-02,Calvin Cycle,BIO-C11-03,Photorespiration,CONTRASTS_WITH,c11,Calvin cycle fixes CO2 while photorespiration wastes energy
BIO-C11-04,C4 Pathway,BIO-C11-03,Photorespiration,CONTRASTS_WITH,c11,C4 plants avoid photorespiration
BIO-C14-03,Cellular Respiration,BIO-C14-04,Fermentation,CONTRASTS_WITH,c14,Aerobic respiration contrasts with anaerobic fermentation
BIO-C14-01,EMP Pathway Reactions and ATP Yield,BIO-C14-04,Fermentation,PRECEDES,c14,Glycolysis precedes fermentation in absence of oxygen
BIO-C08-03,Cell Membrane Structure,BIO-C08-04,Active Transport,REQUIRED_FOR,c08,Fluid mosaic model enables transport proteins
BIO-C08-04,Active Transport,BIO-C08-05,Passive Transport,CONTRASTS_WITH,c08,Active requires ATP while passive does not
BIO-C10-02,Mitosis,BIO-C10-03,Meiosis,CONTRASTS_WITH,c10,Equational division contrasts with reductional division
BIO-C10-02,Mitosis,BIO-C10-04,Cell Cycle Regulation,RELATED_TO,c10,Checkpoints regulate mitotic progression
BIO-C08-06,Nucleus,BIO-C08-07,Ribosomes,REQUIRED_FOR,c08,Nucleolus synthesizes ribosomal RNA
BIO-C01-01,Asexual Reproduction,BIO-C01-02,Sexual Reproduction,CONTRASTS_WITH,c01,Clonal reproduction contrasts with genetic recombination
BIO-C01-02,Sexual Reproduction,BIO-C01-03,Gametogenesis,REQUIRED_FOR,c01,Gamete formation is essential for sexual reproduction
BIO-C01-03,Gametogenesis,BIO-C01-04,Syngamy,PRECEDES,c01,Gametes must form before they can fuse
BIO-C01-04,Syngamy,BIO-C01-05,Embryogenesis,PRECEDES,c01,Zygote formation precedes embryo development
"""

with open(csv_path, 'a', encoding='utf-8') as f:
    f.write(new_data)
print("done")
